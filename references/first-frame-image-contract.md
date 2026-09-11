# 首帧图执行契约

首帧图是某个创作稿段落的“进入状态”静帧，不是完整动作过程、分镜表或
Beat 时间线。内容来源是 Markdown 创作稿，Prompt 由 Agent 在当前段落准备进入
生成时直接创作。

## 数据流

```text
script.md + approved assets
        ↓
Agent 写 prompts/<segment_id>.first_frame_image.prompt.md
        ↓
scripts/prepare_execution.py
        ↓
runs/<run_id>/planning/execution-plan.json
        ↓
scripts/compile_generation_prompts.py
        ↓
runs/<run_id>/planning/execution-bundle.json
```

适配器只复制创作稿的段落内容、版本摘要、时间和素材角色；它不补动作、不
选择模板、不生成机位，也不把多个段落合并成固定动作链。编译器只追加执行
技术约束，不改写 Agent Prompt。

## 执行计划的最小语义

每个首帧段落必须有：

- `segment_id`、`target_time_range`、`segment_seconds`；
- 来自创作稿的 `visual_event`、`continuity`、`must_show`；
- 可选 `asset_roles`，包含有序素材角色；
- Agent 写入的英文 `prompt`；
- `workbook_revision` 与 `workbook_digest`，用于防止旧稿结果回写新稿。

首帧 Prompt 只描述一个清晰的局部进入状态：主体当前是什么姿态、产品在何处、
镜头从哪里看、环境如何承接上一段。不要把“接下来会做什么”写进静帧，也不要
凭产品名称补充未确认的颜色、材质、结构或功能。

## 固定执行约束

首帧请求必须使用：

- `executor=gpt_image_2_5`；
- `model=gpt-image-2.5`；
- 9:16、`1152x2048`、高质量 PNG；
- 每个段落一张完整首帧，不生成网格、接触表、分屏、边框或多张图。

这些是执行参数，不是给 Agent 发挥的内容。素材输入必须保留完整图片、哈希、
本地路径、角色和顺序；产品锚点拥有产品外观，主体锚点拥有主体身份，场景参考
只拥有场景空间和拍摄质感。事实冲突时停止执行，不靠 Prompt 猜测。

控制 Prompt 使用英文；中文或泰语口播不进入首帧图 Prompt。口播、ASR 和视觉
段落关系保留在创作稿及执行记录中。

## 可选 A/B

只有用户要求 A/B 时，才为同一创作稿生成两套完整版本。A/B 应共享产品事实、
主体身份、段落顺序和视觉连续性，但必须有明确的创意差异；不能只替换一句
“更关注产品/更关注反应”。如果不要求 A/B，默认生成一套段落序列。

## 编译与校验

```powershell
python scripts/prepare_execution.py script.md --stage first_frame_image --require-prompts --run-id <run_id>
python scripts/compile_generation_prompts.py --run-id <run_id>
python scripts/validate_prompt_bundle.py --run-id <run_id>
```

缺少 Prompt、段落没有画面事件、稿件版本不合法、时长不是 4/6/8/10 秒，或
Prompt 含中文/泰语控制文字时，准备或校验失败。机器校验只是视觉预检；产品
一致性、动作可执行性和跨段连续性仍需人工检查。
