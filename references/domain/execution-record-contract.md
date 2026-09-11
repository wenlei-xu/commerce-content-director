# 执行记录契约

执行记录是程序自动保存的运行账本，不是第二份创作稿。它记录某个创作稿修订、某个段落和一次生成请求实际使用了什么。

## 记录内容

```json
{
  "run_id": "RUN-...",
  "workbook_path": "script.md",
  "workbook_revision": 3,
  "segment_id": "S02",
  "stage": "first_frame_image",
  "workbook_digest": "...",
  "asset_roles": {"product_anchor": "...", "subject_anchor": "..."},
  "prompt": "...",
  "model": "...",
  "duration_seconds": 6,
  "request_id": "...",
  "result": "...",
  "status": "pending_review"
}
```

Prompt 由 Agent 在当前阶段直接写成自然语言。程序只补充和检查模型、时长、素材顺序、产品事实锁、音频路径、禁止项和请求格式；程序不能用默认动作或兜底段落填充缺失创意。

准备阶段的 `commerce-execution-plan-v1` 由 `scripts/prepare_execution.py` 生成；
提交阶段的 `commerce-execution-bundle-v1` 由
`scripts/compile_generation_prompts.py` 生成。两者都必须携带创作稿修订号和
摘要。Bundle 中的每个 `prompt` 是 Agent Prompt 加技术执行尾部，不是新的脚本版本。

首帧 Prompt 描述段落的进入瞬间；视频 Prompt 描述从首帧开始的变化。首帧生成并通过检查后，Agent 根据实际首帧再写视频 Prompt。

## 提交前检查

- 创作稿修订仍是当前版本。
- 目标段落存在，画面事件明确。
- 引用素材有效且角色顺序正确。
- Prompt 没有改变创作稿中的主体、产品事实、动作结果或连续性。
- Prompt 只包含当前阶段需要的时间、音频和技术要求。
- 实际提交全文、输入素材、模型、请求 ID 和结果路径被保存。

语义检查不能只靠关键词。若 Prompt 把“狗狗叼回”改成“狗狗寻找”，应指出具体偏离并返修；不能因为两个文本都包含“玩具”就通过。

## 运行目录

每次运行使用 `commerce_runs/<run_id>/`，至少保存创作稿快照、TTS/ASR、执行记录、实际提交 Prompt、素材映射、结果和审核证据。飞书记录继续承担资产查询和用户审批；本地执行记录承担恢复和追溯。
