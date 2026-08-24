# Workflow: final video generation and acceptance

Read authority.md, script-contract.md, script-validation.md, execution-accounting.md, mutation-and-recovery.md, configuration.md, product-contract.md, subject-contract.md, delivery-contract.md, video-prompt-contract.md and [doubao-tts.md](../doubao-tts.md).

Use only after the user names a locked script whose storyboard status is passed.

1. Read `plan/language-lock.json`, run preflight with its `target_spoken_language`, then fresh-read the script, final boards, structured script, dialogue manifest, Segment states, English video prompt and accepted-film count. The task lock, `目标口播语言`, and structured-script runtime value must match.
2. Allocate every spoken line to exactly one Segment. A line cannot cross Segment boundaries.
3. For `spoken` or `sparse_spoken`, synthesize each exact approved line with Doubao TTS 2.0, preserving `line_id`, language, speaker, output hash and non-secret provider report. Align the clips to the locked dialogue windows. Never put the API key in run artifacts or Feishu. `natural_sound_only` skips TTS.
4. Compile Segment prompts from the locked script and approved boards. Do not independently rewrite dialogue or CTA.
5. Generate asynchronous jobs with stable run and attempt IDs.
6. For spoken modes, use the aligned Doubao track as the final voiceover authority and ASR-check the assembled film against line IDs and final approved dialogue in the locked language. For natural sound, perform manual audio review.
7. Build subtitles from the final accepted audio timing. New timing artifacts retain `line_id`, `start`, `end` and the exact approved `text`; a legacy timing line without `line_id` is accepted only when its text matches exactly one approved dialogue line. `auto_from_final_audio` produces ordinary SRT; `emphasis_from_final_audio` uses the script's exact keyword spans to produce ASS; `none` produces no subtitle track. Never treat independent screen text as subtitles.
8. Assemble only accepted chronological segments, validate duration, portrait geometry, continuity and subtitles. For emphasized subtitles, visually verify keyword color/scale and confirm the rendered text still exactly matches the approved line in the locked language.
9. After acceptance, create one final-film record linked to the script, attach the playable file and fresh-read it. Increment accepted-film count exactly once.

Stop on exhausted execution limit, any dialogue mismatch, missing storyboard, failed acceptance or failed remote verification.
