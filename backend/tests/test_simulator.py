from app.engines.simulator import simulate


def test_simulate_returns_expected_shape():
    result = simulate(
        protocol="Aave v3", chain="base", asset="USDC",
        amount_usd=500, estimated_gas_usd=0.15,
    )
    assert "success" in result
    assert "expected_asset_changes" in result
    assert result["estimated_gas_usd"] == 0.15
