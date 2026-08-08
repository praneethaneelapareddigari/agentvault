"""
SQLAlchemy models mirroring the AgentVault schema.

NOTE: Uses SQLite by default for zero-setup local/demo running.
Swap DATABASE_URL to a Postgres URL for production; no code changes needed.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    wallet_address = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    policies = relationship("Policy", back_populates="user")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    max_tx_usd = Column(Numeric, nullable=False, default=500)
    max_protocol_exposure_usd = Column(Numeric, nullable=False, default=500)
    max_gas_usd = Column(Numeric, nullable=False, default=5)
    allowed_chains = Column(JSON, nullable=False, default=list)
    allowed_protocols = Column(JSON, nullable=False, default=list)
    min_risk_score = Column(Integer, nullable=False, default=80)
    approval_threshold_usd = Column(Numeric, nullable=False, default=250)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="policies")


class AgentRequest(Base):
    __tablename__ = "agent_requests"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    raw_prompt = Column(String, nullable=False)
    parsed_intent = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="parsing")
    # parsing -> planning -> awaiting_approval -> approved -> executed
    #         -> rejected / failed  (at any point)
    steps = Column(JSON, nullable=True)  # ordered list of {label, status}
    created_at = Column(DateTime, default=datetime.utcnow)


class ExecutionPlan(Base):
    __tablename__ = "execution_plans"

    id = Column(String, primary_key=True, default=gen_uuid)
    request_id = Column(String, ForeignKey("agent_requests.id"), nullable=False)

    protocol = Column(String, nullable=False)
    chain = Column(String, nullable=False)
    amount_usd = Column(Numeric, nullable=False)
    expected_apy = Column(Numeric, nullable=False)
    estimated_gas_usd = Column(Numeric, nullable=False)
    risk_score = Column(Integer, nullable=False)

    policy_status = Column(String, nullable=False, default="PENDING")  # PASS/FAIL
    policy_reasons = Column(JSON, nullable=True)
    simulation_status = Column(String, nullable=False, default="PENDING")  # PASS/FAIL
    simulation_result = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=gen_uuid)
    plan_id = Column(String, ForeignKey("execution_plans.id"), nullable=False)
    tx_hash = Column(String, nullable=True)
    chain = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending/confirmed/failed
    block_number = Column(Integer, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    request_id = Column(String, ForeignKey("agent_requests.id"), nullable=True)
    event_type = Column(String, nullable=False)
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
