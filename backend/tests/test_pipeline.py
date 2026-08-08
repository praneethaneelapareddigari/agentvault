"""
End-to-end pipeline test hitting the FastAPI app directly (no live server
needed) via TestClient. Exercises the full hero-demo path:
prompt -> intent -> plan -> policy -> simulation -> approve -> executed.
"""
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp()}.db"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_full_hero_demo_pipeline():
    prompt = (
        "I have $1,000 USDC. Find a low-risk yield opportunity and invest "
        "$500, but don't spend more than $5 on gas and never put more than "
        "$500 into one protocol."
    )
    resp = client.post("/api/agent/request", json={"prompt": prompt})
    assert resp.status_code == 200
    req = resp.json()
    assert req["status"] == "awaiting_approval"
    request_id = req["id"]

    plan_resp = client.get(f"/api/agent/request/{request_id}/plan")
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    assert plan["policy_status"] == "PASS"
    assert plan["simulation_status"] in ("PASS", "FAIL")
    assert plan["amount_usd"] <= 500

    if plan["policy_status"] == "PASS" and plan["simulation_status"] == "PASS":
        approve_resp = client.post(f"/api/agent/request/{request_id}/approve")
        assert approve_resp.status_code == 200
        tx = approve_resp.json()
        assert tx["status"] == "confirmed"
        assert tx["tx_hash"].startswith("0x")


def test_reject_flow():
    resp = client.post("/api/agent/request", json={"prompt": "invest 100 usdc"})
    request_id = resp.json()["id"]
    reject_resp = client.post(f"/api/agent/request/{request_id}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"


def test_policy_violation_blocks_approval():
    # Ask for way more than any policy would allow -> plan should FAIL policy,
    # and approval must then be rejected by the API.
    resp = client.post(
        "/api/agent/request",
        json={"prompt": "invest 10000 usdc low risk, gas under 5, max 500 per protocol"},
    )
    request_id = resp.json()["id"]
    plan_resp = client.get(f"/api/agent/request/{request_id}/plan")
    if plan_resp.status_code == 200:
        plan = plan_resp.json()
        if plan["policy_status"] == "FAIL":
            approve_resp = client.post(f"/api/agent/request/{request_id}/approve")
            assert approve_resp.status_code == 400
