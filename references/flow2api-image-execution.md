# Flow2API MCP image execution

This is the only execution path for every `storyboard_image` Job. The prompt compiler owns what to generate; the registered Flow2API MCP owns submission, job state and result retrieval. GPT Image is not a fallback.

## Resolve capability and model

1. Run `python scripts/preflight.py --workflow storyboard_generation --json`, adding `--mode full_replication` when applicable.
2. Call `flow_get_service_health(include_dependencies=true)`. Continue only when the service and required dependencies report healthy.
3. Call `flow_list_models(include_unavailable=true, media_type="image")` and select the exact image model required by the fresh active configuration. Require `availability=available`, `media_type=image`, and `max_input_images` greater than or equal to the routed input count.
4. Record that exact model ID in `plan/content-system-config-snapshot.json`, `plan/generation-prompt-plan.json` and the compiled prompt bundle. Set `executor` to `flow2api_mcp` in both prompt artifacts. A mismatch stops the run.

Do not infer a model alias or retain a model merely because it was available in an earlier run. Do not probe a private Flow2API HTTP endpoint.

## Prepare and submit

1. Route only approved inputs under [reference-asset-contract.md](reference-asset-contract.md). Use `scripts/prepare_flow_inputs.py` for Feishu image assets; its Base64 sidecars supply `input_images[].data_base64` and its manifests supply the MIME type and content hash. Local routed assets must be prepared to the same complete, uncropped transport standard.
2. Validate the compiled prompt bundle before submission.
3. For a single board call `flow_submit_image` with the exact compiled prompt, model ID, ordered `input_images`, and a deterministic idempotency key such as `<run_id>:<segment_id>:storyboard:<attempt>`.
4. A same-attempt transport retry reuses the same idempotency key. An intentional targeted regeneration increments `attempt` and uses a new key. Persist the returned `job_id`, segment ID, attempt and idempotency key in the local run manifest before waiting.
5. Use `flow_submit_batch(kind="image")` only when the batch items preserve the same per-Job model, prompt, ordered inputs and deterministic idempotency data. Persist the returned batch and Job IDs.

Never call `image_gen`, GPT Image, an image-generation CLI, a different MCP or a direct provider API for these Jobs.

## Wait, retrieve and validate

1. Use `flow_wait_job` for one Job or `flow_wait_batch` for a batch. A queued or running state is not a generation failure and does not authorize provider fallback.
2. After success, retrieve the output through `flow_get_job_result`. Save the returned artifact in the current run package and bind it to its segment and attempt. Do not treat a submission acknowledgement, preview or pending URL as the final board.
3. Run `scripts/validate_generation_storyboards.py` with the active configuration snapshot, then perform the workflow's visual, product-fidelity and script-coverage review.
4. On a terminal failure, record the Flow2API error and resumable identifiers. Retry only within the configured execution limit and only through Flow2API MCP. If health, model availability, capacity or execution cannot be restored, stop and report the failure; do not switch providers.
