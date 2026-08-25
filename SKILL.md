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
- **Generate, revise, validate, or lock a script**: read [script-production.md](references/workflows/script-production.md).
- **Generate or review a storyboard**: read [storyboard-generation.md](references/workflows/storyboard-generation.md).
- **Generate and accept a final video**: read [final-video.md](references/workflows/final-video.md).
- **Archive the creative chain**: read [lifecycle.md](references/workflows/lifecycle.md).

## Shared invariants

Read only the invariants named by the selected workflow:

- [authority.md](references/invariants/authority.md) — schema and record authority.
- [script-field-contract.md](references/invariants/script-field-contract.md) — object ownership and single source of truth.
- [script-validation.md](references/invariants/script-validation.md) — blocking quality checks.
- [product-execution-contract.md](references/invariants/product-execution-contract.md) — product action correctness.
- [language-policy.md](references/invariants/language-policy.md) — Thai spoken language and audio behavior.
- [execution-accounting.md](references/invariants/execution-accounting.md) — accepted films and execution limits.
- [mutation-and-recovery.md](references/invariants/mutation-and-recovery.md) — staged writes and resumable failures.

## Gates

1. Run python scripts/preflight.py --workflow <workflow> --json.
2. Read config/base-schema.json and fresh-read only the tables needed by the workflow.
3. A script workflow requires one locked creative direction. It must build and validate structured_script locally before creating or revising a Feishu script record. Chinese spoken scripts also follow a **soft lifestyle-delivery guide**, not a blocking gate: aim for 6–14 Chinese characters per line, keep 18 characters as a suggested maximum, let each line express one action or reaction, avoid written connectors such as “直到、而是、之后、从而”, add a natural reaction or现场回应 roughly every 2–3 seconds when the visual beat allows it, and let the dialogue follow what is visibly happening instead of fully explaining the product mechanism. These are review signals and rewrite prompts; exceeding a suggestion does not fail validation by itself.
4. Only validation_status=passed scripts may become locked. Only locked scripts may enter storyboard production. Only storyboard-passed scripts may enter final-video production.
5. Keep structured_script as the only machine source of truth. Render every human-readable script field from it after validation; do not independently edit duplicate text fields.
6. Product hard facts, product assets and selected subjects are execution authority. Do not use publication-risk or claim-verification gates in this first version.
7. For every remote mutation, retain a run ID and fresh-read the changed record. On failure, resume the same run; never create a duplicate direction, script or film.

## Stop condition

Stop the selected workflow at the first missing required input, invalid script report, failed storyboard fidelity review, missing approval, exhausted execution limit, failed remote write, or failed fresh-read verification. Report the concrete missing evidence and resumable run ID.
