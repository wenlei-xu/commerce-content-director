# Workflow: storyboard generation and product fidelity

Read [authority.md](../invariants/authority.md), [content-field-contract.md](../invariants/content-field-contract.md), [mutation-and-recovery.md](../invariants/mutation-and-recovery.md), [configuration.md](../configuration.md), [product-contract.md](../domain/product-contract.md), [subject-contract.md](../domain/subject-contract.md), [content-task-contract.md](../domain/content-task-contract.md), [delivery-contract.md](../delivery-contract.md), [storyboard-spec.md](../storyboard-spec.md), and [interaction-substitution-protocol.md](../interaction-substitution-protocol.md) when applicable.

Use this workflow after an original-planning handoff or for a selected hook/structure/full-replication task. It owns final-generation boards and their product/subject review; it does not submit final-video Jobs.

1. Fresh-read the task, product facts and assets, subject identity, configuration snapshot, selected content version, script, language, and mode. Confirm that the content version has exactly one selected direction and that its script/timeline is not being inferred from competing candidates. Build one `product_asset_plan` per raw segment from actual shot risk.
2. Build the actual image array and position-to-role map. Validate every image's decoded type, MIME, dimensions, hash, count, and role before submission. Never assume an optional role occupies a fixed input position.
3. Use the configured storyboard-image capability from the model catalog. Submit one complete board per configured raw segment with the configured grid, timing, reading order, zero gutter, natural phone-video texture, and no readable text/UI/watermark. Do not locally compose or split a returned board.
4. Review every panel for product identity, scale, openings, `loading_path`, `dispensing_path`, subject continuity, timing, scene continuity, and text contamination. A hard-fact mismatch is FAIL; a documented human-review warning remains unresolved until the required review occurs.
5. Run the configuration-profile storyboard validator on every board. Retain prompts, role maps, hashes, validator results, and visual review in the local package.
6. When every board is present, validated, and accepted, stage the content-library record, upload the complete board set idempotently, re-read the attachment set, and only then publish the schema-resolved pending-review state. A failed upload remains a resumable run, not a new content version.

The workflow stops before any content-library mutation when a board is missing, pending, failed, unvalidated, or visually rejected.
