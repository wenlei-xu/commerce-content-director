---
name: auto-video-storyboard-v3
description: Create UGC ecommerce short-video storyboard packages for Douyin, Xiaohongshu, and Pinduoduo. Use to expand a broad Feishu `内容母题` into scored `创意候选` and converge one into an original planning task, or to create original UGC and hook, structure, or full replications. Read confirmed product facts and current Feishu original rules; use Flow2API MCP's Banana Pro for storyboards and Omni for approved named 20-, 30-, or 40-second video generation. Never use LibTV or browser/UI automation for final-video generation.
---

# UGC ecommerce storyboard planning

Work in exactly one generation mode. `内容母题扩散` is a pre-planning operation, not a generation mode: it may create Feishu candidate records and, after its explicit convergence rule is met, one original planning task; it must not generate images, boards, videos, or `内容库` records. Stop after every required final-generation board—and, for `全量复刻`, every required storyboard master—has been uploaded to the linked Feishu record and a fresh read confirms the expected attachments. Only then set `审核状态 = 待审核`. A human must change that record to `通过` **and explicitly name that exact `content_id` or Feishu record for video generation** before any final-video work can begin.

## Modes

- **逐帧复刻**: Use a readable reference video and an identifiable product asset. This mode requires the linked `内容策划任务.策划模式`: `钩子复刻` reuses only the opening hook; `结构复刻` reuses only the sales narrative skeleton; `全量复刻` preserves source shot order, scene, action, camera, lighting, rhythm, and mobile-video texture. Replace only the product and the pixels or interaction logic that conflict with confirmed product facts. Follow the selected strategy contract and workflow below.
- **原创 UGC 策划**: Do not use a reference video. If the user did not explicitly say `复刻`, select `原创` automatically and do not ask the user to choose a mode. Resolve the product directly from the `产品` table, then read its confirmed facts and anchor plus the current Feishu original-rule configuration. If the user names an existing `内容策划任务`, read its original-only creative fields as additional direction; never require that task's `产品` relation as the product lookup path. Produce the script, per-shot image prompts, and final storyboard masters. Read content history only when the user explicitly requests avoidance of recent content or differentiation; similarity is advisory, never a rejection gate. Follow [references/ugc-original-planning.md](references/ugc-original-planning.md) for the hot-update loading contract. Authentic phone-video texture must support proof and conversion, never replace them with lifestyle or beauty-shot pacing.

For an ordinary original task, generate and score candidates internally, retain only the selected direction and decision rationale in `Agent 自检`, and submit one finished package for review. The exception is an explicitly requested `内容母题扩散`: write every qualified candidate to the `创意候选` table and follow its configured convergence rule. Do not create a storyboard package while a mother topic is still expanding or awaiting manual selection.

### 内容母题扩散

Use this operation only when the user explicitly asks to expand a broad direction, or explicitly names a `内容母题` record for expansion. Read [references/content-strategy-and-assets.md](references/content-strategy-and-assets.md) and [references/ugc-original-planning.md](references/ugc-original-planning.md) before creating or updating candidates.

- Require one `内容母题` record with `产品`、`平台 / 账号`、`大方向 / 营销目标`、`期望候选数`、`收敛方式`、`优先级` and `扩散状态=待扩散`. `期望候选数` must be an integer from 3 to 12; `收敛方式` is exactly `人工筛选` or `自动 Top 1`.
- Fresh-read the linked product, optional subject asset, and the single current original-rule record before ideation. Product hard facts, compliance boundaries, and subject-identity requirements apply equally to candidates.
- Create exactly the requested number of qualified `创意候选` records. Each candidate must be linked to its mother topic, include every original creative field, six 1–5 scores, a calculated arithmetic-mean `综合评分`, `评分说明`, and `候选状态=备选`.
- For `人工筛选`, set the mother topic to `候选待确认` and stop. Create no `内容策划任务` until a fresh read shows exactly one linked `入选候选` and that candidate has `候选状态=入选`.
- For `自动 Top 1`, choose the highest qualified `综合评分` candidate; break ties by product fit, evidence density, then conversion strength. Mark it `入选`, write it into `入选候选`, set the mother topic to `已收敛`, and create exactly one original task.
- Create an original task only from the selected candidate. Copy its creative fields; copy product, platform/account, priority, optional subject asset, and creation requirements from the mother topic; set `策划模式=原创`; link `来源创意候选` to that candidate. Mark the candidate `任务创建状态=已创建` and the mother topic `扩散状态=已收敛`. Do not overwrite an existing linked task or create a second task for the same candidate.

### Planning-mode contract

Use the user's wording to select the mode. `内容母题扩散` is the only pre-planning exception and may create only an `原创` task after convergence. For generation, when the user does not explicitly say `复刻`, default to `原创`; do not stop to ask the user to choose a mode. When the user explicitly says `复刻`, search the Feishu `内容策划任务` table for the named task (or the best exact product/task match), read its non-empty `策划模式`, and use that value to select `钩子复刻`、`结构复刻` or `全量复刻`. A supplied reference video or link never selects a mode by itself.

- **钩子复刻**: Reuse only the opening hook's visual setup, action and rhythm for `0.0–3.0s`. If `钩子复用素材` is populated, it is the preferred hook source; otherwise use only the first three seconds of `爆款视频` or `爆款视频链接`. Produce the remaining duration as original UGC from the current product facts and original-rule configuration. Do not inspect, transcribe, quote, describe, or use any source-video content after 3.0 seconds.
- **结构复刻**: Reuse only the chronological selling skeleton: phase timing, each phase's narrative function, proof target, and transition purpose. Do not reuse the reference's hook image, individual shot, scene, action, subject identity, product placement, wording, audio, or visual prompt. Create every visual and line for the current product from product facts and original-rule configuration.
- **全量复刻**: Use the existing frame-by-frame workflow unchanged. This is the only strategy that may create RF contact sheets, replacement contact sheets, storyboard masters, per-frame plans, or reference-led script adaptations for the whole source video.

For every strategy, archive the selected value in `改编角度` and state it in `Agent 自检`. Never combine strategies in one `content_id`.

### Product interaction hard gate

Treat confirmed product loading paths as hard interaction constraints, not merely selling-point descriptions. Fresh-read the product field `产品审核要求` together with `产品硬事实与禁忌` and `生成注意事项` before review. If that field is present, interpret its `PASS`、`WARN｜人工复核`、`FAIL` sections as product-specific acceptance guidance; an empty field uses the strict defaults below. A product-specific `WARN｜人工复核` may remain reviewable when no product fact is plainly contradicted, but it must be recorded in `quality-report.md`, `package.json`, and the Feishu review notes. It never authorizes final-video generation by itself. Product-specific guidance may add constraints or define an ambiguity for human review, but cannot weaken fixed safety, authenticity, subject-continuity, geometry, or final-generation requirements. For a product whose confirmed loading path is the bottom dispensing hole, the bottom hole is the **唯一装粮路径**: every loading shot must show the product tilted or inverted as needed, with treats entering through the bottom round hole. The leaf crown, side lattice openings, caps, lids, and separable parts must not participate in loading. Do not use vague prompt language such as “把粮放入玩具” or “给玩具装粮”; every applicable prompt must state the exact path, for example: “玩具倒置/倾斜，粮粒从底部圆形漏食孔塞入，叶冠全程不参与，侧面格栅不作为入口”。

Before accepting any generated storyboard, review each loading and dispensing panel separately for: (1) the unique loading path, (2) the visible direction of entry, and (3) unchanged connected product structure. A top-loading action, side-lattice loading action, detached crown/cap/lid, or other plainly contradicted product fact is a hard failure. If the product field explicitly classifies the case as `WARN｜人工复核` and the image does not show a plainly wrong path, keep the board local or upload it only through the documented human-review exception, with the warning preserved; do not silently call it PASS. A review-only board containing timing annotations or other review labels must never be passed to Omni as a final-generation input; regenerate a clean board before video generation. Do not set `通过` or start final-video work while any WARN remains unresolved.

### Subject identity hard gate

Treat a recurring person, animal, or other identifiable subject as a required visual asset, not as a prompt-only description. A subject is recurring when it appears in two or more panels, crosses a raw-segment boundary, or is the named actor in the task's proof scene. The task schema may leave `主体资产` empty; an empty task field is not a blocker because the agent must resolve a suitable asset from `主体资产库` automatically.

Before generating any creative candidate, script, image prompt, or storyboard image:

- Inspect `内容策划任务.主体资产` first. If it names a valid record, use that record. If it is empty or ambiguous, query `主体资产库` and automatically choose one record with `状态=可用`, a non-empty `主体锚点`, and a stable `主体身份描述`; do not ask the user merely because the task field is empty, and do not infer identity from the product image. Select deterministically: (1) exact subject name/type/role match in task text, (2) closest match to the task's proof scene, default scene, and product context, (3) stable first record by `record_id` when candidates remain tied. If no eligible record exists, stop and report `主体资产库无可用匹配资产`.
- Fresh-read exactly the selected `主体资产库` record before generation. Do not create or silently modify a task or subject record as part of selection; keep the selected mapping in the local package and link it to the content version during the normal post-validation archive step.
- Record the selected subject record ID, anchor filename, selection rationale, and an identity-description hash in the local package and `generation-jobs.json`. The mapping from subject name to asset record must be explicit when more than one subject exists.
- Pass the same subject anchor together with the product anchor to **every** storyboard-generation Job containing that subject. Keep the same subject identity description and input filename across all boards; never rely on cross-Job memory. Keep within the three-image Flow2API input limit.
- If the concept intentionally has no recurring subject, write `主体身份不锁定` in the local package before creative generation and do not write prompts that imply the same person/animal continues across panels or segments.

After generation, review subject continuity independently of geometry: face, coat/color, markings, breed/type, body size, and distinctive accessories must remain consistent across panels and segment boundaries. Any unexplained identity drift is a hard failure. Regenerate the affected board once with the same subject anchor and prompt contract; if it still fails, stop and keep the package local. Do not upload or set `待审核` until this gate passes.

### Original-derived planning ordering

Before generating any creative candidate, script, image prompt, or storyboard image in **原创 UGC 策划**, `钩子复刻` continuation, or `结构复刻`, fresh-read the current original-rule configuration from the Base's `原创规则` table (`table_id=tblOeAQHZeY9sr0y`) and run the subject identity hard gate above. Use only `平台合规禁忌`、`通用表达边界`、`必须检查项` and `账号长期定位`; do not derive creative direction from this table. In original UGC, all creative direction comes from the linked `内容策划任务` whose `策划模式=原创`, including its original-only fields. Save the exact four-field snapshot, record ID, and content hash in `plan/creative-rules-snapshot.md` and summarise it in `Agent 自检`.

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
  each operator must set that path in their own MCP registration. Its secrets
  remain in ignored `.env` files. MCP configuration changes require a
  Codex/Hermes restart because tool discovery has no hot reload. Do not print,
  copy, or commit either the bridge token or the gateway key.
- Use Flow2API MCP only: **Banana Pro** for images and **Omni** for final video. In the MCP, Banana Pro's exact portrait image key is `gemini-3.0-pro-image-portrait`; Omni's exact portrait video key is `omni_portrait`. Do not silently substitute another model.
- A complete deliverable video must target **20, 30, or 40 seconds**. Omni produces chronological **10-second raw segments**, so submit respectively 2, 3, or 4 segments (20, 30, or 40 raw seconds). Assemble the segments chronologically to the exact requested duration; no terminal trim is required.
- Omni generates one 10-second segment at a time. Create one final-generation storyboard board per raw segment, with **exactly four chronological panels**. Assign an explicit start and end to every panel; their durations are flexible and must sum to 10 seconds. Choose durations from the action, evidence density, and rhythm—do not force every panel to 2.5 seconds. Maintain action continuity at every segment boundary.
- Final-generation boards use a 2x2, zero-gutter grid with exactly four chronological panels. Every panel must be **portrait 9:16**. Do not impose or validate a separate board-canvas ratio; the zero-gutter grid geometry follows from the panel dimensions. State the 9:16 panel requirement explicitly in every board-generation prompt. A review-only board may retain timing annotations when the user explicitly requests human review or the product audit policy marks them `WARN｜人工复核`; label that artifact as review-only, preserve the warning, and never pass it to Omni. Before any final-video work, replace it with a clean no-text/no-watermark/no-UI board and validate that replacement.
- Generate the complete four-panel board in **one** `flow_submit_image(model="gemini-3.0-pro-image-portrait", ...)` request per raw segment. The prompt must state the four chronological panels, each panel's exact start–end time and duration, portrait 9:16 panel requirement, left-to-right/top-to-bottom order, 2x2 zero-gutter layout, and no text/watermark/UI. Do not submit four independent panel jobs or compose a board locally. Immediately before upload, run `python scripts/validate_generation_storyboards.py <board...>`; record each `PASS` with board filename and dimensions in `quality-report.md`. A failure means the board is not reviewable: regenerate that board once and stop if it still fails.
- Every Flow2API Job is asynchronous. After submission call `flow_wait_job(job_id)` and wait through the Job deadline (normally 1800 seconds) before judging the outcome. `queued`, `submitting`, and `active` are non-terminal in-progress states, not failures; never create a replacement Job, switch models, or report a generation failure while any of them remains. Only `succeeded`, `failed`, `cancelled`, or `timed_out` is terminal. If `flow_wait_job` returns `wait_timeout=true`, retain the same job ID, record its latest state, and report that it is still non-terminal—do not resubmit. Call `flow_get_job_result` only after `succeeded`.
- `RF` one-second evidence is an audit requirement only for `全量复刻`. Do not confuse it with final-generation boards: RFs document the reference, while the four-panel boards direct Omni.
- Name boards `generation-storyboards/Segment-01_00-10s.png`, `Segment-02_10-20s.png`, and so on. Attach every board to Feishu and include the raw segment range, final retained range, and four panel prompts in `分镜摘要` and `画面生成 Prompt`.

## Feishu content, strategy, asset, and review gate

Use the **短视频内容创意库** Base for every run: <https://mcokh0mq9c.feishu.cn/base/QQ1ib0FTHahCUhstRH8cVx9in7S>. Its `内容库` table is `tblGPsdyzMG0o6zP`; its `内容策划任务`、`产品` and `最终成片` tables are defined in [references/content-strategy-and-assets.md](references/content-strategy-and-assets.md). Read that reference before creating, revising, reusing, or delivering content; read [references/ugc-original-planning.md](references/ugc-original-planning.md) for original-mode rule configuration.

- Use `内容策划任务` for task-level direction, not as the product search index. `内容母题扩散` is the sole approved exception to ordinary task creation: after its documented convergence gate, it creates one `原创` task from the selected candidate. When the user does not say `复刻`, select `原创` automatically; if an original task is specified, read its original-only fields (`目标人群`、`痛点`、`核心卖点`、`钩子`、`叙事节奏`、`证明场景`、`核心创意`) but do not require its `产品` relation to locate the product. When the user explicitly says `复刻`, the task is required because its `策划模式` and reference-media fields define the replication boundary. `主体资产` is optional only when no recurring identifiable subject appears; it becomes mandatory under the subject identity hard gate above. `原创` requires original-only fields; `全量复刻` and `结构复刻` require `爆款视频` or `爆款视频链接`; `钩子复刻` requires either `钩子复用素材` or `爆款视频` / `爆款视频链接`. Automatically infer the replication boundary and v1/v2/v3 plan only after reading the explicit replication task. Each version is a separate `内容库` record and `content_id`; link it to the applicable `内容策划任务` and always link it to the directly resolved `产品`, then state `版本号` and `改编角度` as the selected mode. Do not create or update a content-planning task as a side effect of storyboard generation; create or revise one only when the user explicitly requests it, except for the selected-candidate mapping in `内容母题扩散`.
- Before using a product, search the Feishu `产品` table directly by the user-provided `产品名称` or `产品ID`; do not search for the product only inside `内容策划任务` and do not treat a task's product relation as the sole source of truth. Resolve exactly one product record, then fresh-read it and require `状态=可用`, a non-empty `默认产品锚点`, and consistent `产品硬事实与禁忌` plus `生成注意事项`. Also read `产品审核要求` when present; snapshot its text in the local package and apply its `PASS`、`WARN｜人工复核`、`FAIL` policy only to product-specific review. If no record, multiple ambiguous records, or a task/product conflict is found, stop and report the concrete block. Select each content argument from its `核心卖点`、`目标人群`、`典型痛点`、`典型使用场景` and `可用表达 / 可用宣称`; never use an item in `禁用表达 / 禁用宣称`. Do not read local product-route files or a file-by-file asset table as a substitute. Run the subject identity hard gate before any creative generation. A linked `主体资产库` record is mandatory whenever the storyboard uses a recurring subject; require `状态=可用`, a non-empty `主体锚点`, and a stable `主体身份描述`, then pass that same subject anchor together with the product anchor to every applicable storyboard-generation job and preserve the identity description across all segments. In replication mode, reference media belongs directly in the linked `内容策划任务.爆款视频` attachment or `内容策划任务.爆款视频链接`, and reusable hook media belongs in `内容策划任务.钩子复用素材`; original mode must not read or use these fields.
- Create a local `content_id` and run package first. **Do not create, update, upload attachments to, or otherwise write a `内容库` record while any required final-generation storyboard is missing, non-terminal, failed, absent from disk, or has not passed `validate_generation_storyboards.py`.** This includes placeholder records and partial script/prompt writes. Keep the package local and record the block in `quality-report.md` and `package.json`.
- Only after every expected board exists, has exactly four chronological 9:16 panels, has a recorded validator `PASS`, and has passed per-panel interaction/identity/text review, create the new `内容库` record for a new version (or update the same rejected record). If the only remaining issue is an explicit product-level `WARN｜人工复核`, and no fixed global rule or plainly contradicted product fact is present, the user-authorized human-review exception may archive/upload the board with the WARN preserved in `审核意见`; it must not be marked `通过` or used for Omni. Review-only annotations such as timing labels must be removed in a clean replacement board before final-video generation. In that single post-validation archive step, write the final script, `画面生成 Prompt`, creative fields, product-audit snapshot, content fingerprint, `Agent 自检`, selected product image, every final-generation board, and, for `全量复刻`, all final storyboard master attachments. Before writing `待审核`, fresh-read the record and verify that every expected board attachment is present.
- Upload all reusable product images into the relevant `产品` attachment fields; for replication, upload the reference video directly to `内容策划任务.爆款视频` or provide `内容策划任务.爆款视频链接`. In original mode, do not upload reference media to the task. Upload every Flow2API final-generation board to `最终分镜图` **only after the 9:16-panel validator has passed**. When the Feishu MCP exposes record CRUD but no media-upload tool, use the portable client in `scripts/feishu_attachment_uploader.py` through the CLI wrapper `scripts/upload_feishu_attachments.py`. It has no browser or workspace-specific Base dependency: authenticate with `FEISHU_TENANT_ACCESS_TOKEN`, or with `FEISHU_APP_ID` and `FEISHU_APP_SECRET` supplied as environment variables or through `--env`; choose `bitable_image` for images and `bitable_file` for other media; and write the returned attachment tokens to the named record field. Files above 20 MB automatically use Feishu's multipart upload flow. Never print credentials or tokens.
- Example: `python scripts/upload_feishu_attachments.py --app-token <app_token> --table-id <table_id> --record-id <record_id> --field 最终分镜图 <Segment-01.png> <Segment-02.png>`. Do not substitute a local path, a cloud-document link, or a guessed token for an attachment upload. `FEISHU_APP_TOKEN` and `FEISHU_TABLE_ID` may be used instead of the two CLI flags.
- Perform a fresh record read and verify non-empty attachment tokens, filenames, and a count matching the expected segment count. A local path is supplementary evidence only.
- If attachment upload is unavailable or fails, do **not** set `待审核`; record the failure, keep the package local, and report the block.
- `待审核` means stop. Do not submit Flow2API image/video jobs for the final package, generate TTS, or burn subtitles.
- `拒绝` means read `审核意见`, revise the same concept, regenerate the affected script/prompts/storyboards, and return it to `待审核`.
- `通过` is an eligibility state, not a generation command. Generate a final video only when a fresh lookup shows the exact named record has `审核状态 = 通过` **and** the user explicitly instructs generation for that same `content_id` or record. Never choose an approved record yourself or infer authorization from a generic request such as “generate the video”.
- After every named, approved final-generation segment has succeeded, assemble the exact requested 20-, 30-, or 40-second video and technically verify its video stream, audio stream when requested, and duration. Only then create one `最终成片` record linked to that exact `内容库` record. Write `成片名称`, a unique `成片ID`, `内容版本`, `视频时长（秒）`, and `生成时间`, then attach only the complete publishable video to `最终视频`. Do not create a final-film record for failed jobs, raw segments, retries, or unverified assemblies. For uploads up to 20 MB, use `scripts/upload_feishu_attachments.py`; above 20 MB, use a verified multipart upload or the Feishu UI, then verify the attachment token, filename, and playable file before reporting delivery.

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
- Treat user-stated product structure, connections, loading path, and prohibited actions as hard facts. When source action conflicts, write an interaction substitution first. For a bottom-hole feeder, show the side lattice and bottom hole as one coherent connected structure, with treats entering the bottom hole; do not require the whole product to be visible. Never use side lattice openings, caps, lids, or separable parts as the loading route.
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
- Product facts require user confirmation or supplied asset evidence. For example, a one-piece bottom-hole feeder must not be described as opening a lid or as a separable design; use its confirmed loading route instead.
- Keep user-confirmed claims verbatim where appropriate (for example, material, odour, softness, and gum-safety claims). Do not introduce unconfirmed claims.
- Retain each corrected script line with the original `start` and `end` timing, even when its replacement wording differs. Timing-fit and TTS decisions are handled later; script quality is not sacrificed at this stage.

### Flow2API MCP generation execution

- Generate final video only when the user explicitly requests it for a named `content_id` or record **and** a fresh Feishu lookup shows that exact record has `审核状态 = 通过`; otherwise this skill remains storyboard-first. This rule applies equally to original and frame-by-frame replication modes.
- Before submitting anything, call `flow_get_service_health` and `flow_list_models`. Require available keys `gemini-3.0-pro-image-portrait` for storyboard panels and `omni_portrait` for final video. If either is unavailable, stop and report the concrete availability block; do not fall back to another model.
- Use `flow_submit_image` with Banana Pro once for each four-panel storyboard board. A request may include at most three approved image inputs; always include the approved product anchor and, when a recurring subject is present, the exact selected subject anchor plus only any remaining reference/scene inputs needed for that board. Keep its exact board prompt, per-panel timing, model, input filenames, subject record ID, identity hash, content ID, job ID, and result URL in `generation-jobs.json`.
- Download the returned board without cropping, splitting, resizing, or locally composing it. Validate it, then inspect all four panels separately for timing order, product identity, hard interaction facts, and text/UI contamination. No generated board may be uploaded to Feishu until it passes both checks.
- For each approved 10-second raw segment, call `flow_submit_video(model="omni_portrait", ...)` with the exact approved segment prompt and no more than three approved image inputs (normally the validated segment board and the product anchor). Preserve the script, product facts, segment prompt, board, aspect, and user constraints unchanged. Assemble the chronological segments to the approved 20-, 30-, or 40-second target; preserve the individual clips as review candidates and never overwrite them. For an approved original or `结构复刻` package, never introduce a reference video after approval; for `钩子复刻`, never introduce reference media outside the approved `0.0–3.0s` hook.
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

- When the final TTS has been trimmed, do **not** reuse the reference-video timeline for subtitles. Run local ASR again on the final trimmed voice-over to obtain its real speech boundaries.
- Treat ASR as timing evidence, not final copy. Replace ASR mistakes with the approved script text, and merge ASR fragments that belong to one approved sentence.
- Save both a corrected timing-alignment JSON (`start`, `end`, `text`) and an SRT file as run artifacts before burning subtitles.
- Burn subtitles only when explicitly requested. Use white Chinese text with a dark outline and no shadow, and prefer a single readable line over forced multi-line wrapping.
- Tune subtitle size and vertical position against the actual output resolution, not a nominal font value. For the 496x864 mobile preview used here, `Microsoft YaHei`, `FontSize=10`, dark outline about `1.2`, and `MarginV=65` produced a small, single-line, raised-bottom placement. Treat these as a starting preset and adjust after visual review.

## Hook and structure replication workflows

### 钩子复刻

1. Fresh-read `内容策划任务.钩子复用素材`, `爆款视频`, `爆款视频链接`, the selected product, and the current original-rule configuration. If reusable hook media exists, use it as the only hook source; otherwise inspect only `0.0–3.0s` of the reference video.
2. Write `plan/hook-replication.md` with the source, exact hook time window, visual setup, action beat, rhythm, allowed product-logic substitution, and a statement that no source content after 3.0s was read or used. Limit image inputs to the product anchor plus no more than two representative hook images.
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
8. Deliver the evidence package, retained batch audit artifacts, and Flow2API four-panel generation boards defined by `references/delivery-contract.md`; run `scripts/validate_generation_storyboards.py` on every board and record passing dimensions in `quality-report.md`. Upload only passing boards, fresh-read the record to verify the attachments, then archive the required script, prompts, masters, paths, fingerprint, and self-check in Feishu as `待审核`.

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
- `scripts/extract_frames.py <video> --out evidence/raw-second-frames --interval 1.0`: source frames.
- `scripts/make_contact_sheet.py <frame-dir> --out <png> --cols 3 --thumb-width 720 --plain`: full-batch source contact sheet with no labels, borders, or gutter.
- `scripts/assemble_storyboard_masters.py <run> --out <dir>`: validates accepted batch geometry, balances chronological RFs into masters of at most 15 frames, and writes default master contact sheets plus manifests.
- `scripts/assemble_generation_storyboard.py`: legacy utility; do not use for final-generation boards unless the user explicitly requests local panel composition.
- `scripts/validate_generation_storyboards.py <board...>`: blocks final-generation-board upload unless it forms a 2x2 grid whose four equal panels are individually portrait 9:16.
- `scripts/feishu_attachment_uploader.py`: reusable Feishu media client; supports app credentials or an existing tenant token, local files or bytes, automatic image/file parent type, and automatic multipart uploads.
- `scripts/upload_feishu_attachments.py --app-token <app> --table-id <table> --record-id <id> --field <field> <file...>`: CLI wrapper that uploads files and replaces a Base attachment field.
- `scripts/transcribe_audio.py` and `scripts/align_transcript.py`: audio evidence.
