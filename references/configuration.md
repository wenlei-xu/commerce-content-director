# Active content-system configuration

Fresh-read exactly one active `system_config` record and validate it against the current model catalog before creative work. Write `plan/content-system-config-snapshot.json` with the record/config IDs, weights, allowed target durations, raw segment duration, storyboard geometry, selected capability keys, and input limits.

The snapshot is the authority for target duration, raw-segment duration, storyboard rows/columns/ratio, scoring weights, rotation defaults, execution limits, and model capability selection for the run. A target duration must be allowed by both the business configuration and the current model catalog; never guess a fallback.

Use `scripts/snapshot_content_system_config.py` to validate and write the snapshot. It must remain read-only against Feishu. If there are zero or multiple active records, invalid weights, incompatible durations, or unsupported model capabilities, stop.

Schema resolution is separate from business configuration: `config/base-schema.json` owns mappings; this record owns current limits and capabilities. Update the schema before changing structure, and run the lifecycle script's schema check before resuming operations.
