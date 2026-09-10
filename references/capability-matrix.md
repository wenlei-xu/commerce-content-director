# Workflow capability matrix

`config/workflow-capabilities.json` is the machine-readable authority for service and local-runtime requirements. Resolve the selected workflow and its known mode before any external call. A `not_required` capability must not be probed as part of that workflow's preflight.

| Workflow | Feishu | GPT Image | Flow2API | ffmpeg/ffprobe | ASR | Image tools |
| --- | --- | --- | --- | --- | --- | --- |
| `creative_direction` | required | not required | not required | not required | not required | not required |
| `script_production` | required | not required | not required | not required | not required | not required |
| `first_frame_generation` | required | required | not required | not required | not required | required |
| `final_video` | required | not required | required | required | required for `spoken` or `sparse_spoken`; not required for `natural_sound_only` | required |
| `lifecycle` | required | not required | not required | not required | not required | not required |

## Workflow-scoped preflight

1. Run `python scripts/preflight.py --workflow <workflow> --json`. Add `--mode high_fidelity_replication` for a full-replication first-frame run. Add `--audio-mode spoken|sparse_spoken|natural_sound_only` for a final-video run.
2. When `feishu` is required, make a read-only Feishu metadata call only for the logical tables used by that workflow.
3. When `gpt_image` is required, use the configured standard ChatGPT2API MCP endpoint, verify with `chatgpt_health` and `chatgpt_list_models` that it can execute the exact model `gpt-image-2.5`, and confirm it accepts the planned reference count before following [first-frame-execution.md](first-frame-execution.md). Do not switch to a direct API, Flow2API, another image model or another provider.
4. When `flow2api` is required, call the registered Sidecar MCP `flow_get_service_health(include_dependencies=true)` and `flow_list_models(include_unavailable=true)`. This is the final-video path only. Do not call Flow2API for a workflow where it is `not_required`.
5. The local script checks only local requirements. Registered-tool, API-auth, MCP-health and model checks remain at their execution seams; do not emulate them with private provider endpoints.

An unavailable or unverified GPT Image 2.5 route is a stop condition for first-frame generation. Do not substitute Flow2API, another image model or another provider. Flow2API health affects final-video generation only.

For a conditional capability, resolve the condition from freshly read authoritative data before preflight. If that fact is unavailable, stop and request or obtain it; do not probe unrelated services as a fallback.

`natural_sound_only` final-video runs still require the documented manual audio review for unintended speech. They do not require a local ASR backend solely to start the workflow.
