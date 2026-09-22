from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from forex_robot.ai.council import CouncilResult


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
    """Three-agent chain with a hard deterministic risk boundary."""

    def __init__(
        self,
        analyst: Callable[[dict[str, Any]], dict[str, Any]],
        planner: Callable[[dict[str, Any]], dict[str, Any]],
        risk_monitor: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        self.analyst = analyst
        self.planner = planner
        self.risk_monitor = risk_monitor

    @classmethod
    def from_council(cls, council: CouncilResult) -> "TradingAgentOrchestrator":
        def analyst(ctx: dict[str, Any]) -> dict[str, Any]:
            return {
                "stance": council.stance,
                "score": council.consensus_score,
                "agreement": council.agreement,
                "conflicts": council.conflicts,
                "models": council.successful_models,
            }

        def planner(ctx: dict[str, Any]) -> dict[str, Any]:
            analysis = ctx["analysis"]
            return {
                "action": "paper_only" if analysis["stance"] != "WAIT" else "wait",
                "stance": analysis["stance"],
                "confidence": analysis["score"] * analysis["agreement"],
                "execution": "disabled" if analysis["stance"] == "WAIT" else "paper",
            }

        def risk_monitor(ctx: dict[str, Any]) -> dict[str, Any]:
            analysis = ctx["analysis"]
            plan = ctx["execution_plan"]
            blocked = bool(ctx.get("risk_blocked", False))
            return {
                "allowed": not blocked and plan["action"] != "wait" and not analysis["conflicts"],
                "reason": (
                    "deterministic risk engine required" if blocked
                    else "council conflict or WAIT"
                    if plan["action"] == "wait" or analysis["conflicts"]
                    else "await deterministic risk gate"
                ),
            }

        return cls(analyst, planner, risk_monitor)

    def evaluate(self, context: dict[str, Any]) -> AgentDecision:
        analysis = AgentResult("market_analyst", "ok", self.analyst(context))
        plan = AgentResult(
            "execution_planner", "ok",
            self.planner({**context, "analysis": analysis.payload}),
        )
        risk = AgentResult(
            "risk_monitor", "ok",
            self.risk_monitor({
                **context,
                "analysis": analysis.payload,
                "execution_plan": plan.payload,
            }),
        )
        return AgentDecision(analysis, plan, risk)
