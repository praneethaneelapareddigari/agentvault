from app.engines.risk_engine import score_opportunity, meets_risk_tolerance


def test_unvetted_protocol_scores_zero():
    fake_protocol = {"name": "SketchyFarm", "base_risk_score": 99}
    result = score_opportunity(fake_protocol, amount_usd=100, wallet_total_usd=1000)
    assert result["score"] == 0


def test_vetted_protocol_scores_base_score():
    protocol = {"name": "Aave v3", "base_risk_score": 92}
    result = score_opportunity(protocol, amount_usd=100, wallet_total_usd=10000)
    assert result["score"] == 92


def test_large_concentration_penalizes_score():
    protocol = {"name": "Aave v3", "base_risk_score": 92}
    result = score_opportunity(protocol, amount_usd=900, wallet_total_usd=1000)
    assert result["score"] < 92


def test_risk_tolerance_floor_low():
    assert meets_risk_tolerance(85, "low") is True
    assert meets_risk_tolerance(75, "low") is False


def test_risk_tolerance_floor_high():
    assert meets_risk_tolerance(45, "high") is True
    assert meets_risk_tolerance(30, "high") is False
