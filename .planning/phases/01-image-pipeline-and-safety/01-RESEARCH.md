# Phase 1: Image Pipeline and Safety - Research

**Researched:** 2026-03-20
**Domain:** OpenCV image processing pipeline, YAML configuration, Wayland/X11 detection, terminal-guided calibration
**Confidence:** HIGH (all core findings verified against project's own stack/architecture/pitfalls research; greenfield project with no existing code)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Preview Window**
- Black background with contour lines drawn on top (no original image overlay)
- Contours color-coded with rainbow gradient by drawing order (first contour red, last contour blue)
- Any key proceeds to calibration, Esc aborts the tool
- Terminal prints: "Preview ready. Press any key to continue, Esc to abort."

**Calibration Flow**
- 3-second countdown in terminal before capturing each corner click position
- Flow: "Click top-left corner in 3...2...1..." -> capture click -> "Click bottom-right corner in 3...2...1..." -> capture click
- After both clicks: print captured bounding box coordinates, pause 2 seconds for review, then auto-proceed
- No redo mechanism — misclick = Ctrl+C and re-run the tool

**Config File Structure**
- YAML format, grouped by concern (sections like `edge_detection:`, `painting:`, `calibration:`, etc.)
- Config file lives next to the script (same directory as `painter.py`)
- If no config file exists on first run, auto-generate `config.yaml` with annotated defaults
- Canny auto-threshold uses special string value `"auto"` in YAML (e.g., `canny_low: auto`) rather than a separate boolean flag

**Script Invocation**
- Script named `painter.py`
- Basic usage: `python painter.py image.png` (image path as positional argument)
- CLI flags: `--config path/to/config.yaml`, `--dry-run`, `--verbose`
- Everything else configured via YAML

**Safety Infrastructure**
- Wayland detection at startup: check for `WAYLAND_DISPLAY` without `DISPLAY`, fail with actionable error
- `pyautogui.PAUSE = 0` set at startup
- Right-click (`button='right'`) as default mouse button for strokes (configurable in YAML)

### Claude's Discretion
- Preview window sizing (scale to fit screen vs match source dimensions)
- Exact YAML section names and parameter naming conventions
- Log format for --verbose output
- How click position is captured (pyautogui.position() after pynput click event, or other approach)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| IMG-01 | User can load any PNG and have it converted to grayscale automatically | `cv2.imread()` + `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)` — straightforward; reject non-PNG or missing file with clear error |
| IMG-02 | Tool runs Canny edge detection with configurable low/high thresholds and blur kernel size | `cv2.GaussianBlur()` before `cv2.Canny()`; all three params come from YAML `edge_detection:` section |
| IMG-03 | Tool provides Otsu-based auto-threshold as a fallback when thresholds set to "auto" | `cv2.threshold(..., cv2.THRESH_OTSU)` computes Otsu value; use `high = otsu, low = 0.5 * otsu` (standard ratio); triggered by YAML `canny_low: "auto"` string |
| IMG-04 | Tool extracts ordered contour polylines from the edge map | `cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)` — RETR_LIST avoids hierarchy complexity; CHAIN_APPROX_NONE retains all points before simplification step |
| IMG-05 | Tool filters out contours below a configurable minimum arc-length | `cv2.arcLength(contour, closed=False) < min_length` filter after extraction; YAML param `edge_detection.min_contour_px` with default 10 |
| IMG-06 | Tool simplifies contour points using Douglas-Peucker with configurable epsilon | `cv2.approxPolyDP(contour, epsilon, closed=False)` in pixel space; YAML param `edge_detection.simplify_epsilon` default 1.5; simplify BEFORE normalize to keep epsilon intuitive |
| CAL-01 | Tool displays detected contours in an OpenCV preview window before painting | `cv2.imshow()` + `cv2.waitKey(0)` on main thread; draw on a black canvas using `cv2.drawContours()` with rainbow color per contour |
| CAL-02 | User can abort from preview (Esc) or proceed (any other key) | `cv2.waitKey(0) & 0xFF == 27` for Esc; any other return value proceeds |
| CAL-04 | Terminal-guided capture mode: user clicks top-left then bottom-right | 3-second countdown with `time.sleep(1)` per tick; capture via `pyautogui.position()` polled after pynput click event OR `time.sleep(3)` + `pyautogui.position()` (see discretion note) |
| CAL-05 | Tool displays captured bounding box coordinates for confirmation before proceeding | Print `(x1, y1) -> (x2, y2)` after both captures; `time.sleep(2)` then auto-proceed |
| CFG-01 | All parameters stored in a YAML config file with sensible defaults | `pyyaml.safe_load()`; auto-generate `config.yaml` with annotated defaults on first run if file absent |
| CFG-05 | Tool detects Wayland-only sessions and fails with an actionable error message | Check `os.environ.get("WAYLAND_DISPLAY")` AND `os.environ.get("DISPLAY")` at startup; if Wayland present and no DISPLAY, exit with clear message |
| CFG-06 | pyautogui.PAUSE set to 0 at startup to avoid 0.1s default penalty | `pyautogui.PAUSE = 0` immediately after import; documented in code comment |
</phase_requirements>

---

## Summary

Phase 1 builds the entire skeleton of `painter.py` — every component that can be implemented and verified without actually moving the mouse. The image pipeline (load → grayscale → blur → Canny → findContours → arcLength filter → approxPolyDP simplification) is a pure data transformation chain with no side effects; each step is testable in isolation. The OpenCV preview window and terminal calibration flow are the two user-visible outputs. Wayland detection and `pyautogui.PAUSE = 0` are safety preconditions that must be in place before Phase 2 adds mouse replay.

The biggest implementation decision left to Claude's discretion is how click position is captured during calibration. Two viable approaches exist: (1) `time.sleep(3)` countdown then snapshot `pyautogui.position()` — simplest, no extra library, but requires user to hold cursor still; (2) pynput mouse listener that captures the actual click event position. The pynput approach is more accurate but adds a listener to a phase that intentionally has no painting yet. Given that pynput is already in the dependency list for Phase 2's abort mechanism, wiring it here for click capture is consistent and worth the small extra complexity.

The rainbow gradient preview (red → blue by drawing order) requires generating interpolated HSV colors across N contours and converting to BGR for OpenCV drawing. This is a small but non-trivial utility function. The preview window should scale the black canvas to a reasonable screen size (e.g., cap at 1200px on the longer dimension) to avoid rendering a 4K image at full size on a laptop display — this is Claude's discretion to implement.

**Primary recommendation:** Build in the order dictated by ARCHITECTURE.md — Config Loader first (everything reads it), then Image Pipeline, then Preview, then Calibration. Wire them together through an `AppState` dataclass as established in the architecture research.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| opencv-python | 4.13.0.86 | Image load, grayscale, Gaussian blur, Canny, findContours, approxPolyDP, imshow, waitKey | De facto CV standard; all required operations built-in; no alternatives needed |
| numpy | 2.1.x (Python 3.10) / 2.4.3 (Python 3.11+) | Contour array manipulation, color interpolation for preview | OpenCV contours are already numpy arrays; squeeze (N,1,2) to (N,2) before math |
| pyyaml | 6.0.3 | Load and auto-generate YAML config | Safe, stable; `yaml.safe_load()` is the correct API |
| pyautogui | 0.9.54 | `pyautogui.position()` for calibration click capture; `PAUSE = 0` safety setting | Mandated by PROJECT.md; X11/XWayland only on Linux |
| pynput | 1.8.1 | Mouse click listener for calibration capture (discretion), keyboard listener infrastructure | Already in dependency list for Phase 2 abort; wiring here is consistent |
| Python | 3.11+ recommended, 3.10 minimum | Runtime | numpy 2.4.x dropped Python 3.10 — pin numpy to 2.1.x if staying on 3.10 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scikit-image | 0.26.0 | Alternative Canny with sigma control | Only if OpenCV Canny produces unsatisfactory edges on noisy inputs; not needed for clean line art |
| argparse | stdlib | CLI argument parsing (`--config`, `--dry-run`, `--verbose`) | Already in Python stdlib; no additional install |
| time | stdlib | Countdown sleep for calibration, 2-second review pause | stdlib |
| os | stdlib | Environment variable access for Wayland detection | stdlib |
| threading | stdlib | `threading.Event` for abort flag (wired now, used in Phase 2) | stdlib |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `cv2.approxPolyDP` | `rdp` or `simplification` PyPI packages | Never for this project — built-in handles all contour sizes encountered |
| `cv2.Canny` | `skimage.feature.canny` | Use skimage only if sigma control is needed for noisy photographs |
| `yaml.safe_load()` | `yaml.load()` | Never use `yaml.load()` — security risk; `safe_load` is always correct here |
| `cv2.RETR_LIST` | `cv2.RETR_EXTERNAL` | RETR_EXTERNAL discards inner contours (holes); RETR_LIST keeps all — use RETR_LIST for line art |

**Installation:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install opencv-python numpy pyyaml pyautogui pynput
# Optional only if OpenCV Canny is insufficient:
pip install scikit-image
```

---

## Architecture Patterns

### Recommended Project Structure

```
painter.py          # Single file — all components as functions within one script
config.yaml         # Auto-generated on first run if absent; user-editable
requirements.txt    # Pin: opencv-python, numpy, pyyaml, pyautogui, pynput
```

Phase 1 establishes the full single-file structure with section-header comments:

```python
# === CONFIGURATION ===
# === IMAGE PIPELINE ===
# === PREVIEW ===
# === CALIBRATION ===
# === MAIN ===
```

Sections in source order mirror execution order — top-to-bottom reading matches runtime flow.

### Pattern 1: AppState Dataclass as Single Source of Truth

**What:** One `AppState` dataclass instance is created in `main()` and passed explicitly to every phase function. No module-level globals.

**When to use:** This is the established pattern for this project — use it from the first function written.

**Example:**
```python
# Source: .planning/research/ARCHITECTURE.md
from dataclasses import dataclass, field
import threading
from typing import List
import numpy as np

@dataclass
class AppState:
    config: dict = field(default_factory=dict)
    image_path: str = ""
    contours_normalized: List[np.ndarray] = field(default_factory=list)
    bbox: tuple = None          # (x1, y1, x2, y2) screen pixels, set in Phase 1 calibration
    abort_flag: threading.Event = field(default_factory=threading.Event)

def main():
    state = AppState()
    check_display_environment()   # CFG-05: fail fast on Wayland-only
    parse_cli(state)              # sets state.image_path, state.config path, etc.
    load_config(state)            # CFG-01: fills state.config
    run_image_pipeline(state)     # IMG-01..06: fills state.contours_normalized
    run_preview(state)            # CAL-01, CAL-02: show window, proceed or abort
    run_calibration(state)        # CAL-04, CAL-05: fills state.bbox
```

### Pattern 2: Purely Functional Image Pipeline

**What:** Each image processing step is a function that takes data + config values and returns transformed data. No mutations to state inside these functions — only `run_image_pipeline()` writes to `state.contours_normalized`.

**When to use:** Always — these steps have clean inputs/outputs and can be unit-tested without screen interaction.

**Example:**
```python
# Source: .planning/research/ARCHITECTURE.md
def run_image_pipeline(state: AppState):
    img = load_image(state.image_path)           # IMG-01
    gray = to_grayscale(img)
    blur_k = state.config["edge_detection"]["blur_kernel_size"]
    blurred = cv2.GaussianBlur(gray, (blur_k, blur_k), 0)  # IMG-02
    low = state.config["edge_detection"]["canny_low"]
    high = state.config["edge_detection"]["canny_high"]
    if low == "auto" or high == "auto":
        low, high = compute_otsu_thresholds(blurred)        # IMG-03
    edges = cv2.Canny(blurred, low, high)
    raw_contours = cv2.findContours(
        edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE
    )[0]                                                    # IMG-04
    epsilon = state.config["edge_detection"]["simplify_epsilon"]
    min_len = state.config["edge_detection"]["min_contour_px"]
    simplified = [cv2.approxPolyDP(c, epsilon, False) for c in raw_contours]  # IMG-06
    filtered = [c for c in simplified
                if cv2.arcLength(c, False) >= min_len]     # IMG-05
    h, w = img.shape[:2]
    state.contours_normalized = [normalize_contour(c, w, h) for c in filtered]
```

### Pattern 3: Preview on Black Canvas with Rainbow Gradient

**What:** Draw simplified contours (not raw Canny edges) on a black background using per-contour HSV color interpolated from red (index 0) to blue (last index). Scale canvas to fit screen before displaying.

**When to use:** This is the locked decision — must be implemented exactly this way (CAL-01).

**Example:**
```python
def run_preview(state: AppState):
    n = len(state.contours_normalized)
    if n == 0:
        print("No contours detected. Adjust canny thresholds and retry.")
        sys.exit(1)

    # Reconstruct pixel contours for drawing (preview uses pixel coords)
    # Use a fixed canvas size for the preview — scale to max 1200px long side
    canvas_h, canvas_w = 800, 1200  # or derive from screen resolution

    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

    for i, norm_c in enumerate(state.contours_normalized):
        # Rainbow: hue goes from 0 (red) to 240 (blue) across N contours
        hue = int(240 * i / max(n - 1, 1))
        color_hsv = np.uint8([[[hue, 255, 255]]])
        color_bgr = cv2.cvtColor(color_hsv, cv2.COLOR_HSV2BGR)[0][0].tolist()
        # Scale norm coords to canvas
        pts = (norm_c * [canvas_w, canvas_h]).astype(np.int32)
        cv2.polylines(canvas, [pts.reshape(-1, 1, 2)], False, color_bgr, 1)

    print(f"Preview ready. {n} contours. Press any key to continue, Esc to abort.")
    cv2.imshow("Contour Preview", canvas)
    key = cv2.waitKey(0) & 0xFF
    cv2.destroyAllWindows()
    if key == 27:  # Esc
        print("Aborted by user.")
        sys.exit(0)
```

### Pattern 4: Otsu Auto-Threshold

**What:** When `canny_low: "auto"` is set in YAML, compute Otsu threshold from the blurred grayscale image and derive Canny thresholds using the standard 0.5/1.0 ratio.

**When to use:** IMG-03 requirement — must activate when YAML value is the string `"auto"`.

**Example:**
```python
def compute_otsu_thresholds(blurred_gray):
    # Source: https://pyimagesearch.com/2015/04/06/zero-parameter-automatic-canny-edge-detection-with-python-and-opencv/
    otsu_thresh, _ = cv2.threshold(
        blurred_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )
    high = otsu_thresh
    low = 0.5 * otsu_thresh
    return low, high
```

### Pattern 5: Wayland Detection at Startup

**What:** Check environment variables at process start. If `WAYLAND_DISPLAY` is set but `DISPLAY` is not, exit immediately with an actionable error before any library imports that would fail on Wayland.

**When to use:** CFG-05 — must be the very first check in `main()`.

**Example:**
```python
def check_display_environment():
    wayland = os.environ.get("WAYLAND_DISPLAY")
    display = os.environ.get("DISPLAY")
    if wayland and not display:
        print(
            "Error: This tool requires an X11 session.\n"
            "You appear to be running a Wayland-only session "
            f"(WAYLAND_DISPLAY={wayland}, DISPLAY not set).\n"
            "Options:\n"
            "  1. Log out and select an X11 session at your login screen.\n"
            "  2. Start XWayland and set DISPLAY=:0 before running.\n"
            "  3. Run: DISPLAY=:0 python painter.py image.png"
        )
        sys.exit(1)
```

### Pattern 6: YAML Config Auto-Generation

**What:** On startup, if the config file does not exist, write a `config.yaml` with annotated defaults next to `painter.py`. Parse path relative to `__file__`.

**When to use:** CFG-01 — first run experience must be self-documenting.

**Example:**
```python
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

def load_config(state: AppState):
    import yaml
    config_path = state.config_path  # resolved from --config or default next to __file__
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write(DEFAULT_CONFIG_CONTENT)
        print(f"Created default config: {config_path}")
    with open(config_path) as f:
        loaded = yaml.safe_load(f) or {}
    # Merge with defaults so missing keys never cause KeyErrors
    state.config = deep_merge(DEFAULT_DICT, loaded)
```

### Anti-Patterns to Avoid

- **`yaml.load()` without Loader:** Always use `yaml.safe_load()`. `yaml.load()` executes arbitrary Python via YAML tags.
- **OpenCV imshow off main thread:** `cv2.imshow()` and `cv2.waitKey()` must be called from the main thread on Linux. Never spawn a thread just to show the preview.
- **`cv2.RETR_EXTERNAL` for line art:** Discards inner contours (e.g., letters with holes like "O"). Use `cv2.RETR_LIST` to capture all edges.
- **Simplification after normalization:** Always run `cv2.approxPolyDP` in pixel space. If run in normalized 0–1 space, epsilon becomes unintuitive (e.g., `1.5` becomes `1.5 / image_width` which is nearly 0 for large images).
- **Module-level globals for state:** Use the `AppState` dataclass. Plain globals are not thread-safe and obscure data flow.
- **Forgetting `pyautogui.PAUSE = 0`:** Set immediately after import at module level, not inside a function. CFG-06 is a module-level concern.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Douglas-Peucker point reduction | Custom RDP implementation | `cv2.approxPolyDP(contour, epsilon, closed=False)` | Built-in, operates directly on OpenCV contour arrays, handles edge cases |
| Canny auto-threshold | Binary search for threshold | `cv2.threshold(..., cv2.THRESH_BINARY \| cv2.THRESH_OTSU)` | Otsu's method is the standard auto-threshold algorithm; built into OpenCV |
| HSV to BGR color conversion | Manual HSV math | `cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2BGR)` | OpenCV handles all color space math correctly |
| YAML parsing | Custom file parser | `yaml.safe_load()` | PyYAML handles all YAML edge cases including multi-line strings and special characters |
| Contour arc length measurement | Summing point-to-point distances | `cv2.arcLength(contour, closed=False)` | Built-in; handles curve approximation correctly |
| Image normalization | Manual pixel coordinate division | numpy broadcasting: `contour.squeeze() / np.array([w, h])` | One-liner; no loops needed; handles any contour shape |

**Key insight:** OpenCV already implements every image processing operation this phase needs. Custom implementations would be slower, less tested, and harder to maintain.

---

## Common Pitfalls

### Pitfall 1: Wayland Detection Logic Is Insufficient
**What goes wrong:** Checking only `WAYLAND_DISPLAY` without checking `DISPLAY` gives false positives on XWayland setups (where both variables exist and pyautogui works fine).
**Why it happens:** Developer only looks for the Wayland variable, missing that XWayland sets both.
**How to avoid:** Fail only when `WAYLAND_DISPLAY` is set AND `DISPLAY` is not set. If both are set, XWayland is available — proceed normally.
**Warning signs:** Tool exits with Wayland error on a system where XWayland is running.

### Pitfall 2: OpenCV Preview on Non-Main Thread
**What goes wrong:** Preview window appears black, is unresponsive, or crashes with a GTK/Qt error.
**Why it happens:** OpenCV's GUI subsystem on Linux must be driven from the process's main thread. Spawning a thread for preview violates this.
**How to avoid:** Never call `cv2.imshow()` or `cv2.waitKey()` from any thread except the main one. The calibration listener threads must be started after `cv2.destroyAllWindows()`.
**Warning signs:** Black preview window that doesn't respond to keypresses; GTK assertion errors in stderr.

### Pitfall 3: Canny Threshold Strings Not Handled at Load Time
**What goes wrong:** Config yields `canny_low: "auto"` as a Python string; code tries `cv2.Canny(img, "auto", 150)` and crashes with a type error.
**Why it happens:** Config is loaded directly into a dict; the "auto" string sentinel must be intercepted before it reaches OpenCV.
**How to avoid:** In `run_image_pipeline`, check `if low == "auto" or high == "auto"` and replace with Otsu-derived values before calling `cv2.Canny`.
**Warning signs:** `TypeError: expected numeric argument` from `cv2.Canny`.

### Pitfall 4: Contour Shape Convention Mismatch
**What goes wrong:** OpenCV returns contours as arrays of shape `(N, 1, 2)` — an extra dimension that causes index errors or wrong math when treated as `(N, 2)`.
**Why it happens:** The `reshape(-1, 1, 2)` requirement for `cv2.polylines` uses the 3D shape, but math operations (normalization, coordinate transform) need the 2D `(N, 2)` shape. Forgetting to squeeze causes silent axis confusion.
**How to avoid:** Use `.squeeze(axis=1)` or `.reshape(-1, 2)` before any math. Use `.reshape(-1, 1, 2)` only when calling `cv2.polylines` or `cv2.drawContours`.
**Warning signs:** Normalized coordinates outside [0, 1] range; drawing appears as a dot cluster instead of a line.

### Pitfall 5: YAML Config Missing Keys Cause Runtime KeyErrors
**What goes wrong:** User deletes a config key and the tool crashes mid-run with `KeyError: 'simplify_epsilon'`.
**Why it happens:** `yaml.safe_load()` only returns what's in the file; missing keys aren't populated automatically.
**How to avoid:** Always merge loaded config against a full default dict. Use a `deep_merge()` helper that fills in any missing nested keys from defaults. Validate required keys exist after merge; warn on unexpected/unknown keys (possible typos).
**Warning signs:** Tool works on first run (auto-generated config), breaks after user edits config.

### Pitfall 6: blur_kernel_size Must Be Odd
**What goes wrong:** `cv2.GaussianBlur(img, (4, 4), 0)` raises `error: (-215:Assertion failed) ksize.width > 0 && ksize.width % 2 == 1`.
**Why it happens:** Gaussian kernel size must be a positive odd integer — OpenCV enforces this.
**How to avoid:** Validate `blur_kernel_size` at config load time: if even, increment by 1 and log a warning. Document the constraint in the YAML comment.
**Warning signs:** OpenCV assertion error immediately after image load.

### Pitfall 7: Calibration Click Capture Requires Focus-Aware Timing
**What goes wrong:** The 3-second countdown elapses but `pyautogui.position()` captures the cursor position at countdown start, not at click time — user hasn't had time to position cursor.
**Why it happens:** `pyautogui.position()` is a snapshot, not an event. Calling it after `time.sleep(3)` captures wherever the mouse ended up, regardless of whether a click occurred.
**How to avoid:** Use one of two approaches:
  1. **pynput click listener:** Register a `pynput.mouse.Listener` that captures position on the first `on_click` event, then stops. This records the actual click position.
  2. **Extended countdown + position snapshot:** Print "Move cursor to corner and HOLD" during countdown, then snapshot after full delay. Simpler but less accurate — cursor position may drift.
  Option 1 (pynput click) is recommended since pynput is already a dependency. See the Code Examples section.
**Warning signs:** Bounding box coordinates off by 20–50px from where user intended to click.

---

## Code Examples

Verified patterns from official sources and project architecture research.

### Otsu Auto-Threshold Derivation
```python
# Source: https://pyimagesearch.com/2015/04/06/zero-parameter-automatic-canny-edge-detection-with-python-and-opencv/
def compute_otsu_thresholds(blurred_gray: np.ndarray) -> tuple[float, float]:
    otsu_thresh, _ = cv2.threshold(
        blurred_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )
    high = float(otsu_thresh)
    low = 0.5 * high
    return low, high
```

### Contour Extraction (Correct Flags)
```python
# Source: .planning/research/STACK.md + OpenCV docs
# RETR_LIST: all contours, no hierarchy (correct for line art)
# CHAIN_APPROX_NONE: keep all points (simplification happens next)
contours, _ = cv2.findContours(
    edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE
)
```

### Contour Normalization (Correct Array Handling)
```python
# Source: .planning/research/ARCHITECTURE.md (coordinate math section)
def normalize_contour(contour: np.ndarray, img_w: int, img_h: int) -> np.ndarray:
    # contour shape from findContours: (N, 1, 2)
    # squeeze to (N, 2) for math; re-wrap to (N, 1, 2) only for drawing functions
    pts = contour.reshape(-1, 2).astype(np.float32)
    pts[:, 0] /= img_w   # x / width
    pts[:, 1] /= img_h   # y / height
    return pts  # shape (N, 2), values in [0.0, 1.0]
```

### Rainbow Color Per Contour
```python
# Hue 0=red, 120=green, 240=blue — interpolate across N contours
def contour_color_bgr(index: int, total: int) -> tuple:
    hue = int(240 * index / max(total - 1, 1))
    hsv_pixel = np.uint8([[[hue, 255, 255]]])
    bgr = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)[0][0]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])
```

### Preview Canvas Drawing
```python
# Source: .planning/research/ARCHITECTURE.md + locked decisions in CONTEXT.md
def run_preview(state: AppState):
    contours = state.contours_normalized
    n = len(contours)
    if n == 0:
        print("No contours detected. Try lowering canny thresholds or blur.")
        sys.exit(1)

    canvas_h, canvas_w = 900, 1200  # scale to taste; see Claude's Discretion
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

    for i, norm_pts in enumerate(contours):
        color = contour_color_bgr(i, n)
        pixel_pts = (norm_pts * [canvas_w, canvas_h]).astype(np.int32)
        cv2.polylines(canvas, [pixel_pts.reshape(-1, 1, 2)], False, color, 1)

    print(f"Preview ready. {n} contours detected.")
    print("Press any key to continue, Esc to abort.")
    cv2.imshow("Contour Preview", canvas)
    key = cv2.waitKey(0) & 0xFF
    cv2.destroyAllWindows()
    if key == 27:
        print("Aborted by user.")
        sys.exit(0)
```

### Calibration with pynput Click Capture
```python
# Claude's discretion: pynput click listener for accurate position capture
from pynput import mouse as pynput_mouse

def capture_click_position(label: str, countdown: int = 3) -> tuple[int, int]:
    """Block until a mouse click is detected. Print countdown first."""
    print(f"Click {label} in:", end="", flush=True)
    for t in range(countdown, 0, -1):
        print(f" {t}...", end="", flush=True)
        time.sleep(1)
    print(" GO — click now.")

    click_pos = []
    def on_click(x, y, button, pressed):
        if pressed:
            click_pos.append((x, y))
            return False  # stop listener

    with pynput_mouse.Listener(on_click=on_click) as listener:
        listener.join()

    return click_pos[0]

def run_calibration(state: AppState):
    countdown = state.config.get("calibration", {}).get("countdown_seconds", 3)
    x1, y1 = capture_click_position("top-left corner", countdown)
    x2, y2 = capture_click_position("bottom-right corner", countdown)
    print(f"\nCaptured bounding box: ({x1}, {y1}) -> ({x2}, {y2})")
    print("Proceeding in 2 seconds...")
    time.sleep(2)
    state.bbox = (x1, y1, x2, y2)
```

### YAML Deep Merge Helper
```python
def deep_merge(defaults: dict, overrides: dict) -> dict:
    """Merge overrides into defaults, filling missing keys from defaults."""
    result = dict(defaults)
    for key, val in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = val
    return result
```

### CLI Argument Parsing
```python
import argparse

def parse_cli(state: AppState):
    parser = argparse.ArgumentParser(description="Paint image contours via mouse replay")
    parser.add_argument("image", help="Path to input PNG image")
    parser.add_argument("--config", default=None, help="Path to config YAML file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run pipeline and calibration but skip painting")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable debug output")
    args = parser.parse_args()
    state.image_path = args.image
    state.dry_run = args.dry_run
    state.verbose = args.verbose
    if args.config:
        state.config_path = args.config
    else:
        # Default: config.yaml next to painter.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        state.config_path = os.path.join(script_dir, "config.yaml")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Global variables for shared state | `dataclass`-based AppState passed explicitly | Python 3.7+ (dataclasses stdlib) | Thread safety clarity, testability |
| Manual RDP implementation | `cv2.approxPolyDP` built-in | OpenCV 2.x+ | One fewer dependency, faster |
| `yaml.load()` without Loader | `yaml.safe_load()` | PyYAML 5.1 (2019) | Security — `yaml.load()` is now deprecated in favor of explicit Loader or `safe_load` |
| `pyautogui.FAILSAFE` corner as abort | `threading.Event` + pynput listener | Project decision | More intentional, less accidental triggers |

**Deprecated/outdated:**
- `yaml.load(f)` without Loader: insecure, PyYAML 6.x emits a warning; always use `yaml.safe_load(f)`
- `keyboard` library: last release March 2020, requires root on Linux — do not use; use pynput instead
- `cv2.RETR_EXTERNAL` for this use case: acceptable for outer-only contours, but `RETR_LIST` is more appropriate for line art where inner contours (letter holes, etc.) are meaningful

---

## Open Questions

1. **Preview window canvas sizing (Claude's Discretion)**
   - What we know: The preview must render at a reasonable size (not full 4K for a 4K image)
   - What's unclear: Whether to derive canvas size from screen resolution (`pyautogui.size()`) or use a fixed cap
   - Recommendation: Use `pyautogui.size()` to get screen dimensions, then scale the preview canvas to fit within 80% of screen dimensions while preserving the source image's aspect ratio. This is a ~5 line computation.

2. **YAML section naming (Claude's Discretion)**
   - What we know: Sections should be grouped by concern; locked decisions show `edge_detection:`, `painting:`, `calibration:` as section names
   - What's unclear: Whether to use snake_case or camelCase for parameter names
   - Recommendation: Use `snake_case` throughout — consistent with Python conventions and most YAML examples. Example: `simplify_epsilon`, `blur_kernel_size`, `min_contour_px`.

3. **Verbose log format (Claude's Discretion)**
   - What we know: `--verbose` enables debug output
   - What's unclear: Whether to use Python's `logging` module or simple `print()` with a verbose guard
   - Recommendation: Simple `if state.verbose: print(f"[DEBUG] ...")` pattern for a single-file tool. The `logging` module adds boilerplate without meaningful benefit at this scale.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (not yet installed — see Wave 0) |
| Config file | `pytest.ini` or `pyproject.toml` — none exists yet |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| IMG-01 | `load_image()` returns a numpy array for a valid PNG; raises clear error for missing file | unit | `pytest tests/test_image_pipeline.py::test_load_image -x` | Wave 0 |
| IMG-02 | Canny runs with numeric thresholds from config; blurred intermediate is produced | unit | `pytest tests/test_image_pipeline.py::test_canny_numeric -x` | Wave 0 |
| IMG-03 | `compute_otsu_thresholds()` returns (low, high) floats; pipeline uses them when config value is `"auto"` | unit | `pytest tests/test_image_pipeline.py::test_otsu_auto -x` | Wave 0 |
| IMG-04 | `cv2.findContours` returns a list of contours; pipeline does not crash on a blank edge image | unit | `pytest tests/test_image_pipeline.py::test_find_contours -x` | Wave 0 |
| IMG-05 | Contours shorter than `min_contour_px` are excluded from output | unit | `pytest tests/test_image_pipeline.py::test_min_length_filter -x` | Wave 0 |
| IMG-06 | `cv2.approxPolyDP` reduces point count; normalized output is in [0, 1] range | unit | `pytest tests/test_image_pipeline.py::test_simplify_normalize -x` | Wave 0 |
| CAL-01 | Preview draws on a black background with N colored polylines | manual-only | n/a (requires display) | n/a |
| CAL-02 | Esc key exits with code 0; any other key does not exit | manual-only | n/a (requires display + keyboard input) | n/a |
| CAL-04 | Calibration captures two (x, y) positions | manual-only | n/a (requires physical mouse interaction) | n/a |
| CAL-05 | Bounding box is printed before proceeding | manual-only | n/a | n/a |
| CFG-01 | Config file auto-generated with correct keys when absent; existing file loaded without error | unit | `pytest tests/test_config.py::test_config_autogenerate -x` | Wave 0 |
| CFG-01 | Deep merge fills missing keys from defaults | unit | `pytest tests/test_config.py::test_deep_merge -x` | Wave 0 |
| CFG-05 | `check_display_environment()` exits with non-zero when WAYLAND_DISPLAY set and DISPLAY absent | unit | `pytest tests/test_safety.py::test_wayland_exit -x` | Wave 0 |
| CFG-05 | No exit when both WAYLAND_DISPLAY and DISPLAY are set (XWayland) | unit | `pytest tests/test_safety.py::test_xwayland_ok -x` | Wave 0 |
| CFG-06 | `pyautogui.PAUSE == 0` after module initialization | unit | `pytest tests/test_safety.py::test_pause_zero -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_image_pipeline.py` — covers IMG-01..06
- [ ] `tests/test_config.py` — covers CFG-01 (load, auto-generate, deep merge)
- [ ] `tests/test_safety.py` — covers CFG-05, CFG-06
- [ ] `tests/conftest.py` — shared fixtures (tmp config file, sample test PNG, mock environment)
- [ ] Framework install: `pip install pytest` — not yet in requirements

**Note on manual-only tests:** CAL-01, CAL-02, CAL-04, CAL-05 require a live display and physical input — they cannot be automated without complex mocking. Verify these manually during implementation using the success criteria from the phase description.

---

## Sources

### Primary (HIGH confidence)
- `.planning/research/STACK.md` — Library versions, pyautogui Wayland limitation, numpy Python version constraint
- `.planning/research/ARCHITECTURE.md` — AppState dataclass pattern, component boundaries, data flow, coordinate math
- `.planning/research/PITFALLS.md` — Wayland blockers, pyautogui.PAUSE default, contour ordering issues, thread safety
- `.planning/phases/01-image-pipeline-and-safety/01-CONTEXT.md` — Locked implementation decisions for this phase

### Secondary (MEDIUM confidence)
- OpenCV Canny tutorial — https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html
- PyImageSearch Otsu auto-threshold — https://pyimagesearch.com/2015/04/06/zero-parameter-automatic-canny-edge-detection-with-python-and-opencv/
- pynput mouse listener docs — https://pynput.readthedocs.io/en/latest/mouse.html
- PyAutoGUI PAUSE documentation — https://pyautogui.readthedocs.io/en/latest/mouse.html

### Tertiary (LOW confidence)
None — all findings supported by project's own verified research.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified against PyPI in project's STACK.md (2026-03-19)
- Architecture: HIGH — patterns established in project's ARCHITECTURE.md with code examples
- Pitfalls: HIGH — all pitfalls cross-referenced against project's PITFALLS.md and official docs
- Validation: MEDIUM — test structure is a projection; exact pytest fixtures depend on implementation choices made during planning

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable libraries; OpenCV and PyYAML APIs change slowly)
