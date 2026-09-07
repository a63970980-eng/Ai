const $ = (id) => document.querySelector(id);

async function json(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

async function load() {
  try {
    const [health, settings, account, positions] = await Promise.all([
      json('/api/v1/health'),
      json('/api/v1/settings'),
      json('/api/v1/account'),
      json('/api/v1/positions'),
    ]);
    $('#status').textContent = `API healthy • ${health.environment} • ${health.live_trading ? 'LIVE ENABLED' : 'LIVE DISABLED'} • since ${health.uptime_since}`;
    $('#risk').textContent = `${(settings.risk_per_trade * 100).toFixed(2)}%`;
    $('#live').textContent = settings.live_trading_enabled ? 'ON' : 'OFF';
    $('#equity').textContent = Number(account.equity ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
    $('#positions').textContent = String((positions.positions || []).length);
  } catch (error) {
    $('#status').textContent = 'API unavailable';
    console.error(error);
  }
}

load();
setInterval(load, 10000);
