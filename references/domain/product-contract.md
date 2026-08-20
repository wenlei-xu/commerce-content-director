# Product contract

Resolve exactly one active `products` record directly from the product table by the user's name or ID. A task relationship is not a product lookup substitute.

Required facts are the schema-resolved product status, hard facts, generation notes, review requirements, core benefits, approved/prohibited claims, default anchor, and any detail or scene assets required by the planned shots. Product facts, approved claims, prohibited claims, structure, scale, openings, and interaction paths come only from this record.

When a task selects one to three core benefits, copy only the selected value propositions and their product-record provenance into the task. Do not copy structural mechanics into the benefits field.

For each Job, create `product_asset_plan` from shot risk:

- `default_anchor` is the identity baseline for every relevant Job.
- `detail_assets` are required for structure-sensitive shots.
- `scene_assets` are required for scale, placement, or real-use interaction shots.
- A recurring subject adds a subject anchor without displacing required product evidence.

Record each asset's schema field, filename, remote token, local hash, role, input position, and segment mapping. Validate bytes, MIME, dimensions, hash, count, and role mapping before submission. Do not infer an opening, loading path, dispensing path, connection, or permitted action from a name, prior output, or model memory.
