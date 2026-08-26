# Mutation and recovery

Treat Feishu writes and media uploads as a resumable Saga, not an assumed transaction.

1. Build and validate a local package before the first creative mutation.
2. Use `run_id` as the package identity and deterministic idempotency keys for every record or upload intent.
3. Create a staged or submitting record when the target system cannot atomically create fields and attachments. Upload only validated artifacts, then re-read the record and publish it to the workflow's ready state.
4. If a write or upload fails, retain the partial record as a visible failed/submitting state, record the exact missing evidence, and resume the same `run_id`; never create a duplicate record to hide the failure.
5. Never overwrite accepted media or delete failed artifacts. A compensating state change is preferred to destructive cleanup.

For storyboard generation, keep each board and request manifest local until a
complete A/B package is ready. Persist the deterministic request-to-version/
Segment mapping, exact model/output settings, input hashes and idempotency
identities before execution. The only storyboard writeback is the complete A/B
package to its script-version record; there is no remote candidate record,
`提交中`/`待选择` candidate state or storyboard-mapping field.

Completion requires both local evidence and a fresh remote read of the A/B script
version records. A plausible file, cached attachment, or successful upload
response without matching `最终分镜图` attachments is not completion.

For concurrent GPT Image 2 storyboard requests, persist the complete
request-to-Segment/version mapping, exact model/output settings, input hashes
and deterministic idempotency identities before execution. Resume only missing
requests after transport interruption. A partial request-group failure creates
repair work only for missing outputs; it never invalidates or regenerates
successful items. Flow2API batch identity rules still apply separately to the
final-video stage.
