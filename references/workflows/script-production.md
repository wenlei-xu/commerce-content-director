# Workflow: script production

读取任务的 `plan/language-lock.json`；缺失时按用户选择或默认中文创建并锁定。使用同一值运行预检。读取一条已锁定创意方向、产品硬事实、交互限制、主体和当前配置。通过 `python scripts/query_content_interaction_templates.py --product-record-id <record_id>` 查询当前产品可用的互动模板；先用产品硬事实和交互限制核对真实接触路径，没有兼容模板时不得凭常识补互动。先读并执行 [action-direction.md](action-direction.md)：在写 Beat 前形成一段动作导演说明，只描述场景、主体动作、真实接触方式、反应与节奏；不创建 JSON 或新字段。生成本地 structured_script；每个选中的 `interaction_plans` 至少写入 `beat_id`、`template_record_id`、`template_name`、`content_function`、`scene_execution` 与 `visual_acceptance`。兴趣、互动、情绪、节奏和转场计划的 `verified_benefit` 必须为空；只有证明计划可以写入已确认的产品价值。再运行校验器和渲染全部审核字段；只有校验通过才创建或更新待审核脚本。将锁定值原样写入 `structured_script.runtime.target_spoken_language` 和飞书脚本字段 `目标口播语言`，写入后回读验证。

先完成 Beat 的叙事任务和视觉/产品互动；再逐 Beat 判断是否需要口播或屏幕文字。需要生成、优化或返工口播时，读取并执行 [dialogue-copy-optimization.md](dialogue-copy-optimization.md)。该模块可以读取 `句式模板库` 中 `审核状态=可用` 且用途、语言与任务锁匹配的记录，优先取最多 3 条候选；候选确认后才由本流程写入 `structured_script`。不得为了套用句式而改变已锁定的叙事或产品事实。

每条脚本最多使用 3–5 个句式模板，同一行台词最多引用一个模板。`待审核`、`已驳回`、`已合并` 的句式不能被脚本使用。

口播脚本在锁定前调用 dialogue-copy-optimization 模块做台词复盘，但该模块是建议层，不设置口播质量硬门禁。不要只按画面顺序复述“打开、装入、放下、清洗”等产品说明书动作；产品互动由画面证明，台词应尽量把动作转化为观众关心的价值。`structured_script.dialogue_quality_gate` 可以记录 `instruction_manual_restatement_only`、`pain_line_ids`、`benefit_line_ids`、`proof_line_ids`、`natural_cta_line_ids`，用于后续审核和学习；缺少这些记录只产生提示，不阻断脚本或成片。标签不能替代对台词正文的实际审读。

在正式结构校验之外，使用“生活化口播软规则”做创作和审核提示：每句优先 6–14 个字，最长建议不超过 18 个字；一句只说一个动作或反应；少用“直到、而是、之后、从而”等书面连接词；每隔约 2–3 秒根据画面加入一次自然反应（如“哎”“诶”“你看”“真的掉出来了”）；台词跟着画面说，不把整段写成产品原理说明。软规则用于评分和改写建议，不得单独导致脚本校验失败；如果画面、事实或时长需要例外，应保留口语感并在审核备注中说明。

字幕模式只能为普通字幕、重点强调字幕或不生成。重点强调字幕时，在需要强调的台词行填写 `caption.emphasis_spans`；每个 span 的 `text` 必须是该行台词中按顺序出现的原文，`style` 只能表达视觉突出，不得改写或补充台词。数字、结果词、产品名和关键痛点可以强调，但不要默认强调每句话。

审核意见只修改 structured_script。修订后重新校验和渲染。只有检查通过、审核意见处理完毕的脚本才能锁定。
