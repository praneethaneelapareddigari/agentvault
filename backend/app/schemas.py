"""
Pydantic schemas — request/response contracts for the API,
and the strict structured-output schema the Intent Agent must fill in.
"""
from typing import Optional, Any
from pydantic import BaseModel, Field


# ---------- Intent ----------

class Intent(BaseModel):
    goal: str = Field(..., description="e.g. maximize_yield")
    asset: str = Field(..., description="e.g. USDC")
    amount: float = Field(..., gt=0)
    risk: str = Field(..., description="low | medium | high")
    max_gas: float = Field(..., ge=0)
    max_protocol_exposure: float = Field(..., gt=0)


# ---------- Requests ----------

class AgentRequestCreate(BaseModel):
    prompt: str
    wallet_address: Optional[str] = None  # real connected wallet, if any
    user_id: Optional[str] = None  # defaults to demo/wallet user if omitted


class PolicyUpdate(BaseModel):
    max_tx_usd: Optional[float] = None
    max_protocol_exposure_usd: Optional[float] = None
    max_gas_usd: Optional[float] = None
    allowed_chains: Optional[list[str]] = None
    allowed_protocols: Optional[list[str]] = None
    min_risk_score: Optional[int] = None
    approval_threshold_usd: Optional[float] = None


# ---------- Responses ----------

class StepStatus(BaseModel):
    label: str
    status: str  # pending | active | done | failed


class AgentRequestOut(BaseModel):
    id: str
    status: str
    raw_prompt: str
    parsed_intent: Optional[dict[str, Any]] = None
    steps: Optional[list[StepStatus]] = None

    class Config:
        from_attributes = True


class ExecutionPlanOut(BaseModel):
    id: str
    request_id: str
    protocol: str
    chain: str
    amount_usd: float
    expected_apy: float
    estimated_gas_usd: float
    risk_score: int
    policy_status: str
    policy_reasons: Optional[list[str]] = None
    simulation_status: str
    simulation_result: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class TransactionOut(BaseModel):
    id: str
    plan_id: str
    tx_hash: Optional[str]
    chain: str
    status: str
    block_number: Optional[int]
    explorer_url: Optional[str] = None

    class Config:
        from_attributes = True


class ActivityOut(BaseModel):
    id: str
    event_type: str
    detail: Optional[dict[str, Any]] = None
    created_at: str

    class Config:
        from_attributes = True
