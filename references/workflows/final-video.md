# Workflow: final video generation and acceptance

Read authority.md, script-contract.md, script-validation.md, execution-accounting.md, mutation-and-recovery.md, configuration.md, product-contract.md, subject-contract.md, delivery-contract.md and video-prompt-contract.md.

Use only after the user names a locked script whose storyboard status is passed.

1. Fresh-read the script, final boards, structured script, dialogue manifest, Segment states, video prompt and accepted-film count.
2. Allocate every spoken line to exactly one Segment. A line cannot cross Segment boundaries.
3. Compile Segment prompts from the locked script and approved boards. Do not independently rewrite dialogue or CTA.
4. Generate asynchronous jobs with stable run and attempt IDs.
5. For spoken modes, ASR-check the completed segments and assembled film against line IDs and final Thai dialogue. For natural sound, perform manual audio review.
6. Build subtitles from the final accepted audio timing. New timing artifacts retain `line_id`, `start`, `end` and the exact approved `text`; a legacy timing line without `line_id` is accepted only when its text matches exactly one approved dialogue line. `auto_from_final_audio` produces ordinary SRT; `emphasis_from_final_audio` uses the script's exact keyword spans to produce ASS; `none` produces no subtitle track. Never treat independent screen text as subtitles.
7. Assemble only accepted chronological segments, validate duration, portrait geometry, continuity and subtitles. For emphasized subtitles, visually verify keyword color/scale and confirm the rendered text still exactly matches the approved Thai line.
8. After acceptance, create one final-film record linked to the script, attach the playable file and fresh-read it. Increment accepted-film count exactly once.

Stop on exhausted execution limit, any dialogue mismatch, missing storyboard, failed acceptance or failed remote verification.
