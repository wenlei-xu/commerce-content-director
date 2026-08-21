# Authority and schema resolution

This is the shared authority contract. Resolve every logical key through `config/base-schema.json` at runtime; references must not copy Feishu table IDs, localized field names, or localized status values. The schema's `language_policy` is authoritative for spoken language and generation-prompt language; creative workflows must also read [language-policy.md](language-policy.md). When a live Base contains compatibility columns, also read [table-field-hygiene.md](table-field-hygiene.md) and use only its canonical mappings.

## Source precedence

1. `base-schema.json` resolves tables, fields, status keys, and relationship keys.
2. The unique active `system_config` record resolves business limits, durations, storyboard geometry, scoring weights, and the selected model capability snapshot.
3. The freshly read `planning_task` resolves creative direction and replication boundaries.
4. The directly resolved active `product` resolves product facts, approved claims, constraints, and assets.
5. The selected usable `subject_asset` resolves recurring-subject identity.
6. Generated media and previous Jobs are evidence only; they never become product or subject facts.

If two sources at the same authority level conflict, stop and record the conflict. Never infer missing geometry or behavior from a product name, generated image, prior run, or model memory.

## Logical-key rule

Use schema keys in workflow documents, for example `content_library.executed_count_field` and `planning_tasks.duration_field`. Resolve their localized values immediately before a Feishu call. A document that needs a new field or status must update the schema first and pass the schema check; it must not introduce a second mapping. Run `python scripts/check_reference_contract.py <skill>` after reference edits.

## Model capability rule

Workflows name capabilities such as `storyboard_image` and `portrait_video`, not vendor names or model IDs. Select the actual model key and input limit from the current catalog, record them in the run snapshot, and use that snapshot for every Job in the run.
