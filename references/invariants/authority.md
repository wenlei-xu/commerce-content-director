# Authority

Use the current config/base-schema.json as the schema authority. Freshly read the record that starts the selected workflow and then directly linked product, subject, script and final-film records as needed.

The source precedence is:

1. Current Feishu record and field metadata;
2. Current product hard facts and assets;
3. Confirmed `产品动作库` entries for reusable product interactions; they may not override product facts;
4. Locked creative direction and locked structured script;
5. For storyboard generation and review, the two script-version records linked through their actual `来源脚本` relation, plus each record's ordered `最终分镜图`, `脚本版本` and `分镜状态`. There is no separate storyboard-mapping, storyboard-candidate or storyboard-review table;
6. Local run package created for the current run.

Do not infer a direction, script, product action, dialogue or relation from stale local material.
The product action library owns only reusable, confirmed ways to stage a product. A selected action is scenarioized in the script Beat and does not become a storyboard record.
Do not infer storyboard selection from local filenames or folders. The complete
A/B version records and their ordered `最终分镜图` attachments are the
cross-computer authority. Local request manifests and candidate artifacts are
traceability evidence only and are not final approval records.
