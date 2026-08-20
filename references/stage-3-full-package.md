# Stage 3: reviewed batches and default master delivery

Read `delivery-contract.md` and `dynamic-master-review.md`. This stage produces reviewed replacement batches and chronological masters only; final video, subtitles, and voiceover belong to the final-video workflow.

1. Process `plan/reference-batches.json` in order. A full batch has six adjacent RFs in a 3x2 source sheet; a tail batch is horizontal.
2. Use the current catalog-selected `storyboard_image` capability through the registered Flow2API MCP for local product replacement and save `replacement-contact-sheet.png`. Record the returned model key in the run snapshot. This file is the reviewed batch artifact; do not split, crop, or resubmit it before it passes.
3. Save `batch-image-prompt.md`, `batch-review.md`, and `manifest.json`. Review product facts, shot fidelity, product relative scale, full-sheet aspect, and 9:16 panel geometry. Regenerate a failed batch once only.
4. Calculate `plan/master-groups.json` before assembly. With `N` valid RFs, create `K = ceil(N/15)` chronological groups; distribute RFs as evenly as possible so counts differ by at most one. Validate exact coverage, unique RF IDs, chronological order, and a maximum of 15 per group.
5. After all batches pass, run `scripts/assemble_storyboard_masters.py <run> --out masters`. It must refuse unreviewed/failed or materially geometry-drifted inputs and must read only the current run's accepted batch sheets.
6. Save a `master-review.md` and `manifest.json` beside every master, then write `quality-report.md` and `package.json`. Deliver final masters by default; retain batch sheets in the package as audit artifacts.

Output structure:

```text
<run>/
  evidence/
  dynamic-master-breakdown-report.md
  frame-time-map.csv
  plan/user-constraints.md
  plan/product-interaction-facts.md
  plan/interaction-substitutions.md
  plan/reference-batches.json
  plan/storyboard-spec.json
  plan/master-groups.json
  batches/Batch-01/source-contact-sheet.png
  batches/Batch-01/replacement-contact-sheet.png
  batches/Batch-01/batch-image-prompt.md
  batches/Batch-01/batch-review.md
  batches/Batch-01/manifest.json
  batches/Batch-02/...
  masters/Master-01/master-contact-sheet.png
  masters/Master-01/master-review.md
  masters/Master-01/manifest.json
  quality-report.md
  package.json
```
