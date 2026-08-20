# Workflow: content-library lifecycle

Read [authority.md](../invariants/authority.md), [mutation-and-recovery.md](../invariants/mutation-and-recovery.md), `config/base-schema.json`, and `config/lifecycle-policy.json`.

This is an administrative workflow over the branching content chain only. It never archives products, subject assets, or final films and never authorizes video generation.

1. Run `python scripts/lifecycle_sweeper.py --check-schema --json`.
2. Run the default JSON dry-run and retain its report locally.
3. Apply only after explicit user authorization with `--apply --json`.
4. Evaluate bottom-up: content versions, planning tasks, candidates, then mother topics. Use schema-resolved lifecycle fields and policy keys; never infer missing links or create replacement direction as a side effect.
5. Re-read every changed record and verify status, archive time, reason, and protected-record behavior. A single write failure remains visible and is resumed through the same run identity.
