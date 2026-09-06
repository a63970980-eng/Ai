# Risk Management

Risk is deterministic and evaluated before execution. Controls include per-trade risk, daily loss, peak-to-equity drawdown, maximum concurrent positions, total portfolio risk, consecutive-loss lockout, spread limits, news blocks and an emergency kill switch.

Position sizing is based on equity and stop distance; stop loss is mandatory for normal entries. Dynamic exits may use structure/ATR and configurable 1R/1.5R/2R/3R targets, break-even, trailing and partial exits. Martingale and loss-chasing are prohibited.

Live mode requires external broker credentials, independent testing, monitoring and explicit operational approval; this repository never stores those credentials.
