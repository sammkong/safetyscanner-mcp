from safetyscanner.scorer import score_text


def test_score_text_returns_stub_response() -> None:
    assert score_text("sample listing") == "risk_score: 0/100 (stub)"
