---
phase: 1
slug: image-pipeline-and-safety
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (not yet installed — Wave 0 installs) |
| **Config file** | none — Wave 0 creates `pyproject.toml` or `pytest.ini` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 0 | CFG-01 | unit | `pytest tests/test_config.py::test_config_autogenerate -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 0 | CFG-01 | unit | `pytest tests/test_config.py::test_deep_merge -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 0 | CFG-05 | unit | `pytest tests/test_safety.py::test_wayland_exit -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 0 | CFG-05 | unit | `pytest tests/test_safety.py::test_xwayland_ok -x` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 0 | CFG-06 | unit | `pytest tests/test_safety.py::test_pause_zero -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | IMG-01 | unit | `pytest tests/test_image_pipeline.py::test_load_image -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | IMG-02 | unit | `pytest tests/test_image_pipeline.py::test_canny_numeric -x` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | IMG-03 | unit | `pytest tests/test_image_pipeline.py::test_otsu_auto -x` | ❌ W0 | ⬜ pending |
| 01-02-04 | 02 | 1 | IMG-04 | unit | `pytest tests/test_image_pipeline.py::test_find_contours -x` | ❌ W0 | ⬜ pending |
| 01-02-05 | 02 | 1 | IMG-05 | unit | `pytest tests/test_image_pipeline.py::test_min_length_filter -x` | ❌ W0 | ⬜ pending |
| 01-02-06 | 02 | 1 | IMG-06 | unit | `pytest tests/test_image_pipeline.py::test_simplify_normalize -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | CAL-01 | manual | n/a (requires display) | n/a | ⬜ pending |
| 01-03-02 | 03 | 1 | CAL-02 | manual | n/a (requires display + keyboard) | n/a | ⬜ pending |
| 01-04-01 | 04 | 1 | CAL-04 | manual | n/a (requires mouse interaction) | n/a | ⬜ pending |
| 01-04-02 | 04 | 1 | CAL-05 | manual | n/a (requires mouse interaction) | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_image_pipeline.py` — stubs for IMG-01..06
- [ ] `tests/test_config.py` — stubs for CFG-01 (load, auto-generate, deep merge)
- [ ] `tests/test_safety.py` — stubs for CFG-05, CFG-06
- [ ] `tests/conftest.py` — shared fixtures (tmp config file, sample test PNG, mock environment)
- [ ] Framework install: `pip install pytest` — not yet in requirements

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Preview window shows contours on black background with rainbow gradient | CAL-01 | Requires live OpenCV display | Run `python painter.py test.png --dry-run`, verify preview window opens with colored contours |
| Esc in preview aborts without mouse movement | CAL-02 | Requires keyboard input in OpenCV window | Press Esc in preview, verify tool exits cleanly |
| Two-point calibration captures click positions | CAL-04 | Requires physical mouse clicks | Follow terminal countdown prompts, click two corners |
| Bounding box coords printed after calibration | CAL-05 | Requires physical mouse clicks | Complete calibration, verify coords displayed in terminal |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
