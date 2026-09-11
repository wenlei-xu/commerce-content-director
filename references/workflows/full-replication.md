# Workflow: high-fidelity full replication first frames

Read [first-frame-generation.md](first-frame-generation.md), [first-frame-execution.md](../first-frame-execution.md), [authority.md](../invariants/authority.md), [knowledge-library-contract.md](../invariants/knowledge-library-contract.md), [product-contract.md](../domain/product-contract.md), [product-execution-contract.md](../invariants/product-execution-contract.md), [reference-asset-contract.md](../reference-asset-contract.md), [first-frame-image-contract.md](../first-frame-image-contract.md), and [mutation-and-recovery.md](../invariants/mutation-and-recovery.md).

Use this workflow for `high_fidelity_replication`. High-fidelity replication preserves the source's story structure, signature hook, shot/action sequence, camera language, relative pacing, emotional reactions, visual style, information release, proof order, payoff and CTA position. It is a narrative-level, shot-level and style-level replication, not chronological per-second or pixel-level replacement.

Run `python scripts/preflight.py --workflow first_frame_generation --mode high_fidelity_replication --target-spoken-language <th|zh-CN> --json`; when the user did not specify a language, pass the resolved default `zh-CN`. Source-video download and ffmpeg are conditional tools for deriving missing local start/result frames from retained evidence; ASR is not an execution prerequisite when the accepted breakdown already contains the narrative facts and time ranges.

## Mode-selection contract

Default to this mode for any production request that says only “复刻”, “replicate”, “参考原片做一条” or otherwise asks to reproduce a source without explicitly naming a narrower mode. Also select it when the user asks for the result to resemble the source, retain its essence, preserve signature shots or reactions, route start/result frames, or change only product-conflicting details. Select `structure_replication` or `hook_replication` only when the user explicitly requests that mode. `structure_replication` may retain only the abstract selling skeleton and must not be presented as high-fidelity replication. Product substitution does not by itself authorize a lower-fidelity mode.

Once this mode is selected, it cannot silently fall back. A failed compatibility or source-evidence gate stops the run and reports the exact incompatible source element. Continuing as `structure_replication` requires a new explicit user decision and a new run identity.

## Source-essence contract

Before writing the target script, create `plan/source-essence-map.json`. For every source narrative segment, record the signature hook or shot, entering composition/state, ordered visible actions, camera language, result state, relative pacing cue, dialogue function, emotional reaction, proof purpose, transition and CTA relationship. Mark each element as `must_preserve` or `adaptable` and cite the accepted breakdown evidence and source time range.

Then create `plan/source-target-correspondence.json`. Map every source narrative segment to ordered target Beat IDs and record exactly what is preserved, what product conflict requires substitution, and why the substitution retains the original commercial, emotional and visual function. Product substitution may change only facts, geometry or actions that conflict with the current product; it must not replace a compatible signature hook, shot, reaction, proof step, camera treatment, pacing relationship or visual style merely for convenience.

## Visual-style fidelity contract

Before prompt compilation, create `plan/source-visual-style-profile.json` from the accepted breakdown, routed start/result frames and any retained source-video evidence. Record the source's capture medium and platform aesthetic, aspect/framing behavior, camera height and subject distance, lens/perspective feel, composition discipline, lighting, white balance and palette, exposure/contrast/saturation, sharpness/surface texture/compression, depth of field, camera stability, motion blur and any deliberate image degradation. Cite evidence and separate stable global style from segment-specific variation.

The profile must include two concise execution-ready English fields: `style_fingerprint_en` and `anti_style_constraints_en`. Put those exact values into the Markdown creation workbook's replication metadata and the generated execution context; the compiler must pass both values verbatim into every target first-frame Segment. Preserve the source's actual treatment, including ordinary phone-camera imperfections when present. Do not replace it with generic labels such as “UGC”, “cinematic” or “premium”, and do not upgrade casual footage into polished studio advertising. Product identity, product facts and an explicitly selected replacement subject may override conflicting objects or actions, but they do not authorize a different visual style.

## Product compatibility gate

Fresh-read exactly one `资产状态=可用` breakdown and the selected active product. `资产状态=可用` proves the reference is reusable; it does not prove compatibility with this product.

Before any image generation, compare the source and target on product category and user, core interaction, proof chain, required scene, and source-specific functions or claims. Write `plan/replication-compatibility.json` with the decision, evidence and one assessment per narrative segment.

High-fidelity replication passes only when every segment can retain its narrative task, signature source element and proof order without inventing a target-product function or claim. Product facts may change a conflicting visible action, but not the segment's commercial or emotional purpose. If any signature hook, shot, reaction, core segment or proof step cannot be retained, stop this mode and report the incompatibility plus the possible alternatives `structure_replication`, `hook_replication` or `not_recommended`; do not silently continue under another mode.

## Production unit and rhythm authority

Keep source narrative segmentation separate from target production segmentation:

- A `source_narrative_segment` is reference evidence. It retains the source narrative task, order, relative pacing and exactly two local frames.
- A `target_production_segment` is the generation unit. It uses a direct 4/6/8/10-second duration selected from the ASR-timed target action and produces one 9:16 first-frame image for each of the two A/B script versions (with local retry attempts when needed). The first frame represents the Segment's entering state at local `t=0`; it does not depict the full Segment action. Human acceptance happens at the complete first-frame-version level, which contains all target production Segments in order.

Before image generation, write `plan/replication-rhythm-map.json`. Map every source narrative segment in order to one or more target production Segments, then render the locked target-script Beats for each target 4/6/8/10-second window. Several source narrative segments may enter one target production Segment; an important target-product proof action may span adjacent target production Segments.

Authority is fixed:

1. The source reference owns commercial narrative order, proof order and relative pacing cues.
2. The locked target script owns exact target timestamps and Beat duration.
3. Current product facts own the required action, visible state change and minimum legible proof time.
4. Active configuration owns ASR-timed 4/6/8/10-second production segmentation and one 9:16 first frame per generated target production Segment/version pair.

Do not copy source timestamps into the target plan or force one source narrative segment to equal one target production Segment. The local request count is the number of Segment/version pairs plus explicit retry attempts; it is not determined by source narrative segments or evidence frames. Assemble complete A/B first-frame versions before writeback; do not expose loose retry artifacts as the human approval unit.

## Subject strategy gate

Resolve and record one strategy before generation:

| Strategy | Use when | Generation inputs |
| --- | --- | --- |
| `preserve_source_subject` | Same-category full replication and the original person or animal can remain | source keyframes + current product anchor |
| `replace_subject` | The user explicitly selects a breed, person or recurring identity | source keyframes + current product anchor + new subject anchor |
| `structure_only` | Cross-species, cross-category or interaction-incompatible references | source frames are planning evidence only; use the script + current product anchor + target subject |

Compatible full replication normally uses `preserve_source_subject`: replace only the source product and preserve the source person or animal, scene, camera and action state. Do not invent a new recurring subject. `replace_subject` requires explicit user selection and replaces product and subject in one step. `structure_only` exits this workflow and continues as `structure_replication`; do not send its source frames to generation.

## Accepted-source boundary

An `资产状态=可用` breakdown is an accepted source, not a draft to migrate during production. Reading it for replication must not change its attachments, `逐段复刻模板`, quality notes or `资产状态`.

Create the two-frame evidence pool inside the current run package. Reuse accepted start/result attachments when they exist. For an accepted legacy record with fewer frames, derive exactly two frames per source narrative segment locally from its retained source video, evidence frames and source time ranges. This local derivation does not invalidate the source approval and does not require another human review. Only write the derived frames back to `短视频拆解库` when the user explicitly asks to correct or upgrade that shared record; that separate library mutation follows the breakdown review workflow.

## Two-frame narrative evidence and target-first-frame adaptation

1. Validate that the selected record is `资产状态=可用` and has the factual narrative fields and source time ranges needed for adaptation. Create a local evidence manifest in which every source narrative segment links to exactly two distinct files: `开始参考帧` and `结果参考帧`. Missing, duplicated, out-of-range or unstable local frames stop the run; absence of two attachments on an accepted legacy record alone does not.
2. For each source narrative segment, record its narrative task, start/result frames, preserved mechanism, relative pacing cue, required target-product substitution and prohibited source-product carryover. These pairs form the evidence pool; they do not each trigger generation.
3. Build the rhythm map and target 4/6/8/10-second production Segments from the locked target script. For each target production Segment, record its direct duration, contiguous target time range, mapped source narrative IDs and the locked target Beat timeline. Select exactly two routed source boundary frames from the evidence pool: the entering frame of the first mapped source narrative and the result frame of the last mapped source narrative. Intermediate evidence pairs remain planning evidence represented by the target Beats; do not send all retained frames by default.
4. Generate two self-contained first-frame packages for each target production Segment, one for script version A and one for B. The Agent writes each first frame's static moment, camera, composition, performance, continuity and variant difference from the current workbook segment and replication evidence. The generated first frame represents the target Segment's entering composition/state; in high-fidelity replication, the routed start frame owns source entering composition/state and the routed result frame remains evidence for the target workbook's payoff/handoff. The source visual-style profile owns the capture treatment across all first frames and all Segments. Under `preserve_source_subject`, the frames also preserve the original person or animal and no subject anchor is added. Under `replace_subject`, the selected subject anchor overrides source-subject identity. The current product anchor always overrides source-product identity. Keep generation artifacts in the run package; do not create a candidate or review table.
5. Validate both complete A/B packages for target duration, Segment order, source-narrative coverage, target Beat coverage, correct start/result states, signature hook/shot/reaction coverage, camera-language and visual-style fidelity, relative pacing, dialogue-function order, hook/payoff/proof/CTA order, product actions and cross-Segment continuity. A and B must share the same source-essence and visual-style contracts but declare a non-empty `variant_delta`; identical scripts and identical adaptation decisions are not two versions. Write each ordered package directly to its corresponding script-table record with `脚本版本=A/B` and `首帧状态=待审核`. Machine validation is a visual preflight only; human approval is performed on either or both complete script records by setting each approved version to `首帧状态=已通过`, not by checking one candidate per Segment.

## Source-comparison similarity gate

Before either first-frame version can be marked ready for human review, create `plan/source-similarity-review.json` and compare the source evidence with the complete target package side by side. Review the signature hook, entering and result compositions, shot/action order, camera language, relative pacing, dialogue-function order, emotional reactions, proof chain and CTA position. Also compare the visual-style profile dimension by dimension: framing and subject distance, perspective, lighting and palette, exposure/contrast/saturation, sharpness and texture, compression/degradation, depth of field, camera stability and motion character. Each source element must be classified as `preserved`, `adapted_with_product_reason`, or `missing` with evidence.

Any `missing` element marked `must_preserve`, an undocumented substitution, an unrouted start/result frame, a missing or genericized visual-style dimension, or a target package whose similarity comes only from the generic “hook—interaction—result” skeleton fails this mode. Product correctness and prompt-contract validation do not substitute for source similarity. Only packages with no unresolved source-fidelity failure may proceed to human review.

Do not create MF/RF mappings, fixed six-frame batches, replacement contact sheets, balanced dynamic masters, video, subtitles or voiceover in this workflow. If the two local frames do not provide enough evidence, reselect them from retained segment evidence. Return to the breakdown workflow only when the accepted narrative facts or time ranges themselves are wrong or insufficient; do not restart chronological frame replacement.

All target first-frame images in this workflow are GPT Image 2.5 requests with `executor=gpt_image_2_5` and `model=gpt-image-2.5`. Do not use Flow2API for replacement, cleanup, blank-scene preparation or fallback. A subject strategy is resolved through the routed generation inputs described above, not through an extra provider or an intermediate image-cleaning pass.
