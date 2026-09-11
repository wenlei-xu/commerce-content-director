# Authority

Use the current config/base-schema.json as the schema authority. Freshly read the record that starts the selected workflow and then directly linked product, subject, script and final-film records as needed.

The source precedence is:

1. Current Feishu record and field metadata;
2. Current product hard facts and assets;
3. Approved `场景资产库` entries for spatial context, lighting and capture treatment; they may not override product or subject facts;
4. Product `交互能力` / `关键结构锁` and confirmed `内容互动模板库` entries for reusable interaction patterns; templates may not override product facts;
5. Locked creative direction and locked structured script;
6. For first-frame generation and review, the two script-version records linked through their actual `来源脚本` relation, plus each record's ordered `最终首帧图`, `脚本版本` and `首帧状态`. There is no separate Segment mapping, candidate or review table;
7. Local run package created for the current run.

Do not infer a direction, script, product action, dialogue or relation from stale local material.
The product action library owns only reusable, confirmed ways to stage a product. A selected action is scenarioized in the script Beat and does not become a first-frame record.
Do not infer first-frame selection from local filenames or folders. The complete
A/B version records and their ordered `最终首帧图` attachments are the
cross-computer authority. Local request manifests and candidate artifacts are
traceability evidence only and are not final approval records.
