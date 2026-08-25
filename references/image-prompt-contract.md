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
  "target_duration_seconds": 10,
  "raw_segment_seconds": 10,
  "candidates_per_segment": 2,
  "storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"},
  "image_output": {"size": "1152x2048", "quality": "high", "format": "png"},
  "segments": [{
    "segment_id": "Segment-01",
    "target_time_range": {"start": 0, "end": 10},
    "source_narrative_segment_ids": ["SourceNarrative-01", "SourceNarrative-02"],
    "subject_strategy": "preserve_source_subject",
    "product_visible": true,
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

Every storyboard-image plan uses `generation_unit=target_production_segment`, `raw_segment_seconds=10`, one contiguous target time range per Segment and exactly one 2×2 board for each script version (A and B). `target_duration_seconds` must be divisible by 10 and the number of logical Segment entries must equal `target_duration_seconds / 10`. The compiled bundle expands the two complete version packages into deterministic `execution_jobs`, records the version and Segment for every job, and writes only the ordered A/B packages to the script table. Its `submission_policy` must select concurrent GPT Image 2 execution whenever `expected_job_count >= 2`, with maximum concurrency 5; a bundle that silently chooses serial submission fails validation. A transport retry reuses the same logical Segment/version plan and idempotency key; it does not add a Segment or approval record. `target_time_range` is global within the target film; each Segment's `beats` use local `0–10s` timing.

For `storyboard_image`, `beats` are the four panel keyframes, not prose descriptions of motion. They must be chronological, contiguous, cover the whole raw Segment, and occur in exact reading order: `top_left`, `top_right`, `bottom_left`, `bottom_right`. Every keyframe must declare `camera`, one directly observable static `description`, inherited `continuity`, and `human_presence` as `none`, `one_hand`, `partial_person`, or `full_person`. When a beat contains a process such as pouring, loading, opening, turning or dispensing, choose the single frozen instant that proves it: visible orientation, unobstructed path, object positions and the exact carried state. Do not ask one panel to show an entire process.

Panel durations remain an editorial decision. Allocate time to hook, proof, reaction and CTA according to the actual action; do not default to equal panels merely because a board has four cells.

The control prompt uses English (`en`) only. It contains no Thai or Chinese because storyboard generation has no spoken-dialogue payload.

For `full_replication`, every target production Segment declares the ordered `source_narrative_segment_ids` mapped into its 10-second target window. Its input plan contains exactly two routed source-reference roles: `source_segment_start` from the first mapped source narrative and `source_segment_result` from the last. The target-script timeline describes the target-product action connecting those states. Intermediate source evidence, source timestamps, per-second frames, RF batches and replacement contact sheets are not generation inputs.

Source narrative order and relative pacing are planning evidence. The locked target script owns exact Beat timing. Keep source narrative IDs, source timestamps, rhythm-authority explanations and workflow instructions in the plan and compiled bundle metadata; never send them to the image model.

Every replication Segment declares `subject_strategy`. `preserve_source_subject` requires the two source frames and product anchor but forbids a subject anchor. `replace_subject` additionally requires exactly one subject anchor. `structure_only` is valid only for structure replication, requires product and subject anchors, and forbids source frames as generation inputs. Prompts must state which identity authority wins; never create a blank-scene cleaning step.

## Product-appearance authority

When a product anchor is routed, let that input own visual identity. The compiler states that the model must match its exact colourway, silhouette, proportions, surface texture, feature count, openings and relative positions, and must not reinterpret appearance from the product name or category.

Do not add a colour, material, finish, feature count or shape adjective merely because it is typical of the named product category. Name such an attribute only when the current product record explicitly states it. Otherwise refer to the exact appearance shown in the routed anchor. A prompt-plan fact that conflicts with the anchor blocks submission.

## Required prompt blocks

Compile every image prompt from the plan with these blocks, in this order:

1. `OUTPUT SPECIFICATION`: one complete board, raw Segment duration, exact 2×2 layout, four 9:16 panels and reading order. Say that panels touch edge-to-edge, remain visually independent and have hard boundaries, while forbidding blank gutters, gaps, grooves, visible divider lines, decorative borders, labels and cross-panel fusion.
2. `GLOBAL VISUAL CONTINUITY`: concise phone-video style plus the same scene, surface, lighting, product identity, subject identity and spatial relationship across all four panels unless a keyframe explicitly changes one.
3. `REFERENCE AND IDENTITY AUTHORITY`: exact `Input N → role` mapping, product-anchor appearance lock, subject identity lock and the selected subject strategy.
4. `PRODUCT AND ACTION CONSTRAINTS`: only approved product facts and permitted actions relevant to this Segment. Do not repeat generic layout, workflow or source-reference metadata here.
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
