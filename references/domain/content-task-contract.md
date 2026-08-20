# Content task contract

Use one freshly read active `planning_tasks` record as the task-level authority for a generation package. Its mode is a closed schema enum: `original`, `hook_replication`, `structure_replication`, or `full_replication`. Blank, legacy, or unknown modes are data errors and stop the run.

The user not saying “replication” routes to `original`. Hook replication may use only the hook evidence window; structure replication may use only phase order, narrative functions, proof targets, and transition purposes; full replication may use the complete readable source video and its evidence workflow. Never mix modes in one content version.

A content version belongs to exactly one planning task. Changes to an approved version create a new version; they do not overwrite the approved record. Task rotation creates one explicitly linked replacement task, verifies it, then archives the exhausted task according to the lifecycle workflow.
