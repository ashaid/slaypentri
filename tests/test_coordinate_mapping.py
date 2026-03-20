import numpy as np
import pytest

try:
    from painter import (
        compute_draw_region,
        map_contour_to_screen,
        sort_contours_nearest_neighbor,
    )
    PAINTER_AVAILABLE = True
except ImportError:
    PAINTER_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PAINTER_AVAILABLE, reason="painter.py not yet implemented")


# === compute_draw_region ===

def test_letterbox():
    """CAL-06: Wide image (200x100) in tall bbox (1000x800) -> letterbox with top/bottom margins."""
    # bbox 1000 wide, 800 tall. img 200w x 100h (aspect=2.0)
    # width-constrained: draw_w=1000, draw_h=1000/2=500, offset_x=0, offset_y=(800-500)/2=150
    offset_x, offset_y, draw_w, draw_h = compute_draw_region((0, 0, 1000, 800), 200, 100)
    assert draw_w == pytest.approx(1000.0, abs=1e-6)
    assert draw_h == pytest.approx(500.0, abs=1e-6)
    assert offset_x == pytest.approx(0.0, abs=1e-6)
    assert offset_y == pytest.approx(150.0, abs=1e-6)


def test_pillarbox():
    """CAL-06: Tall image (100x200) in wide bbox (800x1000) -> pillarbox with left/right margins."""
    # bbox 800 wide, 1000 tall. img 100w x 200h (aspect=0.5)
    # if bbox_w / img_aspect = 800/0.5 = 1600 > bbox_h=1000 -> height-constrained
    # draw_h=1000, draw_w=1000*0.5=500, offset_x=(800-500)/2=150, offset_y=0
    offset_x, offset_y, draw_w, draw_h = compute_draw_region((0, 0, 800, 1000), 100, 200)
    assert draw_w == pytest.approx(500.0, abs=1e-6)
    assert draw_h == pytest.approx(1000.0, abs=1e-6)
    assert offset_x == pytest.approx(150.0, abs=1e-6)
    assert offset_y == pytest.approx(0.0, abs=1e-6)


def test_square_bbox_no_margins():
    """CAL-06: Square bbox + square image -> no margins, draw fills entire bbox."""
    # bbox 500x500, img 100x100 (aspect=1.0)
    # bbox_w / img_aspect = 500/1.0 = 500 == bbox_h=500 -> width-constrained
    # draw_w=500, draw_h=500, offset_x=0, offset_y=0
    offset_x, offset_y, draw_w, draw_h = compute_draw_region((0, 0, 500, 500), 100, 100)
    assert draw_w == pytest.approx(500.0, abs=1e-6)
    assert draw_h == pytest.approx(500.0, abs=1e-6)
    assert offset_x == pytest.approx(0.0, abs=1e-6)
    assert offset_y == pytest.approx(0.0, abs=1e-6)


# === map_contour_to_screen ===

def test_map_normalized_origin():
    """CAL-06: Normalized (0,0) maps to (offset_x, offset_y)."""
    offset_x, offset_y, draw_w, draw_h = 100.0, 50.0, 800.0, 600.0
    norm_contour = np.array([[0.0, 0.0]], dtype=np.float32)
    result = map_contour_to_screen(norm_contour, offset_x, offset_y, draw_w, draw_h)
    assert result[0, 0] == 100   # x
    assert result[0, 1] == 50    # y


def test_map_normalized_corner():
    """CAL-06: Normalized (1,1) maps to (offset_x+draw_w, offset_y+draw_h) approximately."""
    offset_x, offset_y, draw_w, draw_h = 100.0, 50.0, 800.0, 600.0
    norm_contour = np.array([[1.0, 1.0]], dtype=np.float32)
    result = map_contour_to_screen(norm_contour, offset_x, offset_y, draw_w, draw_h)
    # int(100 + 1.0*800) = 900, int(50 + 1.0*600) = 650
    assert result[0, 0] == 900
    assert result[0, 1] == 650


def test_map_returns_int32():
    """CAL-06: map_contour_to_screen result dtype is np.int32."""
    norm_contour = np.array([[0.5, 0.5]], dtype=np.float32)
    result = map_contour_to_screen(norm_contour, 0.0, 0.0, 100.0, 100.0)
    assert result.dtype == np.int32


# === sort_contours_nearest_neighbor ===

def _contour(points):
    """Helper: create an (N, 2) float32 array from a list of [x, y] pairs."""
    return np.array(points, dtype=np.float32)


def test_sort_reduces_travel():
    """PAINT-04: 3 contours at known positions — sorted order has less total travel than original."""
    # Contour A: at x=0.9, far from origin
    # Contour B: at x=0.1, close to origin
    # Contour C: at x=0.5, middle
    # Unsorted order: A, B, C — huge jump from origin to A, then back to B
    # Nearest-neighbor from (0,0): picks B first, then C, then A
    a = _contour([[0.9, 0.0], [0.95, 0.0]])
    b = _contour([[0.1, 0.0], [0.15, 0.0]])
    c = _contour([[0.5, 0.0], [0.55, 0.0]])

    unsorted = [a, b, c]
    sorted_out = sort_contours_nearest_neighbor(unsorted)

    def total_travel(contours):
        cx, cy = 0.0, 0.0
        dist = 0.0
        for cont in contours:
            dist += ((cont[0, 0] - cx) ** 2 + (cont[0, 1] - cy) ** 2) ** 0.5
            cx, cy = float(cont[-1, 0]), float(cont[-1, 1])
        return dist

    sorted_travel = total_travel(sorted_out)
    unsorted_travel = total_travel(unsorted)
    assert sorted_travel < unsorted_travel, (
        f"Sorted travel ({sorted_travel:.4f}) should be less than unsorted ({unsorted_travel:.4f})"
    )


def test_sort_reverses_contour():
    """PAINT-05: Contour whose far endpoint is closer to cursor gets reversed."""
    # Cursor starts at (0, 0). Contour goes from (0.8, 0) to (0.1, 0).
    # start endpoint (0.8,0) dist=0.8, end endpoint (0.1,0) dist=0.1 -> end is closer -> reverse
    contour = _contour([[0.8, 0.0], [0.5, 0.0], [0.1, 0.0]])
    result = sort_contours_nearest_neighbor([contour])
    # After reversal, first point should be (0.1, 0)
    assert result[0][0, 0] == pytest.approx(0.1, abs=1e-6)
    assert result[0][-1, 0] == pytest.approx(0.8, abs=1e-6)


def test_sort_no_reverse_when_start_closer():
    """PAINT-05: Contour stays in original order when start endpoint is closer to cursor."""
    # Cursor starts at (0, 0). Contour goes from (0.1, 0) to (0.8, 0).
    # start endpoint (0.1,0) dist=0.1, end endpoint (0.8,0) dist=0.8 -> start is closer -> no reverse
    contour = _contour([[0.1, 0.0], [0.5, 0.0], [0.8, 0.0]])
    result = sort_contours_nearest_neighbor([contour])
    assert result[0][0, 0] == pytest.approx(0.1, abs=1e-6)
    assert result[0][-1, 0] == pytest.approx(0.8, abs=1e-6)


def test_sort_empty_list():
    """PAINT-04: Empty input returns empty list."""
    result = sort_contours_nearest_neighbor([])
    assert result == []


def test_sort_single_contour():
    """PAINT-04: Single contour is returned (possibly reversed toward origin)."""
    contour = _contour([[0.5, 0.5], [0.6, 0.6]])
    result = sort_contours_nearest_neighbor([contour])
    assert len(result) == 1
    assert result[0].shape == contour.shape
