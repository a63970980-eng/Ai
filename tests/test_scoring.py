import pytest
from forex_robot.scoring import score_signal


def components(value: float) -> dict[str, float]:
    return {k: value for k in ('trend','momentum','structure','liquidity','volatility','session','news')}


def test_score_bands():
    assert score_signal(components(50)).verdict == 'no_trade'
    assert score_signal(components(65)).verdict == 'watch'
    assert score_signal(components(75)).verdict == 'valid'
    assert score_signal(components(85)).verdict == 'strong'
    assert score_signal(components(95)).verdict == 'premium'


def test_weights_must_sum_to_100():
    with pytest.raises(ValueError):
        score_signal(components(80), {'trend':100,'momentum':0,'structure':0,'liquidity':0,'volatility':0,'session':0,'news':0.1})


def test_components_are_clamped():
    result = score_signal({k: 200 for k in ('trend','momentum','structure','liquidity','volatility','session','news')})
    assert result.total == 100
