from forex_robot.observability import RuntimeMetrics


def test_runtime_metrics_snapshot():
    metrics = RuntimeMetrics()
    metrics.inc("paper_orders")
    metrics.inc("blocked_trades", 2)
    snap = metrics.snapshot()
    assert snap.paper_orders == 1
    assert snap.blocked_trades == 2
