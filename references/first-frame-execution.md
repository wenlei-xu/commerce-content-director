# GPT Image 2 first-frame execution

This is the only execution path for every active video first-frame request (job kind `first_frame_image`). The prompt compiler owns what to generate; GPT Image 2 owns image generation and reference-image editing. Flow2API remains the final-video provider and is never an image-generation fallback.

## Resolve capability and model

1. Run `python scripts/preflight.py --workflow first_frame_generation --json`, adding `--mode high_fidelity_replication` when applicable.
2. Use the standard Streamable HTTP MCP endpoint from `CHATGPT2API_MCP_HTTP_URL`; the configured cloud endpoint is `http://43.153.49.143:38300/mcp`. Read authentication from `CHATGPT2API_MCP_HTTP_TOKEN`; never persist the token in prompts, manifests or logs. Call `chatgpt_health` and `chatgpt_list_models`, and require the exact model ID `gpt-image-2` before submitting work.
3. Record `executor=gpt_image_2`, `model=gpt-image-2`, `size=1152x2048`, `quality=high`, and `format=png` in `plan/content-system-config-snapshot.json`, `plan/generation-prompt-plan.json`, and the compiled prompt bundle.
4. Confirm that the selected route accepts the planned ordered reference-image count. A route that hides or cannot guarantee its model binding is not valid evidence.

Do not infer an alias, use `chatgpt-image-latest`, select another GPT Image model, call Flow2API for images, or silently switch providers. A missing or unverified GPT Image 2 route stops the run.

## Prepare and execute

1. Route only approved inputs under [reference-asset-contract.md](reference-asset-contract.md). Use `scripts/prepare_image_inputs.py` for Feishu image assets. Preserve the complete uncropped image, MIME type, source hash, prepared-image hash, local path, role, and input order.
2. Validate the compiled prompt bundle before generation. Persist the complete request manifest, Segment/version mapping, ordered input paths/hashes, output path, model, output settings, and deterministic idempotency identity before the first call.
3. Upload or import each approved reference image with `chatgpt_upload_input_asset` or `chatgpt_import_input_asset`. Preserve the complete image, MIME type, source hash, prepared-image hash, local path, role, returned `asset_id`, and input order. Generation requests must contain only ordered `input_asset_ids`; never embed Base64 image data in a Job or batch request. The MCP route accepts at most 10 input assets per Job.
4. Compile the complete execution set for one script's first-frame stage before submitting anything. When two or more requests are ready, submit them through `chatgpt_submit_batch`; use `chatgpt_submit_image` only for one ready/repair Job or a recorded batch-interface failure. Do not impose a fixed five-request cap. If the MCP gateway explicitly rejects or times out part of the group because of capacity or rate limits, retry only the missing requests in smaller groups with the same model, ordered asset IDs and idempotency identity; capacity never authorizes a provider/model change.
5. Preserve the compiled prompt, input asset order, requested model and output settings exactly for each request. Record the returned Job ID and batch ID. A same-attempt transport retry reuses the same idempotency identity; an intentional replacement image increments the local `attempt` and never creates a remote Segment record.

## Retrieve and validate

1. Use `chatgpt_get_job_result` or `chatgpt_get_batch`/`chatgpt_wait_batch`, then retrieve the completed asset with `chatgpt_download_asset` or the `chatgpt2api://assets/{asset_id}` MCP resource. Save only completed image bytes as a local first-frame artifact. Do not treat a tool acknowledgement, preview, pending URL, or partial response as the final image.
2. Hash the saved output and update the request manifest with completion state, request ID, artifact path, artifact hash, timing, and error evidence when applicable.
3. Run `scripts/validate_generation_first_frames.py` with the active configuration snapshot, then perform the workflow's first-frame visual, product-fidelity and script-coverage preflight. This is machine/agent preflight evidence, not final human approval.
4. Count qualified first-frame images per script version and Segment. Retry only missing or failed requests; never regenerate a successful image merely because another concurrent request failed.
5. Retry only within the configured execution limit and only with `gpt-image-2`. If authentication, model access, rate limits, input compatibility, execution or validation cannot be restored, stop and report the resumable failure. Never retry through Flow2API or another image model.

Final-video generation begins only after a human locks one complete first-frame version. That later stage follows the separate Flow2API video contract.
