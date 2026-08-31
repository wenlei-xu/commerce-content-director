# 交互替代协议

仅在原片动作与用户商品硬事实冲突时使用。目标是保留原片的叙事位置、动作节奏和可见构图锚点，而不是复制错误的产品机制。

## 必填记录

在 `plan/interaction-substitutions.md` 为每一段冲突连续格建立一条记录，字段如下：

| 字段 | 要求 |
| --- | --- |
| `RF-ID / 时间` | 所有受影响的连续格与源时间 |
| 原片动作 | 只陈述可见动作，不推断机制 |
| 原片硬件机制 | 仅记录产品专属的部件、固定方式、受力或触发路径；与可见行为分开写 |
| 可迁移行为与叙事功能 | 记录人或宠物的可见行为、情绪反应及其在该段的作用，例如互动、追逐、争抢、兴奋或结果证明 |
| 冲突硬事实 | 引用 `product-interaction-facts.md` 的用户事实 |
| 行为处置 | 只能标为 `preserved`、`adapted_with_product_reason` 或 `not_supported_with_evidence`；后者必须说明缺失的目标证据 |
| 可用替代动作 | 只替换冲突的机制、受力或接触路径；明确谁、以何方向、通过哪个已证实部位完成动作 |
| 保留锚点 | 必须保持的机位、手位、景别、背景、节奏、转场 |
| 禁止画面 | 所有会否定硬事实的部件、开口、方向、拆件或接触路径 |
| 可视验收点 | 审图时必须一眼可见的结构、方向和接触证据；如产品存在一体外观锁定，必须同时写明固定连接点、独立开口/部件位置及其不可混淆关系 |

## 规则

1. 用户给出的操作方式优先于原片动作与模型常识；不可把产品的侧孔、纹理、接缝或阴影补成新的功能。
2. 先判定冲突属于哪一层。产品专属硬件机制包括固定或吸附、弹性受力、发声、可拆部件及其操作路径；可迁移行为包括拔河、追逐、叼咬、携带、抢夺和兴奋反应。不得把“源片存在某硬件”直接判定为“整段行为不可用”。
3. 仅替换冲突所必需的机制、受力或接触路径。目标产品若有经证实的接触点或连接方式，应保留该行为的叙事功能，并改为真实的目标接触方式；不得因硬件不同而把可支持的玩法一律改成闻、扒或找食。
4. 只有当目标产品确无证据支持该行为时，才可标为 `not_supported_with_evidence`；必须写明缺失的事实，并设计保留同一叙事位置、节奏和情绪功能的替代行为。不得以类别常识或模型猜测补足缺失机制。
5. 除冲突的产品机制与接触路径外，原片的构图、手位、环境、人物/宠物位置、光线和节奏应保留。
6. Review every affected first-frame output before accepting the package. If a viewer can still read the image as a cap opening, disassembly, wrong-hole filling, or wrong orientation, the package fails.
7. The first-frame prompt must state the substitution action and prohibited imagery literally; never replace this with a vague instruction such as "use correctly".
8. 当目标产品存在固定一体外观结构时，替代动作的接触位置、受力方向和机位必须让该结构保持可读。不得用遮挡、翻转、省略连接部件或改接开口来保留动作表面形式。

不要在本协议中保存任何产品示例。替代动作、禁止画面和可视验收点只能从本次的 `product-interaction-facts.md` 引用；换产品时不得继承此前产品的部件、开口、朝向、装粮路径或出粮/漏食规则。
