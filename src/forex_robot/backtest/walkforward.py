from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class Window:
    train_start:int; train_end:int; validation_end:int; test_end:int

def windows(n:int, train:int, validation:int, test:int, step:int|None=None)->list[Window]:
    if min(train,validation,test)<=0 or n<train+validation+test: return []
    step=step or test; out=[]; start=0
    while start+train+validation+test<=n:
        out.append(Window(start,start+train,start+train+validation,start+train+validation+test)); start+=step
    return out

def walk_forward(df:pd.DataFrame, train:int=1000, validation:int=250, test:int=250, step:int|None=None):
    return [df.iloc[w.train_start:w.test_end] for w in windows(len(df),train,validation,test,step)]
