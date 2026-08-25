---
name: commerce-content-director
description: Run Feishu-driven ecommerce short-video production from creative request and direction through a validated executable script, storyboard, final video, and lifecycle management.
---

# Commerce content director

This Skill runs the production chain:

~~~text
创作需求 → 创意方向 → 脚本 → 分镜 / 视频提示词 → 最终成片
~~~

A script is the only executable content object. It owns the strategy snapshot, Beat timeline, visual/audio/screen-text tracks, dialogue, product actions, continuity, storyboard state, and final-film relationship.

## Workflow routing

Choose one workflow for the requested action:

- **Expand or lock creative directions**: read [creative-direction.md](references/workflows/creative-direction.md).
- **Analyze, distill, or choose an external short-video reference**: read [short-video-breakdown.md](references/workflows/short-video-breakdown.md).
- **Learn, review, or use reusable language patterns**: read [sentence-pattern-learning.md](references/workflows/sentence-pattern-learning.md).
- **Generate, revise, validate, or lock a script**: read [script-production.md](references/workflows/script-production.md).
- **Generate, select, or review a storyboard**: read [storyboard-generation.md](references/workflows/storyboard-generation.md), [storyboard-candidate-contract.md](references/storyboard-candidate-contract.md), and [flow2api-image-execution.md](references/flow2api-image-execution.md). Storyboard images use the registered Flow2API MCP exclusively; never call GPT Image or silently change providers.
- **Assess and produce a full-replication storyboard**: read [full-replication.md](references/workflows/full-replication.md). Full replication starts with product compatibility, resolves one explicit subject strategy, and retains two local evidence frames per source narrative segment. It then follows the original-production geometry: one 2×2 board per 10-second target production Segment. Source order and relative pacing remain evidence; the locked target script owns exact timing.
- **Generate and accept a final video**: read [final-video.md](references/workflows/final-video.md).
- **Archive the creative chain**: read [lifecycle.md](references/workflows/lifecycle.md).

## Shared invariants

Read only the invariants named by the selected workflow:

- [authority.md](references/invariants/authority.md) — schema and record authority.
- [script-field-contract.md](references/invariants/script-field-contract.md) — object ownership and single source of truth.
- [script-validation.md](references/invariants/script-validation.md) — blocking quality checks.
- [product-execution-contract.md](references/invariants/product-execution-contract.md) — product action correctness.
- [language-policy.md](references/invariants/language-policy.md) — Thai/Chinese spoken-language locking and audio behavior.
- [knowledge-library-contract.md](references/invariants/knowledge-library-contract.md) — the two learning-library objects and their review boundaries.
- [model-visual-text-recognition.md](references/invariants/model-visual-text-recognition.md) — model-vision-only screen-text evidence and the legacy OCR field contract.
- [execution-accounting.md](references/invariants/execution-accounting.md) — accepted films and execution limits.
- [mutation-and-recovery.md](references/invariants/mutation-and-recovery.md) — staged writes and resumable failures.

## Gates

1. At production-task start, resolve `target_spoken_language` to `th` or `zh-CN`; use `zh-CN` when the user does not specify it. Persist `plan/language-lock.json` and keep it unchanged for the run and script revision. Every generation control prompt uses English.
2. Run `python scripts/preflight.py --workflow <workflow> [--target-spoken-language <th|zh-CN>] --json`. Omission resolves to the schema default `zh-CN`; persist the resolved value before continuing.
3. Read config/base-schema.json and fresh-read only the tables needed by the workflow.
4. An external video must pass the local source-validity gate before full frame extraction, ASR, breakdown creation, reference-frame upload, or sentence-pattern learning. Invalid or unresolved media stops at preflight evidence and must not enter either learning library.
5. A script workflow requires one locked creative direction. It must build and validate structured_script locally before creating or revising a Feishu script record. It may read only `资产状态=可用` 短视频拆解 and `审核状态=可用` 句式模板；待审核候选不得直接进入脚本。
   Every spoken script must also pass the dialogue-quality gate: it cannot be only an instruction-manual restatement of visible operations, and must explicitly identify line evidence for a viewer pain point, user benefit, visible proof, and a natural CTA.
   A full-replication workflow must additionally pass the source-product compatibility gate before image generation. `资产状态=可用` proves breakdown quality, not compatibility with the selected product.
   Consuming an already-accepted breakdown never authorizes changing its attachments, template or `资产状态`. Two-frame adaptation assets belong to the current local replication package unless the user explicitly requests a shared-library correction.
6. Only validation_status=passed scripts may become locked. Only locked scripts may enter storyboard production. Only storyboard-passed scripts may enter final-video production.
7. Keep structured_script as the only machine source of truth. Render every human-readable script field from it after validation; do not independently edit duplicate text fields.
8. Product hard facts, product assets and selected subjects are execution authority. Do not use publication-risk or claim-verification gates in this first version.
9. For every remote mutation, retain a run ID and fresh-read the changed record. On failure, resume the same run; never create a duplicate direction, script or film.
10. Every storyboard-image plan must declare `executor=flow2api_mcp` and the exact available image-model ID selected from the fresh Flow2API catalog and active configuration snapshot. Submit, wait for and retrieve the image only through the registered Flow2API MCP. If that path is unavailable or fails validation, stop; GPT Image, private HTTP and provider fallback are forbidden.
11. A storyboard candidate is not complete while it exists only as a local file. Upload every validated complete 2×2 candidate board to one linked record in Feishu `分镜候选`; the human selects it with `是否采用`. Finalization requires exactly one selected complete board per target production Segment, writes only those ordered boards to the exact script record's `最终分镜图`, then fresh-reads both candidates and script to verify selection, attachment identity/count and status. A failed upload, association, write, count, or fresh-read blocks completion.
12. Original and replication storyboards share one acceptance unit: every configured 10-second target production Segment ultimately accepts one complete 2×2 board with four 9:16 panels. By default, submit two complete-board candidate image Jobs per Segment (`attempt=1` and `attempt=2`); an explicit user instruction may override this count. Transport retries reuse the same attempt. Candidate Job count is not accepted-board count. Reference-video narrative segmentation never determines either count. The locked target script owns exact Beat timing; do not crop panels, mix panels between candidates, copy source timestamps, or divide the four panels evenly by default.
13. Batch submission is mandatory when two or more independent Flow2API Jobs for the same script and production stage are ready. Compile the complete stage first, call `flow_submit_batch` once, persist the batch-to-Job mapping, and wait with `flow_wait_batch`. Use a single-Job submit tool only for one ready Job, one repair Job, or a recorded batch-interface failure. Capacity limits may split work into the fewest possible batches; they never authorize avoidable per-Job serial submission. Storyboard and final-video stages are separate batches because human storyboard selection is a dependency boundary.
14. Chinese `spoken` and `sparse_spoken` final videos use one mandatory post-production route: Omni generates visuals plus environmental sound only and no BGM or speech; Doubao TTS 2.0 generates the approved Chinese voiceover; the exact approved reference video supplies a separated BGM stem that must pass ASR with no residual speech; final assembly mixes environment, ducked BGM and aligned Doubao voiceover, then derives subtitles from that final voiceover timing. A continuous Chinese voiceover is synthesized as one complete take by default at `speech_rate=15`. If it is slightly too long, shorten only inter-sentence breath gaps; do not split it into line-by-line TTS or globally speed up the voice unless the user explicitly chooses that route.

## Stop condition

Stop the selected workflow at the first missing required input, invalid script report, failed storyboard fidelity review, missing approval, exhausted execution limit, failed remote write, or failed fresh-read verification. Report the concrete missing evidence and resumable run ID.
