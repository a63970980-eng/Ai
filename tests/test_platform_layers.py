import pandas as pd
from forex_robot.market.structure import detect_structure
from forex_robot.market.liquidity import analyze_liquidity
from forex_robot.market.multitimeframe import build_mtf
from forex_robot.analytics import analytics
from forex_robot.robustness.monte_carlo import monte_carlo
from forex_robot.domain.trading import AccountState
from forex_robot.domain.models import Signal, Side
from datetime import datetime, timezone


def frame(n=120):
    idx=pd.date_range('2026-01-01',periods=n,freq='min',tz='UTC'); close=pd.Series([1+i*.00001 for i in range(n)],index=idx)
    return pd.DataFrame({'open':close,'high':close+.00005,'low':close-.00005,'close':close,'volume':100},index=idx)

def test_mtf_structure_liquidity():
    x=frame(); mtf=build_mtf(x); assert len(mtf['5m'])>0 and len(mtf['15m'])>0; assert detect_structure(mtf['5m']).trend in {'bullish','range','unknown'}; assert analyze_liquidity(mtf['5m']).buy_side is not None

def test_analytics_and_monte_carlo():
    a=analytics([1,-.5,2,-.25]); assert a['trades']==4 and a['profit_factor']>1; m=monte_carlo([1,-.5,2],100,7); assert 0<=m['prob_loss']<=1
