# Stage 2: contact-sheet light adaptation

Turn every source MF into a same-time RF. The MF is authoritative for camera, crop, subject distance, background placement, occlusion, lighting, action phase, motion, and rhythm. Replace only product-related pixels and fact-incompatible action.

Write `plan/product-interaction-facts.md` first. Record visible parts, connections, valid contact points, allowed actions, prohibited actions, and evidence source. User-stated product mechanics override source actions and model assumptions. Use existing product assets; do not make six-views unless requested.

Copy user constraints verbatim to `plan/user-constraints.md`. When an action conflicts, create `plan/interaction-substitutions.md` before generation. Keep the original hand position, camera, background, and pacing while making the valid mechanism visually unambiguous.

Create `plan/reference-batches.json` using fixed chronological `6+...+tail` batches. Full source sheets are 3x2; tail source sheets are horizontal. For each RF record source/target time, source anchor, allowed replacement, prohibited changes, final frame, action, product state, transition, evidence, and expected product relative position/width/height. The relative-scale fields are batch-review acceptance inputs, not optional prompt flavor.

Write one `batch-image-prompt.md` per batch. Include the style fingerprint and anti-style constraints verbatim, expected source-sheet aspect ratio, 3x2 or tail layout, reading order, per-panel local replacement, and product relative scale. Require every replacement cell to retain the source 9:16 panel geometry; treat it as a fidelity constraint even though the returned batch is not yet a final master.

Before batch generation, calculate `plan/master-groups.json`: let `K = ceil(valid_rf_count / 15)`, then partition consecutive RFs into `K` chronological groups whose sizes differ by at most one. Do not group by whole batch boundaries.
