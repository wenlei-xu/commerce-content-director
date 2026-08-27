# Storyboard candidate contract (legacy)

> This document is retained only for historical run packages and migration audits. The active workflow does not create, write, or review a `分镜候选` table. New storyboard work writes two complete A/B packages directly to the script table. Do not use the candidate contract for new runs.

Historical generation candidate artifacts represent one complete 2×2
storyboard board for one configured 10-second target production Segment. They
are never one panel, a start frame, or an end frame. A candidate is not a human
approval unit; current approval is performed on a complete A/B storyboard
version that contains the ordered boards for every Segment in the script.

## Remote authority

Historical runs may contain per-Segment candidate records, but current runs
keep boards, request manifests and retry state in the local run package. The
only remote storyboard write is the complete A/B package on its script-version
record. Local artifacts must remain resumable and must not depend on the
computer that generated them.

The human review surface is the script-version record. It owns `脚本版本`
(for example A/B), `最终分镜图` attachments in Segment order, source script
identity and `分镜状态`. A version is written only after its complete package
passes cross-Segment continuity validation.

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

Validate every complete board before packaging. Persist the request manifest,
input/output hashes and deterministic retry identities locally; resume only
missing requests under the same `run_id`.

Human selection is per complete storyboard version. The reviewer may approve
either or both ordered A/B packages by setting each approved version to
`分镜状态=已通过`. No human-facing workflow requires checking one candidate per
Segment. The local run manifest keeps the approved
boards traceable to their generation requests.

Do not crop panels or combine panels from different candidate boards. If one
panel is unusable, reject the complete candidate board and choose or generate
another complete board for that Segment.

## Finalize

Version finalization fresh-reads the source script and each complete A/B version
record. Require one attachment for each contiguous target Segment, deterministic
chronological ordering and continuity evidence. Missing, duplicate, unexpected
or attachment-less Segments block finalization.

Write the ordered attachments to the script-version record, set
`分镜状态=待审核`, and fresh-read again. Any human-approved version
(`分镜状态=已通过`) may enter final-video production.

Rejected candidate artifacts remain in the local run package for audit. Never
overwrite an approved version with a different attachment set.

## Operator commands

The historical `storyboard_candidates.py` operator was removed. Do not revive
it or use its per-Segment record model. Current runs use
`scripts/publish_storyboard_versions.py` and write only complete A/B packages.

Current runs assemble each complete A/B script-version package from the local
run manifest, write only the ordered `最终分镜图` attachments to the
version-record writer configured for the active Feishu schema, and fresh-read
the version record. Set each approved version's `分镜状态=已通过` only after
authorized human approval.
There is no per-Segment checkbox selection in the human workflow.
