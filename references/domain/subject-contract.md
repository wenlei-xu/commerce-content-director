# Subject contract

The `主体资产库` is a reusable identity roster, not a prompt suggestion list. A subject is eligible for a new task only when `状态=可用`, `主体锚点` is present, and `主体身份描述` is complete. `状态=禁用` is a reversible maintenance state: keep the record, anchor, and historical links, but exclude it from all new automatic selection and new generation input routing. Never rewrite a locked script because its subject was later disabled.

When identifiable subjects recur across shots, resolve role-specific usable `subject_assets` records. A task may bind at most one person and at most one animal: prefer explicit `person_subject_link` and `animal_subject_link` links, and never use the legacy multi-link `legacy_subject_link` field as the selection source. An explicit binding to a disabled record is a conflict for a new task and must stop with a clear repair request; it is not silently replaced.

If no explicit binding exists, select from the task's `主体资产池` first, then the eligible global roster. Apply the subject rotation policy from `config/base-schema.json`: avoid the same individual for the previous two jobs when another eligible animal exists, avoid the same breed for the immediately previous job when another eligible breed exists, and use a stable tie-breaker only after those diversity rules. Persist the selected record ID and selection reason in the local run package so a later run cannot default to the first record again. Do not use random selection without recording the result.

Pass the same subject anchor and identity description to every applicable Job. Review species/type, breed, markings, face, body size, ears or hair, accessories, and role independently from product review. “Same person” or “same dog” is not an identity lock. Never transfer a source video's animal identity into the subject library unless the user explicitly approves it as a new asset.

For dog coverage, prioritize visually distinct, locally recognizable identities rather than many near-duplicates. The recommended next additions are Chinese rural dog / 中华田园犬, 柴犬, 柯基, 拉布拉多, 法斗, and for Thai-facing content 泰国邦卡犬、泰国脊背犬、吉娃娃、西施犬、博美犬，以及一只外观明确的本地混种犬。 These are a roster proposal, not usable records: each new record still needs its own approved anchor, stable identity description, breed/type, default scene, and `状态=可用` review.

If no recurring subject is planned, record `subject_identity: none` in the local package. If the eligible animal roster is empty, stop and report the missing anchor/identity evidence instead of inventing a dog.
