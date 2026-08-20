# Storyboard master delivery contract

This document is the delivery and acceptance authority for reference-led work. Its batch, RF, and master requirements apply only to `full_replication`; all strategies share the final-generation-board and Feishu review requirements below.

## Required files

For `full_replication`, deliver globally:

1. `dynamic-master-breakdown-report.md`
2. `frame-time-map.csv`
3. `plan/user-constraints.md`
4. `plan/product-interaction-facts.md`
5. `plan/reference-batches.json`
6. `plan/storyboard-spec.json`
7. `plan/master-groups.json`
8. `quality-report.md`
9. `package.json`

For `hook_replication`, replace the full-replication evidence package with `plan/hook-replication.md`. For `structure_replication`, replace it with `plan/structure-plan.json`. Both strategies still deliver `quality-report.md`, `package.json`, and every required final-generation board.

When applicable to `full_replication`, deliver `evidence/tail-trim.json` and `plan/interaction-substitutions.md`.

For `full_replication`, keep every batch as an audit artifact. Each batch contains:

1. `source-contact-sheet.png`
2. `replacement-contact-sheet.png`
3. `batch-image-prompt.md`
4. `batch-review.md`
5. `manifest.json`

Each full batch has exactly six consecutive RFs in a 3x2 source grid. A tail batch has one to five RFs in a horizontal source row. Every RF belongs to exactly one batch.

For `full_replication`, deliver final masters by default. Each `masters/Master-XX/` directory contains:

1. `master-contact-sheet.png`
2. `master-review.md`
3. `manifest.json`

For `N` valid RFs, make `K = ceil(N / 15)` masters. Partition the RFs into `K` consecutive chronological groups whose counts differ by at most one; no group may have more than 15 frames. Thus 27 RFs are 14+13, 16 RFs are 8+8, and 29 RFs are 15+14. `plan/master-groups.json` is authoritative. It must show every RF exactly once, in order, and only use the accepted replacement sheets from the current run.

At the storyboard-only stage, deliver only the evidence, accepted masters, and final-generation boards required by this contract. Do not deliver subtitles, voiceover, or a finished video. Once the final-video workflow is explicitly authorized for an approved content version, its contract governs the assembled video, approved audio when applicable, and the default burned subtitle layer.

## Flow2API final-generation boards

Reference evidence masters are audit artifacts and may contain up to 15 RFs. They are not Flow2API inputs. Deliver separate final-generation boards in `generation-storyboards/`:

- Use the target duration and raw-segment duration from `plan/content-system-config-snapshot.json`, after confirming the current model catalog can execute them. Assemble the configured chronological segments to the exact approved target.
- Deliver exactly one PNG board per raw segment, named `Segment-XX_start-end.png`.
- Each board has the chronological panel count, grid, ratio and raw duration specified in `plan/content-system-config-snapshot.json`. Set explicit start/end times that sum to the raw segment duration; panel durations may vary with the action. Generate the complete board in one image request. State the layout, reading order, timing, zero gutter, and no-text/no-watermark/no-UI constraints in that prompt. Do not crop, split, resize, or locally compose its returned board; record the board prompt and all panel timings in the package manifest.
- Upload every board to the linked content version's `content_library.storyboard_attachments` field. Re-read the record and verify its attachment count, filenames, and file tokens before setting the schema-resolved pending-review state.
 - Do not create, update, or upload any `content_library` record or attachment until every required board exists locally and has passed the configuration-profile validator. A missing, pending, failed, or unvalidated board is a local-only blocked package, not a partial content record.

## Acceptance

- For `full_replication`, batch sheets retain source time order and recognizable shot, scene, action, lighting, and pacing while changing only product-related pixels.
- For `full_replication`, batch geometry must remain within `plan/storyboard-spec.json` tolerance for the source sheet and its implied 9:16 panels; otherwise regeneration is required before master assembly.
- New product identity, connections, relative position, and user-stated usage are visible. No old product, old packaging, UI, watermark, subtitle, or incompatible copy remains.
- For filling, opening, disassembly, or cleaning, provide an interaction substitution record and visible proof. Wrong hole, direction, cap, lid, separated piece, opaque lattice, or implausible drainage fails.
- For `full_replication`, masters are balanced chronological partitions with full, unique coverage of all valid RFs. A master may not import a batch or master from another run.
- Each Flow2API board maps to one configured raw segment. The complete board set must cover the configured target duration exactly.
- The remote `content_library.storyboard_attachments` field contains all matching board attachments before the schema-resolved pending-review state is set.
- Regenerate a failed batch once only. If it still fails, mark it FAIL and stop rather than changing batch boundaries.
