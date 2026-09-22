import json,urllib.parse,urllib.request
from datetime import datetime,timezone
BASE="https://api.binance.com"
def get(path,params):
    u=BASE+path+"?"+urllib.parse.urlencode(params)
    r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"ai-crypto-bot/3.0"}),timeout=15); return json.loads(r.read().decode())
def snapshot(symbol,interval="5m",limit=200):
    symbol=symbol.upper();s=get("/api/v3/ticker/24hr",{"symbol":symbol});rows=get("/api/v3/klines",{"symbol":symbol,"interval":interval,"limit":limit})
    c=[{"o":float(x[1]),"h":float(x[2]),"l":float(x[3]),"c":float(x[4]),"v":float(x[5])} for x in rows]
    return {"symbol":symbol,"price":float(s["lastPrice"]),"change_24h":float(s["priceChangePercent"])/100,"volume_24h":float(s["volume"]),"candles":c,"timestamp":datetime.now(timezone.utc).isoformat()}
def mtf(symbol): return {x:snapshot(symbol,x,200) for x in ("1m","5m","15m","1h","4h")}
