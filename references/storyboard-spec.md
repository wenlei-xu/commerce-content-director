# Batch and master storyboard specification

Write this file to `plan/storyboard-spec.json` before the first batch:

```json
{
  "schema": "contact-batch-master-storyboard-v2",
  "source_panel": {"width": 720, "height": 1280, "aspect_ratio": "9:16"},
  "full_batch_source_grid": {"columns": 3, "rows": 2, "gutter_px": 0, "reading_order": "left-to-right, top-to-bottom"},
  "tail_batch_source_grid": {"columns": "frame_count", "rows": 1, "gutter_px": 0, "reading_order": "left-to-right"},
  "replacement_geometry": {"expected_full_batch_aspect_ratio": "27:32", "expected_panel_aspect_ratio": "9:16", "max_relative_aspect_drift": 0.05},
  "master_delivery": {"enabled": true, "max_panels_per_master": 15, "partition": "chronological balanced", "formula": "K=ceil(N/15); partition N RFs into K consecutive groups whose sizes differ by at most one", "source_restriction": "current-run accepted batch sheets only"}
}
```

Keep source panels at 9:16. The replacement contact sheet is a reviewed batch artifact. Do not extract panels until it passes geometry review. The default deliverable is one or more chronological final masters, created only by `scripts/assemble_storyboard_masters.py` from accepted current-run batches.
