"""
Agent pipeline router.

POST /api/agent/request runs the pipeline synchronously through:
  intent -> plan -> risk -> policy -> simulate -> awaiting_approval

For a hackathon demo this is simpler and more reliable than a background
job queue, and the "step status" list returned lets the frontend render the
same "Analyzing wallet / Searching protocols / ..." UI the product spec
calls for, without needing websockets.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app import models, schemas
from app.agents.intent_agent import extract_intent
from app.agents.planning_agent import build_plan, NoViableOpportunityError
from app.agents.verification_agent import verify_execution
from app.engines.policy_engine import evaluate_plan
from app.engines.simulator import simulate
from app.smart_wallet.mock_wallet import execute as wallet_execute

router = APIRouter(prefix="/api/agent", tags=["agent"])

STEP_LABELS = [
    "Understanding request",
    "Analyzing wallet",
    "Searching protocols",
    "Comparing opportunities",
    "Checking risk",
    "Validating policy",
    "Simulating transaction",
]


def _get_or_create_demo_user(db: Session) -> models.User:
    user = db.query(models.User).filter_by(wallet_address=settings.DEMO_WALLET_ADDRESS).first()
    if not user:
        user = models.User(wallet_address=settings.DEMO_WALLET_ADDRESS)
        db.add(user)
        db.commit()
        db.refresh(user)
        policy = models.Policy(
            user_id=user.id,
            max_tx_usd=500,
            max_protocol_exposure_usd=500,
            max_gas_usd=5,
            allowed_chains=settings.SUPPORTED_CHAINS,
            allowed_protocols=[],  # empty = "use allowlist from Risk Engine"
            min_risk_score=80,
            approval_threshold_usd=250,
        )
        db.add(policy)
        db.commit()
    return user


@router.post("/request", response_model=schemas.AgentRequestOut)
def create_agent_request(body: schemas.AgentRequestCreate, db: Session = Depends(get_db)):
    user = (
        db.query(models.User).filter_by(id=body.user_id).first()
        if body.user_id
        else _get_or_create_demo_user(db)
    )
    if not user:
        raise HTTPException(404, "User not found")

    policy = db.query(models.Policy).filter_by(user_id=user.id).first()
    if not policy:
        raise HTTPException(400, "User has no policy configured")

    steps = [{"label": l, "status": "pending"} for l in STEP_LABELS]
    req = models.AgentRequest(user_id=user.id, raw_prompt=body.prompt, status="parsing", steps=steps)
    db.add(req)
    db.commit()
    db.refresh(req)

    def mark(i: int, status: str):
        req.steps[i]["status"] = status
        db.add(models.ActivityLog(
            user_id=user.id, request_id=req.id,
            event_type=f"step:{STEP_LABELS[i]}", detail={"status": status},
        ))

    try:
        # Step 0: intent
        mark(0, "active")
        intent = extract_intent(body.prompt)
        req.parsed_intent = intent.model_dump()
        mark(0, "done")

        # Step 1-3: wallet + opportunities + comparison (handled inside build_plan)
        mark(1, "active"); mark(1, "done")
        mark(2, "active"); mark(2, "done")
        mark(3, "active")
        plan_data = build_plan(intent, user.wallet_address)
        mark(3, "done")

        # Step 4: risk (already computed in build_plan, just surface it)
        mark(4, "active"); mark(4, "done")

        # Step 5: policy
        mark(5, "active")
        policy_result = evaluate_plan(
            amount_usd=plan_data["amount_usd"],
            chain=plan_data["chain"],
            protocol=plan_data["protocol"],
            estimated_gas_usd=plan_data["estimated_gas_usd"],
            risk_score=plan_data["risk_score"],
            policy=policy,
        )
        mark(5, "done" if policy_result.passed else "failed")

        # Step 6: simulation (only bother if policy passed, but we still show it)
        mark(6, "active")
        sim_result = simulate(
            protocol=plan_data["protocol"],
            chain=plan_data["chain"],
            asset=plan_data["asset"],
            amount_usd=plan_data["amount_usd"],
            estimated_gas_usd=plan_data["estimated_gas_usd"],
        )
        mark(6, "done" if sim_result["success"] else "failed")

        plan = models.ExecutionPlan(
            request_id=req.id,
            protocol=plan_data["protocol"],
            chain=plan_data["chain"],
            amount_usd=plan_data["amount_usd"],
            expected_apy=plan_data["expected_apy"],
            estimated_gas_usd=plan_data["estimated_gas_usd"],
            risk_score=plan_data["risk_score"],
            policy_status="PASS" if policy_result.passed else "FAIL",
            policy_reasons=policy_result.reasons,
            simulation_status="PASS" if sim_result["success"] else "FAIL",
            simulation_result=sim_result,
        )
        db.add(plan)

        req.status = "awaiting_approval"
        db.commit()
        db.refresh(req)

    except NoViableOpportunityError as e:
        req.status = "failed"
        db.add(models.ActivityLog(
            user_id=user.id, request_id=req.id,
            event_type="pipeline_failed", detail={"reason": str(e)},
        ))
        db.commit()

    return req


@router.get("/request/{request_id}", response_model=schemas.AgentRequestOut)
def get_agent_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(models.AgentRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(404, "Not found")
    return req


@router.get("/request/{request_id}/plan", response_model=schemas.ExecutionPlanOut)
def get_plan(request_id: str, db: Session = Depends(get_db)):
    plan = db.query(models.ExecutionPlan).filter_by(request_id=request_id).first()
    if not plan:
        raise HTTPException(404, "No plan for this request")
    return plan


@router.post("/request/{request_id}/approve", response_model=schemas.TransactionOut)
def approve(request_id: str, db: Session = Depends(get_db)):
    req = db.query(models.AgentRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")
    plan = db.query(models.ExecutionPlan).filter_by(request_id=request_id).first()
    if not plan:
        raise HTTPException(404, "No plan for this request")

    if plan.policy_status != "PASS" or plan.simulation_status != "PASS":
        raise HTTPException(
            400,
            "Cannot approve: plan did not pass policy validation and/or simulation.",
        )

    tx_result = wallet_execute(plan)

    tx = models.Transaction(
        plan_id=plan.id,
        tx_hash=tx_result["tx_hash"],
        chain=plan.chain,
        status=tx_result["status"],
        block_number=tx_result["block_number"],
    )
    db.add(tx)

    verification = verify_execution(
        {"amount_usd": float(plan.amount_usd), "protocol": plan.protocol, "chain": plan.chain},
        tx_result,
    )

    req.status = "executed"
    db.add(models.ActivityLog(
        user_id=req.user_id, request_id=req.id,
        event_type="executed", detail={
            "tx_hash": tx_result["tx_hash"],
            "summary": verification["summary"],
        },
    ))
    db.commit()
    db.refresh(tx)
    return tx


@router.post("/request/{request_id}/reject", response_model=schemas.AgentRequestOut)
def reject(request_id: str, db: Session = Depends(get_db)):
    req = db.query(models.AgentRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")
    req.status = "rejected"
    db.add(models.ActivityLog(
        user_id=req.user_id, request_id=req.id, event_type="rejected", detail={},
    ))
    db.commit()
    db.refresh(req)
    return req
