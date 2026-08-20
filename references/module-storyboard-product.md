# Module 2 — 分镜与产品一致性

Use this module to turn an approved strategy into clean final-generation storyboard boards, review replication evidence, and archive a board package to `内容库` as `待审核`. This module owns visual product identity, structure-sensitive interaction, subject continuity, board geometry, asset routing, and storyboard acceptance. It does not submit Omni final-video Jobs.

## Read for this module

Read the public gates in the parent `SKILL.md`, then read only the references required by the selected mode:

- [configuration.md](configuration.md) for grid, panel ratio, target duration, raw-segment duration, and model limits.
- [content-strategy-and-assets.md](content-strategy-and-assets.md) for product and subject asset routing.
- [delivery-contract.md](delivery-contract.md) for board attachment and delivery requirements.
- [storyboard-spec.md](storyboard-spec.md) for storyboard fields and timing.
- [interaction-substitution-protocol.md](interaction-substitution-protocol.md) when source interaction conflicts with product facts.
- For `全量复刻`, also read [stage-1-evidence.md](stage-1-evidence.md), [stage-2-light-adaptation.md](stage-2-light-adaptation.md), [frame-batch-replacement.md](frame-batch-replacement.md), [stage-3-full-package.md](stage-3-full-package.md), and [dynamic-master-review.md](dynamic-master-review.md).

Do not use the Omni video prompt contract as a storyboard-image contract. The storyboard Job has no storyboard-board input yet; its input roles must be generated from its actual `product_asset_plan` and image array.

## Board preparation and input roles

1. Fresh-read product facts, product review requirements, approved product attachments, selected subject record, task snapshot, and configuration snapshot.
2. Build one `product_asset_plan` per board. At minimum route the default product anchor; add the subject anchor for recurring subjects; add the highest-risk product detail asset for holes, lattice, loading, dispensing, drainage, connections, or openings; add the scene asset when proof depends on real context, scale, or interaction.
3. Generate a per-Job role map from the actual image array, for example `product_anchor`, `subject_anchor`, `product_detail`, and `product_scene`. Record position, role, filename, Feishu field, file token, local hash, and board mapping. Never assume that `Input 3` is a subject when no subject was routed.
4. Prepare inputs through `prepare_flow_inputs.py` or the current approved transport helper. Validate decoded image type, MIME, dimensions, hash, and count before submission. Deduplicate by stable hash only after confirming that the duplicate assets are truly interchangeable.
5. Use Banana Pro with the exact configured image model. Submit one complete board per raw segment with the configured grid, reading order, panel times, zero gutter, natural phone-video texture, and no readable text/UI/watermark. Do not locally compose or split a returned board.

## Product and subject hard gates

Treat product structure and interaction as facts, not selling language. Every sensitive panel must declare and review two separate facts: `loading_path` for putting treats into the product and `dispensing_path` for treats leaving the product. They may be the same or different, but neither may be inferred from the other. When the product record confirms that both paths use the single bottom circular hole, prompts and reviews must state both paths explicitly; the side lattice must not be treated as either an inlet or an outlet unless the product record explicitly says so. A wrong hole, wrong direction, invented cap/lid, detached crown, side-loading action, side-dispensing action, altered lattice, or substituted product is a hard FAIL.

Do not use a contradictory storyboard as an input to Omni and hope prose will correct it. If the board product pixels disagree with the approved anchor/detail asset, regenerate or stop. Product visual facts must be derived from the current routed asset and product record, not from a product name, prior output, or memory.

For a recurring subject, pass the same subject anchor and stable identity description to every applicable board Job. Review breed/type, coat or hair colors, markings, face, body size, ears/hair, accessories, and subject role independently from product review. “Same dog” is not an identity lock.

Review every panel for product identity, product scale, interaction path, subject identity, timing order, scene continuity, text/UI contamination, and mobile-video texture. A `WARN｜人工复核` remains WARN and blocks final-video use until the documented human-review condition is resolved.

## Mode-specific evidence

- `原创`: use no reference video. Produce one complete board per configured raw segment from the selected task and current product facts.
- `钩子复刻`: document the exact hook window and use no source content after `0.0–3.0s`; the continuation is original.
- `结构复刻`: keep only the phase skeleton in `plan/structure-plan.json`; never pass reference frames, screenshots, audio, or source wording to the generation Job.
- `全量复刻`: create chronological one-second evidence, fixed source batches, replacement sheets, reviews, balanced masters, and final-generation boards. Use only accepted artifacts from the current run. A failed batch is regenerated once; a second failure stops the package.

## Archive handoff

Run the current configuration-profile board validator on every final board and record the result with filename and dimensions in `quality-report.md`. Do not create or update `内容库` while any board is missing, pending, failed, unvalidated, or visually rejected.

After all boards pass, write the exact script, creative fields, exact board prompt, `Agent 自检`, product link, and all board attachments in one post-validation archive step. Fresh-read the record and verify the expected attachment count, filenames, and tokens before setting `审核状态=待审核`. Stop there until Module 3 receives explicit named authorization.
