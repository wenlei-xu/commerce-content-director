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
- **Generate or review a storyboard**: read [storyboard-generation.md](references/workflows/storyboard-generation.md).
- **Assess and produce a full-replication storyboard**: read [full-replication.md](references/workflows/full-replication.md). Full replication starts with product compatibility and uses exactly two narrative reference frames per segment; it does not use chronological frame replacement.
- **Generate and accept a final video**: read [final-video.md](references/workflows/final-video.md).
- **Archive the creative chain**: read [lifecycle.md](references/workflows/lifecycle.md).

## Shared invariants

Read only the invariants named by the selected workflow:

- [authority.md](references/invariants/authority.md) — schema and record authority.
- [script-field-contract.md](references/invariants/script-field-contract.md) — object ownership and single source of truth.
- [script-validation.md](references/invariants/script-validation.md) — blocking quality checks.
- [product-execution-contract.md](references/invariants/product-execution-contract.md) — product action correctness.
- [language-policy.md](references/invariants/language-policy.md) — Thai spoken language and audio behavior.
- [knowledge-library-contract.md](references/invariants/knowledge-library-contract.md) — the two learning-library objects and their review boundaries.
- [model-visual-text-recognition.md](references/invariants/model-visual-text-recognition.md) — model-vision-only screen-text evidence and the legacy OCR field contract.
- [execution-accounting.md](references/invariants/execution-accounting.md) — accepted films and execution limits.
- [mutation-and-recovery.md](references/invariants/mutation-and-recovery.md) — staged writes and resumable failures.

## Gates

1. Run python scripts/preflight.py --workflow <workflow> --json.
2. Read config/base-schema.json and fresh-read only the tables needed by the workflow.
3. A script workflow requires one locked creative direction. It must build and validate structured_script locally before creating or revising a Feishu script record. It may read only `资产状态=可用` 短视频拆解 and `审核状态=可用` 句式模板；待审核候选不得直接进入脚本。
   A full-replication workflow must additionally pass the source-product compatibility gate before image generation. `资产状态=可用` proves breakdown quality, not compatibility with the selected product.
4. Only validation_status=passed scripts may become locked. Only locked scripts may enter storyboard production. Only storyboard-passed scripts may enter final-video production.
5. Keep structured_script as the only machine source of truth. Render every human-readable script field from it after validation; do not independently edit duplicate text fields.
6. Product hard facts, product assets and selected subjects are execution authority. Do not use publication-risk or claim-verification gates in this first version.
7. For every remote mutation, retain a run ID and fresh-read the changed record. On failure, resume the same run; never create a duplicate direction, script or film.

## Stop condition

Stop the selected workflow at the first missing required input, invalid script report, failed storyboard fidelity review, missing approval, exhausted execution limit, failed remote write, or failed fresh-read verification. Report the concrete missing evidence and resumable run ID.
