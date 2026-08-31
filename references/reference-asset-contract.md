# Generation reference-asset contract

Read this contract whenever a first-frame image or final-video Job routes product, subject, first-frame, or continuity images. It defines generation inputs, not source-record retention.

## One image, one authority

Use the smallest evidence set that proves the current Segment. Do not send every available asset by default.

| Role | Use it when | Authority | Do not use it for |
| --- | --- | --- | --- |
| `product_anchor` | the product is visible | overall identity and proportions | a specific opening or interaction path |
| `product_detail` | the Segment shows a structure-sensitive feature | that feature's geometry | scale, placement, or subject identity |
| `product_scene` | scale, placement, or real-use context is visually necessary | those contextual facts | product geometry or a different subject identity |
| `subject_anchor` | an identifiable subject recurs | that subject's identity | product structure |
| `scene_anchor` | a reusable environment is needed for spatial continuity or natural capture treatment | room geometry, light direction, usable activity area and lived-in phone-capture texture | product geometry, subject identity, product claims or unsupported interaction |
| `first_frame_asset` | final-video generation | approved Segment entering state, initial composition and continuity handoff | product or subject facts that conflict with approved anchors |
| `continuity_frame` | a later final-video Segment needs a visual handoff | the immediately preceding accepted state | product facts or subject identity |
| `source_segment_start` | full-replication target production first frame | entering scene, composition and visible state selected from the first mapped source narrative segment; source-subject identity only under `preserve_source_subject` | target-product identity, exact target timing or a replacement subject |
| `source_segment_result` | full-replication target production first frame | visible payoff and handoff state selected from the last mapped source narrative segment; source-subject identity only under `preserve_source_subject` | target-product identity, exact target timing or a replacement subject |

For a visible product, route one clean `product_anchor` by default. Add exactly one targeted `product_detail` for a structure-sensitive beat, or one clean `product_scene` for a scale/placement-sensitive beat. Add both only when the same Segment genuinely needs both facts and the catalog input limit permits it. A later final-video Segment normally uses `continuity_frame` instead of a low-value scene reference.

When the product record's `default_anchor` is an approved multi-view product reference, route that reference as the sole product input by default. Do not automatically add the product's detail or scene attachments; retain them as source evidence and use them only when the reference is explicitly insufficient for the current shot. For the pineapple reference, the bottom-hole close-up and inverted loading view establish the loading path; the other overall views establish identity and proportions. A hand shown in the reference demonstrates the product action only and does not replace a selected subject anchor.

For original production, route one approved `scene_anchor` when the Beat depends on a stable room, activity zone or capture treatment. Use the scene anchor only for background geometry, camera direction, lighting, open floor or surface area, and ordinary lived-in smartphone texture. Do not inherit people, animals, products, text, logos, claims or unsupported actions from the scene image. If the selected scene is a casual phone photo, preserve neutral white balance and natural exposure; do not add a warm showroom grade.

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
- A multi-view anchor may contain only enough views to establish identity. Keep important features large enough to survive the configured input resize; use a targeted detail image rather than a crowded multi-image layout.
- Never infer a structure or interaction from a reference image name. Facts remain in the current product record.
- If two assets disagree on product geometry, colourway, packaging, subject identity, or permitted interaction, stop and resolve the source conflict before generation.

## Asset-plan record

Every routed image must appear in the generation prompt plan with `position`, `role`, `asset_id`, `sha256`, and a Segment-specific `reason`. `clean_for_generation` must be `true`. Optional assets require a reason tied to a current beat; “available in the product record” is not a reason.

When the image is sent to the remote Flow2API MCP gateway, persist the gateway's returned `gateway_asset_id` beside the source `asset_id`; these are different authorities. Final-video submission must pass only the gateway IDs through `input_asset_ids` (or public HTTPS `input_asset_urls` for the gateway's import path), never inline Base64 images. The source `asset_id` remains the local/Feishu evidence identity and must not be mistaken for a gateway input asset ID.

Store source field, filename, remote token, local path, source hash, derivative hash when applicable, role, input position, and Segment mapping in the local package. The model input array must match this record exactly.

For high-fidelity replication, retain two local evidence frames per source narrative segment, but route exactly one `source_segment_start` and one `source_segment_result` for the current target 10-second production Segment. Select them from the first and last mapped source narrative segments in `plan/replication-rhythm-map.json`. Intermediate evidence frames remain planning evidence captured by target Beats; do not add them by default. Add the current product anchor. Add a selected subject anchor only for `replace_subject`; `preserve_source_subject` must not route one. `structure_only` routes no source-segment frames.
