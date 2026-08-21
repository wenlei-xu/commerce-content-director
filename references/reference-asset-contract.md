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
| `source_contact_sheet` | full-replication storyboard work | source composition and chronology | the replacement product or subject identity |

For a visible product, route one clean `product_anchor` by default. Add exactly one targeted `product_detail` for a structure-sensitive beat, or one clean `product_scene` for a scale/placement-sensitive beat. Add both only when the same Segment genuinely needs both facts and the catalog input limit permits it. A later final-video Segment normally uses `continuity_frame` instead of a low-value scene reference.

## Input hygiene

Generation inputs must be clean derivatives of authoritative source assets when the source contains labels, borders, watermarks, UI, comparison grids, or unrelated subjects. Retain the original for audit, but submit the clean derivative and record both hashes.

- No readable text, labels, logos, watermarks, UI, panel numbers, or decorative borders in an input intended for generation.
- A scene reference must not contain a person or animal that conflicts with the selected subject. Use a subject-free scale reference or omit it.
- A multi-view anchor may contain only enough views to establish identity. Keep important features large enough to survive the configured input resize; use a targeted detail image rather than a crowded contact sheet.
- Never infer a structure or interaction from a reference image name. Facts remain in the current product record.
- If two assets disagree on product geometry, colourway, packaging, subject identity, or permitted interaction, stop and resolve the source conflict before generation.

## Asset-plan record

Every routed image must appear in the generation prompt plan with `position`, `role`, `asset_id`, `sha256`, and a Segment-specific `reason`. `clean_for_generation` must be `true`. Optional assets require a reason tied to a current beat; “available in the product record” is not a reason.

Store source field, filename, remote token, local path, source hash, derivative hash when applicable, role, input position, and Segment mapping in the local package. The model input array must match this record exactly.
