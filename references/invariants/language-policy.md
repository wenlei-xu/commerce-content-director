# Target-language policy

The current campaign policy fixes `target_spoken_language` to `th` (Thai) in `config/base-schema.json`. Until that schema policy changes, all spoken UGC videos use Thai. This policy does not require image or video generation prompts to be written in Thai.

## Rules

- Resolve `target_spoken_language` from the schema policy before reading or writing a script, video prompt, voice line, or subtitle track. Storyboard/image prompts may use the configured prompt language independently.
- A missing spoken language, a non-Thai spoken language, or mixed spoken languages is a planning-data conflict. Stop and report it; do not guess from `platform_account` or free-text `creative_requirements`.
- Every spoken line, timed dialogue window, voiceover instruction, TTS input, and ASR acceptance check must use Thai. English or Chinese may be used freely for control instructions, visual descriptions, product constraints, and prompt explanations; they are not spoken lines.
- Generation prompts may use English or Chinese. The default is English, but Chinese is allowed when it improves operator clarity. Do not translate the entire prompt into Thai merely because the voice language is Thai.
- A storyboard/image Job has no spoken-dialogue payload. Its control prompt, panel descriptions, layout instructions, and negative constraints must therefore contain no Thai. Select `en` or `zh-CN` from `generation_prompt_languages`, record that selection with the submitted prompt, and stop before submission if the prompt contains Thai control text.
- `audio_mode` is separate from language: `spoken` and `sparse_spoken` still use Thai; `natural_sound_only` contains no dialogue and must not silently add a CTA or voiceover.
- A task or content record cannot override the fixed spoken language with a free-text field. Changing the allowed spoken language requires a schema-policy change and a fresh validation of downstream contracts.
