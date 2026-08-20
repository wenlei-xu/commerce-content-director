# Content field ownership contract

This contract is the single source of truth for the three user-facing fields 核心卖点、核心创意、创作要求. Keep each meaning at one stage and pass only the minimum selected values downstream.

## Field meanings

| Field | May contain | Must not contain |
| --- | --- | --- |
| `core_benefits` / 核心卖点 | One to three user-value propositions selected from approved product claims | Product openings, structural prohibitions, shot actions, CTA, timestamps, or an unapproved benefit claim |
| `core_idea` / 核心创意 | One narrative mechanism in the form “content mechanism → conflict/question → proof process → visible result” | Multiple content formats, a complete script, a product rule inventory, or several competing concepts |
| `creative_requirements` / 创作要求 | Execution constraints unique to the selected task: language, subject, performance balance, sound treatment, capture texture, and other task-specific presentation choices | Mother-topic defaults, product hard facts, structural prohibitions, repeated candidate sets, multiple subjects, multiple formats, multiple CTAs, or a shot-by-shot timeline |

## Ownership by stage

- `products` owns hard facts, approved claims, product assets, and structural review rules. Loading and dispensing paths, openings, detachable parts, and prohibited interactions stay there.
- `mother_topics` owns the shared direction, commercial goal, target duration, subject pool, and public execution boundaries. It does not own a candidate's script or format.
- `candidates` owns one content format, one `core_idea`, one hook, one proof action, one CTA, and its admission/score evidence. Each candidate is a distinct direction.
- `planning_tasks` owns one selected candidate, selected core benefits, one fixed subject mapping, and the selected candidate's `creative_requirements`. It must not contain a timeline.
- `content_library` owns the concrete script, timed dialogue, shot summary, storyboard prompts, and final-generation prompts for one `content_id`.

## Normalization rules

1. Keep product mechanics out of core benefits. A bottom opening, side lattice, one-piece construction, and prohibited leaf/cap action are injected from the product contract during generation and review.
2. Keep shared mother-topic requirements in the mother topic once. Copy only a task-specific delta into `creative_requirements`.
3. Generate one candidate per content format or narrative mechanism. Do not merge reply, POV, test, challenge, and ASMR directions into one task.
4. Select exactly one subject asset per task when a recurring subject is used. A subject pool may contain alternatives, but a task and its content version may not mix breeds or identities.
5. Put exact `0–3s` or other shot timing only in the content-version script/storyboard after a candidate is selected.
6. A benefit such as “helps expend energy” is allowed only when the product record marks the claim as approved.

## Conflict checks

Stop before task creation when any of these occur:

- presenter-majority and owner-minimal requirements appear together;
- ASMR is paired with a continuous spoken-dialogue requirement without an explicit audio policy;
- more than one subject identity or breed is selected;
- a candidate contains more than one content format, core idea, or CTA;
- a task-level requirement repeats mother defaults or restates product hard facts;
- a task contains a shot timeline or a candidate list instead of a selected direction.
