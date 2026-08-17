# Batch and master storyboard review

Write `batches/Batch-XX/batch-review.md` for every batch. List each RF ID, source time, source frame, visible evidence, verdict, and repair action. Review the batch sheet before any master extraction.

Check these items:

1. Product and interaction facts: product appearance, connections, openings, and hand contact match approved assets and facts. Filling, opening, cleaning, and disassembly panels must prove the correct mechanism. Wrong holes, wrong orientation, lids, or separated pieces fail.
2. Shot and rhythm fidelity: compare source and replacement sheets in order for camera, distance, background, occlusion, lighting, exposure, action phase, and cut destination. Do not accept redesigned scenes or polished advertising imagery.
3. Product scale: compare planned product relative width, height, and position in every panel. Fail clearly disruptive scale drift and record minor drift as a limitation.
4. Geometry: verify the replacement full-sheet aspect and every implied panel aspect against `plan/storyboard-spec.json`. A drift above its stated tolerance fails because it would corrupt master extraction.
5. Clean output: no old product, packaging, watermark, UI, subtitle, panel number, or incompatible text.

Any hard-fact, geometry, scale, shot-order, or recognizable-composition failure fails the batch. Regenerate the same batch once only; stop if it still fails.

After batch acceptance, write `masters/Master-XX/master-review.md`. Verify the manifest has only current-run accepted inputs, expected RF range/count, chronological order, complete coverage across all masters, no duplicate RF, and no master with more than 15 frames. The balanced partition must satisfy `K=ceil(N/15)` and have master counts differing by at most one.
