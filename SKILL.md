---
name: commerce-content-director
description: Create UGC ecommerce short-video storyboard packages for Douyin, Xiaohongshu, and Pinduoduo. Every original or replication run must first select and read exactly one Feishu `内容策划任务`; use that task for creative direction and replication boundaries, then verify product facts, current Feishu original rules, active content-system configuration, and model capability. Use to expand a broad Feishu `内容母题` into scored `创意候选` and converge one or more selected candidates into original planning tasks, or to create original UGC and hook, structure, or full replications. Never use LibTV or browser/UI automation for final-video generation.
---

# UGC ecommerce storyboard planning

## Mandatory service preflight

Run this preflight before selecting a task, reading product/rule records, creating a run package, ideating, writing a script, writing a text storyboard, or generating any image/video prompt:

1. Check Flow2API through the registered Sidecar MCP with `flow_get_service_health(include_dependencies=true)` and `flow_list_models(include_unavailable=true)`. Treat Flow2API as unavailable when the health response is not `ok`, `flow_bridge` is not healthy, the bridge is not accepting submissions, or the model catalog cannot be read.
2. Read `config/base-schema.json`, then check Feishu MCP with a read-only metadata call such as `bitable_v1_appTableField_list` against its logical `planning_tasks` mapping. Treat Feishu MCP as unavailable when the call errors, times out, or returns no successful field payload.
3. Record only scrubbed status/error summaries; never print credentials or tokens.

If **both Flow2API and Feishu MCP are unavailable**, stop immediately. Report the two concrete preflight failures and do not read creative records, create candidates, write scripts or text storyboards, create a local content package, submit jobs, upload attachments, or write Feishu records. A failed preflight must not be replaced with a manually invented text plan.

If only one service is unavailable, do not perform actions that require that service. In particular, do not submit Flow2API jobs or archive/upload Feishu content while its corresponding service is unavailable; keep any diagnostic note separate from a creative storyboard package.

Work in exactly one generation mode. `内容母题扩散` is a pre-planning operation, not a generation mode: it may create Feishu candidate records and, after its explicit convergence rule is met, one or more original planning tasks; it must not generate images, boards, videos, or `内容库` records. Stop after every required final-generation board—and, for `全量复刻`, every required storyboard master—has been uploaded to the linked Feishu record and a fresh read confirms the expected attachments. Only then set `审核状态 = 待审核`. A human must change that record to `通过` **and explicitly name that exact `content_id` or Feishu record for video generation** before any final-video work can begin.

## Modes

- **逐帧复刻**: Use a readable reference video and an identifiable product asset. This mode requires the linked `内容策划任务.策划模式`: `钩子复刻` reuses only the opening hook; `结构复刻` reuses only the sales narrative skeleton; `全量复刻` preserves source shot order, scene, action, camera, lighting, rhythm, and mobile-video texture. Replace only the product and the pixels or interaction logic that conflict with confirmed product facts. Follow the selected strategy contract and workflow below.
- **原创 UGC 策划**: Do not use a reference video. If the user did not explicitly say `复刻`, select `原创` automatically and do not ask the user to choose a mode. First select and fresh-read exactly one active `内容策划任务` whose `策划模式=原创`; use its original-only creative fields as the required creative direction. Resolve the product directly from the `产品` table, then read its confirmed facts and anchor plus the current Feishu original-rule configuration; never use the task's `产品` relation as the product lookup path. A product-only request is not permission to invent a direction outside the task table: if no unique usable original task can be selected, stop and report the concrete block. Produce the script, per-shot image prompts, and final storyboard masters. Read content history according to the task-selection and rotation contract; similarity is advisory, never a rejection gate. Follow [references/ugc-original-planning.md](references/ugc-original-planning.md) for the hot-update loading contract. Authentic phone-video texture must support proof and conversion, never replace them with lifestyle or beauty-shot pacing.

For an ordinary original task, first pass the mandatory content-planning-task gate below, then generate and score candidates internally within that task's creative direction, retain only the selected direction and decision rationale in `Agent 自检`, and submit one finished package for review. The exception is an explicitly requested `内容母题扩散`: write every qualified candidate to the `创意候选` table and follow its configured convergence rule. Do not create a storyboard package while a mother topic is still expanding or awaiting manual selection.

### 内容母题扩散

Use this operation only when the user explicitly asks to expand a broad direction, or explicitly names a `内容母题` record for expansion. Read [references/content-strategy-and-assets.md](references/content-strategy-and-assets.md) and [references/ugc-original-planning.md](references/ugc-original-planning.md) before creating or updating candidates.

- For a current mother topic, require `产品`、`平台 / 账号`、`主体资产池`、`母题描述`、`商业目标`、`视频时长`、`期望候选数`、`收敛方式` and `流程状态=待扩散`. `期望候选数` must be an integer from 3 to 12; `收敛方式` is exactly `人工选择` or `自动 Top N`. When using `自动 Top N`, `自动入选数` must be an integer from 1 to `期望候选数`; when using `人工选择`, ignore that field.
- Use `母题描述` as one concise sentence answering who, trigger moment, conflict and desired change. Use `特殊要求` only for round-specific presentation requirements such as duration, language, style, scene or subject preference. Do not paste product mechanisms, hard facts, compliance disclaimers or full rule text into either field; those remain authoritative in the product and original-rule records.
- The mother workflow uses `流程状态` as the only lock signal. Candidate records whose `内容母题` points to this mother and whose `候选状态=入选` are the authoritative selected set; do not require a separate selected-candidate link or checkbox. The reverse `创意候选列表` link is informational and may be hidden in the daily view.
- Fresh-read the linked product, optional subject asset, and the single current original-rule record before ideation. Product hard facts, compliance boundaries, and subject-identity requirements apply equally to candidates.
- Treat `内容母题.特殊要求` as campaign-level execution guidance only. Do **not** copy product hard facts, material or efficacy claims, unique loading paths, structural prohibitions, platform compliance rules, or the full contents of `产品硬事实与禁忌` / `产品审核要求` / `原创规则` into this field. Those remain authoritative in their source records and must be fresh-read and applied during expansion and generation.
- Internally generate 2–3 times the requested candidate count as rough directions. Apply hard gates first, cluster near-duplicates, then write exactly the requested number of qualified candidates. Do not pad the Feishu table with weak variants merely to reach the requested count.
- Each candidate must be linked to its mother topic and include `目标人群`、`痛点`、`核心卖点`、`内容形式`、`核心创意`、`钩子`、`叙事结构`、`主要证明动作` and `互动 / CTA`. The hook is one compact field; do not split it into first-frame, first-line or sound-hook fields. `内容形式` uses the controlled platform-native formats in the candidate table.
- Before ranking, write one combined `准入结果`: `PASS` only when product facts, compliance, asset executability and distinctiveness all pass; otherwise write `FAIL` and the relevant `淘汰原因`. A failed admission result leaves the candidate out of ranking and task creation.
- For a PASS candidate, write the three 1–5 component scores, then fresh-read the active content-system configuration and calculate/write the configured score plus its configuration ID. The configured score is the only score used for automatic convergence; the legacy formula field is display-only.
- For `人工选择`, set `流程状态=候选待确认` and stop. The human may mark any non-empty subset of candidates as `候选状态=入选`, including all candidates. When selection is complete, set `流程状态=选择已锁定`; the system then queries the linked candidates and creates tasks.
- For `自动 Top N`, rank only `准入结果=PASS` candidates by `综合评分`; select exactly `自动入选数` candidates. Break ties by the evidence and conversion explanation recorded in the candidate. Mark selected candidates `候选状态=入选`, set `流程状态=选择已锁定`, and continue to task creation.
- Create original tasks only from the locked selected set. Set `流程状态=任务创建中` and create exactly one task per selected candidate using the mother record ID plus candidate record ID as the idempotency key. Copy candidate creative fields, product, platform/account, optional subject asset and only campaign-level creation requirements; set `策划模式=原创` and link `来源创意候选`. Confirm each task through the `落地内容策划任务` link; only after every selected candidate has a linked task set `流程状态=已收敛`. If one task creation fails, retain successful links and set the mother topic to `处理失败`.

### Planning-mode contract

Use the user's wording to select the requested family, but use the Feishu task to select the actual plan. `内容母题扩散` is the only pre-planning exception and may create only an `原创` task after convergence. The Feishu `内容策划任务.策划模式` field is a closed single-select enum: its only allowed values are exactly `原创`、`钩子复刻`、`结构复刻`、`全量复刻`. Blank values, the legacy `复刻` value, whitespace variants, and any newly encountered value are invalid data: do not guess, silently normalize, or route around them; stop and report the record and field for cleanup. When creating or updating a task, write one of the four allowed values only. For generation, when the user does not explicitly say `复刻`, default to `原创`; do not stop to ask the user to choose a mode. When the user explicitly says `复刻`, search the Feishu `内容策划任务` table for the named task (or the best exact product/task match), read its non-empty `策划模式`, and use that value to select `钩子复刻`、`结构复刻` or `全量复刻`. A supplied reference video or link never selects a mode by itself. In both families, generation is blocked until exactly one usable task has been selected and fresh-read.

- **钩子复刻**: Reuse only the opening hook's visual setup, action and rhythm for `0.0–3.0s`. If `钩子复用素材` is populated, it is the preferred hook source; otherwise use only the first three seconds of `爆款视频` or `爆款视频链接`. Produce the remaining duration as original UGC from the current product facts and original-rule configuration. Do not inspect, transcribe, quote, describe, or use any source-video content after 3.0 seconds.
- **结构复刻**: Reuse only the chronological selling skeleton: phase timing, each phase's narrative function, proof target, and transition purpose. Do not reuse the reference's hook image, individual shot, scene, action, subject identity, product placement, wording, audio, or visual prompt. Create every visual and line for the current product from product facts and original-rule configuration.
- **全量复刻**: Use the existing frame-by-frame workflow unchanged. This is the only strategy that may create RF contact sheets, replacement contact sheets, storyboard masters, per-frame plans, or reference-led script adaptations for the whole source video.

For every strategy, archive the selected value in `改编角度` and state it in `Agent 自检`. Never combine strategies in one `content_id`.

### Mandatory content-planning-task gate

Every original or replication generation run must select and fresh-read exactly one `内容策划任务` before generating any creative candidate, script, image prompt, storyboard image, or reference evidence. The task is the required creative-direction input; the `产品` table remains the only product-fact and product-asset source.

- If the user names a task, use that exact record. If the user gives only a product or product ID, search `内容策划任务` for an active task linked to that product and, when available, the requested platform/account. For original runs require `策划模式=原创`; for replication runs read the task's non-empty `策划模式` and follow its selected replication workflow. Treat a blank `任务状态` as active only where the reference contract permits that default; never use `已归档` tasks for a new version.
- Resolve ambiguity deterministically only when one task is clearly the best exact product/task and platform/account match. If there is no usable task or more than one equally valid task, stop before creative generation and report the task-selection block; do not invent a product-only concept and do not silently create or rewrite a task. Use `内容母题扩散` only when the user explicitly requests it, or use the documented automatic rotation exception for an exhausted task.
- Fresh-read the selected task's mode-specific fields: original creative fields for `原创`; reference media and the selected boundary for `钩子复刻`、`结构复刻` or `全量复刻`. Also fresh-read its `任务状态`、`内容库版本列表`、`内容版本数（自动计数）` and `轮换上限`, and apply the automatic rotation contract before ideation when required. The legacy numeric field `已生成版本数` is a historical snapshot only and must not drive rotation.
- Save the selected task record ID, task name, selection basis, task snapshot/hash, and selected mode in the local package and `Agent 自检`. Link the resulting `内容库` version to that exact task. Do not proceed on a stale task read.

### Product interaction hard gate

Treat confirmed product interaction paths as hard constraints, not selling-point descriptions. Fresh-read the product's hard facts, generation notes, and product-specific review requirements through the Base schema mapping before review. Every prompt involving a constrained action must state the confirmed path, orientation, connected parts, and prohibited alternatives literally; never replace those facts with vague wording. Product-specific guidance may add constraints or define an ambiguity for human review, but cannot weaken fixed safety, authenticity, subject-continuity, geometry, or final-generation requirements. A product-level human-review warning must be recorded in `quality-report.md`, `package.json`, and the Feishu review notes; it never authorizes final-video generation by itself.

Before accepting any generated storyboard, review each loading and dispensing panel separately for: (1) the unique loading path, (2) the visible direction of entry, and (3) unchanged connected product structure. A top-loading action, side-lattice loading action, detached crown/cap/lid, or other plainly contradicted product fact is a hard failure. If the product field explicitly classifies the case as `WARN｜人工复核` and the image does not show a plainly wrong path, keep the board local or upload it only through the documented human-review exception, with the warning preserved; do not silently call it PASS. A review-only board containing timing annotations or other review labels must never be passed to Omni as a final-generation input; regenerate a clean board before video generation. Do not set `通过` or start final-video work while any WARN remains unresolved.

### Product asset-routing hard gate

Reading all product attachment fields is not sufficient: the relevant approved product assets must be routed into the Flow2API Job that needs them. Before creative generation, fresh-read and inventory `默认产品锚点`、`产品三视图`、`产品细节图`、`产品场景图` and `其他产品素材`, then write a per-board `product_asset_plan` in the local package and `generation-jobs.json`.

- Any loading, dispensing, opening, drainage, cleaning, connection, hole, lattice, cap, lid, or other structure-sensitive panel must include the most relevant approved `产品细节图` as an input image. Do not rely on the default three-view anchor plus prose when a detail asset exists.
- Any panel whose proof depends on a real usage context, recurring animal/person interaction, scale, placement, or exploration scene must include the most relevant approved `产品场景图` as an input image when available. A scene asset is evidence, not a decorative reference.
- The prompt must state that the generated product geometry, openings, proportions, connections and part relationships match the supplied detail/scene asset exactly; never enlarge or invent a structure merely to make it visible. Product-specific scale constraints come only from the current product record or supplied asset.
- Flow2API uses media-specific reference-image limits: R2I/Banana Pro accepts at most 10 input images, while Omni R2V accepts at most 7. When a recurring subject exists, the exact subject anchor is mandatory and the default product anchor remains mandatory. Route every approved detail/scene asset needed by the board or segment within the applicable limit; deduplicate identical files by stable hash before counting. If the required routed assets exceed the applicable limit, split the evidence across appropriate Jobs or stop before generation and record the asset conflict. Never silently omit a critical detail or scene asset.
- Record the exact input filenames, Feishu attachment field, file token or local hash, asset role, and board/segment mapping in `product_asset_plan` and `generation-jobs.json`. A detail or scene asset that was only read but not passed to the corresponding Job does not satisfy this gate.
- After generation, compare every structure-sensitive panel against the routed detail asset and every context-sensitive panel against the routed scene asset. Any unexplained product-scale, hole-size, geometry, or interaction drift is a hard failure; do not upload the board or set `待审核`.

### Flow2API input-image serialization gate

Feishu attachment references and Flow2API image inputs are different data types. A Feishu `file_token`, attachment `name`, field name, or audit metadata object is **not** a valid `input_images` item by itself. The registered Flow2API MCP image schema requires every input image to contain the actual image bytes in this shape:

```json
{
  "mime_type": "image/png",
  "data_base64": "<raw Base64 image bytes without credentials>"
}
```

Before every `flow_submit_image` or image-input `flow_submit_video` call:

1. Resolve each approved Feishu attachment by its `file_token` using the Feishu media download interface (`drive_v1_media_batchGetTmpDownloadUrl`) or this skill's download script. Download the temporary URL to a local run input directory. Never pass the Feishu token-only object directly to Flow2API, and never treat the temporary download URL as a durable asset URL.
2. Read the downloaded bytes, determine the actual MIME type, and Base64-encode the bytes. Send only the required `mime_type` and `data_base64` fields in the Flow2API `input_images` payload. Do not send a `file_token` in place of `data_base64`; do not assume that a local path, Feishu URL, or `data:image/...;base64,` URI prefix is accepted unless the current MCP schema explicitly documents it.
3. Validate locally before submission: every item has a supported image MIME type, non-empty Base64, Base64 decodes successfully to an image, and the decoded image matches the downloaded asset. Deduplicate identical files by stable SHA-256 hash before applying the R2I limit of 10 or the Omni R2V limit of 7. If a required asset cannot be serialized or the limit is exceeded, stop before submission and record the asset conflict.
4. Keep the asset audit mapping separately from the request payload. In `product_asset_plan` and `generation-jobs.json`, record the Feishu field, original filename, file token, local routed filename, local SHA-256, asset role, and board/segment mapping. Do not record temporary download URLs, access codes, credentials, or raw Base64 in run reports.
5. If transport-compatible preprocessing is required, preserve the complete image, aspect ratio, product geometry, and subject identity; no crop, compositing, retouching, or geometry-changing edit is allowed. Record the derived local filename and hash while retaining the original Feishu filename and token as provenance.

The first failed request in a run must be classified by where it failed. A validation response such as `input_images.0.mime_type Field required` or `input_images.0.data_base64 Field required` means the request was rejected before a valid Job was created: do not call `flow_wait_job`, do not invent a Job ID, and do not treat it as a model-generation failure. Correct the serialization, then submit the unchanged creative request with a valid idempotency key and record the correction. A response containing a real `job_id` means a Job exists; subsequent status errors must be handled under the Job transport rule below.

### Flow2API Job transport rule

`flow_submit_image`, `flow_submit_video`, `flow_wait_job`, and `flow_get_job` use separate network requests. A transport error from `flow_wait_job` means only that the status request failed; it does not establish that the upstream Job failed or was cancelled. When a real `job_id` was already returned:

- Query `flow_get_job(job_id)` with the same Job ID.
- If the status is `queued`, `submitting`, or `active`, continue waiting with the same Job ID; do not resubmit the payload.
- Call `flow_get_job_result` only after `succeeded`. Treat `failed`, `cancelled`, and `timed_out` as terminal failures and retain the error.
- Do not report progress percentages unless the service supplies a real percentage.

If the submission request itself fails before returning a real Job ID, no valid Job has been established. Classify the error first: fix schema or payload errors before retrying; for an uncertain transport failure, use the exact same idempotency key only to recover the unchanged payload and verify whether the service created a Job. Never create a second deliberate generation attempt under the same key.

### Cached asset preparation and visual-fact gate

After the task, product, and any recurring subject have been fresh-read—but before ideation, script writing, or any image prompt—prepare the required approved inputs once for the entire run. Build `plan/flow-asset-plan.json` with every asset that any planned board will need: default product anchor, required product detail/scene assets, and the subject anchor when applicable. Then run:

```text
python scripts/prepare_flow_inputs.py --asset-plan <run>/plan/flow-asset-plan.json --out <run>/plan/flow-input-cache.json
```

The helper keeps reusable source downloads, uncropped transport renditions, and Base64 sidecars under `skills/commerce-content-director/.cache/flow-inputs/`; this directory is Git-ignored. The cache is an acceleration layer, never a source of product facts:

- Cache identity includes the current Feishu `file_token`, original filename, and render policy. A missing or changed token is a cache miss: download again and do not reuse the prior visual interpretation.
- Reuse cache hits across runs only after the current Feishu record has been fresh-read and its asset token matches the cache manifest. Record hit/miss, local SHA-256, source field, and token in the run's `generation-jobs.json`; never archive the cache itself to Feishu.
- The helper emits local Base64 paths rather than raw Base64. Read those files only when building the in-memory MCP payload; do not paste raw Base64 into prompts, package reports, or Feishu fields.
- Do not use this cache to bypass the mandatory product attachment inventory or to resurrect assets removed or replaced in Feishu.

Immediately inspect the cached product detail asset and every scene/detail asset that will be routed into a board. Write `plan/product-visual-facts.md` before drafting prompts. It must identify only visible, asset-supported facts that affect generation, such as body color, crown shape, lattice opening shape/pattern, bottom-hole shape/proportion, connected-versus-separable parts, and any scale/interaction cue. Include the product record ID, inspected field, source token, local SHA-256, and a visual-fact hash.

Every product-geometry sentence in a board prompt must derive from this run's visual-fact file together with the product's confirmed hard facts. Do not infer a lattice, cap, opening shape, or connection from product names, prior runs, memory, or generic prose. If the visible asset conflicts with a product hard fact or cannot resolve a structure-sensitive point, stop before submission and report the conflict. Do not write this derived visual summary back to Feishu unless the user separately authorizes product-record maintenance.

### Parallel final-generation-board execution

Once the visual-fact gate has passed, all board prompts are complete, and every board has a complete routed input set, independent 10-second storyboard-board Jobs may be submitted in parallel. This applies to the 2, 3, or 4 raw segments of a requested 20-, 30-, or 40-second package; it does not authorize extra boards or video generation.

- Submit all independent board Jobs in one bounded batch of at most the requested segment count (maximum four). Each request must retain its own board prompt, panel timings, product-asset plan, and unique idempotency key. Do not submit boards in parallel when a later prompt requires visual information from an earlier generated board.
- Monitor the established Job IDs concurrently under the Flow2API Job transport rule. A transport error for one waiter affects only that status request; query and continue the same Job without resubmitting it.
- Download, validate, and visually review every completed board independently. A failure or product-geometry drift regenerates only that affected board once; accepted boards are never regenerated merely because another board failed.
- Keep the full package local until every expected board has passed. Never create a partial `内容库` record, upload a partial attachment set, or set `待审核` while any parallel board remains pending, failed, missing, or unvalidated.

### Subject identity hard gate

Treat a recurring person, animal, or other identifiable subject as a required visual asset, not as a prompt-only description. A subject is recurring when it appears in two or more panels, crosses a raw-segment boundary, or is the named actor in the task's proof scene. The task schema may leave `主体资产` empty; an empty task field is not a blocker because the agent must resolve a suitable asset from `主体资产库` automatically.

Before generating any creative candidate, script, image prompt, or storyboard image:

- Inspect `内容策划任务.主体资产` first. If it names a valid record, use that record. If it is empty or ambiguous, query `主体资产库` and automatically choose one record with `状态=可用`, a non-empty `主体锚点`, and a stable `主体身份描述`; do not ask the user merely because the task field is empty, and do not infer identity from the product image. Select deterministically: (1) exact subject name/type/role match in task text, (2) closest match to the task's proof scene, default scene, and product context, (3) stable first record by `record_id` when candidates remain tied. If no eligible record exists, stop and report `主体资产库无可用匹配资产`.
- Fresh-read exactly the selected `主体资产库` record before generation. Do not create or silently modify a task or subject record as part of selection; keep the selected mapping in the local package and link it to the content version during the normal post-validation archive step.
- Record the selected subject record ID, anchor filename, selection rationale, and an identity-description hash in the local package and `generation-jobs.json`. The mapping from subject name to asset record must be explicit when more than one subject exists.
- Pass the same subject anchor together with the default product anchor and the board-specific routed product detail/scene asset to **every** storyboard-generation Job containing that subject. Keep the same subject identity description and input filename across all boards; never rely on cross-Job memory. Keep each R2I Job within 10 images and each Omni R2V Job within 7 images by applying the Product asset-routing hard gate; never drop the critical product detail asset silently.
- If the concept intentionally has no recurring subject, write `主体身份不锁定` in the local package before creative generation and do not write prompts that imply the same person/animal continues across panels or segments.

After generation, review subject continuity independently of geometry: face, coat/color, markings, breed/type, body size, and distinctive accessories must remain consistent across panels and segment boundaries. Any unexplained identity drift is a hard failure. Regenerate the affected board once with the same subject anchor and prompt contract; if it still fails, stop and keep the package local. Do not upload or set `待审核` until this gate passes.

### Original-derived planning ordering

Before generating any creative candidate, script, image prompt, or storyboard image in **原创 UGC 策划**, `钩子复刻` continuation, or `结构复刻`, read [references/configuration.md](references/configuration.md), pass the mandatory content-planning-task gate, fresh-read the current original-rule configuration via the `original_rules` mapping in `config/base-schema.json`, and run the subject identity hard gate above. Use only `平台合规禁忌`、`通用表达边界`、`必须检查项` and `账号长期定位`; do not derive creative direction from this table. In original UGC, all creative direction comes from the selected linked `内容策划任务` whose `策划模式=原创`, including its original-only fields. Save the exact four-field snapshot, record ID, and content hash locally in `plan/creative-rules-snapshot.md` and summarise it in `Agent 自检`; this is local provenance, not a required `内容库` field.

Read the content library only when the user explicitly asks to avoid recent content, seek differentiation, or compare against history. Read `内容标题`, `content_id`, `创作模式`, `审核状态`, and relevant concept fields; save the query date, record IDs, and similarity notes in `plan/library-history.md`. Similarity is information only: never reject, block, or change a concept merely because it resembles history. If the original-rule configuration cannot be read, is not exactly one current record, has a required field missing, or conflicts with product hard facts, stop before creative generation and report the block. A content-library read failure never blocks ordinary original planning.

## Flow2API MCP timing and storyboard contract

- Before any image or video submission, call `flow_get_service_health` and
  `flow_list_models` through the registered `flow2api-mcp` Sidecar. The Sidecar
  is the MCP boundary; never call Omni's private `/internal/mcp/v1` bridge as a
  substitute for the MCP tools. If the health response does not show the Flow
  bridge as healthy, stop and report the connection problem.
- The local Windows registration must launch
  `python -m flow2api_mcp.mcp_stdio` from the configured local `flow2api-mcp`
  workspace (this workspace uses `E:\AIGC短视频带货\flow2api-mcp` as an example);
  each operator must set that path in their own MCP registration. For bundled
  scripts and local MCP-related configuration, default to the `.env` beside
  this `SKILL.md` (`<skill-dir>/.env`); only an explicit `--env`,
  `FEISHU_ENV_FILE`, or `HERMES_ENV_FILE` override may take precedence. Do not
  fall back to `<workspace>/.hermes/.env` when the skill-local `.env` exists.
  Keep the skill-local file ignored and never print, commit, or expose its
  secrets. MCP configuration changes require a Codex/Hermes restart because
  tool discovery has no hot reload.
- Feishu media retrieval has two explicit paths. Prefer the registered
  official MCP operation `drive.v1.media.batchGetTmpDownloadUrl` when a
  temporary media URL is sufficient. When a local binary file is required for
  Flow2API or asset inspection, use `python scripts/download_feishu_media.py
  --file-token <token> --out <path>`; this helper reads only
  `skills/commerce-content-director/.env`, never auto-discovers or falls back
  to `.hermes/.env`, and calls Feishu's official media-download endpoint.
  Do not use web search or another content-platform connector to obtain an
  approved Feishu asset.
- Use Flow2API MCP only: **Banana Pro** for images and **Omni** for final video. In the MCP, Banana Pro's exact portrait image key is `gemini-3.0-pro-image-portrait`; Omni's exact portrait video key is `omni_portrait`. Do not silently substitute another model.
- A complete deliverable video must use the target and raw-segment durations from the active configuration snapshot, after verifying current Omni capability. The ordered segment set must cover the approved target exactly.
- The active configuration and current Omni capability jointly determine the raw-segment duration. Create one final-generation storyboard board per raw segment, with the configured count of chronological panels. Assign an explicit start and end to every panel; their durations are flexible and must sum to that raw segment. Maintain action continuity at every segment boundary.
- Final-generation-board grid, panel count, and panel ratio come from the local content-system configuration snapshot; state them explicitly in every board-generation prompt. A review-only board may retain timing annotations when the user explicitly requests human review or the product audit policy marks them `WARN｜人工复核`; label that artifact as review-only, preserve the warning, and never pass it to Omni. Before any final-video work, replace it with a clean no-text/no-watermark/no-UI board and validate that replacement.
- Generate the complete configured board in one image request per raw segment. Do not submit independent panel jobs or compose a board locally. Immediately before upload, run `python scripts/validate_generation_storyboards.py --profile plan/content-system-config-snapshot.json <board...>`; record each `PASS` with board filename and dimensions in `quality-report.md`. A failure means the board is not reviewable: regenerate that board once and stop if it still fails.
- Every Flow2API Job is asynchronous. After submission call `flow_wait_job(job_id)` and wait through the Job deadline (normally 1800 seconds) before judging the outcome. `queued`, `submitting`, and `active` are non-terminal in-progress states, not failures; never create a replacement Job, switch models, or report a generation failure while any of them remains. Only `succeeded`, `failed`, `cancelled`, or `timed_out` is terminal. If `flow_wait_job` returns `wait_timeout=true`, retain the same job ID, record its latest state, and report that it is still non-terminal—do not resubmit. Call `flow_get_job_result` only after `succeeded`.
- `RF` one-second evidence is an audit requirement only for `全量复刻`. Do not confuse it with final-generation boards: RFs document the reference, while configuration-profile boards direct Omni.
- Name boards by their configuration-derived time ranges. Attach every board to Feishu and include the raw segment range, final retained range, and all panel prompts in `分镜摘要` and `画面生成 Prompt`.

## Feishu content, strategy, asset, and review gate

Use the Base and logical table mappings in `config/base-schema.json` for every run. Read [references/configuration.md](references/configuration.md) and [references/content-strategy-and-assets.md](references/content-strategy-and-assets.md) before creating, revising, reusing, or delivering content; read [references/ugc-original-planning.md](references/ugc-original-planning.md) for original-mode rule configuration.

- Use `内容策划任务` as the mandatory task-level direction input for both original and replication runs, not as the product search index. `内容母题扩散` is the manual ideation entry point; automatic task rotation below is the approved lifecycle exception. When the user does not say `复刻`, select `原创` automatically, then select an active original task and read its original-only fields (`目标人群`、`痛点`、`核心卖点`、`钩子`、`叙事节奏`、`证明场景`、`核心创意`); do not require its `产品` relation to locate the product. When the user explicitly says `复刻`, select and fresh-read the task because its `策划模式` and reference-media fields define the replication boundary. `主体资产` is optional only when no recurring identifiable subject appears; it becomes mandatory under the subject identity hard gate above. `原创` requires original-only fields; `全量复刻` and `结构复刻` require `爆款视频` or `爆款视频链接`; `钩子复刻` requires either `钩子复用素材` or `爆款视频` / `爆款视频链接`. Automatically infer the replication boundary and v1/v2/v3 plan only after reading the selected task. Each version is a separate `内容库` record and `content_id`; link it to the exact selected `内容策划任务` and always link it to the directly resolved `产品`, then state `版本号` and `改编角度` as the selected mode. Do not delete task records; normal original runs may archive and rotate an exhausted task under the automatic task-rotation contract, while other task edits remain user-authorized operations.
- **Automatic task rotation:** before ordinary original ideation, fresh-read the selected task lifecycle fields and the active content-system configuration. The automatic count is derived from the duplex link and is the sole rotation count; the legacy numeric count is not incremented or used for decisions. A blank task limit inherits the active configuration default; never silently lower an explicit limit. If the task is archived or the automatic count is at/above the limit, stop using it. Create one new original task with the same product, platform/account, priority, subject asset and long-term boundaries, but a materially different creative direction selected after reading recent content history; link it to the exhausted task, activate it, and inherit the explicit limit. Archive the exhausted task and preserve every old task/version link. If any write fails, stop and report the inconsistency instead of creating a second replacement task. Never delete a content version; archive it only when it leaves the active workflow.
- Before using a product, search the Feishu `产品` table directly by the user-provided `产品名称` or `产品ID`; do not search for the product only inside `内容策划任务` and do not treat a task's product relation as the sole source of truth. Resolve exactly one product record, then fresh-read it and require `状态=可用`, a non-empty `默认产品锚点`, and consistent `产品硬事实与禁忌` plus `生成注意事项`. Also read `产品审核要求` when present; snapshot its text in the local package and apply its `PASS`、`WARN｜人工复核`、`FAIL` policy only to product-specific review. If no record, multiple ambiguous records, or a task/product conflict is found, stop and report the concrete block. Select each content argument from its `核心卖点`、`目标人群`、`典型痛点`、`典型使用场景` and `可用表达 / 可用宣称`; never use an item in `禁用表达 / 禁用宣称`. Do not read local product-route files or a file-by-file asset table as a substitute. Run the subject identity hard gate before any creative generation. A linked `主体资产库` record is mandatory whenever the storyboard uses a recurring subject; require `状态=可用`, a non-empty `主体锚点`, and a stable `主体身份描述`, then pass that same subject anchor together with the product anchor to every applicable storyboard-generation job and preserve the identity description across all segments. In replication mode, reference media belongs directly in the linked `内容策划任务.爆款视频` attachment or `内容策划任务.爆款视频链接`, and reusable hook media belongs in `内容策划任务.钩子复用素材`; original mode must not read or use these fields.
- Create a minimal local run package first. Its root package file is exactly `package.json` (content ID, selected task/product IDs, mode, and run state), together with `generation-jobs.json` (Flow2API job IDs, states, result addresses, and request digests), `quality-report.md` (local validation evidence), and `generation-storyboards/` (temporary boards held until Feishu attachment verification). Per-batch and per-master audit directories may retain their own `manifest.json` files where the delivery contract requires them; those are not a substitute for the root `package.json`. Keep the exact submitted image prompts in `image-generation-prompts.md` and the exact submitted video prompts in `video-generation-prompts.md`; these are generation provenance, not duplicate product or strategy records. Do not copy Feishu product facts, task fields, or approved assets into the durable package unless needed as a temporary cache. **Do not create, update, upload attachments to, or otherwise write a `内容库` record while any required final-generation storyboard is missing, non-terminal, failed, absent from disk, or has not passed `validate_generation_storyboards.py`.** This includes placeholder records and partial script/prompt writes. Keep the package local and record the block in `quality-report.md`.
- Only after every expected board exists, matches the configuration profile, has a recorded validator `PASS`, and has passed per-panel interaction/identity/text review, create the new `内容库` record for a new version (or update the same rejected record). If the only remaining issue is an explicit product-level `WARN｜人工复核`, and no fixed global rule or plainly contradicted product fact is present, the user-authorized human-review exception may archive/upload the board with the WARN preserved in `审核意见`; it must not be marked `通过` or used for Omni. Review-only annotations such as timing labels must be removed in a clean replacement board before final-video generation. In that single post-validation archive step, write the final script, exact `画面生成 Prompt` from `image-generation-prompts.md`, creative fields, `Agent 自检`, selected product image, every final-generation board, and, for `全量复刻`, all final storyboard master attachments. The deprecated `内容库` fields `内容指纹`、`产品审核要求快照` and `原创规则记录 ID/hash` are not part of the current Base schema: do not create or expect them. Keep detailed product-review evidence and rule provenance in the local `quality-report.md`、`plan/creative-rules-snapshot.md` and package; summarize only the outcome in existing `Agent 自检` or `审核意见` when needed. Before writing `待审核`, fresh-read the record and verify that every expected board attachment is present.
- The `内容库` field `画面生成 Prompt` is mandatory before `待审核`. After the user explicitly authorizes final-video generation for that approved record, write the exact per-10-second prompts from `video-generation-prompts.md` into the same record's `视频生成 Prompt` field before submitting any Omni Job; fresh-read the record after the write and preserve the same text in the local file. A missing video-prompt field or failed write blocks Omni submission.
- Upload all reusable product images into the relevant `产品` attachment fields; for replication, upload the reference video directly to `内容策划任务.爆款视频` or provide `内容策划任务.爆款视频链接`. In original mode, do not upload reference media to the task. Upload every Flow2API final-generation board to `最终分镜图` **only after the 9:16-panel validator has passed**. When the Feishu MCP exposes record CRUD but no media-upload tool, use the portable client in `scripts/feishu_attachment_uploader.py` through the CLI wrapper `scripts/upload_feishu_attachments.py`. It has no browser or workspace-specific Base dependency: authenticate with `FEISHU_TENANT_ACCESS_TOKEN`, or with `FEISHU_APP_ID` and `FEISHU_APP_SECRET` supplied as environment variables or through `--env`; choose `bitable_image` for images and `bitable_file` for other media; and write the returned attachment tokens to the named record field. Files above 20 MB automatically use Feishu's multipart upload flow. Never print credentials or tokens.
- Example: `python scripts/upload_feishu_attachments.py --app-token <app_token> --table-id <table_id> --record-id <record_id> --field 最终分镜图 <Segment-01.png> <Segment-02.png>`. Do not substitute a local path, a cloud-document link, or a guessed token for an attachment upload. `FEISHU_APP_TOKEN` and `FEISHU_TABLE_ID` may be used instead of the two CLI flags.
- Perform a fresh record read and verify non-empty attachment tokens, filenames, and a count matching the expected segment count. A local path is supplementary evidence only.
- If attachment upload is unavailable or fails, do **not** set `待审核`; record the failure, keep the package local, and report the block.
- `待审核` means stop. Do not submit Flow2API image/video jobs for the final package, generate TTS, or burn subtitles.
- `拒绝` means read `审核意见`, revise the same concept, regenerate the affected script/prompts/storyboards, and return it to `待审核`.
- `通过` is an eligibility state, not a generation command. Generate a final video only when a fresh lookup shows the exact named record has `审核状态 = 通过` **and** the user explicitly instructs generation for that same `content_id` or record. Never choose an approved record yourself or infer authorization from a generic request such as “generate the video”.
- Before each actual video-generation submission, fresh-read the approved `内容库` record's `已执行次数` and `执行次数上限`. If the limit is blank, use the active content-system configuration default. If the current count is already at the limit, archive the content version and stop. Otherwise increment the count once, re-read it, and only then submit the generation job; a failed job still consumes that execution. When the count reaches the limit, archive the content version after reserving the final execution; do not create a new content version just to retry the same idea.
- After every named, approved execution succeeds, assemble the configured target video and technically verify its streams and duration. Fresh-read the source `内容库` record and confirm the linked record exists before creating one `最终成片` record. Write `成片名称`, a unique `成片ID`, `内容版本`, `视频时长（秒）`, and `生成时间`, then attach only the complete video to `最终视频`. Each successful repeat execution creates another `最终成片` record linked to the same `内容版本`; this existing association is the sample trace. If the source record cannot be resolved, create no final-film record. Do not create a record for failed jobs, raw segments, or unverified assemblies. For uploads up to 20 MB, use `scripts/upload_feishu_attachments.py`; above 20 MB, use a verified multipart upload or the Feishu UI, then verify the attachment token, filename, and playable file before reporting delivery. Do not create or read a separate execution-record table or an抽卡状态 field.

## Full-replication rules

Apply this section only when `内容策划任务.策划模式 = 全量复刻`.

- Extract source evidence at one frame per second. Before making any contact sheet, trim only a continuous terminal run of black frames, download end cards, or account/UI-only tail frames.
- Split valid frames strictly in chronological batches of six: RF01-RF06, RF07-RF12, and so on. The final batch may contain one to five frames. Do not change boundaries for shots, scenes, or hand close-ups. Twenty-seven valid frames are exactly 6+6+6+6+3.
- Make every full source contact sheet as a 3-column by 2-row, zero-gutter grid read left-to-right and top-to-bottom. Make a tail batch as one horizontal row with only its actual frames. Do not add blank cells, padding, or protection borders.
- Submit one source contact sheet, the existing product asset, product facts, user constraints, and the per-frame plan to Flow2API MCP with Banana Pro (`flow_submit_image`, model `gemini-3.0-pro-image-landscape`). The returned `replacement-contact-sheet.png` is the accepted batch artifact.
- Do not split, crop, resize, assemble, or resubmit a returned replacement contact sheet before it passes batch review. After every batch passes, build final masters only with `scripts/assemble_storyboard_masters.py`; never use a prior run, a legacy delivery folder, or a returned master as input to Banana Pro.
- Deliver balanced master sheets by default. For `N` valid RFs, make `K = ceil(N / 15)` masters, partition RFs chronologically into `K` groups whose counts differ by at most one, and keep every group at most 15. Example: 27 RFs are `RF01-RF14` and `RF15-RF27`, not `15+12` or complete-Batch grouping.
- Banana Pro is not a layout engine. Treat materially wrong full-sheet geometry, per-panel geometry, or product scale as a failed batch, regenerate that batch once, and stop if it still fails. Record minor drift honestly; never claim pixel-perfect geometry.
- Preserve source camera position, crop, background placement, occlusion, lighting, exposure, action phase, and compression. Do not convert phone footage into studio or ecommerce imagery. Remove old products, old packaging, source subtitles, watermarks, UI, and incompatible copy.
- Treat user-stated product structure, connections, interaction path, and prohibited actions as hard facts. When source action conflicts, write an interaction substitution first. Use only the confirmed product facts; do not retain, infer, or reuse facts from a different product.
- Use supplied product assets as identity anchors. Do not generate product or subject six-views unless requested.
- Stop and request a shorter range if the reference video is longer than 30 seconds.

## Optional audio-replication extension

Use this extension only after the Feishu review gate has passed for the exact named record and the user explicitly asks to reuse, separate, transcribe, or replace that record's permitted reference audio. It is separate from the default storyboard-only delivery. `全量复刻` may use the full source audio; `钩子复刻` may use only audio within `0.0–3.0s` and only when the user explicitly requests hook-audio reuse; `结构复刻` must never use source audio.

### Background-music and vocal separation

- Extract the reference audio first and retain the original untouched audio file as evidence.
- Do not use simple centre-channel cancellation as the final music source. It can remove speech, but commonly damages music and produces a hollow or blurry result.
- Default to AI source separation with **UVR MDX-Net `UVR-MDX-NET-Inst_HQ_1`**. Export two clearly named tracks:
  - `instrumental` / `no_vocals`: the background-music track for the remake;
  - `vocals`: the isolated speech track for transcription and review.
- Demucs is an allowed comparison fallback, but choose the output by audible music fidelity, not merely by how little speech remains. Record the selected model and retain both output paths in the run report.
- When placing the selected instrumental under a generated video, match it to the exact video duration, use a short end fade, and preserve the original final video. Export a separate `*_背景音乐版.mp4`; never overwrite the source delivery file.
- If voice-over will later be added, mix the music conservatively. For a loud UVR output, start around `volume=0.10`, then adjust by listening; music must never mask the voice-over.

### Speech transcription and timing evidence

- Use local ASR to turn the isolated `vocals` track into a timestamped draft transcript. Codex reviews and corrects the words, segmentation, and product terminology; ASR is the timestamping/evidence layer.
- Save the corrected result as a run artifact containing at least `start`, `end`, `text`, and the source audio/model used. Keep the original ASR draft too.
- The permitted reference-audio window is the canonical timing evidence. Do not infer speech timing from one-second storyboard frames.
- Correct only what can be heard or what is confirmed by the user. Mark uncertain words instead of silently turning them into product claims.

### Reference-led script adaptation

Apply this subsection only to `全量复刻`, or to the `0.0–3.0s` hook window of `钩子复刻` when the user explicitly requests hook-audio reuse. `结构复刻` must not use it.

- Preserve the reference script's selling-point order, information density, and conversational rhythm. Do not reduce it to generic short slogans merely to make later TTS fit.
- Change only the parts that conflict with confirmed product facts, structure, interaction, material, or safety claims. Record every necessary substitution next to its source line.
- Product facts require user confirmation or supplied asset evidence. Preserve the confirmed structure and interaction route; do not invent opening, separation, or use mechanisms absent from the current product record.
- Keep user-confirmed claims verbatim where appropriate (for example, material, odour, softness, and gum-safety claims). Do not introduce unconfirmed claims.
- Retain each corrected script line with the original `start` and `end` timing, even when its replacement wording differs. Timing-fit and TTS decisions are handled later; script quality is not sacrificed at this stage.

### Flow2API MCP generation execution

- Generate final video only when the user explicitly requests it for a named `content_id` or record **and** a fresh Feishu lookup shows that exact record has `审核状态 = 通过`; otherwise this skill remains storyboard-first. This rule applies equally to original and frame-by-frame replication modes.
- Before submitting anything, call `flow_get_service_health` and `flow_list_models`. Require available keys `gemini-3.0-pro-image-portrait` for storyboard panels and `omni_portrait` for final video. If either is unavailable, stop and report the concrete availability block; do not fall back to another model.
- Use the approved image model once for each configuration-profile storyboard board. Respect the current model catalog's input limit; always include the approved default product anchor and, when a recurring subject is present, the exact selected subject anchor plus every board-specific routed product detail or scene asset required by the Product asset-routing hard gate. Reuse the prepared cache payload only after the Cached asset preparation and visual-fact gate has passed. Save the exact submitted text in `image-generation-prompts.md`, and keep its board mapping, per-panel timing, product asset plan, input filenames/tokens, subject record ID, identity hash, content ID, job ID, and result URL in `generation-jobs.json`. Submit independent boards in parallel only under the Parallel final-generation-board execution rule.
- Download the returned board without cropping, splitting, resizing, or locally composing it. Validate it, then inspect every configured panel separately for timing order, product identity, hard interaction facts, and text/UI contamination. No generated board may be uploaded to Feishu until it passes both checks.
- For each approved configuration-derived raw segment, call the approved video model with the exact approved segment prompt and no more image inputs than the current catalog allows. Save the exact submitted text in `video-generation-prompts.md` and in the approved Feishu video-prompt field before submission. Preserve the script, product facts, segment prompt, board, aspect, and user constraints unchanged. Assemble the chronological segments to the approved configuration target; preserve the individual clips as review candidates and never overwrite them. For an approved original or `结构复刻` package, never introduce a reference video after approval; for `钩子复刻`, never introduce reference media outside the approved `0.0–3.0s` hook.
- Every job is asynchronous. Use `flow_wait_job(job_id)` through the Job deadline; `queued`, `submitting`, and `active` are in progress and must not be treated as failure. Do not invent a progress percentage. Call `flow_get_job_result` only after `succeeded`, then promptly record/download the returned result URL according to the run's delivery convention. On terminal `failed`, `cancelled`, or `timed_out`, retain the error and stop; do not silently retry, switch models, or regenerate another segment.
- Use an idempotency key of 16–128 characters that is unique to the exact content ID, artifact name, and request digest. Reuse the **same** key only to recover from an uncertain/retried submission of unchanged payload; a deliberate regeneration uses a new artifact/attempt key. Record the key hint and job ID, but never store credentials.
- Do not publish, share, delete, overwrite, assemble, or spend credits beyond the explicitly requested generation. Keep returned clips as review candidates until the user directs a later assembly or distribution step.

### TTS generation mode and timing

- Confirm the complete approved script, voice, and speed before generating audio.
- Choose the mode deliberately:
  - **Continuous narration (default for dense copy):** generate the complete script as one TTS track. This preserves context, voice consistency, and natural conversational rhythm. Do not weaken the script into generic short slogans merely to imitate a reference timing slot.
  - **Slot-locked narration:** use only when the user requires exact per-shot starts. Generate each line separately and place it at the original line start; never make the next line follow the previous generated clip's actual end.
- For continuous narration, the final downloaded/decoded audio is the timing authority. Use `ffprobe` on the downloaded file; do not rely on a provider's displayed duration.
- If the voice is still too slow after sensible pause editing, prefer a faster but clear model/voice or a revised generation setting. Do not make content deletion the first response.

### Natural pause trimming

- Optimise speed by removing generated silence before applying any global time-stretch. Preserve speech articulation and natural phrasing.
- Detect low-energy silence with an explicit, reviewable threshold. A useful starting point is below `-38 dB` for at least `80ms`; record the detected ranges and their total duration.
- Remove leading and trailing silence. For internal pauses, retain short pauses and compress only longer pauses toward roughly `100–120ms`.
- Do not reduce internal pauses to extreme values such as `60ms` by default: this can make adjacent phrases sound disconnected. Every trim setting requires a listening check.
- Re-probe the trimmed file and compare its duration with the target video before mixing. If it still exceeds the target, regenerate with a more suitable fast-speaking voice/model or setting rather than silently cutting meaningful words.

### Voice-over, music, and video assembly

- Match the chosen instrumental to the exact final-video duration and apply a short end fade.
- Mix the trimmed voice-over above the instrumental. Begin with the music low enough that every spoken word remains intelligible; audition and lower it further if it masks speech.
- Keep the voice-over at its intended start time. When continuous narration is used, a short music-only tail after speech ends is allowed.
- Never overwrite the original video or an earlier approved export. Export a separately named preview/final candidate and verify it has the expected video stream, audio stream, and duration.

### Subtitle alignment and rendering

- When the final TTS has been trimmed, do **not** reuse the reference-video timeline for subtitles. Run local ASR again on the final trimmed voice-over; use the ASR output primarily to obtain the real speech boundaries and build the subtitle timing.
- Use the approved script as a lightweight text-validation and correction layer, not as a replacement for the ASR timing. Correct clear ASR misrecognitions with the approved script and merge fragments that belong to one sentence; do not force wording that cannot be heard or invent a line that the audio does not contain. If the ASR and approved script conflict, follow the audible final audio and record the uncertainty.
- Save the timing-alignment JSON (`start`, `end`, `text`) and the SRT file as run artifacts before burning subtitles. Full manual rewriting is unnecessary when the ASR text is already accurate; the required outcome is a reviewable, audio-aligned timeline.
- Burn subtitles only when explicitly requested. Use white Chinese text with a dark outline and no shadow, and prefer a single readable line over forced multi-line wrapping.
- Tune subtitle size and vertical position against the actual output resolution, not a nominal font value. For the 496x864 mobile preview used here, `Microsoft YaHei`, `FontSize=10`, dark outline about `1.2`, and `MarginV=65` produced a small, single-line, raised-bottom placement. Treat these as a starting preset and adjust after visual review.

## Hook and structure replication workflows

### 钩子复刻

1. Fresh-read `内容策划任务.钩子复用素材`, `爆款视频`, `爆款视频链接`, the selected product, and the current original-rule configuration. If reusable hook media exists, use it as the only hook source; otherwise inspect only `0.0–3.0s` of the reference video.
2. Write `plan/hook-replication.md` with the source, exact hook time window, visual setup, action beat, rhythm, allowed product-logic substitution, and a statement that no source content after 3.0s was read or used. Route only the representative hook assets needed by each Job, staying within the R2I limit of 10 or the Omni R2V limit of 7.
3. Generate the opening hook and the remaining original-UGC continuation as one coherent storyboard package. The continuation must follow current product facts and original-rule configuration; it must not resemble or derive from the reference-video body.
4. Record the approved hook description in `前 3 秒钩子`, the independent continuation in `叙事结构`, and `钩子复刻` in `改编角度` and `Agent 自检`. Deliver only the common final-generation boards, `quality-report.md`, `package.json`, and `plan/hook-replication.md`; do not create RF evidence, source contact sheets, replacement contact sheets, or masters.

### 结构复刻

1. Fresh-read the reference video, selected product, and the current original-rule configuration. Analyze the reference only to derive phase timings, narrative functions, proof targets, and transition purposes.
2. Write `plan/structure-plan.json` with ordered phases containing only `start`, `end`, `narrative_function`, `proof_target`, and `transition_purpose`. Do not include source-frame paths, visual descriptions, source wording, audio, subject details, scenes, or product interactions.
3. Generate a wholly new hook, script, scenes, actions, and storyboard from that skeleton plus current product facts and original-rule configuration. Do not pass reference video, frames, screenshots, audio, or source contact sheets to Flow2API.
4. Record the new hook in `前 3 秒钩子`, the phase skeleton in `叙事结构`, and `结构复刻` in `改编角度` and `Agent 自检`. Deliver only the common final-generation boards, `quality-report.md`, `package.json`, and `plan/structure-plan.json`; do not create RF evidence, source contact sheets, replacement contact sheets, or masters.

## Full replication workflow

1. Run `scripts/preflight.py`; transcribe audio when available. A transcription failure does not block a storyboard-only visual run, but record it.
2. Read `references/stage-1-evidence.md`; create one-second evidence, trim evidence, a source-shot list, a style profile, a breakdown report, and `frame-time-map.csv`.
3. Write `plan/user-constraints.md` and `plan/product-interaction-facts.md`. When needed, read `references/interaction-substitution-protocol.md` and write `plan/interaction-substitutions.md`.
4. Read `references/stage-2-light-adaptation.md`, `references/frame-batch-replacement.md`, and `references/storyboard-spec.md`. Create a per-RF plan and fixed `6+...+tail` `plan/reference-batches.json`.
5. Make source contact sheets and read `references/stage-3-full-package.md` plus `references/dynamic-master-review.md`. Use Flow2API MCP Banana Pro for local replacement and save `batch-image-prompt.md` plus `replacement-contact-sheet.png` for every batch.
6. Review each source/replacement pair for product facts, shot fidelity, per-panel product scale, and sheet/panel geometry. Regenerate the same batch once for a failure. Stop if it still fails.
7. Write `plan/master-groups.json`, validate that its RFs are chronological, complete, unique, balanced, and at most 15 per master, then run `scripts/assemble_storyboard_masters.py` from accepted current-run batches only.
8. Deliver the evidence package, retained batch audit artifacts, and configuration-profile generation boards defined by `references/delivery-contract.md`; run `scripts/validate_generation_storyboards.py --profile plan/content-system-config-snapshot.json` on every board and record passing dimensions in `quality-report.md`. Upload only passing boards, fresh-read the record to verify the attachments, then archive the required script, prompts, masters, paths, fingerprint, and self-check in Feishu as `待审核`.

## Full-replication input isolation

- Copy `style_fingerprint` and `anti_style_constraints` verbatim into each batch prompt.
- A batch request may contain only its source contact sheet, product asset, applicable subject asset, approved per-frame plan, and user constraints. Never use another batch or a prior replacement sheet as generation input.
- State the exact panel count, 3x2 full-batch layout or horizontal tail layout, reading order, no text, no watermark, and no UI. State that the output is delivered directly as a contact sheet, not an exact splittable pixel canvas.
- Use original video frames only for this local replacement task. Never pass them to a final video model.

## Delivery

Read `references/delivery-contract.md`. For `全量复刻`, deliver the breakdown report, frame-time map, product facts, batch plan, `plan/master-groups.json`, interaction substitutions when applicable, every batch source/replacement contact sheet and review, final-generation boards, `quality-report.md`, and `package.json`. For `钩子复刻`, deliver `plan/hook-replication.md`, product facts, final-generation boards, `quality-report.md`, and `package.json`; for `结构复刻`, replace it with `plan/structure-plan.json`. Upload all boards to Feishu, verify the attachment set by fresh read, then stop at `待审核`.

## Scripts

- `scripts/probe_video.py <video>`: metadata.
- `scripts/preflight.py [--require-asr]`: environment check.
- `scripts/snapshot_content_system_config.py --target-duration <seconds> --image-model <key> --video-model <key> --image-max-inputs <n> --video-max-inputs <n> --out <snapshot.json>`: reads and validates the unique active content-system configuration into the required local snapshot.
- `scripts/extract_frames.py <video> --out evidence/raw-second-frames --interval 1.0`: source frames.
- `scripts/make_contact_sheet.py <frame-dir> --out <png> --cols 3 --thumb-width 720 --plain`: full-batch source contact sheet with no labels, borders, or gutter.
- `scripts/assemble_storyboard_masters.py <run> --out <dir>`: validates accepted batch geometry, balances chronological RFs into masters of at most 15 frames, and writes default master contact sheets plus manifests.
- `scripts/assemble_generation_storyboard.py`: legacy utility; do not use for final-generation boards unless the user explicitly requests local panel composition.
- `scripts/validate_generation_storyboards.py --profile <config-snapshot.json> <board...>`: blocks final-generation-board upload unless it matches the active configuration snapshot's grid and panel ratio.
- `scripts/feishu_attachment_uploader.py`: reusable Feishu media client; supports app credentials or an existing tenant token, local files or bytes, automatic image/file parent type, and automatic multipart uploads.
- `scripts/download_feishu_media.py --file-token <token> --out <path>`: downloads one approved Feishu media asset using only this skill's `.env`.
- `scripts/prepare_flow_inputs.py --asset-plan <json> --out <json>`: downloads or reuses approved assets from the skill-local cache, produces uncropped Flow-compatible image renditions and Base64 sidecars, and writes a per-run cache manifest for audit and reuse.
- `scripts/upload_feishu_attachments.py --app-token <app> --table-id <table> --record-id <id> --field <field> <file...>`: CLI wrapper that uploads files and replaces a Base attachment field.
- `scripts/transcribe_audio.py` and `scripts/align_transcript.py`: audio evidence.

## Branching-chain lifecycle sweep

Run `scripts/lifecycle_sweeper.py` with `config/lifecycle-policy.json` for the four branching tables only: `内容母题`、`创意候选`、`内容策划任务`、`内容库`. The default is a read-only dry-run; `--apply` is the explicit write gate. Evaluate bottom-up (`内容库` → `内容策划任务` → `创意候选` → `内容母题`), set the existing lifecycle status to `已归档`, and write `归档时间` plus `归档原因`. Never delete, move, copy, or silently repair records; skip `归档保护=true` and report deferred cases. Products, `主体资产库`, and `最终成片` remain human-maintained; `最终成片` is read only during the sweep. Keep active/default views filtered to the active status and use the archive view for history. Read [references/lifecycle-archive.md](references/lifecycle-archive.md) before changing the policy.

- `scripts/lifecycle_sweeper.py [--check-schema] [--apply] [--json]`: validates the lifecycle fields and performs a bottom-up soft-archive dry-run or explicit apply.
