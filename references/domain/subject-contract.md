# Subject contract

When identifiable subjects recur across shots, resolve role-specific usable `subject_assets` records with anchors and stable identity descriptions. A task may bind at most one person and at most one animal: prefer explicit `person_subject_link` and `animal_subject_link` links, and never use the legacy multi-link `legacy_subject_link` field as the selection source. If an explicit role link is absent, select deterministically by task role/type, proof scene, product context, then record ID; multiple animal identities or breeds are a conflict.

Pass the same subject anchor and identity description to every applicable Job. Review species/type, markings, face, body size, ears or hair, accessories, and role independently from product review. “Same person” or “same dog” is not an identity lock.

If no recurring subject is planned, record `subject_identity: none` in the local package. Never invent a subject asset or copy identity facts from a reference video into the product or subject table.
