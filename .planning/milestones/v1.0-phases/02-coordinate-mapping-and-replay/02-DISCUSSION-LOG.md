# Phase 2: Coordinate Mapping and Replay - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-20
**Phase:** 02-coordinate-mapping-and-replay
**Areas discussed:** Aspect ratio mapping, Stroke replay speed, Contour ordering, Abort mechanism

---

## Aspect Ratio Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve + center | Fit contours inside bbox maintaining proportions, centered with margins | ✓ |
| Stretch to fill | Map contours to fill entire bbox, possible distortion | |
| Preserve + anchor top-left | Fit with proportions, anchor top-left, margins right/bottom | |

**User's choice:** Preserve + center

| Option | Description | Selected |
|--------|-------------|----------|
| Fill largest axis | Scale to fill bbox on longer matching axis, margins on shorter axis only | ✓ |
| Margin on both axes | Add configurable padding on all sides | |

**User's choice:** Fill largest axis
**Notes:** Contours maximize use of the bounding box while preserving proportions.

---

## Stroke Replay Speed

| Option | Description | Selected |
|--------|-------------|----------|
| Configurable seconds | YAML `painting.start_delay` default 3s, countdown in terminal | ✓ |
| Fixed 5 seconds | Always 5 seconds, no config | |
| Press-to-start | Wait for Enter keypress after calibration | |

**User's choice:** Configurable seconds (default 3)

| Option | Description | Selected |
|--------|-------------|----------|
| Config default 0 | `inter_point_delay: 0`, user increases if app drops inputs | ✓ |
| Config default 0.01 | 10ms safety delay between points | |
| You decide | Claude picks defaults | |

**User's choice:** Config default 0 (fastest)

| Option | Description | Selected |
|--------|-------------|----------|
| Inline overwrite | Single line with `\r`, progress bar | ✓ |
| Per-stroke lines | One line per completed stroke | |
| Silent + final summary | No output during painting | |

**User's choice:** Inline overwrite with progress bar

---

## Contour Ordering

| Option | Description | Selected |
|--------|-------------|----------|
| Nearest-neighbor greedy | Start from bbox top-left, pick closest endpoint, repeat | ✓ |
| Top-to-bottom scan | Sort by topmost Y coordinate | |
| Original detection order | Paint in OpenCV detection order | |

**User's choice:** Nearest-neighbor greedy

| Option | Description | Selected |
|--------|-------------|----------|
| Closest endpoint | Compare distance to both endpoints, start from closer one | ✓ |
| Always first point | Always start from first point in array | |

**User's choice:** Closest endpoint (halves average travel)

---

## Abort Mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Finish current stroke, then stop | Esc sets flag, current contour completes, then break | ✓ |
| Immediate interrupt | mouseUp mid-stroke, may leave partial stroke | |
| You decide | Claude picks safest approach | |

**User's choice:** Finish current stroke, then stop

| Option | Description | Selected |
|--------|-------------|----------|
| pynput background thread | Daemon thread with keyboard.Listener, sets abort_flag on Esc | ✓ |
| Signal handler | SIGINT (Ctrl+C) instead of Esc | |

**User's choice:** pynput background thread (consistent with calibration)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, try/finally | Wrap painting loop in try/finally with mouseUp | ✓ |
| Only on abort + normal | Handle mouseUp explicitly, exceptions may leave stuck button | |

**User's choice:** Yes, try/finally — critical for game use case

---

## Claude's Discretion

- Progress bar formatting details
- Total painting time output
- Edge cases for tiny contours
- Single-pixel contour handling

## Deferred Ideas

None
