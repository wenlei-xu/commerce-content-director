# Workflow capability matrix

`config/workflow-capabilities.json` is the machine-readable authority for service and local-runtime requirements. Resolve the selected workflow and its known mode before any external call. A `not_required` capability must not be probed as part of that workflow's preflight.

| Workflow | Feishu | Flow2API | ffmpeg/ffprobe | ASR | Image tools |
| --- | --- | --- | --- | --- | --- |
| `creative_direction` | required | not required | not required | not required | not required |
| `script_production` | required | not required | not required | not required | not required |
| `storyboard_generation` | required | required | not required | not required | required |
| `final_video` | required | required | required | required for `spoken` or `sparse_spoken`; not required for `natural_sound_only` | required |
| `lifecycle` | required | not required | not required | not required | not required |

## Workflow-scoped preflight

1. Run `python scripts/preflight.py --workflow <workflow> --json`. Add `--mode full_replication` for a full-replication storyboard run. Add `--audio-mode spoken|sparse_spoken|natural_sound_only` for a final-video run.
2. When `feishu` is required, make a read-only Feishu metadata call only for the logical tables used by that workflow.
3. When `flow2api` is required, call the registered Sidecar MCP `flow_get_service_health(include_dependencies=true)` and `flow_list_models(include_unavailable=true)`. For storyboard images, filter the catalog to `media_type=image`, require the selected model to be available and support the planned number of reference images, then follow [flow2api-image-execution.md](flow2api-image-execution.md). Do not call Flow2API for a workflow where it is `not_required`.
4. The local script checks only local requirements. MCP health and model-catalog checks remain at the MCP seam; do not emulate them with private HTTP calls.

Flow2API being unhealthy, absent or incompatible is a stop condition for image-generation workflows. Do not substitute GPT Image, another image provider, a CLI or a private HTTP request.

For a conditional capability, resolve the condition from freshly read authoritative data before preflight. If that fact is unavailable, stop and request or obtain it; do not probe unrelated services as a fallback.

`natural_sound_only` final-video runs still require the documented manual audio review for unintended speech. They do not require a local ASR backend solely to start the workflow.
