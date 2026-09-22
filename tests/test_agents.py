from forex_robot.agents.orchestrator import TradingAgentOrchestrator


def test_three_agent_chain_keeps_risk_last():
    seen = []

    def analyst(ctx):
        seen.append("analysis")
        return {"bias": "neutral"}

    def planner(ctx):
        seen.append("plan")
        assert ctx["analysis"]["bias"] == "neutral"
        return {"action": "paper_only"}

    def risk(ctx):
        seen.append("risk")
        assert ctx["execution_plan"]["action"] == "paper_only"
        return {"allowed": False, "reason": "test"}

    result = TradingAgentOrchestrator(analyst, planner, risk).evaluate({"symbol": "EUR_USD"})
    assert seen == ["analysis", "plan", "risk"]
    assert result.risk.payload["allowed"] is False
