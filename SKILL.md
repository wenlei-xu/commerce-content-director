---
name: commerce-content-director
description: Route Feishu-driven ecommerce UGC work for Douyin, Xiaohongshu, and Pinduoduo when expanding topics, selecting a content task, producing storyboard evidence, generating an explicitly named approved final video, or running the documented lifecycle sweep.
---

# Commerce content director

This skill is a router with public safety gates. Load one workflow for the requested action, then only the domain contracts and invariants that workflow names. Legacy references are archival material and are never part of a normal run.

## Workflow routing

Choose one primary workflow for the current action:

- **Topic expansion and task convergence**: read [topic-expansion.md](references/workflows/topic-expansion.md).
- **Original planning handoff**: read [original-planning.md](references/workflows/original-planning.md).
- **Storyboard generation and product fidelity**: read [storyboard-generation.md](references/workflows/storyboard-generation.md).
- **Full replication evidence**: read [full-replication.md](references/workflows/full-replication.md) in addition to the storyboard workflow when the selected mode is full replication.
- **Final video generation and acceptance**: read [final-video.md](references/workflows/final-video.md).
- **Content-library lifecycle**: read [lifecycle.md](references/workflows/lifecycle.md).

For a normal original or replication run, the handoff order is strategy → storyboard → (after human approval and explicit named authorization) final video. Lifecycle is independent. Topic expansion is not a generation mode.

## Shared invariants

Read these only when the selected workflow names them:

- [authority.md](references/invariants/authority.md): source precedence and schema resolution.
- [execution-accounting.md](references/invariants/execution-accounting.md): attempts, accepted films, and count semantics.
- [mutation-and-recovery.md](references/invariants/mutation-and-recovery.md): staging, idempotency, and resumable failure handling.

## Public gates

Before reading or mutating Feishu creative records, preparing the required local package, or submitting a Job:

1. Call Flow2API through the registered Sidecar MCP with `flow_get_service_health(include_dependencies=true)` and `flow_list_models(include_unavailable=true)`.
2. Read `config/base-schema.json`, then make a read-only Feishu metadata call for the logical tables used by the selected workflow.
3. Record only scrubbed status and error summaries. Never print credentials, access tokens, temporary media URLs, or raw Base64.

If both Flow2API and Feishu MCP are unavailable, stop. If only one is unavailable, block only the workflow actions that require that service and keep diagnostics separate from creative artifacts.

If authoritative records or assets conflict, stop and report the conflict. Do not silently normalize, translate, substitute a product, or reuse a stale local interpretation.

Use the registered Flow2API MCP and the model capability selected from the current catalog. Never call private model endpoints directly. Image payloads must contain validated raw image bytes in the current MCP schema; never place tokens, URLs, audit objects, or Base64 in prompts or Feishu fields.

Create a minimal local run package before generation. At minimum retain `package.json`, `generation-jobs.json`, `quality-report.md`, exact submitted prompts, asset role/hash mappings, and temporary outputs. The package is evidence, not a replacement for Feishu source records.

Final-video generation requires a freshly read approved content version and explicit naming of its exact `content_id` or Feishu record. Preserve failed and accepted artifacts separately. Do not use browser/UI automation or LibTV for final-video generation.

## Stop condition

Stop at the first missing required evidence named by the selected workflow: task, product, subject, configuration, asset, upload receipt, validation, review, approval, Job result, attachment read, or final-film verification. Report the concrete missing evidence and the resumable run identifier when one exists.
