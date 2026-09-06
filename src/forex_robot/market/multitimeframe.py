from __future__ import annotations
from datetime import datetime, timezone
from enum import StrEnum
import pandas as pd

class Session(StrEnum): ASIA='asia'; LONDON='london'; NEW_YORK='new_york'; LONDON_NY_OVERLAP='london_new_york_overlap'; OFF='off'

def classify_session(ts: datetime) -> Session:
    h=ts.astimezone(timezone.utc).hour
    if 13<=h<16: return Session.LONDON_NY_OVERLAP
    if 7<=h<16: return Session.LONDON
    if 13<=h<22: return Session.NEW_YORK
    if 0<=h<8: return Session.ASIA
    return Session.OFF

def add_session_features(df:pd.DataFrame)->pd.DataFrame:
    out=df.copy()
    idx=pd.to_datetime(out.index, utc=True)
    out['session']=idx.map(classify_session).astype(str)
    out['session_hour']=idx.hour
    return out

def resample_ohlc(df:pd.DataFrame, rule:str)->pd.DataFrame:
    x=df.copy(); x.index=pd.to_datetime(x.index,utc=True)
    agg={'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
    return x.resample(rule,label='right',closed='right').agg(agg).dropna()

def build_mtf(df_1m:pd.DataFrame)->dict[str,pd.DataFrame]:
    return {'1m':df_1m.copy(), '5m':resample_ohlc(df_1m,'5min'), '15m':resample_ohlc(df_1m,'15min')}
