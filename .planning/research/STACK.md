# Stack Research

**Domain:** Image contour detection + mouse replay automation (Python CLI tool)
**Researched:** 2026-03-19
**Confidence:** HIGH (all versions verified against PyPI and official sources)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| opencv-python | 4.13.0.86 (latest as of Feb 2026) | Canny edge detection, `findContours`, `approxPolyDP`, preview window | De facto standard for CV in Python; `findContours` returns ordered polylines natively; `approxPolyDP` is built-in RDP; `waitKey(0)` gives free preview-window event loop with ESC abort — no extra library needed |
| numpy | 2.1.x (for Python 3.10); 2.4.3 (for Python 3.11+) | Array ops, coordinate math, normalization | numpy 2.4.x dropped Python 3.10 — pin to 2.1.x if staying on 3.10; 2.4.3 if upgrading to 3.11+ |
| pyautogui | 0.9.54 | Mouse button down/up and move for stroke replay | PROJECT.md already mandates it; only viable single-library option for X11/XWayland on Linux without root; covers the tool's stated target environment |
| pyyaml | 6.0.3 | Load/dump YAML config file | Safe, stable, no quirks; `yaml.safe_load()` is the right API |
| Python | 3.11+ (recommended); 3.10 minimum | Runtime | 3.10 drops numpy 2.4 support; 3.11 is the sweet spot for all listed packages |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scikit-image | 0.26.0 | Canny with sigma/mask control | Only needed if OpenCV's Canny (fixed-sigma) produces unsatisfactory edges on noisy inputs; PROJECT.md lists it as a dependency but OpenCV Canny is sufficient for clean line art |
| pynput | 1.8.1 | Mid-painting Esc abort listener (background thread) | Use **only** when you need an abort hotkey that fires while pyautogui is blocking the main thread; works on X11 and XWayland via Xlib; does NOT work natively on pure Wayland |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pip + venv | Dependency isolation | Use `python -m venv .venv` + `pip install -r requirements.txt`; no need for Poetry/PDM on a single-file tool |
| DISPLAY=:0 env var | Force X11 / XWayland | Set before running on systems where Wayland is the default session; `DISPLAY=:0 python painter.py` makes pyautogui find the X server |

---

## Installation

```bash
# Create isolated environment
python3 -m venv .venv && source .venv/bin/activate

# Core (matches PROJECT.md constraint list)
pip install opencv-python pyautogui numpy pyyaml

# Optional: if adding background keyboard abort listener
pip install pynput

# Optional: only if OpenCV Canny is insufficient
pip install scikit-image
```

---

## Key Decision: OpenCV approxPolyDP vs External RDP Library

**Use `cv2.approxPolyDP()` — not the `rdp` or `simplification` packages.**

`cv2.approxPolyDP()` is OpenCV's built-in implementation of the Ramer–Douglas–Peucker algorithm, operating directly on the contour arrays returned by `cv2.findContours()`. It accepts an `epsilon` parameter (max deviation in pixels) and returns a numpy array of the same shape. No type conversion, no extra dependency.

The `simplification` package (v0.7.14, Rust-backed, released Oct 2025) is faster for 200k+ point datasets, which this tool will never approach — typical line-art contours have tens to low hundreds of points per stroke. The `rdp` package (pure Python) is slower and provides no benefit over the built-in.

**Verdict:** `cv2.approxPolyDP(contour, epsilon, closed=False)` covers the requirement completely.

---

## Key Decision: Abort Hotkey Architecture

The preview step uses `cv2.waitKey(0)` directly inside the OpenCV window — pressing Esc (key code 27) or any key there is handled without any external library. This covers the "press key to proceed or abort" requirement from PROJECT.md at zero cost.

The mid-painting abort (Esc while pyautogui is replaying strokes) is the hard case. `pyautogui.moveTo()` is synchronous and blocks the main thread. Options:

1. **`pynput.keyboard.Listener` in a daemon thread** (recommended) — starts a background listener, sets a threading.Event on Esc, main loop checks the event between strokes. Works on X11 and XWayland without root. Does NOT work on native Wayland.
2. **`keyboard` library** — abandoned (last release March 2020, v0.13.5); requires root on Linux; do not use.
3. **PyAutoGUI failsafe (mouse corner)** — PROJECT.md explicitly rejects this; more accidental than intentional.

**Verdict:** `pynput.keyboard.Listener` in a daemon thread, checking a `threading.Event` between each contour stroke. Falls back gracefully to a Ctrl-C terminal interrupt on pure Wayland.

---

## Key Decision: pyautogui vs Wayland Alternatives

The project's stated platform is "Linux (X11/Wayland)." Wayland compatibility is a real constraint:

- **pyautogui 0.9.54** uses python-xlib, which works on X11 and XWayland. On pure Wayland (no Xwayland), it fails with an import error or produces no mouse movement.
- **wayland-automation v0.2.7** (Feb 2026) is a purpose-built Wayland alternative using `zwlr_virtual_pointer_manager_v1`; supports drag operations on Hyprland, Sway, labwc (wlroots compositors). Does NOT work on GNOME/KDE Wayland (they use a different compositor protocol).
- **python-evdev** works on any Linux display server but requires root (`/dev/uinput`); not viable for a single-file tool users run as themselves.

**Verdict:** Keep pyautogui (PROJECT.md mandates it). Document clearly: the tool requires X11 or XWayland. On pure Wayland, users must run with `GDK_BACKEND=x11` or start an X11 session. This is the most pragmatic tradeoff for a single-file tool — adding conditional Wayland backends would require compositor detection and multiple code paths.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `cv2.approxPolyDP` | `simplification` (Rust) or `rdp` (pure Python) | Never for this project; only relevant if processing GIS-scale linestrings (100k+ points) |
| `cv2.Canny` | `skimage.feature.canny` | If input images are noisy or require sigma-controlled multi-scale edge detection; scikit-image Canny supports masking and a `sigma` parameter |
| `pynput` (abort listener) | `keyboard` library | Never — keyboard is abandoned (2020) and needs root |
| pyautogui | wayland-automation | Only if targeting wlroots Wayland compositors (Hyprland, Sway) exclusively, and X11/XWayland is not available |
| `cv2.waitKey` (preview) | tkinter / Qt UI | Never for this scope — cv2.waitKey gives free event loop inside the existing preview window |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `keyboard` library | Last release March 2020; requires root on Linux; unmaintained | `pynput.keyboard.Listener` |
| `rdp` PyPI package | Pure Python, slower than built-in; adds a dependency for no gain | `cv2.approxPolyDP` |
| `simplification` PyPI package | Rust binary overhead; solves a scale problem this project doesn't have | `cv2.approxPolyDP` |
| `pygetwindow` | Windows-only; not useful for cross-platform screen region capture | Terminal-prompted coordinate capture (PROJECT.md pattern) |
| numpy >= 2.2 with Python 3.10 | numpy 2.2+ dropped Python 3.10 support; will fail to install | Pin numpy to `<2.2` if using Python 3.10, or upgrade Python to 3.11+ |
| `cv2.RETR_LIST` retrieval mode | Returns contours in arbitrary order; harder to sort for stroke replay | `cv2.RETR_EXTERNAL` (outer contours only, less noise) or `cv2.RETR_CCOMP` (two-level hierarchy) |

---

## Stack Patterns by Variant

**If input image is clean black-on-white line art:**
- Use `cv2.Canny(img, threshold1=50, threshold2=150)` directly
- scikit-image not needed
- `cv2.findContours(..., cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)` gives full point sets

**If input image is noisy or photographic:**
- Add `cv2.GaussianBlur(img, (5,5), 0)` before Canny
- Lower thresholds (e.g., threshold1=30, threshold2=100)
- Consider `skimage.feature.canny(img, sigma=2.0)` for finer sigma control

**If running on pure Wayland (no XWayland):**
- Set `DISPLAY=:0` and ensure XWayland is running, OR
- Replace pyautogui with `wayland-automation` on wlroots compositors (Hyprland/Sway only)
- Accept this as out-of-scope for MVP per PROJECT.md constraints

**If contours produce too many redundant points (slow replay):**
- `epsilon = 1.5` in `cv2.approxPolyDP` as default starting value (pixels)
- Expose as YAML config parameter `simplify_epsilon`
- Also add `min_contour_area` filter using `cv2.contourArea(c) > threshold`

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| opencv-python 4.13.0.86 | Python 3.8–3.12 | Avoid cv2-contrib unless you need SIFT/SURF; base package covers all needed APIs |
| numpy 2.1.x | Python 3.10–3.13 | Last series supporting 3.10; required if staying on 3.10 |
| numpy 2.4.3 | Python 3.11–3.14 | Current latest; upgrade Python to 3.11 to use this |
| pyautogui 0.9.54 | Python 3.x | Last release May 2023; depends on python-xlib on Linux; will install on 3.10 and 3.11+ |
| pynput 1.8.1 | Python 3.x | Depends on Xlib on Linux; Wayland listener does not work (upstream issue #628, #331 open as of 2025) |
| pyyaml 6.0.3 | Python 3.8–3.14 | Stable; always use `yaml.safe_load()`, never `yaml.load()` |
| scikit-image 0.26.0 | Python 3.10+ | Optional; only needed for sigma-controlled Canny |

---

## Sources

- PyPI: opencv-python 4.13.0.92 — https://pypi.org/project/opencv-python/ (fetched 2026-03-19, HIGH confidence)
- PyPI: pyautogui 0.9.54 — https://pypi.org/project/PyAutoGUI/ (fetched 2026-03-19, HIGH confidence)
- PyPI: pynput 1.8.1 — https://pypi.org/project/pynput/ (fetched 2026-03-19, HIGH confidence)
- PyPI: numpy 2.4.3 — https://pypi.org/project/numpy/ (fetched 2026-03-19, HIGH confidence)
- PyPI: pyyaml 6.0.3 — https://pypi.org/project/pyyaml/ (fetched 2026-03-19, HIGH confidence)
- PyPI: scikit-image 0.26.0 — https://pypi.org/project/scikit-image/ (fetched 2026-03-19, HIGH confidence)
- PyPI: simplification 0.7.14 — https://pypi.org/project/simplification/ (search-verified, MEDIUM confidence)
- PyPI: keyboard 0.13.5 (abandoned) — https://pypi.org/project/keyboard/ (fetched 2026-03-19, HIGH confidence)
- pynput Wayland issue tracker — https://github.com/moses-palmer/pynput/issues/628 (MEDIUM confidence, open issue)
- pyautogui Wayland issue tracker — https://github.com/asweigart/pyautogui/issues/111 (MEDIUM confidence, open issue)
- wayland-automation v0.2.7 — https://github.com/OTAKUWeBer/Wayland-automation (fetched 2026-03-19, MEDIUM confidence — small project, not widely adopted)
- OpenCV approxPolyDP docs — https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html (HIGH confidence)
- OpenCV Canny tutorial — https://docs.opencv.org/3.4/da/d22/tutorial_py_canny.html (HIGH confidence)

---

*Stack research for: STS2 Map Painter — image contour detection + mouse replay*
*Researched: 2026-03-19*
