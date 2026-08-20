import pytest

from app.services.analytics import (
    metric_registry,
    no_attempt_signal,
    percentile,
    safe_rate,
)


def test_rates_handle_zero_denominator() -> None:
    assert safe_rate(1, 0) is None
    assert safe_rate(1, 4) == 0.25


def test_no_attempt_alert_requires_both_thresholds() -> None:
    current, previous, change, excess, alert = no_attempt_signal(80, 200, 20, 200)
    assert current == 0.4
    assert previous == 0.1
    assert change == pytest.approx(30)
    assert excess == 60
    assert alert is True

    assert no_attempt_signal(14, 100, 9, 100)[-1] is False
    assert no_attempt_signal(25, 1000, 20, 1000)[-1] is False


def test_equal_weight_benchmark_percentiles_are_deterministic() -> None:
    assert percentile([0.1, 0.2, 0.3, 0.4], 0.5) == 0.25
    assert percentile([], 0.5) is None


def test_registry_marks_proposed_composite_and_peer_contract() -> None:
    registry = {metric.metric_id: metric for metric in metric_registry().metrics}
    assert registry["sessions.verified_rate"].proposed is True
    assert registry["benchmarks.category_equal_weighted"].grain == "merchant"
    assert "sessions.no_attempt_rate" in registry
