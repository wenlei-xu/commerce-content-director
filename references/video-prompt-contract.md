# Final-generation video prompt contract

Every final-generation prompt is for the fixed `omni_portrait` model. Each Job generates exactly one 10-second raw portrait 9:16 segment. The complete 20/30/40-second film is assembled from exactly 2/3/4 chronological Omni segments. Do not write a prompt for, or submit, another video model.

Read this contract before writing any Omni video-generation prompt for a portrait 9:16 Segment. For routed image roles and clean-input requirements, also read [reference-asset-contract.md](reference-asset-contract.md). It is not the contract for the first-frame image Job: read [first-frame-image-contract.md](first-frame-image-contract.md) instead.

## Omni prompting principles and compact creative scaffold

Apply the principles from the [Google DeepMind Omni prompt guide](https://deepmind.google/models/gemini-omni/prompt-guide/), [Gemini Omni documentation](https://ai.google.dev/gemini-api/docs/omni), and [Google Cloud video prompt guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/video-gen-prompt-guide):

- Use reference media to establish the subject, key objects, environment and starting composition; use the prompt to describe movement or change.
- Give each Segment one clear main action. Avoid stacking a long checklist of simultaneous actions.
- Describe only the important camera framing, point of view and movement.
- Keep visual style, lighting and mood concise; add detail only when it improves control.
- Request `Single continuous shot, no scene cuts` when the Segment must remain continuous.
- Add timing only when the action needs staging, using short natural-language windows or time ranges.
- Describe ambient sound, action sound, dialogue and music in a separate audio instruction.
- Keep unwanted elements concise rather than writing a long negative-prompt paragraph.
- For an edit, state only the intended change and add `Keep everything else the same.`

Use this as the standard final prompt framework before compiling each Segment prompt:

```text
Reference:
Use the provided [reference image/video] as the starting image and visual reference.
Keep the same [subject], [key objects], and [environment].

[Subject & Core Action]
A [subject] [performs one clear main action] in [location].
Describe the key movement and the interaction with important objects.

[Camera]
[shot size] from [POV].
The camera [camera movement].
Use [handheld / static / tracking] footage.

[Visual Style]
[realistic / cinematic / natural smartphone footage].
[lighting], [color], and [mood].

[Continuity & Timing]
Single continuous shot, no scene cuts.
[Optional timing: 0–2s..., 2–4s...]

[Audio]
Sound design: [ambient sound], [action sound], [dialogue or music if needed].

[Unwanted Elements]
[unwanted elements in short terms]
```

Replace the bracketed content with Segment-specific facts and keep the final prompt concise natural English. This framework is the final prompt structure and does not override the selected provider, model, asset-routing, language-lock or final-video execution contracts.

## Language and source-of-truth gate

Read `plan/language-lock.json` before writing the prompt. `target_spoken_language` must be `th` (Thai) or `zh-CN` (Chinese); when the user did not specify it, the task-start lock is `zh-CN`. Every spoken line, voice instruction, and timed dialogue window must use that one locked language. All generation control text must be English. A script value that differs from the task lock is a planning-data conflict: stop and fix the data before generation. Do not add a translated second dialogue line. If the selected audio mode is `natural_sound_only`, include no dialogue or voiceover at all. Chinese spoken dialogue is post-produced with Doubao TTS 2.0 and therefore remains outside every Omni prompt.

## Segment-scoped dialogue gate

The approved full-film script and video prompt are planning sources, not payloads that may be copied unchanged into every Omni Job. Before writing prompts, create a dialogue allocation manifest that records each approved line's identity, exact text, absolute film timing, assigned Segment, and Segment-local timing.

- Assign each approved spoken line to exactly one 10-second Segment unless the approved script explicitly marks an intentional repeat.
- Rebase the assigned line's timing to the current Job's local `0.0–10.0s` window.
- For Thai native-Omni speech, include only the current Segment's literal spoken lines in its prompt. Do not quote earlier or later Segment dialogue anywhere.
- For Chinese, keep exact lines and local timing in the allocation manifest and compiled bundle metadata for Doubao TTS and subtitle production, but include no literal Chinese dialogue in any Omni prompt. The prompt must contain no Chinese characters.
- A `natural_sound_only` Segment contains no spoken line.
- If any line crosses a Segment boundary or its assignment is ambiguous, stop before submission and fix the approved timing data. Do not improvise a split, duplicate the line, or let Omni continue it across Jobs.

Validate the complete prompt set as one unit before submitting any Job: Thai native-Omni lines must occur in exactly their assigned prompt; Chinese external-TTS lines must occur in no Omni prompt and must remain assigned exactly once in bundle metadata. Store the manifest and exact submitted per-segment prompts in the run package.

## Compiler input and evidence

Create `plan/generation-prompt-plan.json` with schema `commerce-generation-prompt-plan-v1`, `job_kind: "final_video"`, `prompt_language: "en"`, the locked `target_spoken_language`, `raw_segment_seconds: 10`, common approved constraints, and one entry per Segment. Chinese spoken plans must declare `voiceover_provider: "doubao_tts_2_0"` and `omni_audio_policy: "environment_only"`; Thai spoken plans declare `voiceover_provider: "omni_native"` and `omni_audio_policy: "native_dialogue"`. Each entry provides its input role map, continuous `beats` from `0.0` to `10.0`, hard constraints, subject identity, local dialogue allocation, audio mode, and continuity handoff.

Compile and validate before submitting any Job:

```powershell
python scripts/compile_generation_prompts.py plan/generation-prompt-plan.json --out plan/compiled-prompts.json
python scripts/validate_prompt_bundle.py plan/compiled-prompts.json
```

Keep `package.json`, `generation-jobs.json`, `dialogue-allocation.json`, `quality-report.md`, the source plan, compiled prompts, validator output, asset role/hash mappings, and temporary outputs. This evidence supports a resumable run; it never replaces the approved Feishu records.

## Final prompt checks

The final-generation prompt uses the exact framework above. The compiler should produce concise natural English that prioritizes the reference, one clear main action, camera treatment and visual style. Add timing, audio or unwanted elements when they matter. The framework is the prompt structure, but its headings are not a hard validation gate.

Keep the following checks because they protect execution integrity rather than prompt style:

1. Input assets exist, are clean, and their position/role mapping matches the Job payload.
2. The Segment has a valid continuous Beat timeline covering the configured raw duration.
3. Product-visible Segments have the required product reference and use only confirmed product facts; semantic product correctness is reviewed against the product record and generated frames.
4. The selected language, voiceover provider and Omni audio policy agree. Chinese dialogue stays outside Omni prompts and is assigned exactly once in bundle metadata.
5. Dialogue IDs and local timings are valid, and no Segment receives another Segment's dialogue.
6. The prompt is English control text, and the final Job/model/submission plan is valid.

The validator must not use the presence of the seven framework headings, or the old five-block headings, as a final-video acceptance criterion. Product identity, subject consistency, action completion, unwanted text/logo, and cross-Segment visual continuity are post-generation visual-review items.

After generation, ASR-check every Chinese raw Segment and reject any clip containing speech because Chinese Omni output must be environment-only. For Thai native speech, reject and regenerate only the affected Segment when ASR shows an omitted assigned line, an unapproved added line, or dialogue belonging to another Segment. Assembly does not waive these gates; run full-film ASR again after assembly to verify the final approved dialogue and boundaries.
