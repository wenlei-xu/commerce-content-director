# Workflow: structure replication storyboard

Read [storyboard-generation.md](storyboard-generation.md), [gpt-image-2-execution.md](../gpt-image-2-execution.md), [authority.md](../invariants/authority.md), [knowledge-library-contract.md](../invariants/knowledge-library-contract.md), [product-contract.md](../domain/product-contract.md), [product-execution-contract.md](../invariants/product-execution-contract.md), [image-prompt-contract.md](../image-prompt-contract.md), and [mutation-and-recovery.md](../invariants/mutation-and-recovery.md).

Use this workflow only when the user explicitly requests `structure_replication` / “结构复刻”. A generic request to “复刻” defaults to `high_fidelity_replication`; do not choose this mode merely because it is easier to adapt to another product.

## Preservation boundary

Structure replication preserves five source-level relationships:

1. **Story skeleton**: the narrative-task order, such as hook → problem → interaction → proof → payoff → CTA.
2. **Commercial proof chain**: when each selling point, visible proof and benefit is released, and the logical dependency between them.
3. **Relative pacing**: which beats are brief, held for proof, accelerated, or used as the payoff and close. The locked target script still owns exact timestamps.
4. **Emotional curve**: the order and purpose of reactions such as curiosity, anticipation, surprise, relief or satisfaction.
5. **Transferable visual style**: the source's capture medium, platform feel, camera height and subject distance, perspective, lighting/palette, exposure/contrast, texture/compression, depth of field, stability and motion character. Preserve the treatment, not product-specific geometry or impossible actions.

It does not require source shots, source frames, exact framing, specific actions, people/animals, locations, original lines or exact claims to remain unchanged. Product-conflicting shots and actions may be rewritten when the target still preserves the source narrative role and proves the target-product benefit honestly. Do not replace a compatible source visual treatment with generic studio, cinematic or premium styling unless the user explicitly requests a style change.

## Visual-style contract

Create `plan/source-visual-style-profile.json` from the accepted breakdown and available source evidence. Record the dimensions above, cite the evidence and separate stable global treatment from segment-specific variation. The profile must include `style_fingerprint_en` and `anti_style_constraints_en` as concise English control text. Copy both values verbatim into `source_visual_style` in `plan/generation-prompt-plan.json`; the compiler must pass them into every target storyboard Segment. Source frames remain planning evidence only in this mode and must not be routed as generation inputs.

## Source-to-target contract

Before writing the target script, create `plan/source-structure-map.json`. For every source narrative segment, record its story role, commercial function, proof purpose, relative pacing cue, emotional state/transition and CTA relationship. Cite accepted breakdown evidence and source time range, then label source-specific visual elements as `not_preserved_by_mode`.

Create `plan/source-target-structure-correspondence.json`. Map each source narrative segment to ordered target Beat IDs and explain how the target beat preserves the source story role, proof purpose, pacing relationship and emotional function. A target product may require different scenes and actions, but it must not remove a required proof step or replace the source's selling logic with a generic product introduction.

Use `subject_strategy=structure_only`. Route approved target product and subject anchors when they are visible. Do not route `source_segment_start`, `source_segment_result` or `source_contact_sheet` into storyboard generation; source evidence is planning material only in this mode. The source visual-style profile is the permitted style handoff.

## Review gate

Before human review, create `plan/source-structure-similarity-review.json`. Compare the source and target side by side for the five preserved relationships above. Classify each source segment and each style dimension as `preserved`, `adapted_with_product_reason`, or `missing`, with evidence.

Fail the mode when the target loses the source narrative order, skips an essential proof function, changes the relative pacing so the payoff or proof no longer lands in the same role, flattens the emotional curve into a generic demonstration, or discards the transferable visual treatment without a documented reason. Do not fail merely because the target uses different product-conflicting shots, actions, subjects or scenes; those differences are expected in this mode.
