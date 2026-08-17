# 用户约束模板

将用户提供的原文放入 `plan/user-constraints.md`，按下列标题归档，不删除或润色任何事实性锚点。若输入不完整，保留已有部分并将缺失处标记为“未提供”，不得补造。

```markdown
# User constraints

## Subject and hands
[verbatim user constraints]

## Product identity
[verbatim user constraints]

## Packaging identity
[verbatim user constraints]

## Scene and lighting
[verbatim user constraints]

## Timed sequence
[verbatim user timing blocks]
```

当前用户已提供的基础锚点可直接记录为：一位年轻成年男性；浅色皮肤、灰绿色眼睛、浓密蓬松的深棕卷发、轻微自然胡茬、同一件白色敞领衬衫；无鼻环和项链；脸、发型、眼睛、服装、手部肤色、左右手及抓握/贴合/指向/擦拭接触点跨格稳定。产品为两片深紫色、薄、柔软、可弯曲并贴合牙弓的牙贴，分别用于上牙和下牙。包装为深紫色硬质长方体盒，包含已提供的固定英文包装文字。场景为暖米色高级浴室，暖色灯光与正面手机补光稳定照亮人物、牙齿、双手和产品。完整逐时段提示词尚未收到，不能臆补其余动作。

## 时间段脚本语法

保留用户原文，并解析下列形式：

```text
[0.00-1.77秒: 泛黄牙齿痛点微距 | Panels 1-2]
画面从嘴唇、牙龈和泛黄牙列占满画面的口腔极近微距开始……
```

起止秒允许小数，标题和 `Panels` 可选；`Panels 1-2` 仅是原镜头面板索引。每段必须连续、不可重叠；若原文时间存在间隙、重叠或结尾缺失，先在质量报告中标记而非自行补写。解析后的 `TS` 表必须保留原文、精确时长、关联的 `RF` 逐秒格和改版结果。
