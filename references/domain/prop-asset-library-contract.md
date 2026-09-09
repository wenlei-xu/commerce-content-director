# Prop asset library contract

The `道具资产库` stores reusable physical props that appear in a scene but are not the current product, selected subject, or environment. It is a retrieval and identity layer, not a script authority.

## Authority boundary

- A prop asset owns the prop's identity, appearance, state variant and reuse tags.
- A script owns when and why the prop appears in the Beat timeline.
- A product record owns product identity, product facts, claims and permitted product interaction. A prop must never be used as a product anchor or product-fact source.
- A subject record owns pet/person identity. A prop does not become a subject merely because a pet interacts with it.

## Record shape

Each prop record should include:

- `道具资产ID` — stable canonical ID, such as `PROP-DUCK-001`;
- `道具名称`, `道具类别`, `道具角色` and controlled `复用标签`;
- `道具状态` — the visual state represented by the routed anchor, such as `完整`, `咬损`, `破碎`;
- `道具锚点` — the image that proves that exact identity and state;
- `外观描述` and optional `尺寸参考`;
- `适用品类` and `复用范围`;
- `资产状态` — `草稿`, `待审核`, `可用` or `停用`;
- `来源与备注` for provenance and unresolved state variants.

Do not create a large direct relation from every prop to every script template. Use controlled tags for retrieval. Bind the selected `道具资产ID` and state to the current script/Beat only when the prop is actually used.

## State variants

A complete reference does not prove a damaged state. Keep state variants explicit. If a script needs a bitten or broken version and only a complete anchor exists, mark that variant as missing or pending and stop before generation until a matching approved state anchor exists.

## Acceptance

Only `资产状态=可用` records with a valid anchor for the requested state may enter new generation inputs. A record can remain `待审核` while its identity anchor is saved locally, but it is not eligible for automatic selection.
