# Architecture

Market adapters feed validated UTC candles/ticks into the multi-timeframe engine. Features, regime, structure and liquidity are deterministic research components. Strategies emit candidate signals; the scorer ranks them 0–100. News and session policies become explicit risk inputs. The RiskGate is authoritative and can veto any AI/model output. Execution is isolated behind BrokerAdapter and defaults to PaperBroker. Journal and analytics consume immutable trade events. PostgreSQL is the durable persistence target (`db/schema.sql`).

## Pipeline

`Data → Validation → 15M Direction → 5M Confirmation → Liquidity Sweep → BOS/CHoCH → Retest/1M Confirmation → Strategy Ensemble → AI/Statistical Score → News/Spread → Portfolio Risk → Execution → Monitoring → Journal`

## Safety

`LIVE_TRADING_ENABLED=false` is the default. Broker credentials belong only in deployment secrets. No martingale, no guaranteed returns, and no AI path can bypass deterministic risk controls.
