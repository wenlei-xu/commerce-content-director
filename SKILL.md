---
name: commerce-content-director
description: Run Feishu-driven ecommerce short-video production from creative request and direction through a validated executable script, storyboard, final video, and lifecycle management.
---

# Commerce content director

This Skill runs the production chain:

~~~text
创作需求 → 创意方向 → 脚本 → 分镜 / 视频提示词 → 最终成片
~~~

A script is the only executable content object. It owns the strategy snapshot, Beat timeline, visual/audio/screen-text tracks, dialogue, interaction plans, continuity, storyboard state, and final-film relationship.

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
- **Generate, select, or review a storyboard**: read [storyboard-generation.md](references/workflows/storyboard-generation.md), then apply the active production mode and storyboard execution contract below.
- **Generate and accept a final video**: read [final-video.md](references/workflows/final-video.md).
- **Archive the creative chain**: read [lifecycle.md](references/workflows/lifecycle.md).

### Production modes

- **Original production**: use `original` when the work does not reproduce an external source. No replication workflow is loaded.
- **Structure replication**: use `structure_replication` only when the user explicitly requests structure replication, then read [structure-replication.md](references/workflows/structure-replication.md). It preserves the story skeleton, commercial proof chain, relative pacing, emotional curve and transferable visual style while allowing product-conflicting shots, actions, subjects or scenes to change.
- **High-fidelity replication**: use `high_fidelity_replication` for a request that says only “复刻”, “replicate”, “参考原片做一条” or otherwise asks to reproduce a source without naming a narrower mode, then read [full-replication.md](references/workflows/full-replication.md). The legacy value `full_replication` is a compatibility alias. Product substitution is not a reason to lower fidelity. If compatibility fails, stop and require a new explicit mode decision; never downgrade the active run automatically.
- **Hook replication**: select `hook_replication` only when the user explicitly requests it. No active hook-replication workflow is defined; stop and report the unsupported mode instead of improvising or substituting another mode.

### Nested workflows

- [action-direction.md](references/workflows/action-direction.md) is a planning step inside script production and runs before writing Beats. It produces one scene-description paragraph, not a new data object or approval step. Read it directly only when the user requests that paragraph as the complete deliverable.
- [dialogue-copy-optimization.md](references/workflows/dialogue-copy-optimization.md) is the dialogue module used when drafting, reviewing, or revising spoken copy. It returns a local proposal and review report; the parent script workflow remains the only writer of `structured_script` and Feishu.
- The **scene asset library** is a reusable Feishu visual-context table, not a second script authority. Scene assets own spatial layout, lighting direction, lived-in capture treatment and usable activity area; product hard facts and selected subject anchors still own product and identity. When a workflow needs a stable environment, query only `状态=可用` records with a valid `场景锚点`, select by market, scene type and current Beat, and record the selected scene asset ID and reason in the local run package.
- The **content interaction template library** is a cross-SKU Feishu knowledge table, not a workflow or a second script authority. Templates own reusable behavior flow and visible acceptance points; product records own hard facts and interaction constraints. During script production, query `模板状态=可用` templates with `python scripts/query_content_interaction_templates.py --product-record-id <record_id>`, then check each selected template against the freshly read product record before writing its scene-specific execution into `structured_script.interaction_plans`. An `interest`, `interaction`, `emotion`, `rhythm`, or `transition` plan must not be forced to demonstrate a selling point; only a `proof` plan may carry a verified benefit.

### Execution contracts

- Every storyboard workflow and replication mode uses [gpt-image-2-execution.md](references/gpt-image-2-execution.md). Storyboard images use GPT Image 2 exclusively through the configured ChatGPT2API MCP by default; never route image generation through Flow2API or silently change models/providers.
- For this project, storyboard image generation uses the standard Streamable HTTP MCP endpoint from `CHATGPT2API_MCP_HTTP_URL`; the configured cloud endpoint is `http://43.153.49.143:38300/mcp`, authenticated with `CHATGPT2API_MCP_HTTP_TOKEN`. Never write the token into this skill, prompts, manifests, command output or logs. Upload or import approved reference images as MCP assets first, then submit Jobs using ordered `input_asset_ids`.
- Final-video execution belongs to [final-video.md](references/workflows/final-video.md) and the contracts it names; it is not part of storyboard routing.

### Flow2API MCP routing

- External Codex final-video calls must use the standard MCP HTTP endpoint from `FLOW2API_MCP_HTTP_URL`; for the configured cloud deployment this is `http://43.153.49.143:38200/mcp`, authenticated with `FLOW2API_MCP_HTTP_TOKEN`.
- Never use `http://43.153.49.143:38000/internal/mcp/v1` as an external MCP endpoint. Port `38000` is the Flow2API private bridge used internally by the MCP gateway; it is not the public MCP interface.
- Keep `FLOW2API_MCP_FLOW_BRIDGE_URL` only in the server-side MCP deployment configuration. When the standard MCP endpoint returns an error, diagnose the gateway/bridge boundary and do not bypass it by submitting directly to the private bridge.

### ChatGPT2API MCP routing

- External Codex storyboard-image calls must use the standard MCP HTTP endpoint from `CHATGPT2API_MCP_HTTP_URL`; for the configured cloud deployment this is `http://43.153.49.143:38300/mcp`, authenticated with `CHATGPT2API_MCP_HTTP_TOKEN`.
- Before image submission, call `chatgpt_health` and `chatgpt_list_models`, and require the exact `gpt-image-2` model. Use `chatgpt_upload_input_asset` or `chatgpt_import_input_asset` for each approved reference, preserving role and order. Submit with `chatgpt_submit_image` for one item or `chatgpt_submit_batch` for a ready set, passing only ordered `input_asset_ids`.
- Do not put Base64 image data into a generation Job, call the internal `38210/internal/v1` gateway from outside Docker, or use the ChatGPT2API web port `3000` as the MCP transport. A missing/invalid MCP token, unavailable exact model, or failed asset upload is a stop condition.

## Shared invariants

Read only the invariants named by the selected workflow:

- [authority.md](references/invariants/authority.md) — schema and record authority.
- [scene-asset-library-contract.md](references/domain/scene-asset-library-contract.md) — reusable scene context and selection boundaries.
- [content-interaction-template-library-contract.md](references/domain/content-interaction-template-library-contract.md) — reusable interaction templates and script handoff.
- [script-field-contract.md](references/invariants/script-field-contract.md) — object ownership and single source of truth.
- [director-contract.md](references/domain/director-contract.md) — the storyboard Director seam and its non-mutation boundary.
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
3. Read config/base-schema.json and fresh-read only the tables needed by the workflow. For subject work, the schema's `subject_assets.status_values` is authoritative: only `可用` records with a valid anchor and identity description are eligible for new work; `禁用` records remain historical evidence but are excluded from automatic selection and generation inputs. For scene work, use `scene_assets.status_values` in the same way: only `可用` records with a valid `场景锚点` are eligible; `禁用` records remain historical evidence and are excluded from new generation inputs.
4. An external video must pass the local source-validity gate before full frame extraction, ASR, breakdown creation, reference-frame upload, or sentence-pattern learning. Invalid or unresolved media stops at preflight evidence and must not enter either learning library.
5. A script workflow requires one locked creative direction. It must build and validate structured_script locally before creating or revising a Feishu script record. It may read only `资产状态=可用` 短视频拆解 and `审核状态=可用` 句式模板；待审核候选不得直接进入脚本。
   Every spoken script should use the dialogue-copy module for advisory review. It may record line evidence for a viewer pain point, user benefit, visible proof, and a natural CTA, but these copy-quality suggestions do not block script locking or video production.
   Spoken scripts also follow a **soft lifestyle-delivery guide**, not a blocking gate: aim for 6–14 Chinese characters per line, keep a suggested ceiling of 18 characters, let each line express one action or reaction, avoid written connectors such as “直到、而是、之后、从而”, add a natural reaction or现场回应 about every 2–3 seconds when the visual beat allows it, and let the dialogue follow what is visibly happening instead of fully explaining the product mechanism. These are review signals and rewrite prompts; exceeding a suggestion does not fail validation by itself.
   A replication workflow must carry an evidence-backed source visual-style profile into every storyboard-image prompt. `high_fidelity_replication` must additionally pass the source-product compatibility gate before image generation; `structure_replication` preserves transferable capture treatment and, when requested, may reuse one source frame as a scene-space reference while rewriting product-conflicting shots/actions. In scene-space reuse, the source frame controls only spatial layout, camera direction, lighting, background geometry, subject scale and action staging; target product and subject anchors own identity. Never transfer the source subject, product, text, logo or source-specific hardware. `资产状态=可用` proves breakdown quality, not compatibility with the selected product. High-fidelity replication must create a source-essence map, source-to-target correspondence map and source-comparison similarity review. Structure replication must create a source-structure map, source-to-target structure correspondence map and structure-similarity review. Do not silently polish casual UGC into generic advertising imagery. If high-fidelity cannot preserve a signature source element, stop and report the incompatible element; continue only after an explicit structure-replication decision.
   Consuming an already-accepted breakdown never authorizes changing its attachments, template or `资产状态`. Two-frame adaptation assets belong to the current local replication package unless the user explicitly requests a shared-library correction.
6. Only validation_status=passed scripts may enter storyboard production. Only complete versions with `分镜状态=已通过` may enter final-video production.
7. Keep structured_script as the only machine source of truth. Render every human-readable script field from it after validation; do not independently edit duplicate text fields. After the script is locked, the `Director` deep module is the only owner of storyboard-level creative decisions. It reads the locked script and execution evidence and returns panel static moments, camera, composition, performance, continuity and A/B variant differences. It returns a new storyboard plan; it must never mutate the locked script or its semantic Beat timeline.
8. Product hard facts, product assets and selected subjects are execution authority. Subject selection must honor explicit task bindings first, then the configured subject pool and rotation policy; do not repeatedly choose the first record, and do not substitute a disabled subject into an already locked script. Approved scene assets may establish background geometry, light direction, activity area, camera treatment and lived-in phone-capture texture, but may not override product geometry, product claims, subject identity or permitted interaction. Preserve a selected scene's ordinary lifestyle treatment; do not turn it into a warm showroom or cinematic advertisement unless explicitly requested. When the product record declares a fixed integrated visual structure, its components and their relative positions are one indivisible product fact: do not omit, substitute, reconnect or let an action obscure that relationship. Product-first reference routing and structure-preserving action/camera choices are required for every visible-product storyboard Job. Do not use publication-risk or claim-verification gates in this first version.
   The content interaction template library only records reusable behavior patterns and visible acceptance points. It cannot override product hard facts. If a selected template conflicts with the fresh product record, stop and request confirmation or a template/product-fact update instead of guessing.
9. For every remote mutation, retain a run ID and fresh-read the changed record. On failure, resume the same run; never create a duplicate direction, script or film.
10. Every storyboard-image plan must declare `executor=gpt_image_2` and `model=gpt-image-2`. Use the configured ChatGPT2API standard MCP endpoint by default, confirm the exact model through `chatgpt_list_models`, and submit image-to-image Jobs with ordered `input_asset_ids`. Fix output to `1152x2048`, `quality=high`, and PNG. For visible products, `product_anchor` is position 1 and the selected recurring `subject_anchor` is position 2. If no reference image is available, prepare an approved anchor before submission instead of switching to text-only generation. If the MCP route cannot confirm the exact model or accept the routed references, stop. Flow2API image generation, direct web/API fallbacks, model aliases, another image model, and provider fallback are forbidden.
11. The only storyboard approval surface is the script table. For each source script, create exactly two complete script records, versioned A and B, each carrying its full ordered storyboard package. Use `分镜状态` as the sole storyboard approval and execution-selection state: every complete version with `分镜状态=已通过` is eligible for final-video production, so A and B may both be selected. Do not create a script-version approval field, a `分镜候选` table or a `分镜方案审核` table, and never ask the human to choose individual Segments.
12. Original and replication storyboards share one generation unit: every configured 10-second target production Segment generates complete 2×2 boards with four 9:16 panels. Generate two self-contained storyboard packages (A/B) for the script, validate each package across all Segments, and write the ordered attachments to `最终分镜图` directly to the two script records. Segment order is owned by the structured script and preserved in remote attachment write order; deterministic attachment names are integrity checks only. There is no separate storyboard-mapping field or approval record. Internal retries and local artifacts are implementation details; they are not approval records.
   Use `scripts/publish_storyboard_versions.py` as the single A/B writeback seam. Each version record must contain an actual `来源脚本` relation to the source script record and `脚本版本=A` or `B`; never use a guessed text ID or a per-Segment candidate record.
13. Automated storyboard validation is a preflight gate, not final visual approval. It can reject obvious structural, geometry, attachment and prompt-coverage failures, but it cannot guarantee product fidelity or cross-Segment continuity. Label machine results as `视觉预检`; only a human approval of a complete storyboard version may set the version/script storyboard state to approved.
14. Compile the complete production stage before submitting anything. For storyboard images, persist the request-to-Segment/version mapping first, then submit all ready GPT Image 2 image-to-image requests in one concurrent request group by default; do not impose an artificial five-request cap. If the gateway returns an explicit capacity, rate-limit or timeout failure, split only the missing requests into smaller groups and retry with the same model, inputs and idempotency identity; never switch provider/model. For final video, two or more ready Flow2API Jobs still require `flow_submit_batch` plus `flow_wait_batch`; use a single-video submit only for one ready/repair Job or a recorded batch-interface failure. Storyboard and final-video stages remain separate because human storyboard-version approval is a dependency boundary.
15. Chinese `spoken` and `sparse_spoken` final videos use one mandatory post-production route: Omni generates visuals plus environmental sound only and no BGM or speech; Doubao TTS 2.0 generates the approved Chinese voiceover; the default Chinese speaker is `zh_female_qinqienv_uranus_bigtts` and may be overridden only by an explicitly selected compatible Doubao voice; the exact approved reference video supplies a separated BGM stem that must pass ASR with no residual speech; final assembly mixes environment, ducked BGM and aligned Doubao voiceover, then derives subtitles from that final voiceover timing. A continuous Chinese voiceover is synthesized as one complete take by default at `speech_rate=15`. If it is slightly too long, shorten only inter-sentence breath gaps; do not split it into line-by-line TTS or globally speed up the voice unless the user explicitly chooses that route.

## Stop condition

Stop the selected workflow at the first missing required input, invalid script report, failed storyboard fidelity review, missing approval, exhausted execution limit, failed remote write, or failed fresh-read verification. Report the concrete missing evidence and resumable run ID.
