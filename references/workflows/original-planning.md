# Workflow: original planning handoff

Read [authority.md](../invariants/authority.md), [content-field-contract.md](../invariants/content-field-contract.md), [configuration.md](../configuration.md), [product-contract.md](../domain/product-contract.md), [subject-contract.md](../domain/subject-contract.md), and [content-task-contract.md](../domain/content-task-contract.md).

This workflow ends at a validated local planning handoff. It does not generate storyboard images, create content-library records, upload board attachments, or submit video Jobs.

1. Run the public preflight and snapshot the active configuration, target language, current original rules, selected product, selected subject, and one active original planning task.
2. Resolve product facts and approved claims directly from the product record. Resolve a recurring subject from the subject contract when the plan uses one across shots.
3. Generate multiple internal directions. Reject any direction without fact support, credible phone-video execution, compliance support, or required assets. Select one direction using product fit, evidence density, conversion strength, UGC plausibility, executability, and compliance.
4. Write the task-level planning package: title, audience/problem, one to three selected product value propositions, one core idea, one hook, one narrative summary, commercial goal, one proof action, one CTA, task-specific creative requirements, rules snapshot, and self-check. Keep facts, assumptions, and unresolved questions separate.
5. Do not write a complete timed script, shot-by-shot timeline, storyboard prompt, or competing content formats at this stage. Those belong to the selected `content_id` in the storyboard workflow.
6. Validate that the task, product, subject, language, target duration, selected direction, and configuration snapshot are fixed. The handoff is complete only when the package has all required task-level artifacts, passes the field conflict checks, and has no unresolved authority conflict.

Pass the package to [storyboard-generation.md](storyboard-generation.md) only after the handoff criterion is satisfied.
