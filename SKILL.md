---
name: commerce-content-director
description: "Run Feishu-driven ecommerce short-video production around a Markdown creation workbook: align approved voiceover with ASR-timed visual segments, write generation prompts at execution time, generate reusable clips or final films, and preserve resumable execution records."
---

# Commerce content director

This Skill runs the production chain:

~~~text
创作需求 → 创意方向 / 片段意图 → 10秒视频片段 → 草稿库（暂存） → 精选片段库（沉淀） →（可选）最终成片
~~~

For full-film work, one Markdown creation workbook is the content source that people and the Agent review together. It owns the approved spoken copy, ASR-timed segments, visual events, product facts used by the scene, continuity notes and links to generated results. Prompt text is written when a segment is prepared for generation and is saved as an execution record; it is not maintained as a second script. Clip-first work uses a lightweight clip brief and the draft/selected clip library contracts; it does not create a full-film workbook merely to generate a 10-second mother clip.

## Routing model

Resolve the request on four separate axes. They are not peer choices:

1. Select one **primary workflow** for the action being performed now.
2. Resolve one **production mode** when the work uses an external reference.
3. Load any **nested workflow** required by the primary workflow.
4. Load the **execution contract** declared by the selected workflow or mode.

Read the primary workflow first, then the active mode, nested workflow and execution contract. A mode extends a primary workflow; it never replaces that workflow.

### Primary workflows

- **Expand or lock creative directions**: read [creative-direction.md](references/workflows/creative-direction.md).
- **Analyze, distill, or choose an external short-video reference**: read [short-video-breakdown.md](references/workflows/short-video-breakdown.md).
- **Learn, review, or use reusable language patterns**: read [sentence-pattern-learning.md](references/workflows/sentence-pattern-learning.md).
- **Generate, revise, validate, or lock a script**: read [script-production.md](references/workflows/script-production.md).
- **Generate, select, or review video first frames**: read [first-frame-generation.md](references/workflows/first-frame-generation.md), then apply the active production mode and first-frame execution contract below.
- **Generate and accept a final video**: read [final-video.md](references/workflows/final-video.md).
- **Generate reusable 10-second video clips**: read [clip-production.md](references/workflows/clip-production.md), then apply the clip-library contract.
- **Archive the creative chain**: read [lifecycle.md](references/workflows/lifecycle.md).

### Production modes

- **Original production**: use `original` when the work does not reproduce an external source. No replication workflow is loaded.
- **Structure replication**: use `structure_replication` only when the user explicitly requests structure replication, then read [structure-replication.md](references/workflows/structure-replication.md). It preserves the story skeleton, commercial proof chain, relative pacing, emotional curve and transferable visual style while allowing product-conflicting shots, actions, subjects or scenes to change.
- **High-fidelity replication**: use `high_fidelity_replication` for a request that says only “复刻”, “replicate”, “参考原片做一条” or otherwise asks to reproduce a source without naming a narrower mode, then read [full-replication.md](references/workflows/full-replication.md). Product substitution is not a reason to lower fidelity. If compatibility fails, stop and require a new explicit mode decision; never downgrade the active run automatically.
- **Hook replication**: select `hook_replication` only when the user explicitly requests it. No active hook-replication workflow is defined; stop and report the unsupported mode instead of improvising or substituting another mode.

### Nested workflows

- [action-direction.md](references/workflows/action-direction.md) is a lightweight planning aid inside script production. It helps the Agent decide what belongs in each workbook segment; it produces no new data object or approval step. Read it directly only when the user requests that paragraph as the complete deliverable.
- [dialogue-copy-optimization.md](references/workflows/dialogue-copy-optimization.md) is the dialogue module used when drafting, reviewing, or revising spoken copy. It returns a local proposal and review report; the parent script workflow remains the only writer of the creation workbook and the Feishu-facing script record.
- The **scene asset library** is a reusable Feishu visual-context table, not a second script authority. Scene assets own spatial layout, lighting direction, lived-in capture treatment and usable activity area; the current product record and selected subject anchors still own product and identity. When a workflow needs a stable environment, query only `状态=可用` records with a valid `场景锚点`, select by market, scene type and current Beat, and record the selected scene asset ID and reason in the local run package.
- The **prop asset library** is a reusable roster of supporting physical objects that are not the current product, selected subject or scene. Props own object identity, state variants and controlled reuse tags; the script owns when the prop appears. Use tags for retrieval and bind a selected prop asset ID to the current Beat only when used. Read [prop-asset-library-contract.md](references/domain/prop-asset-library-contract.md) when creating or selecting props.
- The **draft clip library** is only the temporary staging and review area for complete generated 10-second mother clips. The **selected clip library** is the actual sedimentation destination: it stores independent extracted clips that are ready for reuse. These are reusable media libraries, not script records and not approval surfaces for a full film; read [clip-library-contract.md](references/domain/clip-library-contract.md) when creating, reviewing or writing either library. That contract also owns the canonical `产品 / SKU` identity rules and the prefixed `片段标签` convention for separating use, action, benefit and reuse scope.
- The **content interaction template library** is a cross-SKU Feishu knowledge table, not a workflow or a second script authority. Templates are optional behavior references; product records own `交互能力` and `关键结构锁`, alongside positioning and confirmed benefits. During script production, query only `模板状态=可用` templates when a behavior reference helps. Put the resulting action directly in the relevant workbook segment. Record a template reference only when one was actually used; otherwise use a product-derived action. The absence of a matching template is not a stop condition.

### Current product-library contract

The active Feishu `产品` table is intentionally compact. Use these fields as the product authority:

- identity and assets: `产品名称`, `产品ID`, `状态`, `默认产品锚点`, `产品三视图`, `产品细节图`, `产品场景图`, `其他产品素材`;
- content inputs: `一句话产品定位`, `核心卖点`, `目标人群`, `典型痛点`, `典型使用场景`;
- execution facts: `交互能力`, `关键结构锁`.

`交互能力` records what the product can visibly do in a real interaction. `关键结构锁` records only the few structural relationships that must survive generation, such as an integrated component, a fixed connection, a real loading opening or the absence of a sound module. Neither field is a script, a full compliance checklist, a prohibited-claims library or a creative idea bank.

Do not look for the removed product fields `可用表达 / 可用宣称`, `禁用表达 / 禁用宣称`, `产品硬事实与禁忌`, `生成注意事项` or `产品审核要求`. Do not recreate them under another name. Keep claims grounded in the current product record and the actual visible action; handle platform or publication review as a workflow-level check rather than adding another per-product policy field.
- The **script library** is a lightweight reusable-template reference library. Its `脚本类型` field is a controlled multi-select for retrieval, such as `带货转化`, `剧情内容` or `悬疑反转`; one template may carry more than one type. Its optional `参考视频` field is an active design reference when present: use it to extract transferable visual style, story structure, camera/viewpoint, shot scale, pacing, transitions and emotional curve for the template. When the user asks to use a script-library template, retrieve one matching approved complete script and treat its `完整口播` as a locked copy baseline in the workbook: copy it first, then allow only the smallest fact substitutions required by the selected product's name, verified material, verified function, interaction, subject/scene reference or grammar. Do not retain unsupported source features such as a squeak function or TPR material, and do not invent a replacement fact. Preserve the hook, sentence/line order, commercial proof sequence, rhythm, CTA position and wording wherever compatible; do not blend templates or optimize the copy by default. The run must compare the source voiceover with the working voiceover and stop if any change falls outside this whitelist or if a source claim conflicts with the current product and cannot be truthfully replaced. It does not replace the short-video breakdown library, product facts or the current workbook; it does not transfer the source product, logo, subject identity or unsupported claims, and it does not by itself authorize high-fidelity replication. Read [script-library-contract.md](references/domain/script-library-contract.md) when creating or classifying a script-template record.

### Execution contracts

- Every first-frame workflow and replication mode uses [first-frame-execution.md](references/first-frame-execution.md). First-frame images use GPT Image 2.5 exclusively through the configured ChatGPT2API MCP by default; never route image generation through Flow2API or silently change models/providers.
- For this project, first-frame image generation uses the standard Streamable HTTP MCP endpoint from `CHATGPT2API_MCP_HTTP_URL`; the configured cloud endpoint is `http://43.153.49.143:38300/mcp`, authenticated with `CHATGPT2API_MCP_HTTP_TOKEN`. Never write the token into this skill, prompts, manifests, command output or logs. Upload or import approved reference images as MCP assets first, then submit Jobs using ordered `input_asset_ids`.
- Final-video execution belongs to [final-video.md](references/workflows/final-video.md) and the contracts it names; it is not part of first-frame routing. Video model selection is fixed by Segment duration: every 4s, 6s, 8s or 10s Segment uses its exact confirmed Omni portrait model. Short Segments are not restricted to the final tail, and Segment-level arbitrary model overrides are forbidden.

### Final-video product reference routing

- For every final-video Segment, route the approved `product_anchor` as a required `input_asset_id` when submitting the video-generation Job, regardless of whether the product is visible in the Segment's starting first frame or planned action. Put `product_anchor` first, followed by the Segment's starting first-frame/subject reference(s), and describe only the product action, placement and critical continuity constraints needed for that Segment.
- Product anchoring is mandatory during video generation. When the anchor is present, do not over-describe or duplicate the product's visual design in the prompt; never rely on prompt text alone for product appearance, geometry, continuity or permitted interaction.

### Flow2API MCP routing

- External Codex final-video calls must use the standard MCP HTTP endpoint from `FLOW2API_MCP_HTTP_URL`; for the configured cloud deployment this is `http://43.153.49.143:38200/mcp`, authenticated with `FLOW2API_MCP_HTTP_TOKEN`.
- Before any final-video submission, upload each local approved reference once with `flow_upload_input_asset`, or import each public HTTPS reference with `flow_import_input_asset`; persist the returned gateway `asset_id` beside the Segment mapping and reuse it across all applicable Segments.
- Submit final-video Jobs and batches with only ordered `input_asset_ids` (or `input_asset_urls` when using the gateway's HTTPS import path). Never put `input_images`, `data_base64`, data URLs, or image bytes into `flow_submit_video` or `flow_submit_batch`. If an old MCP schema still exposes `input_images`, refresh/reconnect the MCP before submitting.
- If a submission returns `413`, do not retry the same payload. Treat it as an inline-image/request-size violation, verify the public MCP tool schema, move the references through the asset-upload/import tools, and resubmit with the same idempotency identity and only gateway asset IDs.
- Never use `http://43.153.49.143:38000/internal/mcp/v1` as an external MCP endpoint. Port `38000` is the Flow2API private bridge used internally by the MCP gateway; it is not the public MCP interface.
- Keep `FLOW2API_MCP_FLOW_BRIDGE_URL` only in the server-side MCP deployment configuration. When the standard MCP endpoint returns an error, diagnose the gateway/bridge boundary and do not bypass it by submitting directly to the private bridge.

### ChatGPT2API MCP routing

- External Codex first-frame image calls must use the standard MCP HTTP endpoint from `CHATGPT2API_MCP_HTTP_URL`; for the configured cloud deployment this is `http://43.153.49.143:38300/mcp`, authenticated with `CHATGPT2API_MCP_HTTP_TOKEN`.
- Before image submission, call `chatgpt_health` and `chatgpt_list_models`, and require the exact `gpt-image-2.5` model. Use `chatgpt_upload_input_asset` or `chatgpt_import_input_asset` for each approved reference, preserving role and order. Submit with `chatgpt_submit_image` for one item or `chatgpt_submit_batch` for a ready set, passing only ordered `input_asset_ids`.
- Do not put Base64 image data into a generation Job, call the internal `38210/internal/v1` gateway from outside Docker, or use the ChatGPT2API web port `3000` as the MCP transport. A missing/invalid MCP token, unavailable exact model, or failed asset upload is a stop condition.

## Shared invariants

Read only the invariants named by the selected workflow:

- [authority.md](references/invariants/authority.md) — schema and record authority.
- [scene-asset-library-contract.md](references/domain/scene-asset-library-contract.md) — reusable scene context and selection boundaries.
- [prop-asset-library-contract.md](references/domain/prop-asset-library-contract.md) — reusable prop identity, state variants and selection boundaries.
- [script-library-contract.md](references/domain/script-library-contract.md) — script-template classification and retrieval boundaries.
- [clip-library-contract.md](references/domain/clip-library-contract.md) — draft and selected clip library fields, states and writeback boundaries.
- [content-interaction-template-library-contract.md](references/domain/content-interaction-template-library-contract.md) — reusable interaction templates and script handoff.
- [script-workbook-contract.md](references/domain/script-workbook-contract.md) — Markdown creation workbook, segment format and ownership.
- [execution-record-contract.md](references/domain/execution-record-contract.md) — generated prompts, requests, results and resumable run evidence.
- [script-validation.md](references/invariants/script-validation.md) — blocking quality checks.
- [batch-creative-diversity.md](references/invariants/batch-creative-diversity.md) — batch-level creative collision checks.
- [product-execution-contract.md](references/invariants/product-execution-contract.md) — product action correctness.
- [language-policy.md](references/invariants/language-policy.md) — Thai/Chinese spoken-language locking and audio behavior.
- [knowledge-library-contract.md](references/invariants/knowledge-library-contract.md) — the two learning-library objects and their review boundaries.
- [video-classification.md](references/invariants/video-classification.md) — the multi-dimensional retrieval taxonomy for approved short-video breakdowns.
- [model-visual-text-recognition.md](references/invariants/model-visual-text-recognition.md) — model-vision-only screen-text evidence and the legacy OCR field contract.
- [execution-accounting.md](references/invariants/execution-accounting.md) — accepted films and execution limits.
- [mutation-and-recovery.md](references/invariants/mutation-and-recovery.md) — staged writes and resumable failures.

### Subtitle and screen-text separation

字幕与独立屏显是两条不同的轨道，任何脚本和人类可读渲染都必须明确区分：

- **字幕**只呈现最终获批口播台词的文字内容和顺序；不得改词、补写产品卖点、安全提醒、标题或 CTA。口播原文和 TTS 仍保留原标点，但字幕作为显示层默认去除句号、逗号、问号等标点，只跟随最终口播音频的时间轴。
- **独立屏显**是可选的，来自 `screen_texts`，用于用户明确要求的标题、标签、问题、安全提醒和 CTA 等未必被说出的文字；它不是字幕，不得被写入字幕轨。
- 默认不生成独立屏显：当用户只提供口播、要求直接按口播制作，或没有明确提出标题/卖点提示/安全提醒/CTA 屏显时，`screen_texts` 保持为空。不能因为脚本流程或模板存在该字段，就擅自补写屏显。
- 当用户说“字幕”时，默认只处理口播字幕；除非用户明确要求，不能把独立屏显混入字幕，也不能把独立屏显误称为字幕。
- 只有存在独立屏显时，人类可读脚本才需要增加 `独立屏显（非字幕）` 栏目；没有屏显时只展示 `字幕（口播文字）`，不要为了凑栏目写“无新增屏显”。

### User-provided spoken-copy lock

当用户提供了明确的口播原文并要求“直接使用”“按这段口播来”或同等意思时，口播文案自动锁定：

- 必须逐字、逐标点、按原顺序写入创作稿的 `口播` 区域；只允许按原文标点拆分显示行、分配时间和匹配画面。
- 不得改词、换句、润色、口语化改写、压缩、扩写、补充 CTA、替换产品称呼或擅自加入安全提示。
- `dialogue-copy-optimization` 只能做时间轴/画面证据检查，不得生成改写候选或自动优化；只有用户明确要求改写、优化、压缩或重新创作时，才能开启文案修订。
- 写入后必须校验所有台词按时间顺序拼接后与用户原文完全一致；不一致就停止，不得锁定脚本。

### Script-library spoken-copy lock

使用 `脚本沉淀库` 时，模板的 `完整口播` 默认视为锁定底稿，不得因为“顺口”“节奏更好”或“适合画面”而自行改写：

- 先原样复制模板口播，再做事实替换；允许替换项仅包括当前产品名称、已核实材质、已核实功能、主体/场景指代和由此产生的必要语法连接。
- 模板里当前产品没有的功能、材质或效果必须删除或替换为当前产品已有且已核实的事实；禁止保留来源产品的发声、TPR 等特征，也禁止凭常识补一个替代卖点。
- 禁止自行润色、压缩、扩写、换句、调序、重写 CTA 或改变卖点顺序。用户没有明确要求改写时，不得开启文案优化模块。
- 必须对比“模板完整口播”和“当前工作口播”。只要出现白名单以外的改动、无法处理的事实冲突或无法保持原句功能，就停止并报告冲突，不得继续生成脚本。
- `复用说明`只是内部提醒，不是改写授权；只有用户明确说“改写/优化/重新创作”时，口播才解除锁定，并按新的任务重新审核。

## First-frame prompt contract

### ChatGPT2API job-state interpretation

`text_review` is not人工审核、人工确认或首帧审批。它表示 ChatGPT2API 的上游返回了文本而不是图片；文本可能是内容政策提示、请求错误、拒绝说明或其他生成失败信息，前端可能把它显示为“审核”。凡是 `text_review`（包括 Job 仍显示 `active` 但最新上游状态为 `text_review`）都不得计为首帧完成，也不得等待人工审核；必须读取并保留文本/错误证据，将该请求视为缺失或失败输出。只有 Job 终态为 `succeeded`、存在非空 `result_asset_ids`，并且下载结果确实是图片字节时，才算生成成功。具体处理规则见 [first-frame-execution.md](references/first-frame-execution.md)。

The active image deliverable is a **video first frame**, not a multi-image board. Every configured production Segment produces one static 9:16 image representing only that Segment's entering state at local `t=0`, whether the Segment is 4s, 6s, 8s or 10s. Camera language remains required because the first frame establishes the video's starting viewpoint, framing and visual focus.

Every first-frame generation prompt should be concise, skimmable and use these blocks in this exact order:

1. `REFERENCE IMAGE ROLE` — identify each routed reference by input position and state which visual facts it owns. A product anchor owns product appearance; it must not be treated as a layout to copy.
2. `OUTPUT SPECIFICATION` — one 9:16 portrait first-frame image for the Segment's entering state at local `t=0`.
3. `CREATIVE INTENT` — what the viewer should notice, feel or initially misunderstand. The Agent derives this from the current workbook segment and the selected creative direction.
4. `CAMERA OPERATOR VIEWPOINT` — make the capture position and the filming person's presence concrete: camera height, viewpoint, framing, hand or body presence and visual focus.
5. `SCENE EVENT` — the single visible situation frozen at local `t=0`, including the relevant environment and continuity state. Do not describe the full video or chain future actions.
6. `SUBJECT PERFORMANCE` — the selected subject's visible identity, expression, pose and performance in this frozen moment.
7. `PRODUCT LOCK` — only the product placement, necessary continuity constraints and permitted product action relevant to this frame. When a `product_anchor` is routed, do not redundantly describe the product's appearance, color, material, texture, dimensions or detailed geometry; the routed anchor owns those facts. Mention only scene-specific placement, visible action or critical constraints that must remain legible, such as a required bottom treat hole.
8. `PHONE IMAGE TEXTURE` — concrete capture evidence such as handheld imperfection, auto-exposure, focus behavior, compression, household light and lived-in texture. Do not use “vlog” or “rough” as unsupported mood labels alone.
9. `NEGATIVE CONSTRAINTS` — preserve identity and geometry, then list only critical exclusions.

Label multi-image inputs by index, for example `Input 1 → product_anchor` and `Input 2 → subject_anchor`. Keep model, size, quality, output format, duration and audio routing in the execution record; let the Agent's prompt describe the current workbook segment. Do not copy a full-film timeline or later actions into an image prompt. See the official [GPT Image Generation Models Prompting Guide](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide).

## Gates

1. At production-task start, resolve `target_spoken_language` to `th` or `zh-CN`; use `zh-CN` when the user does not specify it. Persist `plan/language-lock.json` and keep it unchanged for the run and script revision. Every generation control prompt uses English.
2. Run `python scripts/preflight.py --workflow <workflow> [--target-spoken-language <th|zh-CN>] --json`. Omission resolves to the schema default `zh-CN`; persist the resolved value before continuing.
3. Read config/base-schema.json and fresh-read only the tables needed by the workflow. For subject work, the schema's `subject_assets.status_values` is authoritative: only `可用` records with a valid anchor and identity description are eligible for new work; `禁用` records remain historical evidence but are excluded from automatic selection and generation inputs. For scene work, use `scene_assets.status_values` in the same way: only `可用` records with a valid `场景锚点` are eligible; `禁用` records remain historical evidence and are excluded from new generation inputs. For prop work, use `prop_assets.status_values` and require a valid anchor for the exact requested state; a complete prop anchor cannot stand in for a damaged or broken state.
4. An external video must pass the local source-validity gate before full frame extraction, ASR, breakdown creation, reference-frame upload, or sentence-pattern learning. Invalid or unresolved media stops at preflight evidence and must not enter either learning library.
5. A script workflow requires one locked creative direction. It must create and review the Markdown creation workbook locally before creating or revising a Feishu script record. It may read only `资产状态=可用` 短视频拆解 and `审核状态=可用` 句式模板; pending candidates cannot enter the workbook.
   Every spoken script should use the dialogue-copy module for advisory review. It may record line evidence for a viewer pain point, user benefit, visible proof, and a natural CTA, but these copy-quality suggestions do not block script locking or video production.
   For clip production, generation or extraction success is not selected-library acceptance: apply the selected-clip admission gate in [clip-library-contract.md](references/domain/clip-library-contract.md) before writing `精选片段库`.
   Spoken scripts also follow a **soft lifestyle-delivery guide**, not a blocking gate: aim for 6–14 Chinese characters per line, keep a suggested ceiling of 18 characters, let each line express one action or reaction, avoid written connectors such as “直到、而是、之后、从而”, add a natural reaction or现场回应 about every 2–3 seconds when the visual beat allows it, and let the dialogue follow what is visibly happening instead of fully explaining the product mechanism. These are review signals and rewrite prompts; exceeding a suggestion does not fail validation by itself.
   A replication workflow must carry an evidence-backed source visual-style profile into every first-frame image prompt. `high_fidelity_replication` must additionally pass the source-product compatibility gate before image generation; `structure_replication` preserves transferable capture treatment and, when requested, may reuse one source frame as a scene-space reference while rewriting product-conflicting shots/actions. In scene-space reuse, the source frame controls only spatial layout, camera direction, lighting, background geometry, subject scale and action staging; target product and subject anchors own identity. Never transfer the source subject, product, text, logo or source-specific hardware. `资产状态=可用` proves breakdown quality, not compatibility with the selected product. High-fidelity replication must create a source-essence map, source-to-target correspondence map and source-comparison similarity review. Structure replication must create a source-structure map, source-to-target structure correspondence map and structure-similarity review. Do not silently polish casual UGC into generic advertising imagery. If high-fidelity cannot preserve a signature source element, stop and report the incompatible element; continue only after an explicit structure-replication decision.
   Consuming an already-accepted breakdown never authorizes changing its attachments, template or `资产状态`. Two-frame adaptation assets belong to the current local replication package unless the user explicitly requests a shared-library correction.
6. Only validation_status=passed scripts may enter full-film first-frame production, and only complete versions with `首帧状态=已通过` may enter final-video production. `clip_production` is a separate clip-first workflow: it uses a clip brief and one 10-second first-frame/video package, then writes the complete mother clip to the draft clip library without requiring a full script or full-film approval.
7. Keep one Markdown creation workbook as the content source for full-film work. The Agent and user edit that workbook; Feishu-facing fields and execution manifests are rendered or recorded from it. Prompt text, request parameters, result paths and retry state belong to the execution record. The Agent writes the segment-specific first-frame and video prompts when each stage is ready. Clip production uses its clip brief and library contract instead of creating a full-film workbook.
8. Product positioning, confirmed benefits, product assets, `交互能力`, `关键结构锁` and selected subjects are execution authority. Subject selection must honor explicit task bindings first, then the configured subject pool and rotation policy; do not repeatedly choose the first record, and do not substitute a disabled subject into an already locked script. Approved scene assets may establish background geometry, light direction, activity area, camera treatment and lived-in phone-capture texture, but may not override product geometry, product claims, subject identity or permitted interaction. Preserve a selected scene's ordinary lifestyle treatment; do not turn it into a warm showroom or cinematic advertisement unless explicitly requested. When `关键结构锁` declares a fixed integrated visual structure, its components and their relative positions are one indivisible product fact: do not omit, substitute, reconnect or let an action obscure that relationship. Product-first reference routing and structure-preserving action/camera choices are required for every visible-product first-frame Job. Do not use publication-risk or claim-verification gates in this first version.
   The content interaction template library only records reusable behavior patterns and visible acceptance points. It cannot override the product's `交互能力` or `关键结构锁`. If a selected template conflicts with the fresh product record, discard the template and write a product-supported action in the workbook; stop only when the product facts themselves do not support a safe, visible action.
9. For every remote mutation, retain a run ID and fresh-read the changed record. On failure, resume the same run; never create a duplicate direction, script or film.
10. Every first-frame image plan must declare `executor=gpt_image_2_5` and `model=gpt-image-2.5`. Use the configured ChatGPT2API standard MCP endpoint by default, confirm the exact model through `chatgpt_list_models`, and submit image-to-image Jobs with ordered `input_asset_ids`. Fix output to `1152x2048`, `quality=high`, and PNG. For visible products, `product_anchor` is position 1 and the selected recurring `subject_anchor` is position 2. If no reference image is available, prepare an approved anchor before submission instead of switching to text-only generation. If the MCP route cannot confirm the exact model or accept the routed references, stop. Flow2API image generation, direct web/API fallbacks, model aliases, another image model, and provider fallback are forbidden.
11. For full-film script work, the only first-frame approval surface is the script table. For each source script, create exactly two complete script records, versioned A and B, each carrying its full ordered first-frame package. Use `首帧状态` as the sole first-frame approval and execution-selection state: every complete version with `首帧状态=已通过` is eligible for final-video production, so A and B may both be selected. Do not create a script-version approval field or a Segment-level approval table, and never ask the human to choose individual Segments. Clip production does not create A/B script versions or use the full-film approval surface.
12. Original and replication full-film visual planning share one generation unit: every configured 4/6/8/10-second target production Segment generates exactly one 9:16 first-frame image representing that Segment's `t=0` entering state. Generate two self-contained first-frame packages (A/B) for the workbook when the task requests A/B, validate each package across all Segments, and write the ordered attachments to `最终首帧图` directly to the two script records. Segment order is owned by the Markdown creation workbook and preserved in remote attachment write order; deterministic attachment names are integrity checks only. There is no separate Segment mapping field or approval record. Clip production instead generates one first-frame package per requested 10-second mother clip and stores the complete video in the draft clip library. Internal retries and local artifacts are implementation details; they are not approval records.
   Use `scripts/publish_first_frame_versions.py` as the single A/B writeback seam. Each version record must contain an actual `来源脚本` relation to the source script record and `脚本版本=A` or `B`; never use a guessed text ID or a per-Segment candidate record.
13. Automated first-frame validation is a preflight gate, not final visual approval. It can reject obvious structural, geometry, attachment and prompt-coverage failures, but it cannot guarantee product fidelity or cross-Segment continuity. Label machine results as `视觉预检`. For full-film scripts, only a human approval of a complete first-frame version may set the version/script first-frame state to approved. For `clip_production`, human review marks the generated 10-second mother clip as `待筛选`, `入选` or `淘汰` in the draft clip library.
14. Compile the complete production stage before submitting anything. For first-frame images, persist the request-to-Segment/version mapping first, then submit all ready GPT Image 2.5 image-to-image requests in one concurrent request group by default; do not impose an artificial five-request cap. If the gateway returns an explicit capacity, rate-limit or timeout failure, split only the missing requests into smaller groups and retry with the same model, inputs and idempotency identity; never switch provider/model. For final video, two or more ready Flow2API Jobs still require `flow_submit_batch` plus `flow_wait_batch`; use a single-video submit only for one ready/repair Job or a recorded batch-interface failure. First-frame and final-video stages remain separate because human first-frame-version approval is a dependency boundary.
15. Chinese `spoken` and `sparse_spoken` final videos use one mandatory post-production route: first synthesize the complete approved TTS, then ASR it and lock the timing map before submitting any video Job. Omni generates visuals plus environmental sound only and no BGM or speech; Doubao TTS 2.0 generates the approved Chinese voiceover; the default Chinese speaker is `zh_female_qinqienv_uranus_bigtts` and may be overridden only by an explicitly selected compatible Doubao voice; the exact approved reference video supplies a separated BGM stem that must pass ASR with no residual speech; final assembly mixes environment, ducked BGM and aligned Doubao voiceover, then derives subtitles from that final voiceover timing. A continuous Chinese voiceover is synthesized as one complete take by default at `speech_rate=15`. If it is slightly too long, shorten only inter-sentence breath gaps; do not split it into line-by-line TTS or globally speed up the voice unless the user explicitly chooses that route.

### Final-video audio, subtitle and visual-sync gate

Before accepting any Chinese final video, create a local timing map from the final video segments and the final TTS ASR result. The map must include each segment's absolute start/end, each spoken sentence's start/end, and the first visible frame/time for the product or action being described. Do not approve a timeline merely because the total duration fits.

- **Video-duration and segment models:** use the final TTS duration as the lower bound for the visual runtime, then choose a plan made only from direct 4s, 6s, 8s and 10s Segments. Prefer an exact total; when no exact total is possible, choose the smallest total at least as long as the TTS. Duration is only one input: choose 4–6s for atomic actions, product inserts and reactions, and 8–10s for continuous actions that need a beginning-to-result arc. A valid plan may use `4s + 6s + 4s`, `10s + 6s`, or `8s + 4s + 6s`; short Segments are not tail-only. Submit every Segment directly to its matching model. Never generate a longer Segment and crop it. The visual runtime may continue after speech ends, but subtitles must end with the TTS and the speech must not be stretched merely to fill the runtime.
- **ASR-to-picture segmentation:** TTS must be generated before video. Create a timing map containing each sentence's real ASR start/end, each Segment's absolute start/end, the assigned Beat IDs and the first visible time of every product, feature or described action. Use ASR windows as timing evidence, then align cuts to semantic action boundaries or natural pauses; do not cut a continuous action merely because a sentence ended. Assign each spoken line to exactly one Segment, and do not accept a line that crosses a Segment boundary. A Segment must have one clear main action or reaction, an explicit entering state, a usable ending/handoff state and a reason for the cut. The next Segment inherits only the continuity facts declared in its handoff; independent short shots may intentionally change framing or scene when the cut is visually motivated. Spoken copy must follow visible evidence: a product name, feature or interaction must not begin before the corresponding product/feature/action is visible. If a line leads the visual, preserve the approved wording and first adjust inter-sentence silence, the local edit point or a small local time-stretch; then re-run ASR and update the timing map. Do not globally speed up the full take, split the voice into one TTS file per subtitle line, or rewrite the copy unless the user explicitly requests it.
- **Per-segment acceptance:** independently inspect every generated Segment before assembly. Check its approved first-frame entering state, subject/product identity, 9:16 geometry, actual duration and selected model duration, action continuity, extra objects or deformation, model-generated voice, and whether the local visual action matches its allocated TTS window. A failed Segment blocks assembly and must be repaired or regenerated.
- **Post-production and subtitle order:** assemble accepted Segments chronologically first; then mix accepted environmental sound, the passed BGM stem and the final aligned TTS; then run final-film ASR; then generate subtitles from the final TTS ASR timing. Subtitles use only the exact approved spoken copy. For Chinese 720x1280 final videos, the subtitle style is fixed: `SimHei`, `FontSize=50`, white text, bold, **1px black outline**, `Shadow=0`, no black box/background, bottom-center alignment, `MarginL=28`, `MarginR=28`, and `MarginV=130`. Short cues should stay on one line; long cues may use two lines when needed. Do not generate subtitles from planned estimates or before the final audio is locked.
- **Subtitle content and timing:** derive subtitles from the final TTS audio after all timing edits. Subtitle words and order must match the approved spoken copy; no wording changes, added claims or omitted words are allowed. For display, remove sentence and pause punctuation by default; this does not modify the locked dialogue or TTS. Each cue may occupy one or two lines, but never three lines, accidental automatic wrapping, horizontal clipping or text outside the safe area. Split compound sentences at natural semantic pauses into complete single-sentence or complete-clause cues, such as `我家狗狗折腾了半个月` / `基本没什么痕迹`; never split a cue into isolated words or fragments. If a cue is too wide, re-split it at a natural semantic pause and balance the two lines; do not change the fixed subtitle parameters. Distribute cue durations proportionally across the actual spoken interval.
- **Subtitle styling:** Chinese 720x1280 burned-in subtitles use the fixed style `SimHei`, bold, `FontSize=50`, white text, `Outline=1px` black outline, `Shadow=0`, no black box/background, `Alignment=2`, `MarginL=28`, `MarginR=28`, and `MarginV=130`. These are fixed production parameters, not starting values, and must not be changed per video. Inspect a rendered QA frame at actual output resolution only to verify readability, deliberate one-line/two-line layout, safe-area placement and subject/product obstruction; if a cue is too wide, revise its semantic line break rather than changing the fixed style.
- **Mandatory subtitle self-review:** after subtitle burn-in, the agent must look back at QA frames at the actual output resolution and complete a visual self-review before accepting the video. Check, at minimum: (1) the text is large enough to read on a phone; (2) each cue has a deliberate one-line or two-line layout, with no accidental third line; (3) line breaks follow meaning and both lines are visually balanced; (4) text stays inside the safe area with sufficient bottom margin; and (5) the subtitle does not cover the product or subject. If any item fails, return to subtitle layout, re-render and review again. A subtitle track is not accepted merely because the SRT/ASS file parses successfully.

## Short-video library classification

Approved short-video breakdowns use the retrieval taxonomy in [video-classification.md](references/invariants/video-classification.md). Classification is a set of orthogonal dimensions, not a folder tree: select exactly one value for each single-select field, use a small number of controlled multi-select tags, and keep the detailed narrative evidence in the existing breakdown fields.

When a user asks to classify approved videos, classify every record with `资产状态=可用`, preserve its existing analysis, attachments and approval state, and fresh-read each changed record. Do not infer a new claim just to fill a tag; use the closest evidence-backed option and record uncertainty in the existing quality field when needed.

## Stop condition

Stop the selected workflow at the first missing required input, invalid script report, failed first-frame fidelity review, missing approval, exhausted execution limit, failed remote write, or failed fresh-read verification. Report the concrete missing evidence and resumable run ID.
