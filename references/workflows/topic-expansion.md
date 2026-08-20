# Workflow: topic expansion and task convergence

Read [authority.md](../invariants/authority.md), [content-field-contract.md](../invariants/content-field-contract.md), [configuration.md](../configuration.md), [product-contract.md](../domain/product-contract.md), [subject-contract.md](../domain/subject-contract.md), and [content-task-contract.md](../domain/content-task-contract.md).

Use this workflow only when the user explicitly asks to expand a topic or names a `mother_topics` record.

1. Fresh-read one `mother_topics` record in its schema-resolved pending-expansion state. Require product, platform/account, subject pool, mother description, commercial goal, target duration, requested count, convergence method, and valid configuration snapshot.
2. Read the directly linked product, usable subject candidates, and the unique current original-rules record. Generate two to three times the requested rough directions internally.
3. Apply product-fact, compliance, asset-executability, and distinctiveness gates. Write exactly the requested number of candidates. Every candidate has one content format, one `core_idea`, one hook, one proof action, one CTA, and one to three approved product value propositions. Do not copy product mechanics, mother-topic defaults, or a timeline into candidate creative fields. Score only admitted candidates with the active configuration and record tie-break evidence.
4. For manual selection, write candidates, move the mother topic to its schema-resolved awaiting-selection state, and stop. The user may select any non-empty subset.
5. For automatic Top N, select exactly the configured count from admitted candidates by the configured score and deterministic tie-breaks.
6. After selection is locked, create exactly one `planning_tasks` record per selected candidate. Use `mother_id + candidate_id` as the idempotency key. Copy the selected candidate's one direction, selected value propositions, fixed subject mapping, and task-specific execution delta only; keep product mechanics in the product record and shared defaults in the mother topic. Verify both relationship directions, and move the mother topic to converged only after every selected candidate is linked.

Do not create storyboards, content versions, media, or video Jobs in this workflow. If any write or verification fails, preserve successful records, mark the run failed, and do not retry with a new identity.
