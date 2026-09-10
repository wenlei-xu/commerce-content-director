# First-frame image prompt contract

Read this contract for every video first-frame Job, including original, hook/structure replication, and two-frame full-replication Segment first frames. For routed assets, also read [reference-asset-contract.md](reference-asset-contract.md).

## Prompt-plan source

Before writing prose, create `plan/generation-prompt-plan.json` with this shape:

```json
{
  "schema": "commerce-generation-prompt-plan-v1",
  "job_kind": "first_frame_image",
  "executor": "gpt_image_2_5",
  "model": "gpt-image-2.5",
  "replication_mode": "high_fidelity_replication",
  "generation_unit": "target_production_segment",
  "prompt_language": "en",
  "target_spoken_language": "zh-CN",
  "source_visual_style": {
    "style_fingerprint_en": "Match the source's casual low-angle handheld phone capture, natural indoor exposure, moderate softness and social-platform compression.",
    "anti_style_constraints_en": "Do not turn the source treatment into studio lighting, cinematic depth of field, commercial sharpness or overly polished composition."
  },
  "target_duration_seconds": 10,
  "raw_segment_seconds": 10,
  "versions": ["A", "B"],
  "candidates_per_segment": 1,
  "first_frame_layout": {"aspect_ratio": "9:16"},
  "image_output": {"size": "1152x2048", "quality": "high", "format": "png"},
  "segments": [{
    "segment_id": "Segment-01",
    "target_time_range": {"start": 0, "end": 10},
    "source_narrative_segment_ids": ["SourceNarrative-01", "SourceNarrative-02"],
    "subject_strategy": "preserve_source_subject",
    "product_visible": true,
    "product_visual_lock": "Treat all approved integrated product components as one inseparable structure. Preserve their approved positions and connection path in the first frame; do not omit, replace, reconnect, hide, or rotate them into an ambiguous orientation.",
    "visual_continuity": [
      "Natural handheld phone-video texture.",
      "Use the same room, floor surface and natural light at the Segment boundary."
    ],
    "inputs": [{"position": 1, "role": "product_anchor", "asset_id": "product-v1", "sha256": "...", "clean_for_generation": true, "reason": "Product is visible in beats 2–4."}],
    "beats": [
      {"start": 0, "end": 10, "description": "The locked Beat timeline for this 10-second Segment."}
    ],
    "first_frame": {
      "camera": "Tight handheld close-up.",
      "composition": "Keep the entering product state and relevant subject/action context unobstructed.",
      "static_moment": "One frozen entering-state moment at local t=0 with the problem clearly visible.",
      "performance": "No visible human performance.",
      "continuity": "Opening state in the same room and light as the previous Segment handoff.",
      "human_presence": "none"
    },
    "hard_constraints": ["The approved opening is the only loading path."],
    "negative_constraints": ["No readable text or UI."],
    "subject_identity": "Selected subject description when applicable."
  }]
}
```

`executor` must be exactly `gpt_image_2_5`. `model` must be exactly `gpt-image-2.5`, and `model_catalog.image_model` in `plan/content-system-config-snapshot.json` plus the approved execution route must agree on that exact ID and its usable input limit. `image_output` is fixed to `1152x2048`, high quality, PNG so each generated first frame is an exact 9:16 portrait image. These values are execution requirements, not illustrative examples. Another GPT Image model, `chatgpt-image-latest`, Flow2API image generation, or a compiler/validator mismatch blocks submission.

Every first-frame plan (schema key `first_frame_image`) uses `generation_unit=target_production_segment`, `raw_segment_seconds=10`, one contiguous target time range per Segment and exactly two complete packages (`versions=["A", "B"]`). `target_duration_seconds` must be divisible by 10 and the number of logical Segment entries must equal `target_duration_seconds / 10`; the compiled bundle expands those Segments by version, records the version and Segment for every Job, and writes only the ordered A/B first-frame packages to the script table. Its `submission_policy` must select concurrent GPT Image 2.5 execution whenever `expected_job_count >= 2`, with maximum concurrency 5; a bundle that silently chooses serial submission fails validation. A transport retry reuses the same logical Segment/version plan and idempotency key; it does not add a Segment or approval record. `target_time_range` is global within the target film; each Segment's `beats` use local `0–10s` timing and `first_frame` represents local `t=0`.

For each first-frame image, `Director` owns one first-frame decision per Segment. Its output must declare `camera`, `composition`, one directly observable entering-state `static_moment`, `performance`, inherited `continuity`, and `human_presence` as `none`, `one_hand`, `partial_person`, or `full_person`. The decision is anchored at local `t=0` and must not depict the full 10-second process. The Director output is a derived plan and may not mutate the locked script.

The first frame has no editorial panel duration. Use the locked Beat timeline to decide the Segment's action; the image only establishes the entering state and continuity handoff.

The control prompt uses English (`en`) only. It contains no Thai or Chinese because first-frame image generation has no spoken-dialogue payload.

For `high_fidelity_replication`, every target production Segment declares the ordered `source_narrative_segment_ids` mapped into its 10-second target window. Its input plan contains exactly two routed source-reference roles: `source_segment_start` from the first mapped source narrative and `source_segment_result` from the last. The target-script timeline describes the target-product action connecting those states. Intermediate source evidence, source timestamps and per-second frames are not generation inputs.

For `high_fidelity_replication` and `structure_replication`, the plan must contain `source_visual_style.style_fingerprint_en` and `source_visual_style.anti_style_constraints_en`, copied from the evidence-backed source visual-style profile. Both values must be non-empty English control text and are passed verbatim into every Segment's `PHONE IMAGE TEXTURE` block. They preserve transferable capture treatment, not source-product identity: product and subject authority may replace conflicting objects/actions, but must not restyle the scene without an explicit user request. A replication plan without this source-style payload fails compilation.

Source narrative order and relative pacing are planning evidence. The locked target script owns exact Beat timing. Keep source narrative IDs, source timestamps, rhythm-authority explanations and workflow instructions in the plan and compiled bundle metadata; never send them to the image model.

Every replication Segment declares `subject_strategy`. `preserve_source_subject` requires the two source frames and product anchor but forbids a subject anchor. `replace_subject` additionally requires exactly one subject anchor. `structure_only` is valid only for structure replication, requires product and subject anchors, and forbids source action frames as generation inputs. It may optionally include one `source_scene_reference`, which controls only scene space, camera, light and spatial composition; it must not transfer the source subject, product, text, logo or source-specific hardware. Prompts must state which identity authority wins; never create a blank-scene cleaning step.

## Product-appearance authority

When a product anchor is routed, let that input own visual identity. The compiler states that the model must match its exact colourway, silhouette, proportions, surface texture, feature count, openings and relative positions, and must not reinterpret appearance from the product name or category.

When the product record declares a fixed integrated visual structure, every product-visible Segment must also carry `product_visual_lock`: concise English control text that names the integral components, their approved relative positions and connection path, and the forbidden omission, substitution, reconnection, concealment or ambiguous rotation. Copy it verbatim into that Segment's `PRODUCT LOCK` block. The complete front product anchor that visibly includes every locked component must be Input 1; when both target subject and source scene-space assets are used, route the subject as Input 2 and the source scene-space reference as Input 3. Later references may inform subject identity or scene space, but may not dilute product identity or alter the locked topology.

Do not add a colour, material, finish, feature count or shape adjective merely because it is typical of the named product category. Name such an attribute only when the current product record explicitly states it. Otherwise refer to the exact appearance shown in the routed anchor. A prompt-plan fact that conflicts with the anchor blocks submission.

## Required prompt blocks

Compile every first-frame image prompt from the plan with these required headings, in this order. Keep the content concise and non-duplicative:

1. `REFERENCE IMAGE ROLE`: exact `Input N → role` mapping and concise identity ownership for every routed reference. The product anchor owns product appearance and topology; it is not a layout reference.
2. `OUTPUT SPECIFICATION`: one 9:16 portrait first-frame image for the raw Segment, representing the entering state at local `t=0`. Do not generate multiple images, a grid, a contact sheet, a divider, a border or multiple panels.
3. `CREATIVE INTENT`: the viewer's intended first read, emotional cue or initial misunderstanding. Use the Director's variant direction as the priority signal.
4. `CAMERA OPERATOR VIEWPOINT`: camera height, viewpoint, framing, human presence and visual focus. Make the filming person observable when the scene requires a vlog or UGC feel.
5. `SCENE EVENT`: one directly observable frozen situation at local `t=0`, plus only the environment and continuity facts needed to understand it. Do not describe the full video or future actions.
6. `SUBJECT PERFORMANCE`: the selected subject's visible identity, expression, pose and performance in this entering state.
7. `PRODUCT LOCK`: only approved product placement, geometry, integrated structure and permitted action relevant to this frame. Do not repeat generic workflow or source metadata.
8. `PHONE IMAGE TEXTURE`: concrete evidence of the intended capture treatment, including handheld imperfection, auto-exposure, focus behavior, compression, household light and lived-in texture when relevant.
9. `NEGATIVE CONSTRAINTS`: only critical exclusions such as text, watermark, duplicates, malformed hands or fact-incompatible structure/action.

Never say “use the product images” without the position-to-role map. Do not include dialogue, subtitles, translated spoken lines, source narrative IDs, source timestamps, workflow notes, local assembly instructions or a generic full-film narrative in an image prompt.

## Compile and validate

```powershell
python scripts/compile_generation_prompts.py plan/generation-prompt-plan.json --out plan/compiled-prompts.json
python scripts/validate_prompt_bundle.py plan/compiled-prompts.json
python scripts/validate_image_prompt_language.py --language en plan/compiled-prompts.json
```

The bundle validator checks input records, beat coverage, required prompt sections, and Segment-scoped dialogue metadata. It does not replace visual review or the configuration-profile first-frame validator.
