# Workflow: storyboard generation and script fidelity

Read authority.md, script-contract.md, script-validation.md, product-contract.md, subject-contract.md, product-execution-contract.md, reference-asset-contract.md, image-prompt-contract.md and delivery-contract.md.

Input is one freshly read locked script with script check status passed. Read its structured script, accepted product assets, subjects and configuration. Never infer a different creative direction or rewrite the script.

1. Compile the generation plan from Beat and Segment objects.
2. Map every script Beat to one or more storyboard panels; retain stable Beat, Line and Text IDs in the local package.
3. Generate boards with approved product/subject assets and review product action, state, continuity and timing.
4. Run storyboard fidelity validation. Every Beat, key product action and assigned spoken line must have coverage.
5. Upload accepted boards to the script record, fresh-read attachments, set storyboard status to pending review or passed. Write video prompt only from the locked script and passed boards.

Stop before a script mutation if any required board, coverage or product-fidelity evidence fails.
