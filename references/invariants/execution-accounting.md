# Execution accounting

Keep two counters conceptually separate:

- `attempt_count`: every submitted Job attempt, including retries, terminal failures, timeouts, and partial clips. Store it in `generation-jobs.json` with the payload digest and attempt key.
- `accepted_film_count`: complete target-duration films that passed technical and visual review, were attached to a new final-film record, and were freshly read as present and playable.

The content version's business execution count represents `accepted_film_count`, not Job submissions or credit usage. Increment it exactly once after final-film attachment verification. If the stored count disagrees with qualifying linked final films, stop and report the inconsistency.

Every attempt has a stable `run_id`, `content_id`, `attempt_id`, payload digest, and idempotency key. Reuse the key only to recover an uncertain submission of the unchanged payload. A deliberate visual regeneration receives a new attempt key and preserves the previous artifact and reason.
