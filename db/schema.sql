CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text UNIQUE NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS accounts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    broker text NOT NULL,
    mode text NOT NULL CHECK (mode IN ('backtest', 'paper', 'live')),
    currency text NOT NULL DEFAULT 'USD',
    balance numeric NOT NULL DEFAULT 0 CHECK (balance >= 0),
    equity numeric NOT NULL DEFAULT 0 CHECK (equity >= 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS instruments (
    symbol text PRIMARY KEY,
    base_currency text NOT NULL,
    quote_currency text NOT NULL,
    pip_size numeric NOT NULL CHECK (pip_size > 0),
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS market_data (
    symbol text REFERENCES instruments(symbol),
    timeframe text NOT NULL,
    ts timestamptz NOT NULL,
    open numeric NOT NULL CHECK (open > 0),
    high numeric NOT NULL CHECK (high > 0),
    low numeric NOT NULL CHECK (low > 0),
    close numeric NOT NULL CHECK (close > 0),
    volume numeric NOT NULL DEFAULT 0 CHECK (volume >= 0),
    PRIMARY KEY (symbol, timeframe, ts),
    CHECK (high >= low),
    CHECK (high >= open AND high >= close),
    CHECK (low <= open AND low <= close)
);

CREATE TABLE IF NOT EXISTS signals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid REFERENCES accounts(id) ON DELETE CASCADE,
    symbol text REFERENCES instruments(symbol),
    side text NOT NULL CHECK (side IN ('buy', 'sell')),
    score numeric NOT NULL CHECK (score >= 0 AND score <= 100),
    strategy text,
    regime text,
    session text,
    entry numeric CHECK (entry > 0),
    stop_loss numeric CHECK (stop_loss > 0),
    take_profit numeric CHECK (take_profit > 0),
    explanation jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid REFERENCES accounts(id) ON DELETE CASCADE,
    broker_order_id text,
    client_order_id text UNIQUE,
    symbol text REFERENCES instruments(symbol),
    side text NOT NULL CHECK (side IN ('buy', 'sell')),
    units numeric NOT NULL CHECK (units > 0),
    status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS positions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid REFERENCES accounts(id) ON DELETE CASCADE,
    symbol text REFERENCES instruments(symbol),
    side text NOT NULL CHECK (side IN ('buy', 'sell')),
    units numeric NOT NULL CHECK (units > 0),
    entry numeric NOT NULL CHECK (entry > 0),
    stop_loss numeric CHECK (stop_loss > 0),
    take_profit numeric CHECK (take_profit > 0),
    opened_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trades (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid REFERENCES accounts(id) ON DELETE CASCADE,
    signal_id uuid REFERENCES signals(id),
    symbol text REFERENCES instruments(symbol),
    direction text NOT NULL CHECK (direction IN ('buy', 'sell')),
    entry numeric NOT NULL CHECK (entry > 0),
    exit numeric CHECK (exit > 0),
    stop_loss numeric CHECK (stop_loss > 0),
    take_profit numeric CHECK (take_profit > 0),
    units numeric NOT NULL CHECK (units > 0),
    risk numeric NOT NULL CHECK (risk >= 0),
    pnl numeric,
    r_multiple numeric,
    exit_reason text,
    strategy text,
    regime text,
    session text,
    spread numeric CHECK (spread >= 0),
    slippage numeric CHECK (slippage >= 0),
    ai_analysis jsonb NOT NULL DEFAULT '{}',
    opened_at timestamptz NOT NULL,
    closed_at timestamptz
);

CREATE TABLE IF NOT EXISTS strategies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text UNIQUE NOT NULL,
    config jsonb NOT NULL DEFAULT '{}',
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS risk_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid REFERENCES accounts(id) ON DELETE CASCADE,
    event_type text NOT NULL,
    severity text NOT NULL,
    message text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS news_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    currency text NOT NULL,
    impact text NOT NULL,
    title text NOT NULL,
    event_at timestamptz NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS backtests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid REFERENCES accounts(id) ON DELETE CASCADE,
    name text NOT NULL,
    config jsonb NOT NULL DEFAULT '{}',
    started_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS backtest_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_id uuid REFERENCES backtests(id) ON DELETE CASCADE,
    trades integer NOT NULL CHECK (trades >= 0),
    win_rate numeric NOT NULL CHECK (win_rate >= 0 AND win_rate <= 1),
    profit_factor numeric,
    expectancy numeric,
    sharpe numeric,
    sortino numeric,
    max_drawdown numeric NOT NULL CHECK (max_drawdown >= 0),
    recovery_factor numeric,
    metrics jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS model_predictions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id uuid REFERENCES signals(id) ON DELETE CASCADE,
    model text NOT NULL,
    score numeric NOT NULL CHECK (score >= 0 AND score <= 1),
    features jsonb NOT NULL DEFAULT '{}',
    outcome numeric,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS system_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    level text NOT NULL,
    component text NOT NULL,
    message text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_market_symbol_ts ON market_data(symbol, ts DESC);
CREATE INDEX IF NOT EXISTS idx_signals_account_created ON signals(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_account_created ON orders(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(account_id);
CREATE INDEX IF NOT EXISTS idx_trades_account_closed ON trades(account_id, closed_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_event ON news_events(event_at);
CREATE INDEX IF NOT EXISTS idx_risk_events_account_created ON risk_events(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_events_created ON system_events(created_at DESC);
