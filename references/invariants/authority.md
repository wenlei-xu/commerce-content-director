# Authority

Use the current config/base-schema.json as the schema authority. Freshly read the record that starts the selected workflow and then directly linked product, subject, script and final-film records as needed.

The source precedence is:

1. Current Feishu record and field metadata;
2. Current product hard facts and assets;
3. Locked creative direction and locked structured script;
4. For storyboard generation and review, the linked script-version record, its ordered `最终分镜图`, `脚本版本`, `分镜状态` and `脚本状态`. There is no separate storyboard-mapping, storyboard-candidate or storyboard-review table;
5. Local run package created for the current run.

Do not infer a direction, script, product action, dialogue or relation from stale local material.
Do not infer storyboard selection from local filenames or folders. The complete
A/B version records and their ordered `最终分镜图` attachments are the
cross-computer authority. Local request manifests and candidate artifacts are
traceability evidence only and are not final approval records.
