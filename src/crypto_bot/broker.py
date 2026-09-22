from datetime import datetime,timezone
from .models import Side
class PaperBroker:
    def __init__(self,equity=100000.):self.equity=equity;self.positions={}
    def execute(self,d):
        if not d.risk_allowed or d.side==Side.WAIT:return {"status":"blocked","reason":d.reasons}
        q=self.equity*d.risk_fraction/abs(d.entry-d.stop_loss);i=f"PAPER-{len(self.positions)+1:08d}"
        self.positions[i]={"id":i,"symbol":d.symbol,"side":d.side.value,"quantity":q,"entry":d.entry,"stop_loss":d.stop_loss,"take_profit":d.take_profit,"opened_at":datetime.now(timezone.utc).isoformat()}
        return {"status":"paper_filled",**self.positions[i]}
    def snapshot(self):return list(self.positions.values())
