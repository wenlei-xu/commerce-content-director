---
name: commerce-content-director
description: "Run Feishu-driven ecommerce short-video production with a clip-first workflow: generate reusable 10-second video drafts, curate usable clips, and optionally assemble final films."
---

# Commerce content director

This Skill runs the production chain:

~~~text
创作需求 → 创意方向 / 片段意图 → 10秒视频片段 → 草稿库（暂存） → 精选片段库（沉淀） →（可选）最终成片
~~~

For full-film work, a script is the only executable content object: it owns the strategy snapshot, Beat timeline, visual/audio/screen-text tracks, dialogue, interaction plans, continuity, first-frame version state, and final-film relationship. Clip-first work uses a lightweight clip brief and the draft/selected clip library contracts; it does not create a full-film script merely to generate a 10-second mother clip.

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

- [action-direction.md](references/workflows/action-direction.md) is a planning step inside script production and runs before writing Beats. It produces one scene-description paragraph, not a new data object or approval step. Read it directly only when the user requests that paragraph as the complete deliverable.
- [dialogue-copy-optimization.md](references/workflows/dialogue-copy-optimization.md) is the dialogue module used when drafting, reviewing, or revising spoken copy. It returns a local proposal and review report; the parent script workflow remains the only writer of `structured_script` and Feishu.
- The **scene asset library** is a reusable Feishu visual-context table, not a second script authority. Scene assets own spatial layout, lighting direction, lived-in capture treatment and usable activity area; product hard facts and selected subject anchors still own product and identity. When a workflow needs a stable environment, query only `状态=可用` records with a valid `场景锚点`, select by market, scene type and current Beat, and record the selected scene asset ID and reason in the local run package.
- The **draft clip library** is only the temporary staging and review area for complete generated 10-second mother clips. The **selected clip library** is the actual sedimentation destination: it stores independent extracted clips that are ready for reuse. These are reusable media libraries, not script records and not approval surfaces for a full film; read [clip-library-contract.md](references/domain/clip-library-contract.md) when creating, reviewing or writing either library. That contract also owns the canonical `产品 / SKU` identity rules and the prefixed `片段标签` convention for separating use, action, benefit and reuse scope.
- The **content interaction template library** is a cross-SKU Feishu knowledge table, not a workflow or a second script authority. Templates own reusable behavior flow and visible acceptance points; product records own hard facts and interaction constraints. During script production, query `模板状态=可用` templates with `python scripts/query_content_interaction_templates.py --product-record-id <record_id>`, then check each selected template against the freshly read product record before writing its scene-specific execution into `structured_script.interaction_plans`. An `interest`, `interaction`, `emotion`, `rhythm`, or `transition` plan must not be forced to demonstrate a selling point; only a `proof` plan may carry a verified benefit.

### Execution contracts

- Every first-frame workflow and replication mode uses [first-frame-execution.md](references/first-frame-execution.md). First-frame images use GPT Image 2 exclusively through the configured ChatGPT2API MCP by default; never route image generation through Flow2API or silently change models/providers.
- For this project, first-frame image generation uses the standard Streamable HTTP MCP endpoint from `CHATGPT2API_MCP_HTTP_URL`; the configured cloud endpoint is `http://43.153.49.143:38300/mcp`, authenticated with `CHATGPT2API_MCP_HTTP_TOKEN`. Never write the token into this skill, prompts, manifests, command output or logs. Upload or import approved reference images as MCP assets first, then submit Jobs using ordered `input_asset_ids`.
- Final-video execution belongs to [final-video.md](references/workflows/final-video.md) and the contracts it names; it is not part of first-frame routing.

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
- Before image submission, call `chatgpt_health` and `chatgpt_list_models`, and require the exact `gpt-image-2` model. Use `chatgpt_upload_input_asset` or `chatgpt_import_input_asset` for each approved reference, preserving role and order. Submit with `chatgpt_submit_image` for one item or `chatgpt_submit_batch` for a ready set, passing only ordered `input_asset_ids`.
- Do not put Base64 image data into a generation Job, call the internal `38210/internal/v1` gateway from outside Docker, or use the ChatGPT2API web port `3000` as the MCP transport. A missing/invalid MCP token, unavailable exact model, or failed asset upload is a stop condition.

## Shared invariants

Read only the invariants named by the selected workflow:

- [authority.md](references/invariants/authority.md) — schema and record authority.
- [scene-asset-library-contract.md](references/domain/scene-asset-library-contract.md) — reusable scene context and selection boundaries.
- [clip-library-contract.md](references/domain/clip-library-contract.md) — draft and selected clip library fields, states and writeback boundaries.
- [content-interaction-template-library-contract.md](references/domain/content-interaction-template-library-contract.md) — reusable interaction templates and script handoff.
- [script-field-contract.md](references/invariants/script-field-contract.md) — object ownership and single source of truth.
- [director-contract.md](references/domain/director-contract.md) — the first-frame Director seam and its non-mutation boundary.
- [script-validation.md](references/invariants/script-validation.md) — blocking quality checks.
- [product-execution-contract.md](references/invariants/product-execution-contract.md) — product action correctness.
- [language-policy.md](references/invariants/language-policy.md) — Thai/Chinese spoken-language locking and audio behavior.
- [knowledge-library-contract.md](references/invariants/knowledge-library-contract.md) — the two learning-library objects and their review boundaries.
- [video-classification.md](references/invariants/video-classification.md) — the multi-dimensional retrieval taxonomy for approved short-video breakdowns.
- [model-visual-text-recognition.md](references/invariants/model-visual-text-recognition.md) — model-vision-only screen-text evidence and the legacy OCR field contract.
- [execution-accounting.md](references/invariants/execution-accounting.md) — accepted films and execution limits.
- [mutation-and-recovery.md](references/invariants/mutation-and-recovery.md) — staged writes and resumable failures.

## First-frame prompt contract

The active image deliverable is a **video first frame**, not a multi-image board. A configured 10-second production Segment produces one static 9:16 image representing only that Segment's entering state at local `t=0`. Camera language remains required because the first frame establishes the video's starting viewpoint, framing and visual focus.

Every first-frame generation prompt should be concise, skimmable and use these blocks in this exact order:

1. `REFERENCE IMAGE ROLE` — identify each routed reference by input position and state which visual facts it owns. A product anchor owns product appearance; it must not be treated as a layout to copy.
2. `OUTPUT SPECIFICATION` — one 9:16 portrait first-frame image for the Segment's entering state at local `t=0`.
3. `CREATIVE INTENT` — what the viewer should notice, feel or initially misunderstand. The Director's variant direction supplies this viewer-read priority.
4. `CAMERA OPERATOR VIEWPOINT` — make the capture position and the filming person's presence concrete: camera height, viewpoint, framing, hand or body presence and visual focus.
5. `SCENE EVENT` — the single visible situation frozen at local `t=0`, including the relevant environment and continuity state. Do not describe the full video or chain future actions.
6. `SUBJECT PERFORMANCE` — the selected subject's visible identity, expression, pose and performance in this frozen moment.
7. `PRODUCT LOCK` — only the product placement, necessary continuity constraints and permitted product action relevant to this frame. When a `product_anchor` is routed, do not redundantly describe the product's appearance, color, material, texture, dimensions or detailed geometry; the routed anchor owns those facts. Mention only scene-specific placement, visible action or critical constraints that must remain legible, such as a required bottom treat hole.
8. `PHONE IMAGE TEXTURE` — concrete capture evidence such as handheld imperfection, auto-exposure, focus behavior, compression, household light and lived-in texture. Do not use “vlog” or “rough” as unsupported mood labels alone.
9. `NEGATIVE CONSTRAINTS` — preserve identity and geometry, then list only critical exclusions.

Label multi-image inputs by index, for example `Input 1 → product_anchor` and `Input 2 → subject_anchor`. Keep model, size, quality, output format, duration, voiceover, CTA, full Beat timeline and later actions in the execution plan or script, not in the image prompt. Start with a clean base prompt and make later revisions as single targeted changes. See the official [GPT Image Generation Models Prompting Guide](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide).

## Gates

1. At production-task start, resolve `target_spoken_language` to `th` or `zh-CN`; use `zh-CN` when the user does not specify it. Persist `plan/language-lock.json` and keep it unchanged for the run and script revision. Every generation control prompt uses English.
2. Run `python scripts/preflight.py --workflow <workflow> [--target-spoken-language <th|zh-CN>] --json`. Omission resolves to the schema default `zh-CN`; persist the resolved value before continuing.
3. Read config/base-schema.json and fresh-read only the tables needed by the workflow. For subject work, the schema's `subject_assets.status_values` is authoritative: only `可用` records with a valid anchor and identity description are eligible for new work; `禁用` records remain historical evidence but are excluded from automatic selection and generation inputs. For scene work, use `scene_assets.status_values` in the same way: only `可用` records with a valid `场景锚点` are eligible; `禁用` records remain historical evidence and are excluded from new generation inputs.
4. An external video must pass the local source-validity gate before full frame extraction, ASR, breakdown creation, reference-frame upload, or sentence-pattern learning. Invalid or unresolved media stops at preflight evidence and must not enter either learning library.
5. A script workflow requires one locked creative direction. It must build and validate structured_script locally before creating or revising a Feishu script record. It may read only `资产状态=可用` 短视频拆解 and `审核状态=可用` 句式模板；待审核候选不得直接进入脚本。
   Every spoken script should use the dialogue-copy module for advisory review. It may record line evidence for a viewer pain point, user benefit, visible proof, and a natural CTA, but these copy-quality suggestions do not block script locking or video production.
   For clip production, generation or extraction success is not selected-library acceptance: apply the selected-clip admission gate in [clip-library-contract.md](references/domain/clip-library-contract.md) before writing `精选片段库`.
   Spoken scripts also follow a **soft lifestyle-delivery guide**, not a blocking gate: aim for 6–14 Chinese characters per line, keep a suggested ceiling of 18 characters, let each line express one action or reaction, avoid written connectors such as “直到、而是、之后、从而”, add a natural reaction or现场回应 about every 2–3 seconds when the visual beat allows it, and let the dialogue follow what is visibly happening instead of fully explaining the product mechanism. These are review signals and rewrite prompts; exceeding a suggestion does not fail validation by itself.
   A replication workflow must carry an evidence-backed source visual-style profile into every first-frame image prompt. `high_fidelity_replication` must additionally pass the source-product compatibility gate before image generation; `structure_replication` preserves transferable capture treatment and, when requested, may reuse one source frame as a scene-space reference while rewriting product-conflicting shots/actions. In scene-space reuse, the source frame controls only spatial layout, camera direction, lighting, background geometry, subject scale and action staging; target product and subject anchors own identity. Never transfer the source subject, product, text, logo or source-specific hardware. `资产状态=可用` proves breakdown quality, not compatibility with the selected product. High-fidelity replication must create a source-essence map, source-to-target correspondence map and source-comparison similarity review. Structure replication must create a source-structure map, source-to-target structure correspondence map and structure-similarity review. Do not silently polish casual UGC into generic advertising imagery. If high-fidelity cannot preserve a signature source element, stop and report the incompatible element; continue only after an explicit structure-replication decision.
   Consuming an already-accepted breakdown never authorizes changing its attachments, template or `资产状态`. Two-frame adaptation assets belong to the current local replication package unless the user explicitly requests a shared-library correction.
6. Only validation_status=passed scripts may enter full-film first-frame production, and only complete versions with `首帧状态=已通过` may enter final-video production. `clip_production` is a separate clip-first workflow: it uses a clip brief and one 10-second first-frame/video package, then writes the complete mother clip to the draft clip library without requiring a full script or full-film approval.
7. Keep structured_script as the only machine source of truth for full-film script work. Render every human-readable script field from it after validation; do not independently edit duplicate text fields. Clip production uses its clip brief and library contract instead of creating duplicate full-script fields. After a full script is locked, the `Director` deep module is the only owner of first-frame-level creative decisions. It reads the locked script and execution evidence and returns one first-frame static moment per 10-second Segment, including camera, composition, performance, continuity and A/B variant differences. It returns a new first-frame plan; it must never mutate the locked script or its semantic Beat timeline.
8. Product hard facts, product assets and selected subjects are execution authority. Subject selection must honor explicit task bindings first, then the configured subject pool and rotation policy; do not repeatedly choose the first record, and do not substitute a disabled subject into an already locked script. Approved scene assets may establish background geometry, light direction, activity area, camera treatment and lived-in phone-capture texture, but may not override product geometry, product claims, subject identity or permitted interaction. Preserve a selected scene's ordinary lifestyle treatment; do not turn it into a warm showroom or cinematic advertisement unless explicitly requested. When the product record declares a fixed integrated visual structure, its components and their relative positions are one indivisible product fact: do not omit, substitute, reconnect or let an action obscure that relationship. Product-first reference routing and structure-preserving action/camera choices are required for every visible-product first-frame Job. Do not use publication-risk or claim-verification gates in this first version.
   The content interaction template library only records reusable behavior patterns and visible acceptance points. It cannot override product hard facts. If a selected template conflicts with the fresh product record, stop and request confirmation or a template/product-fact update instead of guessing.
9. For every remote mutation, retain a run ID and fresh-read the changed record. On failure, resume the same run; never create a duplicate direction, script or film.
10. Every first-frame image plan must declare `executor=gpt_image_2` and `model=gpt-image-2`. Use the configured ChatGPT2API standard MCP endpoint by default, confirm the exact model through `chatgpt_list_models`, and submit image-to-image Jobs with ordered `input_asset_ids`. Fix output to `1152x2048`, `quality=high`, and PNG. For visible products, `product_anchor` is position 1 and the selected recurring `subject_anchor` is position 2. If no reference image is available, prepare an approved anchor before submission instead of switching to text-only generation. If the MCP route cannot confirm the exact model or accept the routed references, stop. Flow2API image generation, direct web/API fallbacks, model aliases, another image model, and provider fallback are forbidden.
11. For full-film script work, the only first-frame approval surface is the script table. For each source script, create exactly two complete script records, versioned A and B, each carrying its full ordered first-frame package. Use `首帧状态` as the sole first-frame approval and execution-selection state: every complete version with `首帧状态=已通过` is eligible for final-video production, so A and B may both be selected. Do not create a script-version approval field or a Segment-level approval table, and never ask the human to choose individual Segments. Clip production does not create A/B script versions or use the full-film approval surface.
12. Original and replication full-film visual planning share one generation unit: every configured 10-second target production Segment generates exactly one 9:16 first-frame image representing that Segment's `t=0` entering state. Generate two self-contained first-frame packages (A/B) for the script, validate each package across all Segments, and write the ordered attachments to `最终首帧图` directly to the two script records. Segment order is owned by the structured script and preserved in remote attachment write order; deterministic attachment names are integrity checks only. There is no separate Segment mapping field or approval record. Clip production instead generates one first-frame package per requested 10-second mother clip and stores the complete video in the draft clip library. Internal retries and local artifacts are implementation details; they are not approval records.
   Use `scripts/publish_first_frame_versions.py` as the single A/B writeback seam. Each version record must contain an actual `来源脚本` relation to the source script record and `脚本版本=A` or `B`; never use a guessed text ID or a per-Segment candidate record.
13. Automated first-frame validation is a preflight gate, not final visual approval. It can reject obvious structural, geometry, attachment and prompt-coverage failures, but it cannot guarantee product fidelity or cross-Segment continuity. Label machine results as `视觉预检`. For full-film scripts, only a human approval of a complete first-frame version may set the version/script first-frame state to approved. For `clip_production`, human review marks the generated 10-second mother clip as `待筛选`, `入选` or `淘汰` in the draft clip library.
14. Compile the complete production stage before submitting anything. For first-frame images, persist the request-to-Segment/version mapping first, then submit all ready GPT Image 2 image-to-image requests in one concurrent request group by default; do not impose an artificial five-request cap. If the gateway returns an explicit capacity, rate-limit or timeout failure, split only the missing requests into smaller groups and retry with the same model, inputs and idempotency identity; never switch provider/model. For final video, two or more ready Flow2API Jobs still require `flow_submit_batch` plus `flow_wait_batch`; use a single-video submit only for one ready/repair Job or a recorded batch-interface failure. First-frame and final-video stages remain separate because human first-frame-version approval is a dependency boundary.
15. Chinese `spoken` and `sparse_spoken` final videos use one mandatory post-production route: Omni generates visuals plus environmental sound only and no BGM or speech; Doubao TTS 2.0 generates the approved Chinese voiceover; the default Chinese speaker is `zh_female_qinqienv_uranus_bigtts` and may be overridden only by an explicitly selected compatible Doubao voice; the exact approved reference video supplies a separated BGM stem that must pass ASR with no residual speech; final assembly mixes environment, ducked BGM and aligned Doubao voiceover, then derives subtitles from that final voiceover timing. A continuous Chinese voiceover is synthesized as one complete take by default at `speech_rate=15`. If it is slightly too long, shorten only inter-sentence breath gaps; do not split it into line-by-line TTS or globally speed up the voice unless the user explicitly chooses that route.

## Short-video library classification

Approved short-video breakdowns use the retrieval taxonomy in [video-classification.md](references/invariants/video-classification.md). Classification is a set of orthogonal dimensions, not a folder tree: select exactly one value for each single-select field, use a small number of controlled multi-select tags, and keep the detailed narrative evidence in the existing breakdown fields.

When a user asks to classify approved videos, classify every record with `资产状态=可用`, preserve its existing analysis, attachments and approval state, and fresh-read each changed record. Do not infer a new claim just to fill a tag; use the closest evidence-backed option and record uncertainty in the existing quality field when needed.

## Stop condition

Stop the selected workflow at the first missing required input, invalid script report, failed first-frame fidelity review, missing approval, exhausted execution limit, failed remote write, or failed fresh-read verification. Report the concrete missing evidence and resumable run ID.
