# Phase 3: UX Polish and Docs - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the tool usable by someone who has never run it. Add painting time estimate to preview output, enhance config annotations with value ranges, write a README with quick-start guide and config reference, and include example PNG(s). No new painting/processing features — this is documentation and UX polish only.

</domain>

<decisions>
## Implementation Decisions

### Time Estimate in Preview
- **D-01:** Estimate painting time using point count x inter_point_delay + stroke count x inter_stroke_delay + start_delay countdown
- **D-02:** Display estimate in terminal output only (not in the preview window title bar) — alongside the existing contour count message
- **D-03:** Estimate reads from the user's current config values so it reflects their actual settings

### README Content
- **D-04:** Quick-start + reference style — what it does (1 paragraph), install, basic usage, config reference table, example workflow. Concise, no fluff.
- **D-05:** Include a screenshot of the preview window showing detected contours as visual media
- **D-06:** README lives at repo root as `README.md`

### Example Images
- **D-07:** Claude's discretion on which example PNGs to include — should demonstrate the tool works well
- **D-08:** Example images go in an `examples/` subfolder, referenced from README

### Config Annotations
- **D-09:** Enhance DEFAULT_CONFIG_CONTENT inline comments with acceptable value ranges and example values (e.g., `# 0-255, or "auto"`)
- **D-10:** Ensure all Phase 2 config keys (start_delay, inter_point_delay, inter_stroke_delay, mouse_button) have annotated comments with ranges

### Claude's Discretion
- Choice of example PNG images (simple line art, existing test_preview.png, etc.)
- Exact README section ordering and wording
- Screenshot generation approach (programmatic or manual)
- Time estimate formatting (e.g., "~12s" vs "approximately 12 seconds")

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Core value, constraints (single file, specific dependencies, Linux/Python 3.10+)
- `.planning/REQUIREMENTS.md` — Phase 3 requirements: CAL-03, CFG-02, CFG-03, CFG-04

### Prior Phase Context
- `.planning/phases/01-image-pipeline-and-safety/01-CONTEXT.md` — Config structure decisions, CLI flags, preview window behavior
- `.planning/phases/02-coordinate-mapping-and-replay/02-CONTEXT.md` — Replay speed config keys, progress bar formatting, contour sorting

### Existing Config
- `config.yaml` — Current user config with inline comments (reference for annotation style)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DEFAULT_CONFIG_CONTENT` (painter.py) — Auto-generated config template with inline YAML comments. Phase 3 enhances these comments with value ranges.
- `_DEFAULTS` (painter.py) — Default values dict, source of truth for all config parameters
- `run_preview()` (painter.py) — Preview function that already prints contour count. Time estimate gets added here.
- `state.contours_normalized` — List of (N,2) arrays, point counts available for time estimation

### Established Patterns
- Lazy imports: pyautogui and pynput imported inside functions (Wayland fix)
- Config access: `state.config.get("section", {}).get("key", default)`
- Terminal output: `print()` for user-facing messages, `[DEBUG]` prefix for verbose mode
- Requirement tracing: docstrings reference requirement IDs (e.g., `"""CAL-03: ...`)

### Integration Points
- Time estimate calculation happens after contours are loaded but before preview displays
- Config comment enhancement modifies `DEFAULT_CONFIG_CONTENT` string in painter.py
- README references `examples/` subfolder for example images
- Preview screenshot captured from existing `run_preview()` output

</code_context>

<specifics>
## Specific Ideas

- Time estimate should use the user's actual config values (inter_point_delay, inter_stroke_delay) so the estimate is meaningful for their setup
- Config comments should include range info like `# 0-255, or "auto"` to help users know valid values without reading docs
- README screenshot shows the rainbow-gradient contour preview — the most visually distinctive part of the tool

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-ux-polish-and-docs*
*Context gathered: 2026-03-20*
