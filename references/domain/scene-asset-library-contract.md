# Scene asset library contract

The `场景资产库` is the reusable visual-context roster for ordinary, repeatable production environments. It is not a script, storyboard approval surface or product-fact source.

## Eligibility

A scene is eligible for new generation only when `状态=可用` and `场景锚点` contains a valid image. `状态=禁用` is reversible maintenance state: preserve the record and historical links, but exclude it from automatic selection and generation inputs. The current Feishu field metadata and `config/base-schema.json` are authoritative for field names and option values.

## Selection

Select by the current market or language, `场景类型`, the Beat's action surface, usable activity area and the requested capture treatment. Prefer a scene that already matches the intended room and camera treatment over a generic “nice-looking” image. Persist the selected `场景资产ID`, record ID, anchor filename or token, and selection reason in the local run package.

## Authority boundary

Scene anchors may establish room geometry, light direction, camera position, scale context, open floor or counter space, and lived-in smartphone texture. They do not establish product geometry, product claims, subject identity, dialogue, text, logos or permitted interaction. Product records, selected subject anchors and the locked structured script remain authoritative for those facts.

## Capture treatment

Default scene treatment is ordinary user-generated phone capture: neutral white balance, natural window or household light, realistic exposure, mild phone-lens perspective and modest sensor texture. Avoid yellow/orange grading, glossy showroom styling, studio symmetry, cinematic lighting and excessive HDR unless the user explicitly asks for them. Keep enough uncluttered space for the planned product or subject action.
