# Mutation and recovery

Treat Feishu writes and media uploads as a resumable Saga, not an assumed transaction.

1. Build and validate a local package before the first creative mutation.
2. Use `run_id` as the package identity and deterministic idempotency keys for every record or upload intent.
3. Create a staged or submitting record when the target system cannot atomically create fields and attachments. Upload only validated artifacts, then re-read the record and publish it to the workflow's ready state.
4. If a write or upload fails, retain the partial record as a visible failed/submitting state, record the exact missing evidence, and resume the same `run_id`; never create a duplicate record to hide the failure.
5. Never overwrite accepted media or delete failed artifacts. A compensating state change is preferred to destructive cleanup.

For storyboard candidates, create or resume the same deterministic candidate
record in `提交中`, upload exactly one complete board, fresh-read its attachment,
then publish it to `待选择`. A partial candidate never authorizes a new record
with a different identity, and no local-only candidate counts as published.

Completion requires both local evidence and a fresh remote read. A plausible file, cached attachment, or successful upload response without a matching remote record is not completion.

For Flow2API batches, persist the deterministic batch ID and its complete
item-to-Job mapping before waiting. Resume the same batch and Job identities
after transport interruption. A partial batch failure creates repair work only
for missing outputs; it never invalidates or regenerates successful items.
