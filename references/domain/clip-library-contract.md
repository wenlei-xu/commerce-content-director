# Clip library contract

The clip-first workflow uses two reusable media libraries. They are separate from scripts, first-frame approvals and final-film records.

Terminology is intentional: `草稿库` is temporary staging for generated
mother clips, while `精选片段库` is the only destination called
“沉淀”. A clip is not considered沉淀 unless it is written to
`精选片段库`.

## Draft clip library

Temporarily store the complete generated 10-second mother clip after a
video-generation Job finishes. Keep the original playable file unchanged so it
can be reviewed again or used to derive a selected clip. A draft record is not
a沉淀结果.

Required fields:

- `video_attachment` — original 10-second video
- `product_link` — product or SKU
- `generation_prompt` — the actual submitted video prompt
- `generated_at` — generation time
- `status` — 待筛选、入选 or 淘汰

Do not store the product anchor as a library field. The product anchor remains a required generation input and belongs to the execution package.

## Selected clip library

Store an extracted, independently playable clip as the沉淀结果 and reusable
media asset. Do not require or expose a source-record field or extraction-time
field; once selected, the clip is treated as an independent asset.

Required fields:

- `video_attachment` — selected clip video
- `product_link` — product or SKU
- `tags` — reusable selling-point or scene tags
- `visual_description` — what the clip visibly shows
- `voiceover_direction` — suitable future spoken direction, not final audio
- `status` — 待筛选、可用 or 淘汰

## Selected-clip admission gate

Being successfully generated or successfully extracted is not enough for a
clip to enter 精选片段库. The following three checks are the only blocking
quality requirements:

1. **动作完整，有开始和结果** — the entering state, main action and visible
   result are all present. Do not cut through the key bite, reveal,
   treat-loading, washing or interaction moment. A static product shot must
   have a stable readable hold.
2. **画面稳定，无穿帮、变形** — no black frame, severe blur, accidental
   transition, frozen frame, subject morphing, product deformation or visible
   continuity break. If a clip contains more than one shot, the shots must
   still cut cleanly as one usable unit.
3. **视频干净可播放** — the file is independently playable, portrait 9:16,
   and free of broken frames, generated subtitles, final CTA and watermark.
   Keep final voiceover out by default; retain audio only when it is clean
   environmental sound or explicitly requested.

Product/SKU, tags, visual description and voiceover direction remain required
writeback fields, but they are metadata completeness requirements rather than
additional video-quality gates. If any of the three blocking checks is
uncertain or fails, do not call the clip沉淀 and do not write it to
精选片段库. Keep the mother clip in 草稿库 for review, or mark it 淘汰 when
the failure is conclusive. Only an explicit human selection or selection rule
may move a candidate into 精选片段库 with `status=可用`.

## Reuse identity and tagging

The selected clip library distinguishes the product that owns the current
media from the level at which that media can be reused. Keep `product_link`
canonical and do not invent a SKU code:

- Use the exact product name when the clip shows product-specific geometry,
  material, structure or interaction.
- Append `｜SKU-...` only when a real SKU code is supplied by the product
  authority.
- Use `通用` for product-agnostic media, or `通用｜品类名称` when the clip is
  reusable within a product category but still needs a category-matched
  product.

Use the `tags` multi-select field with short prefixed tags. Normally keep a
record to 3–5 tags and select only the dimensions that are relevant:

- `用途｜` — 钩子、产品展示、卖点证明、玩法演示、收尾
- `动作｜` — 拆家、抢玩具、啃咬、塞食、掏食、叼回、冲洗、互动
- `卖点｜` — 耐磨耐咬、辅助洁牙、益智漏食、方便清洁、一体结构
- `复用｜` — 通用、品类可复用、单SKU

Do not mix unprefixed roles, actions and benefits in the same tag namespace.
Do not tag a benefit that is not visibly demonstrated or supported by product
facts. A reusable spoken sentence or sentence pattern belongs in the sentence
template library; `voiceover_direction` stores only future delivery guidance,
not final copy.

Examples:

```text
product_link: 菠萝狗狗玩具
tags: 用途｜钩子、动作｜抢玩具、复用｜品类可复用

product_link: 菠萝狗狗玩具
tags: 用途｜卖点证明、动作｜啃咬、卖点｜耐磨耐咬、卖点｜辅助洁牙、复用｜单SKU
```

## Boundaries

- The default clip-production deliverable is a complete 10-second draft clip, not a final film.
- The clip library does not burn in final subtitles or final voiceover. Final voiceover and subtitles are created only after a clip sequence is selected for a final film.
- A clip-generation Job must still route the approved `product_anchor` as an input asset. Omitting it is an execution failure, even though the draft library does not store it.
- Do not create a selected-clip record until a human or an explicitly requested selection rule marks the extracted clip as usable.
- A rejected clip remains review evidence in the draft library; do not silently overwrite or delete it.
