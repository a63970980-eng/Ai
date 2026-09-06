from __future__ import annotations
import numpy as np
import pandas as pd

def ema(s,n): return s.ewm(span=n,adjust=False).mean()
def sma(s,n): return s.rolling(n).mean()
def rsi(close,n=14):
 d=close.diff(); up=d.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); dn=(-d.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean(); rs=up/dn.replace(0,np.nan); return 100-100/(1+rs)
def atr(df,n=14):
 p=df.close.shift(); tr=pd.concat([(df.high-df.low),(df.high-p).abs(),(df.low-p).abs()],axis=1).max(axis=1); return tr.ewm(alpha=1/n,adjust=False).mean()
def macd(close):
 line=ema(close,12)-ema(close,26); sig=ema(line,9); return line,sig,line-sig
def adx(df,n=14):
 up=df.high.diff(); dn=-df.low.diff(); plus=up.where((up>dn)&(up>0),0.0); minus=dn.where((dn>up)&(dn>0),0.0); a=atr(df,n).replace(0,np.nan); p=100*plus.ewm(alpha=1/n,adjust=False).mean()/a; m=100*minus.ewm(alpha=1/n,adjust=False).mean()/a; dx=100*(p-m).abs()/(p+m).replace(0,np.nan); return dx.ewm(alpha=1/n,adjust=False).mean()
def bollinger(close,n=20,k=2):
 mid=close.rolling(n).mean(); std=close.rolling(n).std(); return mid,mid+k*std,mid-k*std
def vwap(df):
 vol=df.volume.replace(0,np.nan); return ((df.high+df.low+df.close)/3*vol).cumsum()/vol.cumsum()
def build_features(df):
 o=df.copy(); o['ema20']=ema(o.close,20); o['ema50']=ema(o.close,50); o['ema200']=ema(o.close,200); o['rsi14']=rsi(o.close); o['atr14']=atr(o,14); o['adx14']=adx(o,14); o['macd'],o['macd_signal'],o['macd_hist']=macd(o.close); o['bb_mid'],o['bb_upper'],o['bb_lower']=bollinger(o.close); o['vwap']=vwap(o); o['volatility']=o.close.pct_change().rolling(20).std(); o['range']=o.high-o.low; return o
