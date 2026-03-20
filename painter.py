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

import pyautogui
from pynput import mouse as pynput_mouse

# CFG-06: Set PAUSE to 0 immediately after import to avoid 0.1s default per-call penalty
pyautogui.PAUSE = 0


# === CONFIGURATION ===

DEFAULT_CONFIG_CONTENT = """\
# painter.py configuration
# All parameters have sensible defaults — edit to tune for your image.

edge_detection:
  blur_kernel_size: 5        # Gaussian blur kernel (must be odd). Higher = more noise reduction.
  canny_low: 50              # Canny low threshold. Use "auto" for Otsu-based automatic selection.
  canny_high: 150            # Canny high threshold. Use "auto" for Otsu-based automatic selection.
  min_contour_px: 10         # Discard contours shorter than this (arc-length in image pixels).
  simplify_epsilon: 1.5      # Douglas-Peucker epsilon in image pixels. Higher = fewer points.

calibration:
  countdown_seconds: 3       # Seconds to count down before each calibration click capture.

painting:
  mouse_button: right        # Mouse button for strokes: "right" or "left".
  inter_stroke_delay: 0.05   # Seconds between contour strokes (mouseUp -> mouseDown pause).
"""

# Default values as a nested dict (mirrors DEFAULT_CONFIG_CONTENT) for deep_merge
_DEFAULTS = {
    "edge_detection": {
        "blur_kernel_size": 5,
        "canny_low": 50,
        "canny_high": 150,
        "min_contour_px": 10,
        "simplify_epsilon": 1.5,
    },
    "calibration": {
        "countdown_seconds": 3,
    },
    "painting": {
        "mouse_button": "right",
        "inter_stroke_delay": 0.05,
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


# === IMAGE PIPELINE (stubs — implemented in Plan 03) ===

def run_image_pipeline(state: AppState) -> None:
    """IMG-01..06: Placeholder — implemented in Plan 03."""
    raise NotImplementedError("run_image_pipeline not yet implemented")


# === PREVIEW / CALIBRATION (stubs — implemented in Plan 04) ===

def run_preview(state: AppState) -> None:
    """CAL-01, CAL-02: Placeholder — implemented in Plan 04."""
    raise NotImplementedError("run_preview not yet implemented")


def run_calibration(state: AppState) -> None:
    """CAL-04, CAL-05: Placeholder — implemented in Plan 04."""
    raise NotImplementedError("run_calibration not yet implemented")


# === MAIN ===

def main() -> None:
    state = AppState()

    check_display_environment()   # CFG-05: fail fast on Wayland-only
    parse_cli(state)              # sets state.image_path, state.config_path, state.dry_run, state.verbose
    load_config(state)            # CFG-01: fills state.config; auto-generates config.yaml if absent

    # Phase 1 stubs — filled in by Plans 03 and 04
    run_image_pipeline(state)     # IMG-01..06: fills state.contours_normalized
    run_preview(state)            # CAL-01, CAL-02: show window, proceed or abort
    run_calibration(state)        # CAL-04, CAL-05: fills state.bbox


if __name__ == "__main__":
    main()
