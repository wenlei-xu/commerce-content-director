# Final-generation video prompt contract

Every final-generation prompt is for the fixed `omni_portrait` model. Each Job generates exactly one 10-second raw portrait 9:16 segment. The complete 20/30/40-second film is assembled from exactly 2/3/4 chronological Omni segments. Do not write a prompt for, or submit, another video model.

Read this contract before writing any Omni video-generation prompt for a portrait 9:16 Segment. It is not the contract for the storyboard-image Job: that Job has no storyboard-board input yet and must use the actual role map prepared by [storyboard-generation.md](workflows/storyboard-generation.md).

## Language and source-of-truth gate

Resolve `target_spoken_language` from the schema's language policy before writing the prompt. The current policy is `th` (Thai), so every spoken line, voice instruction, and timed dialogue window must be Thai. The surrounding generation prompt may be written in English or Chinese; it is control text, not spoken content. A task or script that requests Chinese, English, or another spoken language is a planning-data conflict: stop and fix the data before generation. Do not add a translated second dialogue line. If the selected audio mode is `natural_sound_only`, include no dialogue or voiceover at all.

## Segment-scoped dialogue gate

The approved full-film script and video prompt are planning sources, not payloads that may be copied unchanged into every Omni Job. Before writing prompts, create a dialogue allocation manifest that records each approved line's identity, exact text, absolute film timing, assigned Segment, and Segment-local timing.

- Assign each approved spoken line to exactly one 10-second Segment unless the approved script explicitly marks an intentional repeat.
- Rebase the assigned line's timing to the current Job's local `0.0–10.0s` window.
- Include only the current Segment's literal spoken lines in its prompt. Do not quote earlier or later Segment dialogue anywhere, including summaries, continuity context, examples, or negative instructions; use a generic instruction such as `Do not speak any other line` instead.
- A `natural_sound_only` Segment contains no spoken line.
- If any line crosses a Segment boundary or its assignment is ambiguous, stop before submission and fix the approved timing data. Do not improvise a split, duplicate the line, or let Omni continue it across Jobs.

Validate the complete prompt set as one unit before submitting any Job: every manifest line must occur in exactly its assigned prompt and no other prompt, subject only to an explicitly approved intentional repeat. Store the manifest and exact submitted per-segment prompts in the run package.

## The five mandatory blocks

### 1. INPUT IMAGE ROLES AND AUTHORITY

Name every routed Omni input by its actual position and role in every Segment prompt. The following is the default authority order, not a promise that every optional input exists:

- `storyboard_board`: authoritative only for chronology, timing, actions, camera intent and scene progression. Its product pixels and subject pixels never override approved product facts or the subject anchor.
- `product_anchor`: authoritative for overall product identity and proportions.
- `subject_anchor`: authoritative for recurring subject identity when a recurring subject exists.
- `product_detail`: authoritative for openings, lattice, holes, connections, and other structure-sensitive geometry.
- `product_scene`: authoritative for real-use context, scale, and placement, not for inventing product geometry.
- `continuity_frame`: authoritative for the handoff from the previous accepted Segment when routed; it cannot override product facts or subject identity.

The prompt must include the exact `position → role` mapping generated for that Job. Do not write `Input 3` as the subject if the subject was not routed, and do not silently omit a required detail or scene asset.

Product detail assets and confirmed product hard facts override conflicting product pixels in the storyboard or scene reference. The subject anchor and its identity description override a different animal or person shown in a storyboard or scene reference. If the inputs conflict in a way that cannot be resolved, stop before submission and record the conflict. Pass the same required inputs in the same role mapping to every applicable Segment; never rely on cross-Job memory.

### 2. PRODUCT STRUCTURE AND INTERACTION HARD CONSTRAINTS

Copy only the current `product-visual-facts.md` and confirmed product hard facts into this block. State the exact body, openings, proportions, connected parts, orientation, `loading_path`, `dispensing_path`, and permitted use action as separate facts. Never collapse them into one vague “loading/dispensing path”: the two paths may be identical or different only when the product record confirms it. If the confirmed product facts say both loading and dispensing use the single bottom circular hole, write that exact rule twice and state that the side lattice is neither an inlet nor an outlet. State prohibited alternatives literally: no invented openings, no top or side loading when prohibited, no side dispensing when prohibited, no detached crown/cap/lid, no separated parts, no alternate lattice, no altered scale. Do not use a product name or generic visual language to infer missing geometry.

### 3. SUBJECT IDENTITY LOCK

State that the routed `subject_anchor` and selected subject record are the only identity authority. Repeat the stable identity description in every Segment prompt: species/breed or person type, coat/skin or hair colors, markings, face, body size, age impression, ears/hair, and distinctive accessories where applicable. Require the exact same individual across all panels and Segment boundaries. Explicitly prohibit substitutions, including a different breed/type, different markings, different body size, or a generic replacement subject. A phrase such as “same dog” without the stable identity description is insufficient. If there is intentionally no recurring subject, state `主体身份不锁定` and do not imply continuity.

### 4. LANGUAGE, AUDIO AND TIMED DIALOGUE

State `target_spoken_language=th`, the voice type/style, audio behavior and every dialogue window assigned to the current Segment. Use only Segment-local `0.0–10.0s` times. Each assigned line must have an explicit start and end time and must be spoken exactly in Thai. The block headings and visual/product instructions may remain in English or Chinese. State whether the raw Omni segment should generate native voice audio or remain natural-sound-only. Spoken dialogue is audio only; it must never be visualized as text. Do not add a second-language translation or Chinese transliteration as an alternate spoken line. For spoken modes, write the actual approved Thai lines for this Segment only, state `no Mandarin and no Chinese speech`, and state `Do not speak any other line` without quoting dialogue assigned to another Segment.

### 5. NO TEXT AND CROSS-SEGMENT CONTINUITY

State: `No captions, subtitles, burned-in text, dialogue transcription, labels, lower thirds, logos, watermarks, UI, or readable text in any language.` The no-text rule applies even when the prompt contains dialogue lines. State the exact continuity handoff: Segment 02 starts from the last approved state of Segment 01, with the same subject, product, room, lighting, camera texture, scale, orientation and audio environment. Do not introduce a new room, animal/person, product design, visual style, or unexplained time jump at the boundary.

## Required assembly and validation

Use the five block headings verbatim or an unambiguous equivalent in every final-generation prompt. Before submission, validate that:

1. all five blocks are present;
2. the position → role map matches `product_asset_plan` and the model input array;
3. only the approved target language appears in spoken lines;
4. the prompt contains no conflicting product geometry or subject description;
5. every Segment repeats the subject identity lock and continuity handoff;
6. the no-text rule is explicit and does not conflict with the dialogue block;
7. every approved spoken line appears in exactly its assigned Segment prompt and no other prompt, except an explicitly approved intentional repeat;
8. every dialogue window uses Segment-local `0.0–10.0s` timing; and
9. no prompt quotes dialogue from an earlier or later Segment anywhere in its text.

If the prompt fails any check, do not submit the Job. Fix the task/script/data conflict first or stop and report it.

After generation, run ASR on each raw Segment before assembly. Reject and regenerate only the affected Segment when ASR shows an omitted assigned line, an unapproved added line, or dialogue belonging to another Segment. Assembly does not waive this per-Segment gate; run full-film ASR again after assembly to verify order and boundaries.
