# GPT Image 2 storyboard execution

This is the only execution path for every active `storyboard_image` request. The prompt compiler owns what to generate; GPT Image 2 owns image generation and reference-image editing. Flow2API remains the final-video provider and is never an image-generation fallback.

## Resolve capability and model

1. Run `python scripts/preflight.py --workflow storyboard_generation --json`, adding `--mode full_replication` when applicable.
2. Require an approved route that guarantees the exact model ID `gpt-image-2`. Use the configured GPT Image 2 generation tool when its model binding is explicit. Otherwise use the official OpenAI Images API with `model=gpt-image-2` and valid `OPENAI_API_KEY` authentication.
3. Record `executor=gpt_image_2`, `model=gpt-image-2`, `size=1152x2048`, `quality=high`, and `format=png` in `plan/content-system-config-snapshot.json`, `plan/generation-prompt-plan.json`, and the compiled prompt bundle.
4. Confirm that the selected route accepts the planned ordered reference-image count. A route that hides or cannot guarantee its model binding is not valid evidence.

Do not infer an alias, use `chatgpt-image-latest`, select another GPT Image model, call Flow2API for images, or silently switch providers. A missing or unverified GPT Image 2 route stops the run.

## Prepare and execute

1. Route only approved inputs under [reference-asset-contract.md](reference-asset-contract.md). Use `scripts/prepare_image_inputs.py` for Feishu image assets. Preserve the complete uncropped image, MIME type, source hash, prepared-image hash, local path, role, and input order.
2. Validate the compiled prompt bundle before generation. Persist the complete request manifest, Segment/version mapping, ordered input paths/hashes, output path, model, output settings, and deterministic idempotency identity before the first call.
3. Every storyboard request has routed reference images, so an official API implementation uses `v1/images/edits` with ordered `image[]` inputs. Map the plan's `format=png` to the API's `output_format=png`. Use `v1/images/generations` only for a future validated request with no image inputs. With `gpt-image-2`, omit `input_fidelity`; the model already processes image inputs at high fidelity.
4. Compile the complete execution set for one script's storyboard stage before submitting anything. When two or more requests are ready, execute them concurrently with maximum concurrency 5. Capacity or rate limits may reduce concurrency; they do not authorize a provider/model change. Use one request only when exactly one initial or repair request is ready.
5. Preserve the compiled prompt, input order, requested model and output settings exactly for each request. Record the returned request ID when the transport exposes one. A same-attempt transport retry reuses the same idempotency identity; an intentional new visual candidate increments `attempt`.

## Retrieve and validate

1. Save only a completed image response as the candidate artifact. Do not treat a tool acknowledgement, preview, pending URL, or partial response as the final board.
2. Hash the saved output and update the request manifest with completion state, request ID, artifact path, artifact hash, timing, and error evidence when applicable.
3. Run `scripts/validate_generation_storyboards.py` with the active configuration snapshot, then perform the workflow's visual, product-fidelity and script-coverage preflight. This is machine/agent preflight evidence, not final human approval.
4. Count qualified boards per script version and Segment. Retry only missing or failed requests; never regenerate a successful board merely because another concurrent request failed.
5. Retry only within the configured execution limit and only with `gpt-image-2`. If authentication, model access, rate limits, input compatibility, execution or validation cannot be restored, stop and report the resumable failure. Never retry through Flow2API or another image model.

Final-video generation begins only after a human locks one complete storyboard version. That later stage follows the separate Flow2API video contract.
