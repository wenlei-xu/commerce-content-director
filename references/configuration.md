# Active content-system configuration

Fresh-read exactly one active `system_config` record before creative work. Write `plan/content-system-config-snapshot.json` with the record/config IDs, weights, allowed target durations, raw segment duration, storyboard geometry, fixed storyboard executor `gpt_image_2`, fixed image-model ID `gpt-image-2`, fixed image output `1152x2048`/high/PNG, fixed `omni_portrait` video model key, and input limits.

The snapshot is the authority for target duration, raw-segment duration, storyboard rows/columns/ratio, scoring weights, rotation defaults, execution limits, and model input limits for the run. For final video, the invariant profile is `video_model=omni_portrait`, `raw_segment_seconds=10`, and portrait `9:16` output. A target duration must be allowed by the business configuration and must be divisible by 10; never guess a fallback.

Use `scripts/snapshot_content_system_config.py` to validate and write the snapshot. It must remain read-only against Feishu. Supply `--image-model gpt-image-2`; the storyboard execution preflight must confirm that exact model and the planned routed input count. If there are zero or multiple active records, invalid weights, a raw segment other than 10 seconds, a non-portrait 9:16 profile, a target duration not divisible by 10, an unavailable/unverified GPT Image 2 route, an unavailable `omni_portrait` model, or an unreadable input limit, stop. Flow2API's model catalog is consulted only for final-video capability.

Schema resolution is separate from business configuration: `config/base-schema.json` owns mappings; this record owns current limits and capabilities. Update the schema before changing structure, and run the lifecycle script's schema check before resuming operations.
