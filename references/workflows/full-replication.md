# Workflow: full replication storyboard

Read [storyboard-generation.md](storyboard-generation.md), [storyboard-candidate-contract.md](../storyboard-candidate-contract.md), [flow2api-image-execution.md](../flow2api-image-execution.md), [authority.md](../invariants/authority.md), [knowledge-library-contract.md](../invariants/knowledge-library-contract.md), [product-contract.md](../domain/product-contract.md), [product-execution-contract.md](../invariants/product-execution-contract.md), [reference-asset-contract.md](../reference-asset-contract.md), [image-prompt-contract.md](../image-prompt-contract.md), and [mutation-and-recovery.md](../invariants/mutation-and-recovery.md).

Use this workflow only for the `full_replication` task mode. Full replication preserves the complete commercial narrative chain: hook, segment order, information release, proof order, payoff, emotion and CTA position. It does not perform chronological per-second or per-frame product replacement.

Run `python scripts/preflight.py --workflow storyboard_generation --mode full_replication --target-spoken-language <th|zh-CN> --json`; when the user did not specify a language, pass the resolved default `zh-CN`. Source-video download and ffmpeg are conditional tools for deriving missing local start/result frames from retained evidence; ASR is not an execution prerequisite when the accepted breakdown already contains the narrative facts and time ranges.

## Product compatibility gate

Fresh-read exactly one `资产状态=可用` breakdown and the selected active product. `资产状态=可用` proves the reference is reusable; it does not prove compatibility with this product.

Before any image generation, compare the source and target on product category and user, core interaction, proof chain, required scene, and source-specific functions or claims. Write `plan/replication-compatibility.json` with the decision, evidence and one assessment per narrative segment.

Full replication passes only when every segment can retain its narrative task and the source proof order without inventing a target-product function or claim. Product facts may change the visible action, but not the segment's commercial purpose. If any core segment or proof step must be replaced, stop this mode and report `structure_replication`, `hook_replication` or `not_recommended`; do not silently continue as full replication.

## Production unit and rhythm authority

Keep source narrative segmentation separate from target production segmentation:

- A `source_narrative_segment` is reference evidence. It retains the source narrative task, order, relative pacing and exactly two local frames.
- A `target_production_segment` is the generation unit. It is always the configured 10 seconds and produces one or more complete 2×2 storyboard-board candidates. Human acceptance happens at the complete storyboard-version level, which contains all target production Segments in order.

Before image generation, write `plan/replication-rhythm-map.json`. Map every source narrative segment in order to one or more target production Segments, then render the locked target-script Beats for each target 10-second window. Several source narrative segments may enter one target production Segment; an important target-product proof action may span adjacent target production Segments.

Authority is fixed:

1. The source reference owns commercial narrative order, proof order and relative pacing cues.
2. The locked target script owns exact target timestamps and Beat duration.
3. Current product facts own the required action, visible state change and minimum legible proof time.
4. Active configuration owns 10-second production segmentation and one complete 2×2 board per generated target production Segment candidate.

Do not copy source timestamps into the target plan, force one source narrative segment to equal one candidate Job, or divide the four panels into equal durations merely because the board has four cells. Candidate Job count may be larger than the number of target production Segments and is not determined by source narrative segments or evidence frames. Assemble complete A/B storyboard versions after candidate generation; do not expose loose candidates as the human approval unit.

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

## Two-frame narrative evidence and target-board adaptation

1. Validate that the selected record is `资产状态=可用` and has the factual narrative fields and source time ranges needed for adaptation. Create a local evidence manifest in which every source narrative segment links to exactly two distinct files: `开始参考帧` and `结果参考帧`. Missing, duplicated, out-of-range or unstable local frames stop the run; absence of two attachments on an accepted legacy record alone does not.
2. For each source narrative segment, record its narrative task, start/result frames, preserved mechanism, relative pacing cue, required target-product substitution and prohibited source-product carryover. These pairs form the evidence pool; they do not each trigger generation.
3. Build the rhythm map and target 10-second production Segments from the locked target script. For each target production Segment, record its contiguous target time range, mapped source narrative IDs and four target Beats. Select exactly two routed source boundary frames from the evidence pool: the entering frame of the first mapped source narrative and the result frame of the last mapped source narrative. Intermediate evidence pairs remain planning evidence represented by the target Beats; do not send all retained frames by default.
4. Generate the configured complete 2×2 candidates for each target production Segment; the default is two attempts per Segment. The routed start frame owns entering composition/state and the routed result frame owns visible payoff/handoff. Under `preserve_source_subject`, they also preserve the original person or animal and no subject anchor is added. Under `replace_subject`, the selected subject anchor overrides source-subject identity. The current product anchor always overrides source-product identity. Publish each passing complete board to the backend Feishu `分镜候选`; never split or recombine its panels.
5. Assemble one or more complete storyboard versions from the backend candidates, then validate target duration, Segment order, source-narrative coverage, target Beat coverage, correct start/result states, hook/payoff/proof/CTA order, product actions and cross-Segment continuity. Machine validation is a visual preflight only; human approval is performed on the complete version package, not one candidate per Segment.

Do not create MF/RF mappings, fixed six-frame batches, replacement contact sheets, balanced dynamic masters, video, subtitles or voiceover in this workflow. If the two local frames do not provide enough evidence, reselect them from retained segment evidence. Return to the breakdown workflow only when the accepted narrative facts or time ranges themselves are wrong or insufficient; do not restart chronological frame replacement.

All target storyboard boards in this workflow are Flow2API MCP image Jobs. Do not use GPT Image for replacement, cleanup, blank-scene preparation or fallback. A subject strategy is resolved through the routed generation inputs described above, not through an extra provider or an intermediate image-cleaning pass.
