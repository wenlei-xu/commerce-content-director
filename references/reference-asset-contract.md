# Generation reference-asset contract

Read this contract whenever a storyboard-image or final-video Job routes product, subject, board, or continuity images. It defines generation inputs, not source-record retention.

## One image, one authority

Use the smallest evidence set that proves the current Segment. Do not send every available asset by default.

| Role | Use it when | Authority | Do not use it for |
| --- | --- | --- | --- |
| `product_anchor` | the product is visible | overall identity and proportions | a specific opening or interaction path |
| `product_detail` | the Segment shows a structure-sensitive feature | that feature's geometry | scale, placement, or subject identity |
| `product_scene` | scale, placement, or real-use context is visually necessary | those contextual facts | product geometry or a different subject identity |
| `subject_anchor` | an identifiable subject recurs | that subject's identity | product structure |
| `storyboard_board` | final-video generation | chronology, action, camera intent, and progression | product or subject facts that conflict with approved anchors |
| `continuity_frame` | a later final-video Segment needs a visual handoff | the immediately preceding accepted state | product facts or subject identity |
| `source_segment_start` | full-replication storyboard work | entering scene, composition and visible state; source-subject identity only under `preserve_source_subject` | target-product identity or a replacement subject |
| `source_segment_result` | full-replication storyboard work | visible payoff and handoff state; source-subject identity only under `preserve_source_subject` | target-product identity or a replacement subject |

For a visible product, route one clean `product_anchor` by default. Add exactly one targeted `product_detail` for a structure-sensitive beat, or one clean `product_scene` for a scale/placement-sensitive beat. Add both only when the same Segment genuinely needs both facts and the catalog input limit permits it. A later final-video Segment normally uses `continuity_frame` instead of a low-value scene reference.

When the product record's `default_anchor` is an approved six-panel product board, route that board as the sole product input by default. Do not automatically add the product's detail or scene attachments; retain them as source evidence and use them only when the board is explicitly insufficient for the current shot. For the pineapple board, the bottom-hole close-up and inverted loading panel establish the loading path; the other overall panels establish identity and proportions. The board's hand demonstrates the product action only and does not replace a selected subject anchor.

## Subject strategy

Resolve one strategy before routing generation inputs:

| Strategy | Use when | Generation inputs |
| --- | --- | --- |
| `preserve_source_subject` | Same-category full replication and the original person or animal can remain | source start/result frames + target product anchor |
| `replace_subject` | The user explicitly selects a breed, person or recurring identity | source start/result frames + target product anchor + target subject anchor |
| `structure_only` | Cross-species, cross-category or interaction-incompatible references | source frames remain planning evidence only; use the script + target product anchor + target subject anchor |

`preserve_source_subject` is the default decision for compatible full replication, but it must still be written explicitly in the plan. Do not add a subject anchor or erase the source subject in that strategy. `replace_subject` performs product and subject replacement in the same generation step; do not create an empty-scene intermediate. `structure_only` is not full replication and must route to structure replication before generation.

## Input hygiene

Generation inputs must be clean derivatives of authoritative source assets when the source contains labels, borders, watermarks, UI, comparison grids, or genuinely unrelated subjects. Retain the original for audit, but submit the clean derivative and record both hashes.

- No readable text, labels, logos, watermarks, UI, panel numbers, or decorative borders in an input intended for generation.
- A generic `product_scene` reference must not contain a person or animal that conflicts with a selected subject. This restriction does not require removing the narratively active source person, animal or product from `source_segment_start` or `source_segment_result`; their authority is controlled by `subject_strategy`.
- Cleaning source-segment frames removes text, watermark, UI, borders and unrelated overlays. It must not erase the source subject or source product merely to avoid identity competition. If `replace_subject` remains visually unstable, use a targeted mask as a fallback instead of synthesizing a blank scene.
- A multi-view anchor may contain only enough views to establish identity. Keep important features large enough to survive the configured input resize; use a targeted detail image rather than a crowded contact sheet.
- Never infer a structure or interaction from a reference image name. Facts remain in the current product record.
- If two assets disagree on product geometry, colourway, packaging, subject identity, or permitted interaction, stop and resolve the source conflict before generation.

## Asset-plan record

Every routed image must appear in the generation prompt plan with `position`, `role`, `asset_id`, `sha256`, and a Segment-specific `reason`. `clean_for_generation` must be `true`. Optional assets require a reason tied to a current beat; “available in the product record” is not a reason.

Store source field, filename, remote token, local path, source hash, derivative hash when applicable, role, input position, and Segment mapping in the local package. The model input array must match this record exactly.

For full replication, route exactly one `source_segment_start` and one `source_segment_result` for the current narrative segment. Do not add intermediate source-video frames or a chronological contact sheet. Add the current product anchor. Add a selected subject anchor only for `replace_subject`; `preserve_source_subject` must not route one. `structure_only` routes no source-segment frames.
