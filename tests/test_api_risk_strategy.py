from datetime import datetime, timezone

from fastapi.testclient import TestClient

from forex_robot.api import app


client = TestClient(app)


def signal_payload(confidence: float = 0.80) -> dict:
    return {
        "symbol": "EURUSD",
        "side": "buy",
        "confidence": confidence,
        "entry": 1.1000,
        "stop_loss": 1.0990,
        "take_profit": 1.1020,
        "reason": "test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def test_risk_api_approves_valid_signal():
    response = client.post("/api/v1/risk/evaluate", json={"signal": signal_payload(), "spread": 0.00005})
    assert response.status_code == 200
    assert response.json() == {"allowed": True, "reason": "approved"}


def test_risk_api_blocks_low_confidence_signal():
    response = client.post("/api/v1/risk/evaluate", json={"signal": signal_payload(0.40), "spread": 0.00005})
    assert response.status_code == 200
    assert response.json()["reason"] == "signal_confidence"


def test_risk_api_blocks_portfolio_limit():
    response = client.post(
        "/api/v1/risk/evaluate",
        json={"signal": signal_payload(), "spread": 0.00005, "portfolio_risk": 0.019, "proposed_risk": 0.002},
    )
    assert response.status_code == 200
    assert response.json()["reason"] == "portfolio_risk_limit"
