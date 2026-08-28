# Approved short-video classification

This taxonomy makes the short-video breakdown library searchable without turning it into a deep folder hierarchy. It is applied after a valid breakdown exists and does not replace the ten commercial narrative fields, evidence fields, or review status.

## Fields and cardinality

Use the following fields in `short_video_breakdowns`:

| Field | Type | Rule |
|---|---|---|
| `主类目` | Single select | Exactly one production/content format. |
| `内容目的` | Single select | Exactly one primary funnel job. |
| `主叙事结构` | Single select | Exactly one dominant way the video unfolds. |
| `证明方式` | Multi-select | Select the visible proof mechanisms, normally no more than three. |
| `场景标签` | Multi-select | Select the relevant use and capture contexts, normally no more than three. |
| `拍摄形式` | Single select | Exactly one dominant capture format. |
| `CTA分类` | Single select | Exactly one dominant purchase/interaction ending. |

The fields are independent. A video can be `测评和开箱` as its main category, `容量实测` as its narrative structure, and `链接CTA` as its ending. Do not force the category to repeat the narrative structure.

## Controlled vocabulary

### 主类目

- `平替` — price comparison or value substitution is the content frame.
- `产品拍摄` — product-led demonstration with little or no creator-led explanation.
- `测评和开箱` — reveal, unboxing, comparison or test-led content.
- `使用场景模拟` — a lived-in use case or creator experience is the primary frame.

### 内容目的

- `拉新` — earns attention through novelty, emotion, or a recognizable problem.
- `种草` — builds preference and desire through aesthetic, experience, or proof.
- `转化` — gives a concrete purchase reason, offer, link, or direct recommendation.

### 主叙事结构

- `价格反差`
- `场景点名`
- `问题—解决方案`
- `开箱揭晓`
- `容量实测`
- `清单穷举`
- `多色/风格比较`
- `真人体验推荐`

### 证明方式

- `物品实装`
- `结构展示`
- `价格证明`
- `上身效果`
- `真人口播`
- `多色比较`
- `使用前后对比`
- `清单穷举`

### 场景标签

- `上学`、`通勤`、`旅行`、`礼拜`、`育儿`
- `购物`、`卧室`、`车内`、`桌面`、`镜面试背`

### 拍摄形式

- `手部静物`
- `真人室内`
- `真人车内`
- `双人出镜`
- `镜面上身`
- `开箱拍摄`

### CTA分类

- `无CTA`
- `软推荐`
- `链接CTA`
- `低价促销`
- `套装价值`
- `送礼推荐`

## Decision procedure

Classify in this order:

1. Read the existing title, narrative summary, proof chain, CTA field and segment handoff. For an already-approved historical record, do not re-analyze or overwrite those fields unless the user explicitly requests a correction.
2. Choose `主类目` from the production/content frame, not from the product domain alone.
3. Choose `内容目的` from the strongest ending effect: attention, preference, or purchase action.
4. Choose `主叙事结构` from the dominant sequence of problem, reveal, demonstration and result. Pick one even when secondary beats are present.
5. Choose up to three `证明方式` tags and up to three `场景标签` tags that are directly visible or supported by the existing ASR/visual evidence.
6. Choose `拍摄形式` and `CTA分类` from the dominant capture and ending behavior. If no purchase or interaction request is present, use `无CTA`.

When evidence is mixed, prefer the earliest stable structure that governs the whole video and keep secondary nuance in the existing narrative fields. Never invent a category value or upgrade an unsupported claim merely to make a record fit the taxonomy.

## Examples

- A bag video that names church/school/diaper use, fills the bag with items, states a low price, and gives a TikTok Shop link: `平替｜转化｜场景点名｜物品实装+价格证明+真人口播｜链接CTA`.
- A bedroom creator who opens three colors, tests a laptop and ends by wearing the bag: `测评和开箱｜种草｜开箱揭晓｜多色比较+物品实装+上身效果｜软推荐`.
- A travel makeup-bag tour that lists skincare and makeup categories, shows the zipper and links a two-bag offer: `使用场景模拟｜转化｜清单穷举｜物品实装+结构展示+清单穷举｜链接CTA`.

The taxonomy is a retrieval aid. It must not alter `资产状态`, replace the evidence layer, or turn an AI-generated sentence candidate into an approved reusable sentence.
