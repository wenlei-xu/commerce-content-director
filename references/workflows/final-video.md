# Workflow: final video generation and acceptance

Read authority.md, script-contract.md, script-validation.md, execution-accounting.md, mutation-and-recovery.md, configuration.md, product-contract.md, subject-contract.md, delivery-contract.md and video-prompt-contract.md.

Use only after the user names a locked script whose storyboard status is passed.

1. Fresh-read the script, final boards, structured script, dialogue manifest, Segment states, video prompt and accepted-film count.
2. Allocate every spoken line to exactly one Segment. A line cannot cross Segment boundaries.
3. Compile Segment prompts from the locked script and approved boards. Do not independently rewrite dialogue or CTA. For Chinese Doubao TTS 2.0 voiceover, default to `zh_female_qinqienv_uranus_bigtts` unless the user explicitly selects another compatible voice, and keep the selected voice consistent across the continuous take.
4. Generate asynchronous jobs with stable run and attempt IDs.
5. For spoken modes, ASR-check the completed segments and assembled film against line IDs and final Thai dialogue. For natural sound, perform manual audio review.
6. Assemble only accepted chronological segments, validate duration, portrait geometry, continuity and subtitles.
7. After acceptance, create one final-film record linked to the script, attach the playable file and fresh-read it. Increment accepted-film count exactly once.

Stop on exhausted execution limit, any dialogue mismatch, missing storyboard, failed acceptance or failed remote verification.
