# Director deep-module contract

`Director` is the single seam between a locked script and first-frame image prompt
execution. It is a pure derivation step, not a Feishu table and not a second
script authority.

## Input

- the freshly read, validated and locked script projection;
- current product hard facts, subject anchors and selected product actions;
- the resolved production mode and any evidence-backed source constraints;
- the current run's visual goal and the two requested variants, A and B.

## Output

For every target production Segment and each version, return exactly one ordered
First-frame decision. A First-frame decision contains:

- one directly observable `static_moment`;
- `camera` and `composition`;
- `performance` and permitted human presence;
- inherited `continuity`;
- the version-level `variant_delta`.

The first frame represents the Segment's entering state at local `t=0`. It does
not depict the full 10-second action or replace the locked Beat timeline.

The output is a new local first-frame plan consumed by the prompt compiler. It
must include `script_mutation=forbidden`. The Director cannot edit the locked
script, Beat timing, dialogue, product facts, product-action links or Feishu
approval fields.

## Authority and seam

Product facts and safety constraints win over replication evidence; replication
evidence and the locked script's semantics win over the Director's visual
choices; historical examples are reference only. The prompt compiler formats
Director output into the nine-block first-frame prompt architecture and performs
structural checks; it does not choose camera, composition, performance or
continuity.

The only remote first-frame mutation is the complete A/B package written by
`scripts/publish_first_frame_versions.py` to two script records linked through
`来源脚本`. Retry artifacts and request manifests remain local.

The writer manifest is intentionally small:

```json
{
  "run_id": "RUN-...",
  "source_script_record_id": "rec-source",
  "versions": {
    "A": {"variant_delta": "...", "first_frames": [{"segment_id": "Segment-01", "path": "...", "sha256": "..."}]},
    "B": {"variant_delta": "...", "first_frames": [{"segment_id": "Segment-01", "path": "...", "sha256": "..."}]}
  }
}
```
