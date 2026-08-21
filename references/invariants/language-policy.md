# Target-language policy

The current campaign policy fixes `target_language` to `th` (Thai) in `config/base-schema.json`. Until that schema policy changes, all spoken UGC videos use Thai.

## Rules

- Resolve `target_language` from the schema policy before reading or writing a script, storyboard prompt, video prompt, voice line, or subtitle track.
- A missing language, a non-Thai language, or mixed spoken languages is a planning-data conflict. Stop and report it; do not guess from `platform_account` or free-text `creative_requirements`.
- Every spoken line, timed dialogue window, voiceover instruction, and ASR acceptance check must use Thai. Chinese or English may appear in control notes or a human-facing explanation, but never as a second spoken line in a generation prompt.
- `audio_mode` is separate from language: `spoken` and `sparse_spoken` still use Thai; `natural_sound_only` contains no dialogue and must not silently add a CTA or voiceover.
- A task or content record cannot override the fixed language with a free-text field. Changing the allowed language requires a schema-policy change and a fresh validation of downstream contracts.
