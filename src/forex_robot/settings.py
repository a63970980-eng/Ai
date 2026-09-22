from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Crypto Quant Trading Robot"
    environment: str = "development"
    okx_demo: bool = True
    live_trading_enabled: bool = False
    paper_trading_enabled: bool = True
    max_risk_per_trade: float = 0.005
    max_daily_loss: float = 0.02
    max_drawdown: float = 0.10
    max_open_positions: int = 3
    max_spread_fraction: float = 0.0015
    max_slippage_fraction: float = 0.001
    min_signal_confidence: float = 0.65

    def __post_init__(self) -> None:
        if not 0 < self.max_risk_per_trade <= 0.05: raise ValueError("max_risk_per_trade must be in (0, 0.05]")
        if not 0 < self.max_daily_loss <= 1 or not 0 < self.max_drawdown <= 1: raise ValueError("loss and drawdown limits must be in (0, 1]")
        if self.max_open_positions <= 0: raise ValueError("max_open_positions must be positive")
        if self.max_spread_fraction <= 0 or self.max_slippage_fraction < 0: raise ValueError("spread/slippage limits invalid")
        if not 0 <= self.min_signal_confidence <= 1: raise ValueError("min_signal_confidence must be in [0, 1]")
        if self.live_trading_enabled and self.environment != "production": raise ValueError("live trading requires production environment")
        if self.live_trading_enabled and self.okx_demo: raise ValueError("live trading cannot use OKX demo")

    @classmethod
    def from_env(cls) -> "Settings":
        def flag(name: str, default: bool) -> bool:
            return os.getenv(name, str(default)).lower() in {"1","true","yes","on"}
        return cls(
            app_name=os.getenv("APP_NAME", cls.app_name),
            environment=os.getenv("ENVIRONMENT", cls.environment),
            okx_demo=flag("OKX_DEMO", True),
            live_trading_enabled=flag("LIVE_TRADING_ENABLED", False),
            paper_trading_enabled=flag("PAPER_TRADING_ENABLED", True),
            max_risk_per_trade=float(os.getenv("MAX_RISK_PER_TRADE", cls.max_risk_per_trade)),
            max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", cls.max_daily_loss)),
            max_drawdown=float(os.getenv("MAX_DRAWDOWN", cls.max_drawdown)),
            max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", cls.max_open_positions)),
            max_spread_fraction=float(os.getenv("MAX_SPREAD_FRACTION", cls.max_spread_fraction)),
            max_slippage_fraction=float(os.getenv("MAX_SLIPPAGE_FRACTION", cls.max_slippage_fraction)),
            min_signal_confidence=float(os.getenv("MIN_SIGNAL_CONFIDENCE", cls.min_signal_confidence)),
        )


settings = Settings.from_env()
