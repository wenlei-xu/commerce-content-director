# Flow2API MCP image execution

This is the only execution path for every `storyboard_image` Job. The prompt compiler owns what to generate; the registered Flow2API MCP owns submission, job state and result retrieval. GPT Image is not a fallback.

## Resolve capability and model

1. Run `python scripts/preflight.py --workflow storyboard_generation --json`, adding `--mode full_replication` when applicable.
2. Call `flow_get_service_health(include_dependencies=true)`. Continue only when the service and required dependencies report healthy.
3. Call `flow_get_capacity` and record the current queue/capacity evidence. Capacity determines whether one logical stage must be split into smaller batches; it does not authorize serial submission by preference.
4. Call `flow_list_models(include_unavailable=true, media_type="image")` and locate the exact fixed model `gemini-3.1-flash-image-portrait`. Require `availability=available`, `media_type=image`, and `max_input_images` greater than or equal to the routed input count. Do not select a `-2k` or `-4k` variant.
5. Record `gemini-3.1-flash-image-portrait` in `plan/content-system-config-snapshot.json`, `plan/generation-prompt-plan.json` and the compiled prompt bundle. Set `executor` to `flow2api_mcp` in both prompt artifacts. A missing fixed model or any model mismatch stops the run.

Do not infer a model alias, choose another available image model, or retain availability from an earlier run. Do not probe a private Flow2API HTTP endpoint.

## Prepare and submit

1. Route only approved inputs under [reference-asset-contract.md](reference-asset-contract.md). Use `scripts/prepare_flow_inputs.py` for Feishu image assets; its Base64 sidecars supply `input_images[].data_base64` and its manifests supply the MIME type and content hash. Local routed assets must be prepared to the same complete, uncropped transport standard.
2. Validate the compiled prompt bundle before submission.
3. Compile the complete execution set for one script's storyboard stage before submitting anything. Expand every Segment by its `candidate_attempts`; the default two-attempt policy yields six ready Jobs for a 30-second script.
4. When the ready set contains two or more Jobs, call `flow_submit_batch(kind="image")` once with every item that fits current capacity. Batch items may use different Segment prompts and ordered inputs; each item must exactly preserve its own compiled model, prompt, inputs, content ID and deterministic idempotency key. Persist the batch ID and complete batch-to-Job mapping before waiting.
5. Use `flow_submit_image` only when exactly one Job is ready, exactly one failed/invalid candidate needs repair, or `flow_submit_batch` has produced a recorded interface failure. Do not replace a valid batch with a loop of single submissions. If capacity or payload limits require chunking, use the fewest batches possible and record the reason.
6. A same-attempt transport retry reuses the same idempotency key and candidate identity. An intentional new visual candidate for the same Segment increments `attempt` and uses a new key. Multiple candidate Jobs do not change the number of Segments in a complete storyboard version.

Never call `image_gen`, GPT Image, an image-generation CLI, a different MCP or a direct provider API for these Jobs.

## Wait, retrieve and validate

1. For a submitted batch, call `flow_wait_batch`; do not wait for its Jobs one by one. Use `flow_wait_job` only for a permitted single-Job submission. A queued or running state is not a generation failure and does not authorize provider fallback.
2. After the batch reaches the requested terminal condition, read its aggregate state and call `flow_get_job_result` for each successful Job. Save each returned artifact in the current run package and bind it to its Segment and attempt. Do not treat a submission acknowledgement, preview or pending URL as the final board.
3. Run `scripts/validate_generation_storyboards.py` with the active configuration snapshot, then perform the workflow's visual, product-fidelity and script-coverage preflight. Treat this as machine/agent preflight evidence, not final visual approval. Publish every passing complete board with `scripts/storyboard_candidates.py publish`; never publish four panels as four candidates.
4. Count qualified candidates per Segment. Technical failures and invalid complete boards create only the missing candidate slots. Submit all simultaneously known missing slots as one repair batch when there are two or more; use a single submit only for one missing slot. Never regenerate successful candidates merely because another batch item failed.
5. Retry only within the configured execution limit and only through Flow2API MCP. If health, model availability, capacity or execution cannot be restored, stop and report the failure; do not switch providers.
