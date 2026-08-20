# Table field hygiene

The live Feishu Base may retain compatibility columns after a schema migration. The schema-resolved canonical field wins; compatibility columns are read-only evidence and must not receive new business values.

## Canonical fields

- Mother-topic duration: `mother_topics.duration_field`; ignore `mother_topics.legacy_duration_field`.
- Candidate score: `candidates.configured_score_field`; ignore `candidates.legacy_score_field` for selection.
- Task version count: `planning_tasks.count_formula_field`; never increment `planning_tasks.legacy_manual_count_field`.
- Candidate/task/content direction: the single-select `content_format`; ignore content-library `legacy_content_format_field`.
- Subject selection: role-specific single links `person_subject_link` and `animal_subject_link`. The old multi-link `legacy_subject_link` is a compatibility snapshot only.

## Required checks

Before creating or updating a task or content version:

1. Read the field metadata and resolve every canonical field through `config/base-schema.json`.
2. Reject a record when a legacy field is being used as an input, when a canonical field is missing, or when a canonical value conflicts with its selected candidate.
3. Treat an empty legacy column as harmless; do not backfill it merely to make old views look complete.
4. Verify that the task/version has at most one person subject and at most one animal subject. A person-plus-one-animal pair is valid; multiple animals, breeds, or identities are not.
5. After any migration write, re-read the record and record only scrubbed field/status evidence in the local package.

This invariant does not authorize deleting compatibility columns. Removal is a separate schema-migration operation requiring explicit approval and a verified backup.
