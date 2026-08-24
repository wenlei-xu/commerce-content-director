# Workflow: storyboard generation and script fidelity

Read authority.md, script-contract.md, script-validation.md, product-contract.md, subject-contract.md, product-execution-contract.md, reference-asset-contract.md, image-prompt-contract.md, [flow2api-image-execution.md](../flow2api-image-execution.md) and delivery-contract.md.

Input is one freshly read locked script with script check status passed. For a user-explicit local storyboard request that does not ask for Feishu archival, a locally validated script package may be locked by that authorization and used directly; do not create remote direction or script records merely to satisfy the production chain. Read its structured script, accepted product assets, subjects and configuration. Never infer a different creative direction or rewrite the script.

1. Run the workflow-scoped preflight, fresh-read the active configuration and Flow2API image-model catalog, then lock the exact available model ID into the configuration snapshot and generation plan. Set `executor` to `flow2api_mcp`; no other value is valid for a storyboard-image Job.
2. Compile the generation plan from Beat and Segment objects.
3. Map every script Beat to one or more storyboard panels; retain stable Beat, Line and Text IDs in the local package.
4. Prepare approved product, subject and routed reference images with `scripts/prepare_flow_inputs.py`. Submit, wait and retrieve each board only through the registered Flow2API MCP sequence defined by the execution contract.
5. Review product action, state, continuity and timing, then run storyboard fidelity validation. Every Beat, key product action and assigned spoken line must have coverage.
6. Upload accepted boards to the script record, fresh-read attachments, set storyboard status to pending review or passed. Write video prompt only from the locked script and passed boards.

Stop before a script mutation if any required board, coverage or product-fidelity evidence fails. A Flow2API health, catalog, submission, wait or result failure remains a resumable Flow2API failure; never retry it through GPT Image.
