import os
from dataclasses import dataclass
@dataclass(frozen=True)
class Settings:
    app_name:str="AI Crypto Autonomous Trading System"; environment:str="development"; live_trading_enabled:bool=False; paper_trading_enabled:bool=True
    ai_min_confidence:float=.68; max_risk_per_trade:float=.005; max_daily_loss:float=.02; max_drawdown:float=.10; max_open_positions:int=5
    symbols:str="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
    @classmethod
    def from_env(cls):
        f=lambda n,d:os.getenv(n,str(d)).lower() in {"1","true","yes","on"}
        return cls(os.getenv("APP_NAME",cls.app_name),os.getenv("ENVIRONMENT",cls.environment),f("LIVE_TRADING_ENABLED",False),f("PAPER_TRADING_ENABLED",True),float(os.getenv("AI_MIN_CONFIDENCE",cls.ai_min_confidence)),float(os.getenv("MAX_RISK_PER_TRADE",cls.max_risk_per_trade)),float(os.getenv("MAX_DAILY_LOSS",cls.max_daily_loss)),float(os.getenv("MAX_DRAWDOWN",cls.max_drawdown)),int(os.getenv("MAX_OPEN_POSITIONS",cls.max_open_positions)),os.getenv("CRYPTO_SYMBOLS",cls.symbols))
settings=Settings.from_env()
if settings.live_trading_enabled and settings.environment!="production": raise ValueError("LIVE_TRADING_ENABLED requires ENVIRONMENT=production")
