# Module 3 — 最终视频生成与验收

Use this module only after the exact `内容库` record has been freshly read as `审核状态=通过` and the user has explicitly named that record or `content_id`. This module owns Omni raw-segment Jobs, segment assembly, default subtitle generation and burn-in, final-film acceptance, and the valid execution count.

The final deliverable is a complete package: video + approved spoken audio when the script calls for speech + subtitles aligned to the actual final audio. Omni may provide the video and spoken audio together, but Omni is not the subtitle owner. Subtitle generation and burn-in are a required local post-assembly step by default.

## Read for this module

Read the public gates in the parent `SKILL.md`, then read:

- [configuration.md](configuration.md) for target duration, raw-segment duration, grid, and model capability.
- [video-prompt-contract.md](video-prompt-contract.md) for the five-block Omni prompt contract.
- [delivery-contract.md](delivery-contract.md) for the board set that Omni is allowed to consume.
- [english-subtitles.md](english-subtitles.md) when the approved target language is English or when its typography guidance is needed.
- The audio scripts and relevant reference-audio guidance when the run uses reference audio, TTS, music, or another non-Omni audio layer.

## Pre-submission gates

1. Fresh-read the exact named content version, its approval state, product/task links, approved storyboard attachments, script, target language, and `视频生成 Prompt` field.
2. Fresh-read `已执行次数`, `执行次数上限`, and all linked `最终成片` records. Count only complete, playable, technically and visually accepted films whose delivered file includes the required audio and subtitle layer. If the stored count disagrees with qualifying linked films, stop and report the inconsistency.
3. If the limit is reached, archive according to Module 4 and stop. Do not reserve, increment, or submit a Job before a valid execution slot is established. A reservation, if implemented by the data layer, must be recorded and confirmed before submission, then committed only after final-film verification.
4. Confirm every storyboard board is the clean, validated board from Module 2. Review-only timing labels or annotations must never enter Omni.
5. Build the actual input array and role map for each Segment. The recommended Omni roles are: storyboard board, default product anchor, recurring subject anchor when present, product detail reference, product scene reference, and an explicit previous-segment continuity frame when the model/input limit allows. Do not use fixed positions when optional roles are absent.

## Omni prompt and Job execution

Every Segment prompt must use the five blocks in [video-prompt-contract.md](video-prompt-contract.md): input roles/authority, product structure constraints, subject identity lock, target language/audio/timed dialogue, and no-text/cross-Segment continuity. The prompt must match the actual input role map and approved script exactly.

For raw Omni generation:

- State the target spoken language explicitly. Do not put Chinese translations or agent explanations alongside Thai dialogue.
- State whether audio is native Omni dialogue or natural-sound-only. Spoken dialogue is audio-only.
- Explicitly forbid captions, subtitles, dialogue transcription, labels, logos, watermarks, UI, and readable text in every language.
- Repeat stable subject identity attributes in every Segment.
- State `loading_path` and `dispensing_path` separately, including their direction and whether they are the same. For a product whose record confirms both use the bottom circular hole, repeat that exact fact for both paths and state that the side lattice is neither an inlet nor an outlet. Do not ask the model to repair a contradictory board.
- State the boundary handoff. Where continuity matters, generate Segment 02 after Segment 01 and route the accepted terminal frame as a continuity reference instead of relying on prose alone.

Submit only the configured `omni_portrait` model, within the current R2V input limit. Save the exact prompt, request digest, role map, input hashes, idempotency key hint, Job ID, and state. Wait through the Job deadline; non-terminal states are not failures. A deliberate regeneration gets a new attempt key and a targeted correction.

## Assembly and acceptance

After every required Segment succeeds:

1. Download every clip and preserve the originals.
2. Assemble only the chronological configured Segment set into an intermediate video. Verify video stream, the expected audio stream, codec readability, exact target duration, and no missing range.
3. Run ASR on the **assembled intermediate video's final audio**, not on storyboard timing or the raw prompt. Compare the actual language and audible words with the approved script; do not accept a Thai task that produced Chinese speech.
4. Align the approved script to the ASR timing and write reviewable subtitle artifacts: `subtitle-timing.json` with `start`, `end`, `text`, plus an SRT file. Correct only clear ASR errors supported by the audible audio and approved script; do not invent claims or force text that is not spoken.
5. Burn the generated subtitle file into a separately named final candidate. Subtitles are required by default whenever approved speech exists. An explicit `无口播` task produces no spoken subtitle lines; it must not receive invented dialogue. An explicit user request for `无字幕` is the only normal exception and must be recorded in the package and review report.
6. Run OCR on the final burned candidate, verify subtitle presence/timing when speech exists, verify no unintended text outside the subtitle layer, and repeat the product/subject/scene/audio review on the final candidate.
7. Keep raw Omni output, intermediate no-subtitle assembly, burned final candidate, subtitle timing artifacts, QA evidence, and rejected attempts separately named. Never overwrite an earlier candidate.

Omni-generated speech, any provider-generated text, music, and local post-processing are separate ownership layers. Treat Omni as the owner of its generated audio only; this skill owns the default subtitle timing, subtitle source, and burn-in output. Raw generation prompts must never contain subtitle text as a way to request burned-in captions. If a provider returns visible text despite the raw no-text rule, reject or repair the raw candidate before subtitle burn-in; do not count provider text as the required subtitle layer.

## Final-film commit and count

Only after technical and visual acceptance:

1. Fresh-read the source content record.
2. Create one idempotent `最终成片` record with the exact content version, unique `成片ID`, duration, and generation time.
3. Attach only the complete accepted video and fresh-read the final-film record. Require the expected content link, filename, attachment token, and playable media.
4. Commit the source `已执行次数` increment by exactly one and re-read it. If any create, upload, read, or count write fails, retain artifacts and report the inconsistency; do not create a duplicate final-film record.

The business execution count is not a Job count. Record attempts, retries, failures, credit usage, and partial clips in `generation-jobs.json` only.
