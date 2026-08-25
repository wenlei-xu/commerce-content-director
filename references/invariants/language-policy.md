# Target-language policy

The final spoken language supports exactly `th` (Thai) and `zh-CN` (Chinese). Resolve and lock it at task start. When the user does not specify a language, use the schema default `zh-CN`. All generation control prompts use English.

## Rules

- At task start, take `target_spoken_language` from the user's explicit choice; otherwise use `default_target_spoken_language=zh-CN`. Persist `plan/language-lock.json` with `schema`, `target_spoken_language`, `locked_at`, and `source` (`user` or `schema_default`).
- The lock is immutable within one run and script revision. Changing it starts a new run or script revision; never silently convert downstream dialogue, subtitles, prompts, or audio.
- Copy the exact lock into `structured_script.runtime.target_spoken_language` and the Feishu script field `目标口播语言`. Fresh-read the script and verify both before storyboard or final-video work.
- A language outside `th` and `zh-CN`, mixed spoken languages, or inconsistent lock/script values is a planning-data conflict. Stop and report it.
- Every spoken line, timed dialogue window, voiceover instruction, TTS input, subtitle line, and ASR acceptance check uses the locked language. Thai dialogue must contain Thai script; Chinese dialogue must contain Chinese Han characters.
- Chinese `spoken` and `sparse_spoken` always use `voiceover_provider=doubao_tts_2_0` and `omni_audio_policy=environment_only`. Chinese dialogue must never be sent to Omni; Omni generates visuals and synchronized environmental sound only, without speech or background music.
- Thai `spoken` and `sparse_spoken` use the approved `omni_native` route unless the user explicitly approves a new script revision and provider route.
- Subtitle text is the exact final approved dialogue aligned to accepted audio. Emphasis metadata may style exact substrings but must not translate, paraphrase, or add claims.
- `audio_mode` is independent of language. `spoken` and `sparse_spoken` use the lock. `natural_sound_only` has no dialogue or voiceover, but still retains the task language lock.
- Every storyboard and final-video control prompt uses `prompt_language=en`. Do not use Chinese or Thai for control instructions. Thai native-Omni prompts may contain approved Thai dialogue only inside the timed-dialogue payload; Chinese Omni prompts contain no Chinese text because dialogue is produced after generation.
