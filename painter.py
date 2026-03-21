#!/usr/bin/env python3
"""
painter.py — STS2 Map Painter
Traces image contours as mouse strokes within a screen bounding box.

Usage:
    python painter.py image.png [--config path/to/config.yaml] [--dry-run] [--verbose]
"""

import os
import sys
import time
import threading
import argparse
from dataclasses import dataclass, field
from typing import List, Optional

# Suppress Qt font/platform warnings from OpenCV's Qt backend before importing cv2.
# On Wayland+XWayland, Qt emits noisy warnings about fonts and session type.
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

import numpy as np
import cv2
import yaml

# Patch mouseinfo stub before pyautogui import if tkinter is unavailable (headless/test environments).
# pyautogui's mouseinfo dependency calls sys.exit() if tkinter is missing, which breaks imports.
try:
    import tkinter as _tkinter  # noqa: F401 — test if tkinter is present
    _TKINTER_AVAILABLE = True
except ImportError:
    _TKINTER_AVAILABLE = False
    import types as _types
    _mouseinfo_stub = _types.ModuleType("mouseinfo")
    sys.modules.setdefault("mouseinfo", _mouseinfo_stub)

# CFG-05 / CFG-06: pyautogui connects to X display at import time on Linux.
# If DISPLAY is unset (Wayland-only session), the import crashes with Xlib.error.DisplayNameError
# BEFORE check_display_environment() ever runs. Wrap the import so the module can load cleanly;
# check_display_environment() in main() will exit(1) before any pyautogui call is made.
try:
    import pyautogui
    pyautogui.PAUSE = 0  # CFG-06: eliminate 0.1s default per-call penalty
    _PYAUTOGUI_AVAILABLE = True
except Exception:
    pyautogui = None  # type: ignore[assignment]
    _PYAUTOGUI_AVAILABLE = False

# pynput also connects to X at import time. Guard it the same way as pyautogui.
try:
    from pynput import mouse as pynput_mouse
    _PYNPUT_AVAILABLE = True
except Exception:
    pynput_mouse = None  # type: ignore[assignment]
    _PYNPUT_AVAILABLE = False


# === CONFIGURATION ===

DEFAULT_CONFIG_CONTENT = """\
# painter.py configuration
# All parameters have sensible defaults — edit to tune for your image.

edge_detection:
  blur_kernel_size: 5        # Gaussian blur kernel size (odd integer, 1-31). Higher = more noise reduction.
  canny_low: 50              # Canny low threshold (0-255, or "auto" for Otsu-based). Lower = more edges detected.
  canny_high: 150            # Canny high threshold (0-255, or "auto" for Otsu-based). Higher = fewer weak edges kept.
  min_contour_px: 10         # Minimum contour arc-length in pixels (0+). Increase to discard small noise contours.
  simplify_epsilon: 1.5      # Douglas-Peucker simplification in pixels (0.0-10.0). Higher = fewer points, coarser lines.
  merge_distance_px: 5       # Merge distance in pixels (0 = disabled). Contours closer than this are merged, keeping the longest.

calibration:
  countdown_seconds: 3       # Seconds before each calibration click (1-10). Time to position your cursor.

painting:
  mouse_button: right        # Mouse button for strokes: "right" or "left".
  inter_stroke_delay: 0.05   # Seconds between strokes (0.0-1.0). Increase if target app drops strokes.
  start_delay: 3             # Seconds countdown before painting begins (0-30).
  inter_point_delay: 0       # Seconds between points within a stroke (0.0-0.1). 0 = fastest. Increase for slow apps.
"""

# Default values as a nested dict (mirrors DEFAULT_CONFIG_CONTENT) for deep_merge
_DEFAULTS = {
    "edge_detection": {
        "blur_kernel_size": 5,
        "canny_low": 50,
        "canny_high": 150,
        "min_contour_px": 10,
        "simplify_epsilon": 1.5,
        "merge_distance_px": 8,
    },
    "calibration": {
        "countdown_seconds": 3,
    },
    "painting": {
        "mouse_button": "right",
        "inter_stroke_delay": 0.05,
        "start_delay": 3,
        "inter_point_delay": 0,
    },
}


def deep_merge(defaults: dict, overrides: dict) -> dict:
    """Recursively merge overrides into defaults, filling missing keys from defaults.

    Neither input dict is mutated.
    """
    result = dict(defaults)
    for key, val in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = val
    return result


@dataclass
class AppState:
    config: dict = field(default_factory=dict)
    image_path: str = ""
    config_path: str = ""
    contours_normalized: List[np.ndarray] = field(default_factory=list)
    bbox: Optional[tuple] = None          # (x1, y1, x2, y2) screen pixels
    abort_flag: threading.Event = field(default_factory=threading.Event)
    dry_run: bool = False
    verbose: bool = False


def load_config(state: AppState) -> None:
    """CFG-01: Load YAML config from state.config_path.

    If the file does not exist, auto-generate it with annotated defaults.
    Missing keys in an existing file are filled from _DEFAULTS via deep_merge.
    """
    if not os.path.exists(state.config_path):
        with open(state.config_path, "w") as f:
            f.write(DEFAULT_CONFIG_CONTENT)
        print(f"Created default config: {state.config_path}")

    with open(state.config_path) as f:
        loaded = yaml.safe_load(f) or {}

    # Enforce odd blur_kernel_size (OpenCV requirement)
    blur_k = (loaded.get("edge_detection") or {}).get("blur_kernel_size")
    if blur_k is not None and isinstance(blur_k, int) and blur_k % 2 == 0:
        loaded["edge_detection"]["blur_kernel_size"] = blur_k + 1
        if state.verbose:
            print(f"[DEBUG] blur_kernel_size was even ({blur_k}), incremented to {blur_k + 1}")

    state.config = deep_merge(_DEFAULTS, loaded)

    if state.verbose:
        print(f"[DEBUG] Config loaded from: {state.config_path}")
        print(f"[DEBUG] Effective config: {state.config}")


# === SAFETY ===

def check_display_environment() -> None:
    """CFG-05: Fail fast on Wayland-only sessions.

    Wayland-only: WAYLAND_DISPLAY set, DISPLAY not set -> exit with actionable error.
    XWayland: both WAYLAND_DISPLAY and DISPLAY set -> proceed (pyautogui works via XWayland).
    X11: only DISPLAY set -> proceed.
    """
    wayland = os.environ.get("WAYLAND_DISPLAY")
    display = os.environ.get("DISPLAY")
    if wayland and not display:
        print(
            "Error: This tool requires an X11 session.\n"
            f"You appear to be running a Wayland-only session "
            f"(WAYLAND_DISPLAY={wayland}, DISPLAY not set).\n"
            "Options:\n"
            "  1. Log out and select an X11 session at your login screen.\n"
            "  2. Start XWayland and set DISPLAY=:0 before running.\n"
            "  3. Run: DISPLAY=:0 python painter.py image.png"
        )
        sys.exit(1)


# === CLI ===

def parse_cli(state: AppState) -> None:
    """Parse command-line arguments into state."""
    parser = argparse.ArgumentParser(
        description="Paint image contours via mouse replay",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("image", help="Path to input PNG image")
    parser.add_argument(
        "--config", default=None,
        help="Path to YAML config file (default: config.yaml next to painter.py)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run pipeline and calibration but skip painting entirely"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug output for troubleshooting"
    )
    args = parser.parse_args()

    state.image_path = args.image
    state.dry_run = args.dry_run
    state.verbose = args.verbose

    if args.config:
        state.config_path = args.config
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        state.config_path = os.path.join(script_dir, "config.yaml")


# === IMAGE PIPELINE ===

def load_image(path: str) -> np.ndarray:
    """IMG-01: Load PNG from disk. Exits with clear error if file missing or unreadable."""
    if not os.path.exists(path):
        print(f"Error: Image file not found: {path}")
        sys.exit(1)
    img = cv2.imread(path)
    if img is None:
        print(f"Error: Could not read image (unsupported format or corrupted): {path}")
        sys.exit(1)
    return img


def to_grayscale(img: np.ndarray) -> np.ndarray:
    """IMG-01: Convert BGR image to single-channel grayscale."""
    if img.ndim == 2:
        return img  # already grayscale
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def compute_otsu_thresholds(blurred_gray: np.ndarray) -> tuple:
    """IMG-03: Derive Canny thresholds from Otsu's method.

    Standard ratio: low = 0.5 * otsu, high = otsu.
    Source: https://pyimagesearch.com/2015/04/06/zero-parameter-automatic-canny-edge-detection-with-python-and-opencv/
    """
    otsu_thresh, _ = cv2.threshold(
        blurred_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )
    high = float(otsu_thresh)
    low = 0.5 * high
    return low, high


def normalize_contour(contour: np.ndarray, img_w: int, img_h: int) -> np.ndarray:
    """IMG-06 + coordinate math: Convert pixel contour to normalized [0, 1] coordinates.

    Input contour shape: (N, 1, 2) from findContours, or (N, 2) from approxPolyDP.
    Output shape: (N, 2) float32 with values in [0.0, 1.0].

    IMPORTANT: Must be called AFTER approxPolyDP (in pixel space) and BEFORE any drawing.
    Squeeze axis=1 to handle the (N, 1, 2) case before math.
    """
    pts = contour.reshape(-1, 2).astype(np.float32)
    pts[:, 0] = pts[:, 0] / img_w   # x / width
    pts[:, 1] = pts[:, 1] / img_h   # y / height
    return pts


def contour_color_bgr(index: int, total: int) -> tuple:
    """Preview rainbow gradient: hue 0 (red) to 240 (blue) across N contours.

    Uses HSV->BGR conversion via OpenCV to avoid manual color math.
    """
    hue = int(240 * index / max(total - 1, 1))
    hsv_pixel = np.uint8([[[hue, 255, 255]]])
    bgr = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)[0][0]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])


def deduplicate_contours(contours: list, merge_distance_px: float) -> list:
    """IMG-07: Remove near-duplicate contours caused by thick lines in the input image.

    Thick lines produce two parallel contours from Canny edge detection (one per edge).
    This function merges pairs that are close together, keeping only the longer one.

    Algorithm:
      1. If merge_distance_px <= 0, return contours unchanged (feature disabled).
      2. For each pair (i, j) where both are still kept:
         - Sample up to 10 evenly-spaced points on contour i.
         - Compute the mean minimum distance from those sample points to contour j.
         - If mean distance < merge_distance_px, mark the shorter contour as not-kept.
      3. Return only kept contours.

    Args:
        contours: List of OpenCV contours (each shape (N, 1, 2) or (N, 2), int32), in pixel space.
        merge_distance_px: Distance threshold in pixels. 0 or negative disables deduplication.

    Returns:
        Filtered list with near-duplicate contours removed (shorter of each pair discarded).
    """
    if merge_distance_px <= 0 or len(contours) == 0:
        return list(contours)

    # Pre-compute arc lengths for all contours (used to decide which to keep when merging)
    arc_lengths = [cv2.arcLength(c, closed=False) for c in contours]

    keep = [True] * len(contours)

    for i in range(len(contours)):
        if not keep[i]:
            continue
        # Get evenly-spaced sample points from contour i (up to 10)
        pts_i = contours[i].reshape(-1, 2).astype(np.float32)
        n_samples = min(10, len(pts_i))
        indices = np.linspace(0, len(pts_i) - 1, n_samples, dtype=int)
        sample_pts = pts_i[indices]

        for j in range(i + 1, len(contours)):
            if not keep[j]:
                continue
            pts_j = contours[j].reshape(-1, 2).astype(np.float32)

            # For each sample point on i, compute min distance to any point in j
            # Using vectorized computation: broadcast (n_samples, 1, 2) vs (1, len_j, 2)
            diffs = sample_pts[:, np.newaxis, :] - pts_j[np.newaxis, :, :]  # (n_samples, len_j, 2)
            sq_dists = np.sum(diffs ** 2, axis=2)                            # (n_samples, len_j)
            min_dists = np.sqrt(np.min(sq_dists, axis=1))                   # (n_samples,)
            mean_dist = float(np.mean(min_dists))

            if mean_dist < merge_distance_px:
                # Mark the shorter contour as not-kept
                if arc_lengths[i] >= arc_lengths[j]:
                    keep[j] = False
                else:
                    keep[i] = False
                    break  # i is dropped; skip remaining j comparisons

    return [c for c, k in zip(contours, keep) if k]


def run_image_pipeline(state: AppState) -> None:
    """IMG-01..06: Full image processing pipeline.

    Steps (in order — order matters for correctness):
      1. Load PNG (IMG-01)
      2. Convert to grayscale (IMG-01)
      3. Gaussian blur — must use odd kernel (IMG-02)
      4. Canny edge detection — numeric or Otsu auto (IMG-02, IMG-03)
      5. findContours with RETR_LIST + CHAIN_APPROX_NONE (IMG-04)
      6. approxPolyDP simplification in PIXEL space — before normalization (IMG-06)
      7. arcLength filter — after simplification, before normalization (IMG-05)
      8. Normalize to [0, 1] per-contour (coordinate prep for Phase 2)
    """
    img = load_image(state.image_path)
    if state.verbose:
        print(f"[DEBUG] Loaded image: {state.image_path}, shape={img.shape}")

    gray = to_grayscale(img)
    h, w = gray.shape[:2]

    blur_k = state.config["edge_detection"]["blur_kernel_size"]
    # Guarantee odd kernel (OpenCV requirement: AssertionError if even)
    if blur_k % 2 == 0:
        blur_k += 1
    blurred = cv2.GaussianBlur(gray, (blur_k, blur_k), 0)

    low = state.config["edge_detection"]["canny_low"]
    high = state.config["edge_detection"]["canny_high"]
    # IMG-03: intercept "auto" string sentinel BEFORE passing to cv2.Canny
    if low == "auto" or high == "auto":
        low, high = compute_otsu_thresholds(blurred)
        if state.verbose:
            print(f"[DEBUG] Otsu thresholds: low={low:.1f}, high={high:.1f}")

    edges = cv2.Canny(blurred, float(low), float(high))

    # IMG-04: RETR_LIST keeps all contours (not just outer); CHAIN_APPROX_NONE keeps all points
    raw_contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    epsilon = state.config["edge_detection"]["simplify_epsilon"]
    min_len = state.config["edge_detection"]["min_contour_px"]

    # IMG-06: Simplify in PIXEL space (epsilon is in pixels; must happen before normalize)
    simplified = [
        cv2.approxPolyDP(c, epsilon, closed=False)
        for c in raw_contours
    ]

    # IMG-05: Filter by arc-length AFTER simplification
    filtered = [
        c for c in simplified
        if cv2.arcLength(c, closed=False) >= min_len
    ]

    merge_dist = state.config["edge_detection"]["merge_distance_px"]
    deduped = deduplicate_contours(filtered, merge_dist)

    if state.verbose:
        print(f"[DEBUG] Raw contours: {len(raw_contours)}, after filter: {len(filtered)}, after dedup: {len(deduped)}")

    # Normalize each contour to [0, 1] coordinates for resolution-independent downstream use
    state.contours_normalized = [
        normalize_contour(c, w, h) for c in deduped
    ]

    print(f"Detected {len(state.contours_normalized)} contours.")


# === PREVIEW ===

def estimate_painting_time(contours: list, config: dict) -> float:
    """CAL-03: Estimate total painting time in seconds from contour data and config.

    Formula: start_delay + (total_points * inter_point_delay) + (num_strokes * inter_stroke_delay)
    Per D-01, D-03: uses the user's actual config values so the estimate is meaningful.
    """
    painting = config.get("painting", {})
    start_delay = painting.get("start_delay", 3)
    inter_point = painting.get("inter_point_delay", 0)
    inter_stroke = painting.get("inter_stroke_delay", 0.05)

    total_points = sum(len(c) for c in contours)
    num_strokes = len(contours)

    return start_delay + (total_points * inter_point) + (num_strokes * inter_stroke)


def run_preview(state: AppState) -> None:
    """CAL-01, CAL-02: Show detected contours in an OpenCV window on a black canvas.

    IMPORTANT: Must be called from the main thread. cv2.imshow/waitKey will fail or
    produce a black window if called from any other thread.

    Canvas sizing: scales to fit within 80% of screen resolution while preserving the
    source image's aspect ratio.

    Key behavior:
      - Any key except Esc: proceed to calibration
      - Esc (key == 27): print "Aborted by user." and sys.exit(0)
    """
    contours = state.contours_normalized
    n = len(contours)

    if n == 0:
        print("No contours detected. Try lowering canny thresholds or increasing blur.")
        print("Hint: Set canny_low: auto in config.yaml to use automatic thresholding.")
        sys.exit(1)

    # Determine canvas dimensions: scale source image aspect ratio to fit 80% of screen
    # Lazy import: by the time run_preview is called, check_display_environment() has already
    # confirmed DISPLAY is set, so this import is safe even if module-level import was skipped.
    import pyautogui as _pyautogui
    screen_w, screen_h = _pyautogui.size()
    max_canvas_w = int(screen_w * 0.8)
    max_canvas_h = int(screen_h * 0.8)

    # Infer source aspect ratio from the loaded image dimensions
    src_img = cv2.imread(state.image_path)
    src_h, src_w = src_img.shape[:2] if src_img is not None else (1, 1)
    aspect = src_w / src_h

    # Fit within max_canvas dimensions preserving aspect ratio
    if max_canvas_w / aspect <= max_canvas_h:
        canvas_w = max_canvas_w
        canvas_h = max(1, int(canvas_w / aspect))
    else:
        canvas_h = max_canvas_h
        canvas_w = max(1, int(canvas_h * aspect))

    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

    for i, norm_pts in enumerate(contours):
        color = contour_color_bgr(i, n)
        # Scale normalized [0,1] coords to canvas pixel coords
        pixel_pts = (norm_pts * np.array([canvas_w, canvas_h])).astype(np.int32)
        # cv2.polylines requires shape (N, 1, 2)
        cv2.polylines(canvas, [pixel_pts.reshape(-1, 1, 2)], isClosed=False, color=color, thickness=1)

    est = estimate_painting_time(contours, state.config)
    total_points = sum(len(c) for c in contours)
    if est < 60:
        time_str = f"~{est:.0f}s"
    else:
        mins = int(est // 60)
        secs = int(est % 60)
        time_str = f"~{mins}m {secs}s"
    print(f"Preview ready. {n} contours, {total_points} points. Estimated painting time: {time_str}")
    print("Press any key to continue, Esc to abort.")

    cv2.imshow("Contour Preview", canvas)
    key = cv2.waitKey(0) & 0xFF
    cv2.destroyAllWindows()

    if key == 27:  # Esc
        print("Aborted by user.")
        sys.exit(0)

    if state.verbose:
        print(f"[DEBUG] Preview key pressed: {key}")


# === CALIBRATION ===

def capture_click_position(label: str, countdown: int = 3) -> tuple:
    """CAL-04: Block until a mouse click is detected. Print countdown first.

    Uses pynput mouse listener to capture the ACTUAL click position (not a snapshot
    after sleep — those can drift from where user intended to click).

    Returns: (x, y) tuple of integer screen coordinates.
    """
    print(f"Click {label} in:", end="", flush=True)
    for t in range(countdown, 0, -1):
        print(f" {t}...", end="", flush=True)
        time.sleep(1)
    print(" GO — click now.")

    click_pos = []

    # Lazy import: safe here because check_display_environment() confirmed DISPLAY is set.
    from pynput import mouse as _pynput_mouse

    def on_click(x, y, button, pressed):
        if pressed:
            click_pos.append((int(x), int(y)))
            return False  # returning False stops the listener

    with _pynput_mouse.Listener(on_click=on_click) as listener:
        listener.join()

    return click_pos[0]


def run_calibration(state: AppState) -> None:
    """CAL-04, CAL-05: Terminal-guided two-point bounding box capture.

    Flow:
      1. Countdown + capture top-left click
      2. Countdown + capture bottom-right click
      3. Print captured coordinates: "(x1, y1) -> (x2, y2)"
      4. Wait 2 seconds for user to review
      5. Auto-proceed (set state.bbox)

    No redo — misclick requires Ctrl+C and re-run.
    """
    countdown = state.config.get("calibration", {}).get("countdown_seconds", 3)

    print("\n--- Calibration ---")
    print("You will click two corners to define the painting canvas.")
    print("No redo: if you misclick, press Ctrl+C and re-run.\n")

    x1, y1 = capture_click_position("top-left corner", countdown)
    x2, y2 = capture_click_position("bottom-right corner", countdown)

    print(f"\nCaptured bounding box: ({x1}, {y1}) -> ({x2}, {y2})")
    print("Proceeding in 2 seconds...")
    time.sleep(2)

    state.bbox = (x1, y1, x2, y2)

    if state.verbose:
        print(f"[DEBUG] Bounding box set: {state.bbox}")
        print(f"[DEBUG] Width: {x2 - x1}px, Height: {y2 - y1}px")


# === COORDINATE MAPPING ===

def compute_draw_region(bbox: tuple, img_w: int, img_h: int) -> tuple:
    """CAL-06: Compute the letterboxed/pillarboxed draw region within bbox.

    Preserves source image aspect ratio — no stretching or distortion (D-01, D-02, D-03).
    The image fills the largest fitting axis; the shorter axis is centered with margins.

    Args:
        bbox: (x1, y1, x2, y2) screen pixel bounding box.
        img_w: Source image width in pixels.
        img_h: Source image height in pixels.

    Returns:
        (offset_x, offset_y, draw_w, draw_h) as floats.
        Caller converts to int at point-mapping time to avoid accumulated rounding error.
    """
    bx1, by1, bx2, by2 = bbox
    # Normalize so (bx1, by1) is always top-left regardless of click order
    bx1, bx2 = min(bx1, bx2), max(bx1, bx2)
    by1, by2 = min(by1, by2), max(by1, by2)
    bbox_w = bx2 - bx1
    bbox_h = by2 - by1
    img_aspect = img_w / img_h

    if bbox_w / img_aspect <= bbox_h:
        # Width-constrained (letterbox): fill width, margins top/bottom
        draw_w = float(bbox_w)
        draw_h = draw_w / img_aspect
    else:
        # Height-constrained (pillarbox): fill height, margins left/right
        draw_h = float(bbox_h)
        draw_w = draw_h * img_aspect

    # Center the draw area within the bbox
    offset_x = bx1 + (bbox_w - draw_w) / 2
    offset_y = by1 + (bbox_h - draw_h) / 2
    return offset_x, offset_y, draw_w, draw_h


def map_contour_to_screen(
    norm_contour: np.ndarray,
    offset_x: float,
    offset_y: float,
    draw_w: float,
    draw_h: float,
) -> np.ndarray:
    """CAL-06: Convert (N, 2) normalized [0, 1] contour to (N, 2) integer screen pixels.

    screen[:,0] = int(offset_x + norm[:,0] * draw_w)   # x (horizontal)
    screen[:,1] = int(offset_y + norm[:,1] * draw_h)   # y (vertical)

    Args:
        norm_contour: (N, 2) float32 array with x in column 0, y in column 1, values in [0, 1].
        offset_x: Left edge of the draw region in screen pixels (from compute_draw_region).
        offset_y: Top edge of the draw region in screen pixels (from compute_draw_region).
        draw_w: Width of the draw region in screen pixels (from compute_draw_region).
        draw_h: Height of the draw region in screen pixels (from compute_draw_region).

    Returns:
        (N, 2) int32 array of screen pixel coordinates.
    """
    screen = np.empty(norm_contour.shape, dtype=np.int32)
    screen[:, 0] = (offset_x + norm_contour[:, 0] * draw_w).astype(np.int32)
    screen[:, 1] = (offset_y + norm_contour[:, 1] * draw_h).astype(np.int32)
    return screen


def sort_contours_nearest_neighbor(contours: list) -> list:
    """PAINT-04, PAINT-05: Greedy nearest-neighbor sort starting from (0, 0) in normalized space.

    Starts from top-left of normalized space (0.0, 0.0), which maps to bbox top-left (D-08).
    For each remaining contour, measures squared euclidean distance to both endpoints.
    Picks the contour with the closest endpoint; reverses the contour if the far end is closer
    (so painting always starts from the nearer endpoint, halving average travel — D-09).
    Updates cursor position to the last painted point of each chosen contour.

    Time complexity: O(n^2) — acceptable for n < 5,000 contours (PAINT-04).

    Args:
        contours: List of (N, 2) float32 numpy arrays in normalized [0, 1] space.

    Returns:
        New sorted list of (N, 2) float32 arrays; originals are not mutated.
    """
    if not contours:
        return []

    remaining = list(contours)
    sorted_out = []
    # Start from top-left of normalized space (maps to bbox top-left after coordinate transform)
    cx, cy = 0.0, 0.0

    while remaining:
        best_idx = 0
        best_dist = float("inf")
        best_reversed = False

        for i, c in enumerate(remaining):
            # Squared distance to first and last points (no sqrt needed — comparison only)
            d_start = (c[0, 0] - cx) ** 2 + (c[0, 1] - cy) ** 2
            d_end = (c[-1, 0] - cx) ** 2 + (c[-1, 1] - cy) ** 2
            d = min(d_start, d_end)
            if d < best_dist:
                best_dist = d
                best_idx = i
                best_reversed = d_end < d_start

        chosen = remaining.pop(best_idx)
        if best_reversed:
            chosen = chosen[::-1]  # paint from the closer endpoint
        sorted_out.append(chosen)
        # Update cursor to the last painted point of this contour
        cx, cy = float(chosen[-1, 0]), float(chosen[-1, 1])

    return sorted_out


# === REPLAY ENGINE ===

def _print_progress(done: int, total: int, bar_width: int = 30) -> None:
    """PAINT-07: Single-line inline progress overwrite using \\r.

    Computes percentage, builds a filled/empty bar, and overwrites the current
    terminal line in-place. Caller must print a newline after the loop exits
    (Pitfall 7: progress bar leaves terminal in dirty state if no trailing newline).
    """
    pct = done / total if total > 0 else 1.0
    filled = int(bar_width * pct)
    bar = "#" * filled + "-" * (bar_width - filled)
    print(f"\rPainting: {done}/{total} strokes ({pct:.0%}) [{bar}]", end="", flush=True)


def _start_abort_listener(state: "AppState") -> None:
    """PAINT-06: Start pynput keyboard daemon that sets abort_flag on Esc.

    Lazy import matches Phase 1 pattern (capture_click_position).
    Must be called AFTER run_preview (cv2.imshow must be on the main thread only).
    Returning False from the callback stops the listener automatically.
    """
    from pynput import keyboard as _pynput_keyboard

    def on_press(key):
        if key == _pynput_keyboard.Key.esc:
            state.abort_flag.set()
            return False  # stops the listener

    listener = _pynput_keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()


def run_replay(state: "AppState") -> None:
    """PAINT-01, PAINT-02, PAINT-03, PAINT-06, PAINT-07, PAINT-08, CAL-06, CAL-07:
    Drive pyautogui to paint sorted, screen-mapped contours as mouse strokes.

    Entry point for the full painting session. Handles:
    - dry_run bypass
    - countdown before first stroke (CAL-07)
    - Esc abort listener start (PAINT-06)
    - nearest-neighbor contour sort (PAINT-04, PAINT-05)
    - letterbox/pillarbox coordinate mapping (CAL-06)
    - mouseDown -> moveTo sequence -> mouseUp per contour (PAINT-01)
    - configurable mouse button and delays (PAINT-02, PAINT-03)
    - inline progress reporting (PAINT-07)
    - guaranteed mouseUp on ALL exit paths via try/finally (PAINT-08)
    """
    if state.dry_run:
        print("Dry run: skipping painting.")
        return

    # CAL-06: read source image dimensions for aspect-ratio-preserving mapping
    src_img = cv2.imread(state.image_path)
    img_h, img_w = src_img.shape[:2]
    offset_x, offset_y, draw_w, draw_h = compute_draw_region(state.bbox, img_w, img_h)

    # PAINT-04, PAINT-05: sort contours in normalized space before screen mapping
    sorted_contours = sort_contours_nearest_neighbor(state.contours_normalized)

    # Map all contours to screen pixel arrays once (not per-stroke, Pitfall 5)
    screen_contours = [
        map_contour_to_screen(c, offset_x, offset_y, draw_w, draw_h)
        for c in sorted_contours
        if len(c) >= 2  # skip degenerate single-point contours
    ]

    # CAL-07: configurable countdown before first stroke
    start_delay = state.config.get("painting", {}).get("start_delay", 3)
    if start_delay > 0:
        print(f"Painting starts in:", end="", flush=True)
        for t in range(int(start_delay), 0, -1):
            print(f" {t}...", end="", flush=True)
            time.sleep(1)
        print(" GO")

    # PAINT-06: start Esc abort listener in daemon thread
    _start_abort_listener(state)

    total = len(screen_contours)
    button = state.config.get("painting", {}).get("mouse_button", "right")
    inter_stroke = state.config.get("painting", {}).get("inter_stroke_delay", 0.05)
    inter_point = state.config.get("painting", {}).get("inter_point_delay", 0)

    painted = 0
    t_start = time.time()

    # PAINT-08: try/finally guarantees mouseUp on crash, abort, or FailSafeException
    try:
        for i, pts in enumerate(screen_contours):
            if state.abort_flag.is_set():
                break

            x0, y0 = int(pts[0, 0]), int(pts[0, 1])
            pyautogui.mouseDown(x0, y0, button=button)

            for pt in pts[1:]:
                pyautogui.moveTo(int(pt[0]), int(pt[1]))
                if inter_point > 0:
                    time.sleep(inter_point)

            pyautogui.mouseUp(button=button)
            painted += 1

            # PAINT-07: inline progress overwrite
            _print_progress(painted, total)

            # Pitfall 6: skip inter-stroke delay after the last stroke
            if i < total - 1:
                time.sleep(inter_stroke)

    finally:
        # PAINT-08: unconditional release — safe to call even if button not currently held
        pyautogui.mouseUp(button=button)

    elapsed = time.time() - t_start

    # Pitfall 7: print newline to clear the \r progress line before final message
    if state.abort_flag.is_set():
        print(f"\nAborted after {painted}/{total} strokes.")
    else:
        print(f"\nDone. {painted} strokes in {elapsed:.1f}s.")


# === MAIN ===

def main() -> None:
    state = AppState()

    check_display_environment()   # CFG-05: fail fast on Wayland-only
    parse_cli(state)              # sets state.image_path, state.config_path, state.dry_run, state.verbose
    load_config(state)            # CFG-01: fills state.config; auto-generates config.yaml if absent

    run_image_pipeline(state)     # IMG-01..06: fills state.contours_normalized
    run_preview(state)            # CAL-01, CAL-02: show window, proceed or abort
    run_calibration(state)        # CAL-04, CAL-05: fills state.bbox
    run_replay(state)             # PAINT-01..08, CAL-06, CAL-07: paint contours via mouse


if __name__ == "__main__":
    main()
