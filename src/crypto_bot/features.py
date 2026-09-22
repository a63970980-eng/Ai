from statistics import pstdev
def calc(c):
    p=[x["c"] for x in c]
    if len(p)<30: raise ValueError("insufficient candles")
    def ema(n):
        a=2/(n+1);e=p[0]
        for x in p[1:]:e=a*x+(1-a)*e
        return e
    r=[p[i]/p[i-1]-1 for i in range(1,len(p))]
    return {"price":p[-1],"ema20":ema(20),"ema50":ema(50),"ema200":ema(200),"momentum":p[-1]/p[-20]-1,"volatility":pstdev(r[-50:]),"high":max(x["h"] for x in c[-50:]),"low":min(x["l"] for x in c[-50:]),"volume_ratio":c[-1]["v"]/(sum(x["v"] for x in c[-20:])/20 or 1)}
def context(m):return {k:calc(v["candles"]) for k,v in m.items()}
