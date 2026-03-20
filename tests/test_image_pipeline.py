import numpy as np
import pytest

try:
    from painter import (
        load_image,
        to_grayscale,
        compute_otsu_thresholds,
        normalize_contour,
        run_image_pipeline,
        AppState,
        load_config,
    )
    PAINTER_AVAILABLE = True
except ImportError:
    PAINTER_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PAINTER_AVAILABLE, reason="painter.py not yet implemented")


# --- IMG-01: Load image ---

def test_load_image_returns_ndarray(sample_png):
    """IMG-01: load_image() returns a numpy ndarray for a valid PNG."""
    img = load_image(sample_png)
    assert isinstance(img, np.ndarray), "load_image must return a numpy ndarray"
    assert img.ndim >= 2, "Image must have at least 2 dimensions"


def test_load_image_missing_file_raises():
    """IMG-01: load_image() raises SystemExit or FileNotFoundError for a missing file."""
    with pytest.raises((SystemExit, FileNotFoundError, ValueError)):
        load_image("/nonexistent/path/image.png")


def test_load_image_converts_to_grayscale(sample_png):
    """IMG-01: The image pipeline produces a grayscale (single channel) intermediate."""
    img = load_image(sample_png)
    gray = to_grayscale(img)
    # Grayscale image is 2D (H, W) or 3D with 1 channel
    assert gray.ndim == 2 or (gray.ndim == 3 and gray.shape[2] == 1), \
        "to_grayscale must produce a 2D array"


# --- IMG-02: Canny with numeric thresholds ---

def test_canny_numeric(sample_png, tmp_config_path):
    """IMG-02: Pipeline runs Canny with numeric thresholds without error."""
    import yaml
    with open(tmp_config_path, "w") as f:
        yaml.dump({
            "edge_detection": {
                "blur_kernel_size": 5,
                "canny_low": 50,
                "canny_high": 150,
                "min_contour_px": 5,
                "simplify_epsilon": 1.5,
            }
        }, f)
    state = AppState()
    state.image_path = sample_png
    state.config_path = tmp_config_path
    state.verbose = False
    load_config(state)
    run_image_pipeline(state)
    # Must complete without exception; contours_normalized is a list
    assert isinstance(state.contours_normalized, list)


# --- IMG-03: Otsu auto-threshold ---

def test_otsu_auto(sample_png):
    """IMG-03: compute_otsu_thresholds returns (low, high) floats where high >= low >= 0."""
    import cv2
    img = load_image(sample_png)
    gray = to_grayscale(img)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    low, high = compute_otsu_thresholds(blurred)
    assert isinstance(low, (int, float)), "low must be numeric"
    assert isinstance(high, (int, float)), "high must be numeric"
    assert high >= low >= 0, "high >= low >= 0 must hold"


def test_otsu_auto_triggered_by_string(sample_png, tmp_config_path):
    """IMG-03: When canny_low is 'auto', pipeline uses Otsu thresholds without crashing."""
    import yaml
    with open(tmp_config_path, "w") as f:
        yaml.dump({
            "edge_detection": {
                "blur_kernel_size": 5,
                "canny_low": "auto",
                "canny_high": "auto",
                "min_contour_px": 5,
                "simplify_epsilon": 1.5,
            }
        }, f)
    state = AppState()
    state.image_path = sample_png
    state.config_path = tmp_config_path
    state.verbose = False
    load_config(state)
    # Must not raise TypeError from cv2.Canny receiving string args
    run_image_pipeline(state)
    assert isinstance(state.contours_normalized, list)


# --- IMG-04: findContours ---

def test_find_contours(sample_png, tmp_config_path):
    """IMG-04: Pipeline extracts at least one contour from an image with a white square."""
    import yaml
    with open(tmp_config_path, "w") as f:
        yaml.dump({
            "edge_detection": {
                "blur_kernel_size": 3,
                "canny_low": 30,
                "canny_high": 100,
                "min_contour_px": 1,
                "simplify_epsilon": 0.5,
            }
        }, f)
    state = AppState()
    state.image_path = sample_png
    state.config_path = tmp_config_path
    state.verbose = False
    load_config(state)
    run_image_pipeline(state)
    assert len(state.contours_normalized) >= 1, \
        "White square image should produce at least one contour"


def test_find_contours_blank_image(blank_png, tmp_config_path):
    """IMG-04: Pipeline does not crash on a blank image (zero contours is valid)."""
    import yaml
    with open(tmp_config_path, "w") as f:
        yaml.dump({
            "edge_detection": {
                "blur_kernel_size": 3,
                "canny_low": 50,
                "canny_high": 150,
                "min_contour_px": 1,
                "simplify_epsilon": 1.5,
            }
        }, f)
    state = AppState()
    state.image_path = blank_png
    state.config_path = tmp_config_path
    state.verbose = False
    load_config(state)
    # Should not raise; result is an empty list
    run_image_pipeline(state)
    assert state.contours_normalized == [] or isinstance(state.contours_normalized, list)


# --- IMG-05: min arc-length filter ---

def test_min_length_filter(sample_png, tmp_config_path):
    """IMG-05: Contours shorter than min_contour_px are excluded."""
    import yaml
    # Run with a very large min_contour_px to force all contours to be filtered
    with open(tmp_config_path, "w") as f:
        yaml.dump({
            "edge_detection": {
                "blur_kernel_size": 3,
                "canny_low": 30,
                "canny_high": 100,
                "min_contour_px": 100000,  # absurdly large — all contours filtered
                "simplify_epsilon": 0.5,
            }
        }, f)
    state = AppState()
    state.image_path = sample_png
    state.config_path = tmp_config_path
    state.verbose = False
    load_config(state)
    run_image_pipeline(state)
    assert state.contours_normalized == [], \
        "All contours should be filtered with min_contour_px=100000"


# --- IMG-06: Douglas-Peucker simplification + normalization ---

def test_simplify_normalize(sample_png):
    """IMG-06: normalize_contour returns array in [0.0, 1.0] range."""
    import cv2
    img = load_image(sample_png)
    h, w = img.shape[:2]
    # Create a simple synthetic contour: a line across the image
    contour = np.array([[[0, 0]], [[w // 2, h // 2]], [[w - 1, h - 1]]], dtype=np.int32)
    normalized = normalize_contour(contour, w, h)
    assert normalized.shape[1] == 2, "Normalized contour must be (N, 2)"
    assert normalized.min() >= 0.0, "All values must be >= 0.0"
    assert normalized.max() <= 1.0, "All values must be <= 1.0"


def test_normalize_contour_shape(sample_png):
    """IMG-06: normalize_contour output shape is always (N, 2)."""
    import cv2
    img = load_image(sample_png)
    h, w = img.shape[:2]
    # Synthetic contour with known point count
    contour = np.array([[[0, 0]], [[w - 1, 0]], [[w - 1, h - 1]], [[0, h - 1]]], dtype=np.int32)
    normalized = normalize_contour(contour, w, h)
    assert normalized.ndim == 2, "Output must be 2D array"
    assert normalized.shape[1] == 2, "Second dimension must be 2 (x, y)"
    assert normalized.shape[0] == 4, "Must preserve point count"


def test_simplify_reduces_points(sample_png, tmp_config_path):
    """IMG-06: approxPolyDP with epsilon > 0 reduces point count compared to CHAIN_APPROX_NONE."""
    import yaml, cv2
    with open(tmp_config_path, "w") as f:
        yaml.dump({
            "edge_detection": {
                "blur_kernel_size": 3,
                "canny_low": 30,
                "canny_high": 100,
                "min_contour_px": 1,
                "simplify_epsilon": 5.0,  # aggressive simplification
            }
        }, f)
    state_simplified = AppState()
    state_simplified.image_path = sample_png
    state_simplified.config_path = tmp_config_path
    state_simplified.verbose = False
    load_config(state_simplified)
    run_image_pipeline(state_simplified)

    # Run again with epsilon=0 (no simplification)
    with open(tmp_config_path, "w") as f:
        yaml.dump({
            "edge_detection": {
                "blur_kernel_size": 3,
                "canny_low": 30,
                "canny_high": 100,
                "min_contour_px": 1,
                "simplify_epsilon": 0.0,
            }
        }, f)
    state_raw = AppState()
    state_raw.image_path = sample_png
    state_raw.config_path = tmp_config_path
    state_raw.verbose = False
    load_config(state_raw)
    run_image_pipeline(state_raw)

    # Total points should be fewer after simplification (or equal if image is very simple)
    total_simplified = sum(len(c) for c in state_simplified.contours_normalized)
    total_raw = sum(len(c) for c in state_raw.contours_normalized)
    assert total_simplified <= total_raw, \
        "Simplified contours should have fewer or equal points than raw"
