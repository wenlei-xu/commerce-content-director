# Mutation and recovery

Treat Feishu writes and media uploads as a resumable Saga, not an assumed transaction.

1. Build and validate a local package before the first creative mutation.
2. Use `run_id` as the package identity and deterministic idempotency keys for every record or upload intent.
3. Create a staged or submitting record when the target system cannot atomically create fields and attachments. Upload only validated artifacts, then re-read the record and publish it to the workflow's ready state.
4. If a write or upload fails, retain the partial record as a visible failed/submitting state, record the exact missing evidence, and resume the same `run_id`; never create a duplicate record to hide the failure.
5. Never overwrite accepted media or delete failed artifacts. A compensating state change is preferred to destructive cleanup.

Completion requires both local evidence and a fresh remote read. A plausible file, cached attachment, or successful upload response without a matching remote record is not completion.
