# Content task contract

Use one freshly read active `planning_tasks` record as the task-level authority for a generation package. Read [content-field-contract.md](../invariants/content-field-contract.md) before creating or updating its creative fields. Its mode is a closed schema enum: `original`, `hook_replication`, `structure_replication`, or `full_replication`. Blank, legacy, or unknown modes are data errors and stop the run.

The user not saying “replication” routes to `original`. Hook replication may use only the hook evidence window; structure replication may use only phase order, narrative functions, proof targets, and transition purposes; full replication may use the complete readable source video and its evidence workflow. Never mix modes in one content version.

One task contains exactly one selected candidate direction, one to three selected product value propositions, exactly one `content_format`, one `proof_action`, one `cta`, the schema-fixed `target_language=th`, a role-resolved subject mapping when needed, and only the selected candidate's execution delta. It does not contain competing formats, repeated mother-topic defaults, product mechanics, or a shot timeline. A concrete script and timed storyboard are created later for one `content_id`.

Subject mapping is role-based: at most one `person_subject_link` and at most one `animal_subject_link`. A person-plus-one-animal pair is valid for a host-led UGC task; multiple animals, breeds, or identities are not. The legacy multi-link `legacy_subject_link` field is not a selection source.

A content version belongs to exactly one planning task. Changes to an approved version create a new version; they do not overwrite the approved record. Task rotation creates one explicitly linked replacement task, verifies it, then archives the exhausted task according to the lifecycle workflow.
