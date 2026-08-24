# Workflow: full replication storyboard

Read [storyboard-generation.md](storyboard-generation.md), [authority.md](../invariants/authority.md), [knowledge-library-contract.md](../invariants/knowledge-library-contract.md), [product-contract.md](../domain/product-contract.md), [product-execution-contract.md](../invariants/product-execution-contract.md), [reference-asset-contract.md](../reference-asset-contract.md), [image-prompt-contract.md](../image-prompt-contract.md), and [mutation-and-recovery.md](../invariants/mutation-and-recovery.md).

Use this workflow only for the `full_replication` task mode. Full replication preserves the complete commercial narrative chain: hook, segment order, information release, proof order, payoff, emotion and CTA position. It does not perform chronological per-second or per-frame product replacement.

Run `python scripts/preflight.py --workflow storyboard_generation --mode full_replication --json`. This mode reads the two reviewed narrative reference frames already attached to each segment, so source-video download, ffmpeg and ASR are not execution prerequisites.

## Product compatibility gate

Fresh-read exactly one `资产状态=可用` breakdown and the selected active product. `资产状态=可用` proves the reference is reusable; it does not prove compatibility with this product.

Before any image generation, compare the source and target on product category and user, core interaction, proof chain, required scene, and source-specific functions or claims. Write `plan/replication-compatibility.json` with the decision, evidence and one assessment per narrative segment.

Full replication passes only when every segment can retain its narrative task and the source proof order without inventing a target-product function or claim. Product facts may change the visible action, but not the segment's commercial purpose. If any core segment or proof step must be replaced, stop this mode and report `structure_replication`, `hook_replication` or `not_recommended`; do not silently continue as full replication.

## Two-frame segment adaptation

1. Validate the selected breakdown locally. Every segment must link to exactly two distinct attachments: `开始参考帧` and `结果参考帧`. Missing, extra, duplicated or unattached frames stop the run.
2. For each segment, create one adaptation entry containing its time range, narrative task, start frame, result frame, preserved mechanism, target-product action, product start/result state and prohibited source-product carryover.
3. Use only those two source frames as composition/state references for the segment. The start frame owns the entering scene and composition; the result frame owns the visible payoff and handoff state. Current product and subject anchors remain identity authority.
4. Generate the segment's target storyboard frames or board. Keep segment order and approximate duration, but let the locked script and current product facts determine the action between the two states.
5. Assemble accepted segment boards in narrative order into the final storyboard. Validate exact segment coverage, correct start/result state, hook/payoff/proof/CTA order, product actions and cross-segment continuity.

Do not create MF/RF mappings, fixed six-frame batches, replacement contact sheets, balanced dynamic masters, video, subtitles or voiceover in this workflow. If the two stored frames do not provide enough evidence, return to the breakdown workflow to correct the segment; do not restart chronological frame replacement.
