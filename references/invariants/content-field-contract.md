# Content field ownership contract

This contract is the single source of truth for the user-facing creative fields and their stage handoff. Keep each meaning at one stage and pass only the minimum selected values downstream.

## Field meanings

| Field | May contain | Must not contain |
| --- | --- | --- |
| `core_benefits` / 核心卖点 | One to three user-value propositions selected from approved product claims | Product openings, structural prohibitions, shot actions, CTA, timestamps, or an unapproved benefit claim |
| `core_idea` / 核心创意 | One narrative mechanism in the form “content mechanism → conflict/question → proof process → visible result” | Multiple content formats, a complete script, a product rule inventory, or several competing concepts |
| `creative_requirements` / 创作要求 | Execution constraints unique to the selected task: language, subject, performance balance, sound treatment, capture texture, and other task-specific presentation choices | Mother-topic defaults, product hard facts, structural prohibitions, repeated candidate sets, multiple subjects, multiple formats, multiple CTAs, or a shot-by-shot timeline |

The direction fields are also separate and singular at task handoff:

- `content_format` / 内容形式 is one single-select value copied from the selected candidate. The content-library `legacy_content_format_field` multi-select is a legacy snapshot and is never a source of truth.
- `proof_action` / 主要证明动作 is one observable proof process, not a scene description, full script, or timeline.
- `cta` / 互动 / CTA is one interaction or call to action. It is not embedded in `creative_requirements`.

## Ownership by stage

- `products` owns hard facts, approved claims, product assets, and structural review rules. Loading and dispensing paths, openings, detachable parts, and prohibited interactions stay there.
- `mother_topics` owns the shared direction, commercial goal, target duration, subject pool, and public execution boundaries. It does not own a candidate's script or format.
- `candidates` owns one content format, one `core_idea`, one hook, one proof action, one CTA, and its admission/score evidence. Each candidate is a distinct direction. Its old `legacy_subject_link` field is compatibility-only; use role-specific subject links when available.
- `planning_tasks` owns one selected candidate, selected core benefits, one content format, one proof action, one CTA, a fixed role mapping, and the selected candidate's `creative_requirements`. It must not contain a timeline. The formula `count_formula_field` is authoritative; `legacy_manual_count_field` is a historical snapshot and must not be incremented.
- `content_library` owns the concrete script, timed dialogue, shot summary, storyboard prompts, final-generation prompts, and one canonical `content_format` for one `content_id`. Its old `legacy_content_format_field` and `legacy_subject_link` fields are compatibility snapshots only.

## Normalization rules

1. Keep product mechanics out of core benefits. A bottom opening, side lattice, one-piece construction, and prohibited leaf/cap action are injected from the product contract during generation and review.
2. Keep shared mother-topic requirements in the mother topic once. Copy only a task-specific delta into `creative_requirements`.
3. Generate one candidate per content format or narrative mechanism. Do not merge reply, POV, test, challenge, and ASMR directions into one task.
4. Resolve subjects by role: at most one `person_subject_link` and at most one `animal_subject_link` per task/version. A subject pool may contain alternatives, and a person-plus-one-animal pair is valid; multiple animal identities or breeds are not.
5. Put exact `0–3s` or other shot timing only in the content-version script/storyboard after a candidate is selected.
6. A benefit such as “helps expend energy” is allowed only when the product record marks the claim as approved.

## Conflict checks

Stop before task creation when any of these occur:

- presenter-majority and owner-minimal requirements appear together;
- ASMR is paired with a continuous spoken-dialogue requirement without an explicit audio policy;
- more than one subject identity or breed is selected;
- a candidate contains more than one content format, core idea, or CTA;
- a task-level requirement repeats mother defaults or restates product hard facts;
- the canonical `content_format` is empty, multi-valued, or differs from the selected candidate;
- a task/version uses more than one person or more than one animal subject, or uses the legacy multi-link field as the selection source;
- a task contains a shot timeline or a candidate list instead of a selected direction.
