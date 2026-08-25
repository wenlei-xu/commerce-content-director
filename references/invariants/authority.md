# Authority

Use the current config/base-schema.json as the schema authority. Freshly read the record that starts the selected workflow and then directly linked product, subject, script and final-film records as needed.

The source precedence is:

1. Current Feishu record and field metadata;
2. Current product hard facts and assets;
3. Locked creative direction and locked structured script;
4. For storyboard review, linked Feishu `分镜候选` records and their `是否采用` checkbox;
5. Local run package created for the current run.

Do not infer a direction, script, product action, dialogue or relation from stale local material.
Do not infer storyboard selection from local filenames or folders. The complete
candidate attachment and its Feishu checkbox are the cross-computer authority.
