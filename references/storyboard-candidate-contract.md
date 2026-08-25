# Storyboard candidate contract

The generation candidate unit is one complete 2×2 storyboard board for one
configured 10-second target production Segment. It is never one panel, a start
frame, or an end frame. A candidate is not a human approval unit; approval is
performed on a complete storyboard version that contains the ordered boards
for every Segment in the script.

## Remote authority

Every successful candidate is persisted as one backend record in the Feishu
`分镜候选` table (or the configured internal candidate store) and linked to
exactly one locked script and Segment. The record owns one `候选四宫格`
attachment, `Segment ID`, `Segment 序号`, target time range, attempt, run ID,
Flow2API Job ID, idempotency key, model ID and attachment hash. Local files are
resumable staging caches only; no candidate may depend on the computer that
generated it. The candidate table is an audit/execution surface, not the human
approval surface.

The human review surface is the script-version record. It owns `脚本版本`
(for example A/B), `完整分镜方案` attachments in Segment order,
`分镜组合映射`, source script identity and `版本审核状态`. A version may mix
Segment candidates only when the complete package passes cross-Segment
continuity validation.

## Counts and identity

Keep these counts separate:

- `candidates_per_segment = 2` by default;
- `candidate_job_count = target_duration_seconds / 10 × candidates_per_segment` for the initial batch;
- `candidate_count_by_segment = the persisted candidate records for that Segment`.

Thus a 30-second script has three logical Segments and six initial candidate
Jobs. The final accepted object is one complete storyboard version containing
three ordered boards, not three independently approved candidate records.
Extra targeted regeneration is allowed after the initial two and increments
`attempt`; it does not change the default.
The six initial Jobs belong to one script-stage image batch. If validation or
execution leaves several missing candidate slots, submit those slots in one
repair batch; never rerun already qualified candidates.

Use `<run_id>:<segment_id>:storyboard:<attempt>` as the Flow2API idempotency
key. Use `<script_record_id>:<segment_id>:attempt-<NN>` as the candidate ID.
A same-attempt transport retry reuses both identities. A new visual candidate
increments attempt and creates one new record; it never creates another script.

## Publish and select

Validate the complete board before the first Feishu candidate mutation. Create
the candidate record in `候选状态=提交中`, upload exactly one board, fresh-read
its attachment identity and hash, then publish it as `待选择`. A partial upload
remains visible and resumes on the same candidate ID.

Human selection is per complete storyboard version. The reviewer compares the
ordered A/B packages and marks at most one version `版本审核状态=已通过`; the
other version becomes `未采用`. No human-facing workflow requires checking one
candidate per Segment. The selected version's mapping remains explicit so the
chosen Segment boards are traceable to their backend candidates.

Do not crop panels or combine panels from different candidate boards. If one
panel is unusable, reject the complete candidate board and choose or generate
another complete board for that Segment.

## Finalize

Version finalization fresh-reads the source script, the complete version record
and every mapped backend candidate. Require one attachment for each contiguous
target Segment, chronological ordering, complete source-candidate mapping and
continuity evidence. Missing, duplicate, unexpected or attachment-less
Segments block finalization.

Write the ordered attachments and mapping to the script-version record, set
`版本审核状态=待审核`, and fresh-read again. Only the human-approved version
(`版本审核状态=已通过`) may enter final-video production.

Rejected candidates remain in the backend candidate log for audit unless an
explicit lifecycle policy authorizes archival/deletion after all version records
have been verified. Never overwrite an approved version with a different
attachment set.

## Operator commands

After each successful Flow2API result, publish the complete board:

```powershell
python scripts/storyboard_candidates.py publish `
  --script-record-id <record_id> --segment-index <N> --attempt <N> `
  --run-id <run_id> --job-id <flow_job_id> `
  --idempotency-key <run_id>:Segment-<NN>:storyboard:<N> `
  --model-id <model_id> --board <board_path> --profile <config_snapshot_path>
```

Assemble and publish a complete script-version package, then use the
version-record writer configured for the active Feishu schema. It must
fresh-read the version record and mapped candidates, write the ordered package,
and set `版本审核状态=已通过` only after authorized human approval. There is
no per-Segment checkbox selection in the human workflow.
