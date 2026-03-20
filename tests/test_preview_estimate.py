"""Tests for estimate_painting_time — CAL-03 time estimation logic.

Import guard: tests skip if painter.py does not yet define estimate_painting_time.
"""
import numpy as np
import pytest

try:
    from painter import estimate_painting_time
    _ESTIMATE_AVAILABLE = True
except (ImportError, AttributeError):
    _ESTIMATE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _ESTIMATE_AVAILABLE,
    reason="estimate_painting_time not yet defined in painter.py",
)


def _make_contour(n_points: int) -> np.ndarray:
    """Return a (N, 2) float32 contour with N points."""
    return np.zeros((n_points, 2), dtype=np.float32)


def test_estimate_basic_formula():
    """Test 1: estimate returns start_delay + (total_points * inter_point_delay) + (stroke_count * inter_stroke_delay)."""
    config = {
        "painting": {
            "start_delay": 5,
            "inter_point_delay": 0.01,
            "inter_stroke_delay": 0.1,
        }
    }
    # 3 strokes, 10 points each = 30 total points
    contours = [_make_contour(10), _make_contour(10), _make_contour(10)]
    result = estimate_painting_time(contours, config)
    expected = 5 + (30 * 0.01) + (3 * 0.1)
    assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"


def test_estimate_default_config_100_strokes_500_points():
    """Test 2: Default config (inter_point_delay=0, inter_stroke_delay=0.05, start_delay=3),
    100 strokes with 500 total points returns 3 + 0 + 5.0 = 8.0 seconds."""
    config = {
        "painting": {
            "start_delay": 3,
            "inter_point_delay": 0,
            "inter_stroke_delay": 0.05,
        }
    }
    # 100 strokes, 5 points each = 500 total points
    contours = [_make_contour(5) for _ in range(100)]
    result = estimate_painting_time(contours, config)
    expected = 3 + (500 * 0) + (100 * 0.05)  # 3 + 0 + 5.0 = 8.0
    assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"
    assert abs(result - 8.0) < 1e-9, f"Expected 8.0, got {result}"


def test_estimate_with_inter_point_delay():
    """Test 3: With inter_point_delay=0.01, 3 strokes with 30 total points returns
    start_delay + 0.30 + (3 * inter_stroke_delay)."""
    config = {
        "painting": {
            "start_delay": 2,
            "inter_point_delay": 0.01,
            "inter_stroke_delay": 0.05,
        }
    }
    # 3 strokes, 10 points each = 30 total points
    contours = [_make_contour(10), _make_contour(10), _make_contour(10)]
    result = estimate_painting_time(contours, config)
    expected = 2 + (30 * 0.01) + (3 * 0.05)  # 2 + 0.30 + 0.15 = 2.45
    assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"


def test_estimate_empty_contours():
    """Test 4: Empty contours list returns just start_delay."""
    config = {
        "painting": {
            "start_delay": 3,
            "inter_point_delay": 0.01,
            "inter_stroke_delay": 0.05,
        }
    }
    contours = []
    result = estimate_painting_time(contours, config)
    expected = 3  # just start_delay
    assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"


def test_estimate_zero_start_delay():
    """Test 5: Zero start_delay still works correctly."""
    config = {
        "painting": {
            "start_delay": 0,
            "inter_point_delay": 0.02,
            "inter_stroke_delay": 0.1,
        }
    }
    contours = [_make_contour(20), _make_contour(30)]
    result = estimate_painting_time(contours, config)
    expected = 0 + (50 * 0.02) + (2 * 0.1)  # 0 + 1.0 + 0.2 = 1.2
    assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"
