---
name: commerce-content-director
description: Route Feishu-driven ecommerce UGC workflows for Douyin, Xiaohongshu, and Pinduoduo across content strategy, storyboard/product fidelity, final-video generation and acceptance, and lifecycle management. Use when expanding content topics, creating original or replication storyboard packages, generating an explicitly named approved final video, or running the documented archive sweep. Never use LibTV or browser/UI automation for final-video generation.
---

# Commerce content director

This skill is a router and a set of public safety gates. Read only the execution module that matches the current request, then read the references that module names. Do not load all modules for an ordinary run.

## Module routing

Use exactly one primary module for each action:

- **内容策略与任务收敛**: expand a `内容母题`, rank or select `创意候选`, select a `内容策划任务`, choose original/hook/structure/full replication, or perform task rotation. Read [module-content-strategy.md](references/module-content-strategy.md).
- **分镜与产品一致性**: create, review, regenerate, validate, or archive final-generation storyboard boards and full-replication evidence. Read [module-storyboard-product.md](references/module-storyboard-product.md).
- **最终视频生成与验收**: generate Omni raw segments for an explicitly named approved content version, assemble them, generate and burn the default subtitle track, and create or verify the complete `最终成片`. Read [module-video-generation.md](references/module-video-generation.md).
- **内容库生命周期管理**: run the read-only or explicitly authorized soft-archive sweep. Read [module-lifecycle.md](references/module-lifecycle.md).

For a normal original or replication run, use modules in this order: strategy → storyboard → (after human approval and explicit named authorization) video. Lifecycle is an independent administrative operation. `内容母题扩散` is not a generation mode.

## Public gates

These gates apply before any module-specific work.

### Service and schema preflight

Before reading creative records, writing prompts, creating a local package, or submitting a Job:

1. Call Flow2API through the registered Sidecar MCP with `flow_get_service_health(include_dependencies=true)` and `flow_list_models(include_unavailable=true)`.
2. Read `config/base-schema.json`, then make a read-only Feishu metadata call against the logical table mapping used by the current module.
3. Record only scrubbed status and error summaries. Never print credentials, access tokens, temporary media URLs, or raw Base64.

If both Flow2API and Feishu MCP are unavailable, stop immediately. Do not invent a text plan, create records, create a package, upload media, or submit Jobs. If only one is unavailable, block only the actions that require that service and keep diagnostics separate from a creative package.

### Authority order

- `config/base-schema.json` is the only source for Base/table/field/status mappings.
- The current `内容系统配置` record controls target duration, raw-segment duration, storyboard grid, scoring weights, limits, and model-input limits.
- The selected and fresh-read `内容策划任务` controls creative direction and replication boundaries.
- The directly resolved, available `产品` record is the only source for product facts, hard constraints, approved claims, and product assets.
- A selected `主体资产库` record and its anchor/identity description control recurring subject identity.
- A generated image or previous Job never becomes a product fact merely because it looks plausible.

If two authoritative records or assets conflict, stop and report the conflict. Do not silently normalize, translate, substitute a product, or reuse a stale local interpretation.

### Artifact and mutation boundary

Create a minimal local run package before generation. At minimum retain `package.json`, `generation-jobs.json`, `quality-report.md`, the exact submitted prompts, asset role/hash mappings, and temporary generation outputs. The package is evidence, not a replacement for Feishu source records.

Do not write or upload a partial `内容库` record. Every required storyboard must exist, match the active configuration, pass the relevant validator, pass product/subject/text review, and be confirmed by a fresh Feishu attachment read before setting `审核状态=待审核`.

`审核状态=通过` is eligibility only. Final-video generation additionally requires the user to explicitly name the exact `content_id` or Feishu record. A generic “generate the approved ones” may be resolved only when the current task/product scope produces a deterministic, freshly read set; record that resolved set before submission.

`内容库.已执行次数` means completed, accepted final films. It is never incremented for a submission, segment Job, retry, failure, timeout, partial clip, or credit usage. Increment it exactly once only after a complete target-duration video has passed technical and visual review, has been attached to a new `最终成片` record, and that attachment has been freshly read as present and playable.

### Flow2API input boundary

Use the registered Flow2API MCP only. Use the exact configured model keys and current model catalog limits; never call Omni private endpoints directly.

The MCP image payload must contain actual image bytes in the schema accepted by the current MCP, not a Feishu token, filename, URL, or audit object. For the current schema:

```json
{
  "mime_type": "image/png",
  "data_base64": "<raw Base64 image bytes>"
}
```

For ordinary `.png/.jpg/.jpeg/.webp` files, read binary bytes and Base64-encode once. For `.b64` sidecars, read the Base64 text directly after trimming surrounding whitespace; never encode it again. Validate MIME, strict Base64 decoding, image magic/decode, byte/hash mapping, input count, and role mapping before submission. Do not put raw Base64 in prompts, reports, or Feishu fields.

### Job and retry boundary

Every Job is asynchronous. `queued`, `submitting`, and `active` are non-terminal. Use the same idempotency key only to recover an uncertain submission of the unchanged payload. A deliberate visual regeneration gets a new attempt key and retains the failed artifact and reason. Do not silently switch models, alter the product, skip a required asset, or resubmit a known terminal failure.

When the upstream bridge reports media upload or project-scoping failure, classify it as an input-attachment/transport failure, not as proof that the model generated a wrong product. Retain the input hashes, expected roles, upstream error, and Job state so the failure can be diagnosed.

### Scope boundary

Do not use browser/UI automation or LibTV for final-video generation. Do not modify product facts, subject records, task direction, lifecycle policy, or Base schema unless the user explicitly requests that maintenance action. Do not delete records or overwrite prior media; preserve failed and accepted artifacts separately.

## Stop condition

If a required task, product, subject, configuration, asset, upload receipt, prompt validation, storyboard review, approval, Job result, attachment read, or final-film verification is missing, stop at that boundary and report the concrete missing evidence. A plausible-looking output is not a substitute for a passed gate.
