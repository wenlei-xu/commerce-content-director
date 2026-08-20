# Workflow: final video generation and acceptance

Read [authority.md](../invariants/authority.md), [execution-accounting.md](../invariants/execution-accounting.md), [mutation-and-recovery.md](../invariants/mutation-and-recovery.md), [configuration.md](../configuration.md), [content-task-contract.md](../domain/content-task-contract.md), [delivery-contract.md](../delivery-contract.md), and [video-prompt-contract.md](../video-prompt-contract.md).

Use this workflow only after the exact content-library record is freshly read as approved and the user explicitly names that record or `content_id`.

1. Fresh-read the exact content version, links, approved boards, script, target language, video prompt, business execution limit, and qualifying linked final films. Resolve the execution slot using [execution-accounting.md](../invariants/execution-accounting.md); do not submit when the count is inconsistent or exhausted.
2. Build the actual per-segment input array and role map from the accepted boards and routed product/subject assets. Write every prompt using the five blocks in [video-prompt-contract.md](../video-prompt-contract.md), with the actual catalog-selected portrait-video model key.
3. Submit asynchronous Jobs with stable attempt identities. Wait through the configured deadline; non-terminal states are not failures. Preserve raw outputs and deliberate regeneration reasons.
4. Assemble only the chronological configured segments. Verify stream presence, codec readability, target duration, audio, and range coverage.
5. Run ASR on the assembled video's final audio. Compare the actual spoken language and words with the approved script, produce aligned subtitle timing and SRT, and burn subtitles unless the approved task explicitly has no speech or the user explicitly requests no subtitles.
6. OCR and review the burned candidate for subtitle timing, unintended text, product identity, subject continuity, scene, audio, and technical acceptance. Keep raw, intermediate, final, and rejected artifacts separately named.
7. After acceptance, create one idempotent final-film record, attach the complete playable file, fresh-read its link/token/media, and increment the accepted-film count exactly once. Any failure leaves evidence and a resumable run; it does not justify a duplicate final-film record.
