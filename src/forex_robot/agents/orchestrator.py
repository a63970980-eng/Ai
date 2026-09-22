from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class AgentResult:
    agent: str
    status: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class AgentDecision:
    analysis: AgentResult
    execution_plan: AgentResult
    risk: AgentResult


class TradingAgentOrchestrator:
    """Deterministic three-agent boundary.

    Agents may analyse and propose. The risk engine remains authoritative and
    this orchestrator never submits broker orders.
    """

    def __init__(
        self,
        analyst: Callable[[dict[str, Any]], dict[str, Any]],
        planner: Callable[[dict[str, Any]], dict[str, Any]],
        risk_monitor: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        self.analyst = analyst
        self.planner = planner
        self.risk_monitor = risk_monitor

    def evaluate(self, context: dict[str, Any]) -> AgentDecision:
        analysis = AgentResult("market_analyst", "ok", self.analyst(context))
        plan_context = {**context, "analysis": analysis.payload}
        plan = AgentResult("execution_planner", "ok", self.planner(plan_context))
        risk_context = {**plan_context, "execution_plan": plan.payload}
        risk = AgentResult("risk_monitor", "ok", self.risk_monitor(risk_context))
        return AgentDecision(analysis, plan, risk)
