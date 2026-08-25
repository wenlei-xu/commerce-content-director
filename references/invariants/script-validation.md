# 脚本校验

运行 scripts/validate_structured_script.py。阻断项包括：缺少策略或 CTA、ID 重复、时间线不连续、台词跨分段、自然声模式含台词、未回收钩子、CTA 不唯一、产品动作冲突或状态衔接失败。

`spoken` 与 `sparse_spoken` 还必须具有通过的 `dialogue_quality_gate`：`instruction_manual_restatement_only` 必须为 `false`；`pain_line_ids`、`benefit_line_ids`、`proof_line_ids`、`natural_cta_line_ids` 均不得为空且只能引用现有台词；结尾的 `cta_line_id` 必须包含在 `natural_cta_line_ids`。缺少任一角色、仅用说明书式台词复述可见动作，或 CTA 与前文脱节，均阻断脚本锁定。

只有脚本检查状态为通过的脚本能锁定。
