# Storyboard-image prompt contract

Read this contract for every storyboard-image Job, including original, hook/structure replication, and two-frame full-replication segment boards. For routed assets, also read [reference-asset-contract.md](reference-asset-contract.md).

## Prompt-plan source

Before writing prose, create `plan/generation-prompt-plan.json` with this shape:

```json
{
  "schema": "commerce-generation-prompt-plan-v1",
  "job_kind": "storyboard_image",
  "executor": "gpt_image_2",
  "model": "gpt-image-2",
  "replication_mode": "full_replication",
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
  "storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"},
  "image_output": {"size": "1152x2048", "quality": "high", "format": "png"},
  "segments": [{
    "segment_id": "Segment-01",
    "target_time_range": {"start": 0, "end": 10},
    "source_narrative_segment_ids": ["SourceNarrative-01", "SourceNarrative-02"],
    "subject_strategy": "preserve_source_subject",
    "product_visible": true,
    "product_visual_lock": "Treat all approved integrated product components as one inseparable structure. Preserve their approved positions and connection path in every panel; do not omit, replace, reconnect, hide, or rotate them into an ambiguous orientation.",
    "visual_continuity": [
      "Natural handheld phone-video texture.",
      "Use the same room, floor surface and natural light across all four panels."
    ],
    "inputs": [{"position": 1, "role": "product_anchor", "asset_id": "product-v1", "sha256": "...", "clean_for_generation": true, "reason": "Product is visible in beats 2–4."}],
    "beats": [
      {
        "panel": "top_left",
        "start": 0,
        "end": 1.5,
        "camera": "Tight handheld close-up.",
        "description": "One frozen hook moment with the problem clearly visible.",
        "continuity": "Opening state in the same room and light.",
        "human_presence": "none"
      },
      {
        "panel": "top_right",
        "start": 1.5,
        "end": 4,
        "camera": "Product-forward medium close-up.",
        "description": "One frozen product-introduction moment.",
        "continuity": "Carry forward the same room, subject and product scale.",
        "human_presence": "one_hand"
      },
      {
        "panel": "bottom_left",
        "start": 4,
        "end": 7,
        "camera": "Unobstructed proof close-up.",
        "description": "One directly observable proof instant, not a multi-step process.",
        "continuity": "Carry forward the exact product orientation established in the previous panel.",
        "human_presence": "one_hand"
      },
      {
        "panel": "bottom_right",
        "start": 7,
        "end": 10,
        "camera": "Natural reaction medium shot.",
        "description": "One frozen reaction and closing state.",
        "continuity": "Same scene, light, product and subject; show the final state only.",
        "human_presence": "none"
      }
    ],
    "hard_constraints": ["The approved opening is the only loading path."],
    "negative_constraints": ["No readable text or UI."],
    "subject_identity": "Selected subject description when applicable."
  }]
}
```

`executor` must be exactly `gpt_image_2`. `model` must be exactly `gpt-image-2`, and `model_catalog.image_model` in `plan/content-system-config-snapshot.json` plus the approved execution route must agree on that exact ID and its usable input limit. `image_output` is fixed to `1152x2048`, high quality, PNG so the complete 2×2 board and each equal panel remain exact 9:16. These values are execution requirements, not illustrative examples. Another GPT Image model, `chatgpt-image-latest`, Flow2API image generation, or a compiler/validator mismatch blocks submission.

Every storyboard-image plan uses `generation_unit=target_production_segment`, `raw_segment_seconds=10`, one contiguous target time range per Segment and exactly two complete packages (`versions=["A", "B"]`). `target_duration_seconds` must be divisible by 10 and the number of logical Segment entries must equal `target_duration_seconds / 10`; the compiled bundle expands those Segments by version, records the version and Segment for every Job, and writes only the ordered A/B packages to the script table. Its `submission_policy` must select concurrent GPT Image 2 execution whenever `expected_job_count >= 2`, with maximum concurrency 5; a bundle that silently chooses serial submission fails validation. A transport retry reuses the same logical Segment/version plan and idempotency key; it does not add a Segment or approval record. `target_time_range` is global within the target film; each Segment's `beats` use local `0–10s` timing.

For `storyboard_image`, `Director` owns the four panel keyframes. Its output must declare `camera`, `composition`, one directly observable `static_moment`, `performance`, inherited `continuity`, and `human_presence` as `none`, `one_hand`, `partial_person`, or `full_person`. They must be chronological, contiguous, cover the whole raw Segment, and occur in exact reading order: `top_left`, `top_right`, `bottom_left`, `bottom_right`. When a beat contains a process such as pouring, loading, opening, turning or dispensing, choose the single frozen instant that proves it: visible orientation, unobstructed path, object positions and the exact carried state. Do not ask one panel to show an entire process. The Director output is a derived plan and may not mutate the locked script.

Panel durations remain an editorial decision. Allocate time to hook, proof, reaction and CTA according to the actual action; do not default to equal panels merely because a board has four cells.

The control prompt uses English (`en`) only. It contains no Thai or Chinese because storyboard generation has no spoken-dialogue payload.

For `full_replication`, every target production Segment declares the ordered `source_narrative_segment_ids` mapped into its 10-second target window. Its input plan contains exactly two routed source-reference roles: `source_segment_start` from the first mapped source narrative and `source_segment_result` from the last. The target-script timeline describes the target-product action connecting those states. Intermediate source evidence, source timestamps, per-second frames, RF batches and replacement contact sheets are not generation inputs.

For `high_fidelity_replication`, its `full_replication` alias, and `structure_replication`, the plan must contain `source_visual_style.style_fingerprint_en` and `source_visual_style.anti_style_constraints_en`, copied from the evidence-backed source visual-style profile. Both values must be non-empty English control text and are passed verbatim into every Segment's `GLOBAL VISUAL CONTINUITY` block. They preserve transferable capture treatment, not source-product identity: product and subject authority may replace conflicting objects/actions, but must not restyle the scene without an explicit user request. A replication plan without this source-style payload fails compilation.

Source narrative order and relative pacing are planning evidence. The locked target script owns exact Beat timing. Keep source narrative IDs, source timestamps, rhythm-authority explanations and workflow instructions in the plan and compiled bundle metadata; never send them to the image model.

Every replication Segment declares `subject_strategy`. `preserve_source_subject` requires the two source frames and product anchor but forbids a subject anchor. `replace_subject` additionally requires exactly one subject anchor. `structure_only` is valid only for structure replication, requires product and subject anchors, and forbids source action frames and source contact sheets as generation inputs. It may optionally include one `source_scene_reference`, which controls only scene space, camera, light and spatial composition; it must not transfer the source subject, product, text, logo or source-specific hardware. Prompts must state which identity authority wins; never create a blank-scene cleaning step.

## Product-appearance authority

When a product anchor is routed, let that input own visual identity. The compiler states that the model must match its exact colourway, silhouette, proportions, surface texture, feature count, openings and relative positions, and must not reinterpret appearance from the product name or category.

When the product record declares a fixed integrated visual structure, every product-visible Segment must also carry `product_visual_lock`: concise English control text that names the integral components, their approved relative positions and connection path, and the forbidden omission, substitution, reconnection, concealment or ambiguous rotation. Copy it verbatim into that Segment's `PRODUCT AND ACTION CONSTRAINTS` block. The complete front product anchor that visibly includes every locked component must be Input 1; when both target subject and source scene-space assets are used, route the subject as Input 2 and the source scene-space reference as Input 3. Later references may inform subject identity or scene space, but may not dilute product identity or alter the locked topology.

Do not add a colour, material, finish, feature count or shape adjective merely because it is typical of the named product category. Name such an attribute only when the current product record explicitly states it. Otherwise refer to the exact appearance shown in the routed anchor. A prompt-plan fact that conflicts with the anchor blocks submission.

## Required prompt blocks

Compile every image prompt from the plan with these blocks, in this order:

1. `OUTPUT SPECIFICATION`: one complete board, raw Segment duration, exact 2×2 layout, four 9:16 panels and reading order. Say that panels touch edge-to-edge, remain visually independent and have hard boundaries, while forbidding blank gutters, gaps, grooves, visible divider lines, decorative borders, labels and cross-panel fusion.
2. `GLOBAL VISUAL CONTINUITY`: for any replication mode, first include the exact source `style_fingerprint_en` and `anti_style_constraints_en`; then include Segment continuity plus the same scene, surface, lighting, product identity, subject identity and spatial relationship across all four panels unless a keyframe explicitly changes one.
3. `REFERENCE AND IDENTITY AUTHORITY`: exact `Input N → role` mapping, product-anchor appearance lock, subject identity lock and the selected subject strategy. A product-visible Segment with `product_visual_lock` makes the complete front product anchor Input 1 the highest-priority identity reference.
4. `PRODUCT AND ACTION CONSTRAINTS`: first copy `product_visual_lock` verbatim when present, then include only approved product facts and permitted actions relevant to this Segment. Product contact, force path and camera must preserve the lock; do not omit or conceal an integrated component to imitate a source action. Do not repeat generic layout, workflow or source-reference metadata here.
5. `FOUR STATIC KEYFRAMES`: exactly one entry for each panel in reading order. Each entry includes its target time range, camera intent, one frozen visible instant, inherited continuity and minimum human presence. Restate carried orientation or state whenever omitting it could invert the action.
6. `NEGATIVE CONSTRAINTS`: no readable text, captions, UI, watermark, logo, timecode or panel label; no visible grid lines, gutters, borders, panel fusion, duplicate subjects/products, malformed hands or fact-incompatible structure/action.

Never say “use the product images” without the position-to-role map. Do not include dialogue, subtitles, translated spoken lines, source narrative IDs, source timestamps, workflow notes, local assembly instructions or a generic full-film narrative in an image prompt.

## Compile and validate

```powershell
python scripts/compile_generation_prompts.py plan/generation-prompt-plan.json --out plan/compiled-prompts.json
python scripts/validate_prompt_bundle.py plan/compiled-prompts.json
python scripts/validate_image_prompt_language.py --language en plan/compiled-prompts.json
```

The bundle validator checks input records, beat coverage, required prompt sections, and Segment-scoped dialogue metadata. It does not replace visual review or the configuration-profile storyboard validator.
