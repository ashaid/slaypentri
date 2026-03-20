---
phase: 02
slug: coordinate-mapping-and-replay
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | none — existing from Phase 1 |
| **Quick run command** | `python3 -m pytest tests/ -q --tb=short` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/ -q --tb=short`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | CAL-06, PAINT-04, PAINT-05 | unit | `pytest tests/test_coordinate_mapping.py -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | PAINT-01, PAINT-02, PAINT-03 | unit+mock | `pytest tests/test_coordinate_mapping.py -q` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | PAINT-06, PAINT-08 | unit+mock | `pytest tests/test_coordinate_mapping.py -q` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | PAINT-07, CAL-07 | unit | `pytest tests/test_coordinate_mapping.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_coordinate_mapping.py` — stubs for CAL-06, CAL-07, PAINT-01..08
- [ ] Extend `tests/conftest.py` — fixtures for normalized contours, mock bbox, mock pyautogui

*Existing infrastructure (pytest, conftest.py) covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Mouse strokes appear on screen | PAINT-01 | Requires physical display + target app | Run `python3 painter.py test.png`, verify strokes appear in target window |
| Esc stops painting within one stroke | PAINT-06 | Requires physical keyboard + display | Press Esc during painting, verify mouse stops and button released |
| Aspect ratio looks correct visually | CAL-06 | Visual verification of proportions | Compare painted output to source image proportions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
