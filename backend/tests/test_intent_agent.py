from app.agents.intent_agent import extract_intent


def test_extracts_amount_asset_and_constraints():
    prompt = (
        "I have $1,000 USDC. Find a low-risk yield opportunity and invest "
        "$500, but don't spend more than $5 on gas and never put more than "
        "$500 into one protocol."
    )
    intent = extract_intent(prompt)
    assert intent.asset == "USDC"
    assert intent.risk == "low"
    assert intent.max_gas == 5.0
    assert intent.max_protocol_exposure == 500.0


def test_defaults_are_sane_for_sparse_prompt():
    intent = extract_intent("invest 200 dai")
    assert intent.asset == "DAI"
    assert intent.amount == 200.0
    assert intent.risk == "low"
