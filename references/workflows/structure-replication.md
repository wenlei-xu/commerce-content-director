# Workflow: structure replication first frames

Read [first-frame-generation.md](first-frame-generation.md), [first-frame-execution.md](../first-frame-execution.md), [authority.md](../invariants/authority.md), [knowledge-library-contract.md](../invariants/knowledge-library-contract.md), [product-contract.md](../domain/product-contract.md), [product-execution-contract.md](../invariants/product-execution-contract.md), [interaction-substitution-protocol.md](../interaction-substitution-protocol.md), [first-frame-image-contract.md](../first-frame-image-contract.md), and [mutation-and-recovery.md](../invariants/mutation-and-recovery.md).

Use this workflow only when the user explicitly requests `structure_replication` / “结构复刻”. A generic request to “复刻” defaults to `high_fidelity_replication`; do not choose this mode merely because it is easier to adapt to another product.

## Preservation boundary

Structure replication preserves six source-level relationships:

1. **Story skeleton**: the narrative-task order, such as hook → problem → interaction → proof → payoff → CTA.
2. **Commercial proof chain**: when each selling point, visible proof and benefit is released, and the logical dependency between them.
3. **Relative pacing**: which beats are brief, held for proof, accelerated, or used as the payoff and close. The locked target script still owns exact timestamps.
4. **Emotional curve**: the order and purpose of reactions such as curiosity, anticipation, surprise, relief or satisfaction.
5. **Transferable visual style**: the source's capture medium, platform feel, camera height and subject distance, perspective, lighting/palette, exposure/contrast, texture/compression, depth of field, stability and motion character. Preserve the treatment, not product-specific geometry or impossible actions.
6. **Scene space**: when the source evidence is useful and the user wants it reused, preserve the source frame's spatial layout, camera direction, background geometry, lighting direction, subject scale and action staging. The source scene is a space authority only; it is not identity authority.

It does not require source shots, exact framing, specific actions, people/animals, original lines or exact claims to remain unchanged. Product-conflicting shots and actions may be rewritten when the target still preserves the source narrative role and proves the target-product benefit honestly. Do not replace a compatible source visual treatment or reusable scene space with generic studio, cinematic or premium styling unless the user explicitly requests a style change.

## Action-substitution boundary

Before deciding that a source action conflicts, split it into two layers:

1. **Product-specific hardware mechanism**: the source product's physical mechanism or component, including fixed mounts or suction, elastic elements, sound-making units, detachable parts, and their specific operating paths.
2. **Transferable behavior and narrative function**: the visible human or animal behavior and its story purpose, including tugging, chasing, biting, carrying, competing for an item, and excitement reactions.

Only a conflict in the first layer authorizes a replacement. A changed or unavailable hardware mechanism must not automatically delete a compatible second-layer behavior. When the target has an evidence-backed contact point or attachment path, preserve the behavior's narrative function through that real target interaction. Replace only the mechanism, force path, or contact path that conflicts with target-product facts.

If a transferable behavior is not supported by the target product, record the missing evidence and design another target-supported behavior with the same story role, pacing cue, proof purpose, and emotional transition. Do not silently collapse it into generic sniffing, pawing, or food-search behavior merely because the source hardware differs.

When the target product has a fixed integrated visual structure, preserve every integral component and its relative position while adapting the behavior. Change the contact point, pulling path, framing or camera angle before considering a different action; never make the product appear to lose, relocate or reconnect a component just to imitate the source action.

## Visual-style contract

Create `plan/source-visual-style-profile.json` from the accepted breakdown and available source evidence. Record the dimensions above, cite the evidence and separate stable global treatment from segment-specific variation. The profile must include `style_fingerprint_en` and `anti_style_constraints_en` as concise English control text. Copy both values verbatim into `source_visual_style` in `plan/generation-prompt-plan.json`; the compiler must pass them into every target first-frame Segment. If scene reuse is selected, route at most one cleaned `source_scene_reference` per Segment. It controls only scene space, camera, light and spatial staging; it must never control target subject, target product, text, logo or source-specific hardware identity. Source action frames remain planning evidence only.

## Source-to-target contract

Before writing the target script, create `plan/source-structure-map.json`. For every source narrative segment, record its story role, commercial function, proof purpose, relative pacing cue, emotional state/transition and CTA relationship. Cite accepted breakdown evidence and source time range, then label source-specific visual elements as `not_preserved_by_mode`.

Create `plan/source-target-structure-correspondence.json`. Map each source narrative segment to ordered target Beat IDs and explain how the target beat preserves the source story role, proof purpose, pacing relationship and emotional function. For every changed interaction, record the source hardware mechanism, transferable behavior, target contact path, and whether the behavior is `preserved`, `adapted_with_product_reason`, or `not_supported_with_evidence`. A target product may require different scenes and actions, but it must not remove a required proof step or replace the source's selling logic with a generic product introduction.

Use `subject_strategy=structure_only`. Route approved target product and subject anchors when they are visible. Do not route `source_segment_start` or `source_segment_result` into first-frame generation. When the source scene is intentionally reused, `source_scene_reference` is the only permitted source-frame role: it is a scene-space reference, not a subject/product/action-frame reference. The source visual-style profile and optional scene reference are the permitted source handoff.

## Review gate

Before human review, create `plan/source-structure-similarity-review.json`. Compare the source and target side by side for the five preserved relationships above. Classify each source segment and each style dimension as `preserved`, `adapted_with_product_reason`, or `missing`, with evidence.

Fail the mode when the target loses the source narrative order, skips an essential proof function, changes the relative pacing so the payoff or proof no longer lands in the same role, flattens the emotional curve into a generic demonstration, discards the transferable visual treatment or selected scene space without a documented reason, or removes a target-supported transferable behavior solely because the source hardware mechanism changed. Do not fail merely because the target uses different product-conflicting shots, mechanisms, contact paths, subjects or scenes when scene reuse was not selected; those differences are expected in this mode.
