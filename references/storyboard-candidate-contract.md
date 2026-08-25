# Storyboard candidate contract

The candidate unit is one complete 2×2 storyboard board for one configured
10-second target production Segment. It is never one panel, a start frame, an
end frame, or a full-film storyboard package.

## Remote authority

Every successful candidate is persisted as one record in the Feishu
`分镜候选` table and linked to exactly one locked script. The record owns one
`候选四宫格` attachment, `Segment ID`, `Segment 序号`, target time range,
attempt, run ID, Flow2API Job ID, idempotency key, model ID and attachment hash.
Local files are resumable staging caches only; no candidate may depend on the
computer that generated it.

The table's `人工选片` gallery view is the human review surface. Group it by
script and Segment order, use `候选四宫格` as the card cover, and expose
`是否采用`, `候选状态` and `审核意见` on each card.

## Counts and identity

Keep these counts separate:

- `expected_accepted_board_count = target_duration_seconds / 10`;
- `candidate_job_count = the number of intentional Flow2API candidate Jobs`;
- `candidate_count_by_segment = the persisted candidate records for that Segment`.

Use `<run_id>:<segment_id>:storyboard:<attempt>` as the Flow2API idempotency
key. Use `<script_record_id>:<segment_id>:attempt-<NN>` as the candidate ID.
A same-attempt transport retry reuses both identities. A new visual candidate
increments attempt and creates one new record; it never creates another script.

## Publish and select

Validate the complete board before the first Feishu candidate mutation. Create
the candidate record in `候选状态=提交中`, upload exactly one board, fresh-read
its attachment identity and hash, then publish it as `待选择`. A partial upload
remains visible and resumes on the same candidate ID.

Human selection is per `(script_record_id, Segment ID)`. Exactly one candidate
must have `是否采用=true` for that key. The checkbox is selection authority;
`候选状态` is only workflow display state. The human checks one card per Segment
in the gallery. A selection helper may clear the former checkbox for that same
Segment when replacing a choice, but it must not change any other Segment.

Do not crop panels or combine panels from different candidate boards. If one
panel is unusable, reject the complete candidate board and choose or generate
another complete board for that Segment.

## Finalize

Finalization fresh-reads the locked script and all linked candidate records.
Require exactly one selected candidate for every contiguous Segment from 1 to
`expected_accepted_board_count`. Missing, duplicate, unexpected or attachment-
less selections block finalization.

Order the accepted attachments by `Segment 序号` and write only those boards to
the exact script record's `最终分镜图`. The observed attachment count must equal
`expected_accepted_board_count`. Write the selected candidate IDs to
`分镜审核意见`, write or retain the script-derived `视频提示词`, set the requested
review state and fresh-read the script again. Only `已通过` may enter final-video
production.

Rejected candidates remain in `分镜候选` as `已淘汰`; never delete them to hide
failures. Never overwrite a script whose storyboard is already `已通过` with a
different accepted attachment set.

## Operator commands

After each successful Flow2API result, publish the complete board:

```powershell
python scripts/storyboard_candidates.py publish `
  --script-record-id <record_id> --segment-index <N> --attempt <N> `
  --run-id <run_id> --job-id <flow_job_id> `
  --idempotency-key <run_id>:Segment-<NN>:storyboard:<N> `
  --model-id <model_id> --board <board_path> --profile <config_snapshot_path>
```

The human then checks one `是否采用` box per Segment in `人工选片`. Finalize the
checked set with:

```powershell
python scripts/storyboard_candidates.py finalize `
  --script-record-id <record_id> --video-prompt-file <prompt_path>
```

Add `--approve` only when that checked set is the authorized accepted
storyboard. The `select --candidate-record-id <record_id>` helper is optional;
it is useful for programmatic replacement because it clears the old checkbox
for the same Segment without touching other Segments.
