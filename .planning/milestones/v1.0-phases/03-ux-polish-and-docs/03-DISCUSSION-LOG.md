# Phase 3: UX Polish and Docs - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-20
**Phase:** 03-ux-polish-and-docs
**Areas discussed:** Time Estimate, README, Example Images, Config Annotations

---

## Time Estimate in Preview

| Option | Description | Selected |
|--------|-------------|----------|
| Point count x delay | Sum all contour points, multiply by inter_point_delay + inter_stroke_delay overhead | ✓ |
| Fixed per-stroke average | Use hardcoded average time per stroke (e.g., 0.2s) | |
| You decide | Claude picks best approach | |

**User's choice:** Point count x delay
**Notes:** Simple, accurate for the config the user has set.

| Option | Description | Selected |
|--------|-------------|----------|
| Preview window title bar | OpenCV window title shows estimate | |
| Terminal output only | Print to terminal alongside contour count | ✓ |
| Both | Terminal and preview window title | |

**User's choice:** Terminal output only

---

## README Content and Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Quick start + reference | What it does, install, usage, config reference table, example workflow | ✓ |
| Minimal | Just what/how, 20 lines max | |
| Comprehensive | Full docs with troubleshooting, FAQ, screenshots/GIFs | |

**User's choice:** Quick start + reference

| Option | Description | Selected |
|--------|-------------|----------|
| No visuals | Text only | |
| Example output screenshot | Screenshot of preview window showing detected contours | ✓ |
| You decide | Claude decides | |

**User's choice:** Example output screenshot

---

## Example Images

| Option | Description | Selected |
|--------|-------------|----------|
| Simple line art | Clean black-and-white outline | |
| test_preview.png (existing) | Keep existing test image | |
| Complex/detailed image | Many contours for larger inputs | |
| You decide | Claude picks appropriate examples | ✓ |

**User's choice:** You decide

| Option | Description | Selected |
|--------|-------------|----------|
| examples/ folder | Clean separation, README references them | ✓ |
| Repo root | Alongside painter.py | |

**User's choice:** examples/ folder

---

## Config Annotations

| Option | Description | Selected |
|--------|-------------|----------|
| Current comments sufficient | Existing comments are fine, just ensure Phase 2 keys have comments | |
| Add value ranges/examples | Add acceptable ranges or example values in comments | ✓ |
| Separate config guide | Dedicated CONFIG.md or README section | |

**User's choice:** Add value ranges/examples

---

## Claude's Discretion

- Choice of example PNG images
- Exact README section ordering and wording
- Screenshot generation approach
- Time estimate formatting

## Deferred Ideas

None
