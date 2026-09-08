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
    const live = Boolean(settings.live_trading_enabled);
    $('#connection').textContent = 'API ONLINE';
    $('#status-pill').textContent = 'HEALTHY';
    $('#status').textContent = `API healthy • ${health.environment} • ${live ? 'LIVE ENABLED' : 'LIVE DISABLED'} • since ${health.uptime_since}`;
    $('#mode').textContent = live ? 'LIVE MODE' : 'PAPER MODE';
    $('#risk').textContent = `${(settings.risk_per_trade * 100).toFixed(2)}%`;
    $('#live').textContent = live ? 'ON' : 'OFF';
    $('#equity').textContent = Number(account.equity ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
    $('#positions').textContent = String((positions.positions || []).length);
  } catch (error) {
    $('#connection').textContent = 'API OFFLINE';
    $('#status-pill').textContent = 'UNAVAILABLE';
    $('#status').textContent = 'API unavailable';
    console.error(error);
  }
}

load();
setInterval(load, 10000);
