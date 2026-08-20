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

This archive template intentionally contains no project-specific subject, product, packaging, scene, or timing facts. Populate the sections only from the current user's run input.

## 时间段脚本语法

保留用户原文，并解析下列形式：

```text
[0.00-1.77秒: 泛黄牙齿痛点微距 | Panels 1-2]
画面从嘴唇、牙龈和泛黄牙列占满画面的口腔极近微距开始……
```

起止秒允许小数，标题和 `Panels` 可选；`Panels 1-2` 仅是原镜头面板索引。每段必须连续、不可重叠；若原文时间存在间隙、重叠或结尾缺失，先在质量报告中标记而非自行补写。解析后的 `TS` 表必须保留原文、精确时长、关联的 `RF` 逐秒格和改版结果。
