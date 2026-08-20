# Module 1 — 内容策略与任务收敛

Use this module for `内容母题` expansion, candidate convergence, task selection, original planning, replication-boundary selection, and automatic task rotation. This module decides **what** to make and **which task** authorizes the work; it does not generate images, boards, videos, TTS, or `内容库` records.

## Read for this module

Read the public gates in the parent `SKILL.md`, then read:

- [configuration.md](configuration.md) for the unique active content-system configuration and snapshot.
- [content-strategy-and-assets.md](content-strategy-and-assets.md) for Base roles, product fields, candidate fields, and task fields.
- [ugc-original-planning.md](ugc-original-planning.md) for original-rule loading and planning details.
- [lifecycle-archive.md](lifecycle-archive.md) only when task rotation or archive implications need to be evaluated.

## Common selection workflow

1. Run the public service/schema preflight and fresh-read the unique active content-system configuration. Validate target duration against the configuration and current model capability; write `plan/content-system-config-snapshot.json`.
2. Resolve exactly one product directly from `产品` by the user’s product name or ID. Require `状态=可用`, a non-empty `默认产品锚点`, consistent product hard facts, generation notes, and any product-specific review requirements. A task relation is not a product lookup substitute.
3. If the content uses a recurring person, animal, or other identifiable subject, resolve one usable `主体资产库` record with anchor and stable identity description. Prefer a valid task binding; otherwise select deterministically by task role/type, proof scene, product context, then `record_id`. Record the selection and identity hash locally.
4. Select and fresh-read exactly one usable `内容策划任务` for a generation package. Save its ID, name, mode, selection basis, snapshot/hash, platform/account, lifecycle fields, and target duration locally. Blank, legacy, or unknown `策划模式` is a data error; stop instead of guessing.

## Mode routing

- If the user did not say `复刻`, use `策划模式=原创`.
- `钩子复刻` may use only the hook source and the `0.0–3.0s` boundary; the continuation is original.
- `结构复刻` may use only ordered phases, narrative functions, proof targets, and transition purposes. Do not reuse source visuals, subject, wording, audio, or product placement.
- `全量复刻` may use the complete readable source video and its frame-evidence workflow.
- Never combine strategies inside one `content_id`. Record the selected mode in `改编角度` and `Agent 自检`.

## 内容母题扩散

Use only when the user explicitly asks for expansion or names a `内容母题` record. Require the product, platform/account, subject pool, mother description, commercial goal, target duration, requested candidate count, convergence method, and `流程状态=待扩散`.

Generate rough directions internally at 2–3 times the requested count. Apply product facts, compliance, asset executability, and distinctiveness gates before writing exactly the requested number of candidates. Each candidate must contain the controlled creative fields and a combined `准入结果`; only `PASS` candidates receive component scores and the active configuration’s `配置综合评分`.

- `人工选择`: write candidates, set `流程状态=候选待确认`, and stop. The user may select any non-empty subset, including all candidates.
- `自动 Top N`: select exactly the configured number from `PASS` candidates by `配置综合评分`, with documented tie-break evidence.
- After `流程状态=选择已锁定`, create exactly one original task per selected candidate using mother ID + candidate ID as the idempotency key. Copy only campaign-level requirements; product facts remain in the product record. Fresh-read each reverse link before setting `流程状态=已收敛`.

Do not create a storyboard, video, or `内容库` record during expansion, and do not create tasks for unselected candidates.

## Original planning handoff

For an ordinary original task, use its original-only fields as the creative direction. History is optional and should be read only when the user asks for differentiation or comparison. Internally explore multiple directions, reject unsupported or unexecutable ideas, choose one, and save the script, shot summary, prompts-in-progress, creative-rule snapshot, and self-check in the local package. Hand off only after the selected task, product, subject, configuration, language, and target duration are fixed.

## Rotation rule

Use the automatic linked version count and configured/explicit `轮换上限`; the legacy numeric `已生成版本数` is historical only. If the task is exhausted, create one materially different replacement task with an idempotency key and explicit source-task link, verify it, activate it, then archive the exhausted task according to the lifecycle module. If any write or verification fails, stop; do not create a second replacement task.
