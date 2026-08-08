from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import agent, wallet, policies, activity, transactions

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgentVault API",
    description=(
        "Permissioned AI-agent execution layer for on-chain finance. "
        "AI proposes -> Policy Engine validates -> Simulation -> User "
        "approves -> Smart Wallet executes -> Verification."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(wallet.router)
app.include_router(policies.router)
app.include_router(activity.router)
app.include_router(transactions.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "AgentVault API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
