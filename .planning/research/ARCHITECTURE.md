# Architecture Research

**Domain:** Single-file Python image-to-mouse-stroke automation tool
**Researched:** 2026-03-19
**Confidence:** HIGH (core pipeline patterns well-established; Wayland caveat MEDIUM)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Entry Point / Orchestrator               │
│  main() — loads config, runs phases in sequence, handles abort  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────────┐  │
│  │  Config       │  │  Image         │  │  Calibration       │  │
│  │  Loader       │  │  Pipeline      │  │  / Capture         │  │
│  │               │  │                │  │                    │  │
│  │ YAML → dict   │  │ load → gray    │  │ terminal prompts   │  │
│  │ validation    │  │ → canny → find │  │ → click 2 points   │  │
│  │ defaults      │  │ contours →     │  │ → confirm bbox     │  │
│  └───────┬───────┘  │ simplify →     │  └────────┬───────────┘  │
│          │          │ filter →       │           │              │
│          │          │ normalize      │           │              │
│          │          └───────┬────────┘           │              │
│          │                  │                    │              │
├──────────┼──────────────────┼────────────────────┼──────────────┤
│          │           Shared State                │              │
│          │  ┌─────────────────────────────────┐  │              │
│          └─►│  AppState dataclass             │◄─┘              │
│             │  config, contours, bbox,        │                 │
│             │  abort_flag (threading.Event)   │                 │
│             └─────────────┬───────────────────┘                 │
│                           │                                     │
├───────────────────────────┼─────────────────────────────────────┤
│                           │                                     │
│  ┌────────────────┐  ┌────▼────────────┐  ┌──────────────────┐  │
│  │  Preview       │  │  Coordinate     │  │  Hotkey          │  │
│  │  (OpenCV)      │  │  Transformer    │  │  Listener        │  │
│  │                │  │                 │  │  (daemon thread) │  │
│  │ draw contours  │  │ normalize 0-1   │  │                  │  │
│  │ on image copy  │  │ → scale to bbox │  │ pynput Listener  │  │
│  │ waitKey        │  │ pixel coords    │  │ ESC → sets       │  │
│  │ proceed/abort  │  │                 │  │ abort_flag       │  │
│  └────────────────┘  └────┬────────────┘  └──────────────────┘  │
│                           │                                     │
├───────────────────────────┼─────────────────────────────────────┤
│                           │                                     │
│  ┌────────────────────────▼──────────────────────────────────┐  │
│  │                   Replay Engine                            │  │
│  │                                                           │  │
│  │  for each contour:                                        │  │
│  │    mouseDown → moveTo(pts) → mouseUp                      │  │
│  │    check abort_flag between strokes                       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Boundary |
|-----------|----------------|----------|
| Config Loader | Read YAML, apply defaults, validate ranges | Owns all user-facing parameters; no other component reads YAML directly |
| Image Pipeline | grayscale → Canny → findContours → simplify → filter → normalize | Purely functional — takes image path + config, returns list of normalized polylines (0.0–1.0 coords) |
| Calibration / Capture | Terminal-guided capture of two reference points defining screen bbox | Owns screen interaction before painting; outputs `(x1,y1,x2,y2)` bounding box |
| Preview | Draw normalized contours on image, show OpenCV window, await user keypress | Read-only view; outputs proceed/abort decision |
| Coordinate Transformer | Map normalized `(0.0–1.0, 0.0–1.0)` → screen pixel `(px, py)` | Purely math — stateless function, no side effects |
| Hotkey Listener | daemon thread watching keyboard; sets `abort_flag` on Esc | Writes only to `abort_flag`; never touches contours or mouse |
| Replay Engine | Drives pyautogui stroke-by-stroke; polls `abort_flag` between strokes | Owns mouse control; reads from Coordinate Transformer + AppState |
| AppState | Shared dataclass passed through all phases | Single source of truth — config, contours, bbox, abort_flag |

## Recommended Project Structure

```
slaypentri.py          # Single file — all components as functions/classes within it
config.yaml            # User-facing parameters (Canny thresholds, delays, epsilon)
config.example.yaml    # Documented defaults shipped with tool
examples/
├── logo.png           # Sample input image
└── simple_outline.png # Sample input image
```

### Structure Rationale

- **Single file:** Project constraint. Components are organized as functions grouped by logical section with clear section-header comments (`# === IMAGE PIPELINE ===`, `# === REPLAY ENGINE ===`, etc.)
- **Sections in file order match execution order:** Reading top-to-bottom mirrors the runtime flow, reducing cognitive overhead
- **Config separate from script:** Lets users iterate parameters without touching code

## Architectural Patterns

### Pattern 1: Linear Phase Pipeline with Shared State

**What:** Each phase is a function that receives an `AppState` dataclass, mutates specific fields, and returns. `main()` calls phases in sequence.

**When to use:** Small tools where a full event-driven architecture would be overkill. Single-threaded execution with one exception (the hotkey listener daemon).

**Trade-offs:** Simple to reason about. No async complexity. Abort requires polling rather than interruption, so the check granularity is per-stroke (acceptable here).

**Example:**
```python
from dataclasses import dataclass, field
import threading
from typing import List
import numpy as np

@dataclass
class AppState:
    config: dict = field(default_factory=dict)
    contours_normalized: List[np.ndarray] = field(default_factory=list)
    bbox: tuple = None          # (x1, y1, x2, y2) screen pixels
    abort_flag: threading.Event = field(default_factory=threading.Event)

def main():
    state = AppState()
    load_config(state)          # fills state.config
    run_image_pipeline(state)   # fills state.contours_normalized
    run_calibration(state)      # fills state.bbox
    run_preview(state)          # may raise SystemExit on abort
    start_hotkey_listener(state) # starts daemon thread
    run_replay(state)           # drives mouse strokes
```

### Pattern 2: Abort via threading.Event Polling (not signal/exception)

**What:** The Esc hotkey listener runs as a pynput daemon thread. On Esc it calls `abort_flag.set()`. The replay loop checks `abort_flag.is_set()` between strokes (not mid-stroke).

**When to use:** Any long-running loop that must be stoppable. Polling is appropriate here because individual strokes are short (<100ms each) so response latency is acceptable.

**Trade-offs:** Maximum abort latency equals one full stroke duration. Simpler than injecting exceptions across threads. The listener cannot be restarted once stopped (pynput limitation) — this is acceptable since abort ends the session.

**Example:**
```python
from pynput import keyboard

def start_hotkey_listener(state: AppState):
    def on_press(key):
        if key == keyboard.Key.esc:
            state.abort_flag.set()
            return False  # stops listener
    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()

def run_replay(state: AppState):
    for contour in state.contours_normalized:
        if state.abort_flag.is_set():
            print("Aborted by user.")
            return
        pts = transform_contour(contour, state.bbox)
        paint_stroke(pts, state.config)
```

### Pattern 3: Purely Functional Image Pipeline (no side effects)

**What:** `run_image_pipeline` is a sequence of pure transformations. Each step takes data and config values, returns transformed data. No global state mutations inside these functions.

**When to use:** Image processing stages — they have clear inputs/outputs and benefit from being individually testable.

**Trade-offs:** Slightly more verbose (passing config dict to each step) but makes unit testing trivial without needing to instantiate AppState.

**Example:**
```python
def run_image_pipeline(state: AppState):
    img = load_image(state.config["image_path"])
    gray = to_grayscale(img)
    edges = run_canny(gray, state.config["canny_low"], state.config["canny_high"])
    raw_contours = extract_contours(edges, state.config["retrieval_mode"])
    simplified = [simplify_contour(c, state.config["epsilon"]) for c in raw_contours]
    filtered = filter_short_contours(simplified, state.config["min_length"])
    state.contours_normalized = [normalize_contour(c, img.shape) for c in filtered]
```

## Data Flow

### Primary Execution Flow

```
YAML file
    │
    ▼
load_config() ──────────────────────────────────► AppState.config
                                                        │
PNG file                                               │
    │                                                  ▼
    ▼                                          run_image_pipeline()
load_image()                                           │
    │                                                  │
    ▼                                    AppState.contours_normalized
to_grayscale()                                (List of np.ndarray,
    │                                          coords 0.0–1.0)
    ▼                                                  │
run_canny()                                            │
    │                                                  ▼
    ▼                                          run_calibration()
extract_contours()                                     │
    │                                     AppState.bbox (x1,y1,x2,y2)
    ▼                                                  │
simplify_contour()  ← epsilon from config              │
    │                                                  ▼
    ▼                                          run_preview()
filter_short_contours() ← min_length                   │
    │                                         proceed / SystemExit
    ▼                                                  │
normalize_contour()                                    │
  (pts / img_width, pts / img_height)                  ▼
                                               start_hotkey_listener()
                                               (daemon thread, sets abort_flag)
                                                        │
                                                        ▼
                                               run_replay()
                                               for each contour:
                                                 transform_contour()
                                                   (norm_x * bbox_w + bbox_x1,
                                                    norm_y * bbox_h + bbox_y1)
                                                 paint_stroke()
                                                   mouseDown → moveTo → mouseUp
                                                 check abort_flag
```

### Coordinate Transformation Math

```
Image coords (pixels, origin top-left):
  raw_pt = (px, py), image size = (W, H)

Normalize (image → 0–1 space):
  norm_x = px / W
  norm_y = py / H

Scale to screen bbox (0–1 → screen pixels):
  bbox = (bx1, by1, bx2, by2)
  bbox_w = bx2 - bx1
  bbox_h = by2 - by1
  screen_x = bx1 + norm_x * bbox_w
  screen_y = by1 + norm_y * bbox_h

Both steps can be composed into one linear mapping:
  screen_x = bx1 + (px / W) * (bx2 - bx1)
  screen_y = by1 + (py / H) * (by2 - by1)
```

### State Management

```
AppState (dataclass, created once in main())
    │
    ├── .config          written by: load_config()
    │                    read by:    all phases
    │
    ├── .contours_normalized
    │                    written by: run_image_pipeline()
    │                    read by:    run_preview(), run_replay()
    │
    ├── .bbox            written by: run_calibration()
    │                    read by:    run_replay() (via transform_contour)
    │
    └── .abort_flag      written by: hotkey listener thread (set())
                         read by:    run_replay() (is_set())
                         -- only cross-thread field --
```

## Suggested Build Order

Build in this order — each step has no dependency on a later step:

| Step | Component | Why First |
|------|-----------|-----------|
| 1 | Config Loader | Everything reads config; validate once at startup |
| 2 | Image Pipeline | Core value; fully testable without screen interaction |
| 3 | Preview | Depends on contours being available; validates pipeline output visually |
| 4 | Calibration / Capture | Depends on nothing except pyautogui; validates screen math before replay |
| 5 | Coordinate Transformer | Pure math function; can be unit tested before integrating into replay |
| 6 | Replay Engine | Depends on calibration + transformer + contours |
| 7 | Hotkey Listener | Integrate last — cross-thread concern; test abort path once replay works |
| 8 | Full integration | Wire AppState through main(), test end-to-end |

## Integration Points

### External Libraries

| Library | Integration Pattern | Notes |
|---------|---------------------|-------|
| opencv-python | `cv2.imread`, `cv2.Canny`, `cv2.findContours`, `cv2.approxPolyDP`, `cv2.imshow`, `cv2.waitKey` | All sync; preview blocks main thread intentionally |
| pyautogui | `pyautogui.mouseDown`, `pyautogui.moveTo`, `pyautogui.mouseUp` | Set `pyautogui.PAUSE = 0` inside replay loop for speed; restore after |
| pynput | `keyboard.Listener` as daemon thread | Cannot be restarted after stop; create once per run |
| numpy | Array ops for contour normalization and coordinate math | Contours from OpenCV are `np.ndarray` of shape `(N, 1, 2)` — squeeze to `(N, 2)` before math |
| pyyaml | `yaml.safe_load()` for config | Use `safe_load`, not `load` — never `load` untrusted YAML |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Image Pipeline → Preview | `AppState.contours_normalized` | Preview draws normalized coords scaled to image size for display |
| Image Pipeline → Replay | `AppState.contours_normalized` | Replay passes through Coordinate Transformer |
| Calibration → Replay | `AppState.bbox` | `(x1, y1, x2, y2)` in screen pixels |
| Hotkey Listener → Replay | `AppState.abort_flag` (threading.Event) | Only cross-thread boundary in the system |
| Config → All | `AppState.config` dict | No phase writes to config after load_config() |

## Anti-Patterns

### Anti-Pattern 1: Aborting with a Signal or Exception Across Threads

**What people do:** Raise `KeyboardInterrupt` or a custom exception from the listener thread to stop the replay loop.

**Why it's wrong:** Python exceptions cannot be reliably raised in another thread. The main thread won't receive exceptions thrown in the pynput daemon thread. Using `os.kill(os.getpid(), signal.SIGINT)` from a thread can work but is fragile and platform-dependent.

**Do this instead:** Set a `threading.Event` in the listener callback. Check `abort_flag.is_set()` at the top of the replay loop. This is the documented pynput abort pattern and works on all platforms.

### Anti-Pattern 2: Using Global Variables for State

**What people do:** Define `CONTOURS = []`, `BBOX = None`, `ABORT = False` as module-level globals.

**Why it's wrong:** In a single-file script that may be extended, globals make data flow invisible, testing harder, and threading semantics unclear (non-Event booleans are not thread-safe without a GIL assumption that may change in Python 3.13+ with free-threading).

**Do this instead:** Use an `AppState` dataclass. Pass it explicitly to each phase function. One dataclass instance per run.

### Anti-Pattern 3: Calling pyautogui with Default PAUSE Between Every Point

**What people do:** Call `pyautogui.moveTo(x, y)` in a loop without adjusting `PAUSE`, resulting in 0.1s delay per point.

**Why it's wrong:** A contour with 200 points takes 20 seconds to paint. Dense contours become unusably slow.

**Do this instead:** Set `pyautogui.PAUSE = 0` before the replay loop and add delay only between strokes (mouseUp → mouseDown pause), controlled by a `inter_stroke_delay` config value. Restore `PAUSE` to default after replay completes.

### Anti-Pattern 4: Normalizing After Simplification vs Before

**What people do:** Simplify raw pixel-coordinate contours using Douglas-Peucker with a pixel-space epsilon, then normalize.

**Why it's fine but needs care:** The epsilon value for `cv2.approxPolyDP` is in the same coordinate units as the contour. If simplification happens in pixel space, epsilon is intuitive (e.g., `3` pixels). If done in normalized space (0–1), epsilon would be `3/image_width`. Do simplification in pixel space with a pixel-unit epsilon from config — it's more user-friendly to tune.

### Anti-Pattern 5: Hardcoding pyautogui on Wayland

**What people do:** Assume pyautogui works on Linux without checking display server.

**Why it's wrong:** pyautogui on Linux requires X11 (via Xlib). It does not support Wayland natively. Users running a Wayland-only session (no XWayland) will get import errors or silent failures.

**Do this instead:** At startup, detect the display server with `os.environ.get("WAYLAND_DISPLAY")` and `os.environ.get("DISPLAY")`. If Wayland-only detected, print a clear error message pointing to the `DISPLAY=:0` workaround or XWayland requirement. Most gaming setups run XWayland so this is usually not a blocker, but the check makes failures debuggable.

## Scaling Considerations

This is a local CLI tool — scaling means "what happens as image complexity grows."

| Scale | Concern | Approach |
|-------|---------|----------|
| Small images, few contours (<50) | None | Works as-is |
| Complex images, many contours (50–500) | Preview responsiveness, replay duration | Minimum length filter and epsilon simplification reduce count; preview still instant |
| Very dense line art (500+ contours) | Replay may take many minutes | Add contour count display in preview; let user abort and adjust config before committing |
| Extremely large images (>4K) | OpenCV memory, findContours performance | OpenCV handles large images fine; no action needed at this scale |

## Sources

- [PyAutoGUI Mouse Control Documentation](https://pyautogui.readthedocs.io/en/latest/mouse.html)
- [pynput Keyboard Listener Documentation](https://pynput.readthedocs.io/en/latest/keyboard.html)
- [OpenCV Contour Features](https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html)
- [OpenCV findContours Tutorial](https://docs.opencv.org/3.4/d4/d73/tutorial_py_contours_begin.html)
- [PyAutoGUI Wayland Issue #111](https://github.com/asweigart/pyautogui/issues/111) — confirmed no native Wayland support
- [rdp PyPI package](https://pypi.org/project/rdp/) — Python RDP implementation (alternative to cv2.approxPolyDP)
- [Modular image processing pipeline with Python generators](https://medium.com/deepvisionguru/modular-image-processing-pipeline-using-opencv-and-python-generators-9edca3ccb696)
- [OpenCV Contour Approximation — PyImageSearch](https://pyimagesearch.com/2021/10/06/opencv-contour-approximation/)

---
*Architecture research for: image-to-mouse-stroke automation (STS2 Map Painter)*
*Researched: 2026-03-19*
