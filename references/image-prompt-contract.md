# Storyboard-image prompt contract

Read this contract for every storyboard-image Job, including original, hook/structure replication, and full-replication replacement boards. For routed assets, also read [reference-asset-contract.md](reference-asset-contract.md).

## Prompt-plan source

Before writing prose, create `plan/generation-prompt-plan.json` with this shape:

```json
{
  "schema": "commerce-generation-prompt-plan-v1",
  "job_kind": "storyboard_image",
  "prompt_language": "en",
  "raw_segment_seconds": 10,
  "storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"},
  "common_constraints": ["Natural handheld phone-video texture."],
  "segments": [{
    "segment_id": "Segment-01",
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

`beats` must be chronological, contiguous, and cover the whole raw Segment. Their durations are an editorial decision: allocate time to hook, proof, reaction, and CTA according to the actual action. Do not default to equal panels merely because a board has four cells. A constant duration is valid only when the selected action genuinely warrants it.

The control prompt uses `en` by default or `zh-CN`; it contains no Thai because storyboard generation has no spoken-dialogue payload.

## Required prompt blocks

Compile every image prompt from the plan with these blocks, in this order:

1. `OUTPUT`: one complete board, raw Segment duration, grid, panel ratio, reading order, zero gutter, and no local composition.
2. `INPUT IMAGE ROLES`: exact `Input N → role` mapping and the authority boundaries from the reference-asset contract.
3. `HARD FACTS`: only approved product/subject constraints relevant to the Segment.
4. `TIMELINE`: one beat per panel or action window with start/end times, action, product state, camera intent, and transition when needed.
5. `NEGATIVE CONSTRAINTS`: no readable text, captions, UI, watermark, logo, panel labels, or fact-incompatible structure/action.

Never say “use the product images” without the position-to-role map. Do not include dialogue, subtitles, translated spoken lines, or a generic full-film narrative in an image prompt.

## Compile and validate

```powershell
python scripts/compile_generation_prompts.py plan/generation-prompt-plan.json --out plan/compiled-prompts.json
python scripts/validate_prompt_bundle.py plan/compiled-prompts.json
python scripts/validate_image_prompt_language.py --language en plan/compiled-prompts.json
```

The bundle validator checks input records, beat coverage, required prompt sections, and Segment-scoped dialogue metadata. It does not replace visual review or the configuration-profile storyboard validator.
