# Storyboard-image prompt contract

Read this contract for every storyboard-image Job, including original, hook/structure replication, and two-frame full-replication segment boards. For routed assets, also read [reference-asset-contract.md](reference-asset-contract.md).

## Prompt-plan source

Before writing prose, create `plan/generation-prompt-plan.json` with this shape:

```json
{
  "schema": "commerce-generation-prompt-plan-v1",
  "job_kind": "storyboard_image",
  "executor": "flow2api_mcp",
  "model": "gemini-3.1-flash-image-portrait",
  "replication_mode": "full_replication",
  "generation_unit": "target_production_segment",
  "prompt_language": "en",
  "target_duration_seconds": 10,
  "raw_segment_seconds": 10,
  "storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"},
  "common_constraints": ["Natural handheld phone-video texture."],
  "segments": [{
    "segment_id": "Segment-01",
    "target_time_range": {"start": 0, "end": 10},
    "source_narrative_segment_ids": ["SourceNarrative-01", "SourceNarrative-02"],
    "subject_strategy": "preserve_source_subject",
    "product_visible": true,
    "inputs": [{"position": 1, "role": "product_anchor", "asset_id": "product-v1", "sha256": "...", "clean_for_generation": true, "reason": "Product is visible in beats 2–4."}],
    "beats": [
      {"start": 0, "end": 1.5, "description": "Hook: show the problem."},
      {"start": 1.5, "end": 4, "description": "Introduce the product."},
      {"start": 4, "end": 7, "description": "Show the proof action."},
      {"start": 7, "end": 10, "description": "Show the reaction and CTA state."}
    ],
    "hard_constraints": ["No readable text or UI."],
    "subject_identity": "Selected subject description when applicable."
  }]
}
```

`executor` must be exactly `flow2api_mcp`. `model` must exactly match the available image-model ID selected from the fresh Flow2API catalog and recorded at `model_catalog.image_model` in `plan/content-system-config-snapshot.json`; the example value is illustrative, not a fixed default. A compiler or validator failure on either field blocks submission. Do not rewrite the plan to `gpt_image` and do not call GPT Image outside the plan.

Every storyboard-image plan uses `generation_unit=target_production_segment`, `raw_segment_seconds=10`, one contiguous target time range per Segment and exactly one 2×2 board per Segment. `target_duration_seconds` must be divisible by 10 and the number of Segment entries must equal `target_duration_seconds / 10`. This output rule is identical for original and replication modes. `target_time_range` is global within the target film; each Segment's `beats` use local `0–10s` timing.

`beats` must be chronological, contiguous, and cover the whole raw Segment. Their durations are an editorial decision: allocate time to hook, proof, reaction, and CTA according to the actual action. Do not default to equal panels merely because a board has four cells. A constant duration is valid only when the selected action genuinely warrants it.

The control prompt uses `en` by default or `zh-CN`; it contains no Thai because storyboard generation has no spoken-dialogue payload.

For `full_replication`, every target production Segment declares the ordered `source_narrative_segment_ids` mapped into its 10-second target window. Its input plan contains exactly two routed source-reference roles: `source_segment_start` from the first mapped source narrative and `source_segment_result` from the last. The target-script timeline describes the target-product action connecting those states. Intermediate source evidence, source timestamps, per-second frames, RF batches and replacement contact sheets are not generation inputs.

Source narrative order and relative pacing are evidence. The locked target script owns exact Beat timing. A prompt must state this rhythm authority and must not copy source timecodes or default to equal 2.5-second panels.

Every replication Segment declares `subject_strategy`. `preserve_source_subject` requires the two source frames and product anchor but forbids a subject anchor. `replace_subject` additionally requires exactly one subject anchor. `structure_only` is valid only for structure replication, requires product and subject anchors, and forbids source frames as generation inputs. Prompts must state which identity authority wins; never create a blank-scene cleaning step.

## Required prompt blocks

Compile every image prompt from the plan with these blocks, in this order:

1. `OUTPUT`: one complete board, raw Segment duration, grid, panel ratio, reading order, zero gutter, and no local composition.
2. `INPUT IMAGE ROLES`: exact `Input N → role` mapping and the authority boundaries from the reference-asset contract.
3. `HARD FACTS`: only approved product/subject constraints relevant to the Segment.
4. `RHYTHM AUTHORITY`: the locked target script owns exact timing; replication source order and relative pacing are evidence only.
5. `TIMELINE`: one beat per panel or action window with start/end times, action, product state, camera intent, and transition when needed.
6. `NEGATIVE CONSTRAINTS`: no readable text, captions, UI, watermark, logo, panel labels, or fact-incompatible structure/action.

Never say “use the product images” without the position-to-role map. Do not include dialogue, subtitles, translated spoken lines, or a generic full-film narrative in an image prompt.

## Compile and validate

```powershell
python scripts/compile_generation_prompts.py plan/generation-prompt-plan.json --out plan/compiled-prompts.json
python scripts/validate_prompt_bundle.py plan/compiled-prompts.json
python scripts/validate_image_prompt_language.py --language en plan/compiled-prompts.json
```

The bundle validator checks input records, beat coverage, required prompt sections, and Segment-scoped dialogue metadata. It does not replace visual review or the configuration-profile storyboard validator.
