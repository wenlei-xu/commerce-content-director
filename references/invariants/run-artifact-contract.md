# 运行产物契约

当前 Skill 的运行产物统一放在 Skill 根目录下的：

```text
runs/<run_id>/
```

`<run_id>` 由运行适配器创建或用于恢复已有运行；不使用机器绝对路径，也不把
运行产物写到当前工作目录、`plan/`、`scripts/` 或 `references/`。

## 标准目录

```text
runs/<run_id>/
├── run-manifest.json
├── inputs/
├── audio/
│   └── timing-map.json
├── planning/
├── prompts/
├── assets/
├── generation/
├── renders/
├── subtitles/
├── qa/
├── delivery/
└── tmp/
```

`run-manifest.json` 至少记录运行 ID、工作流、当前阶段、当前创作稿修订号、选定的
`render_backend`（`ffmpeg`、`remotion` 或 `hybrid`）和运行内相对产物路径。使用
Remotion 或 hybrid 时，还要登记 `renders/render-spec.json`、Remotion 项目相对路径、
composition ID、实际渲染命令和最终 MP4 路径。外部素材可以作为输入读取，但需要先快照到 `inputs/` 或
登记其哈希；执行记录中的路径使用相对于本次运行的路径。

## 写入规则

活动脚本通过 `scripts/run_context.py` 模块获取运行上下文。新运行调用
`create_run()`，恢复运行调用 `open_run()`；所有输出必须使用上下文生成的路径。
运行上下文拒绝路径穿越和运行目录外写入，并创建唯一的标准子目录。

首帧和视频的 Prompt 分别写入 `prompts/`，执行计划和请求包写入 `planning/`，
生成结果写入 `generation/`，Remotion 的渲染规格和渲染日志写入 `renders/`，字幕、
`subtitle-layout.json` 和字幕 QA 写入 `subtitles/`，最终交付写入 `delivery/`。
`tmp/` 只放可重建的中间文件。

`subtitles/subtitle-layout.json` 是字幕位置的唯一机器可读来源。它声明 720x1280
基准画布上的底部居中抖音安全框 `x=28..692`、`y=820..940`、底部预留 340px、最多两行和视觉 QA
状态。最终合成会校验这份文件，防止 SRT、ASS 和 FFmpeg 参数各自漂移；主体或商品
被遮挡仍必须通过最终渲染帧的视觉 QA 才能发现。

运行产物属于本地执行证据，`runs/` 已加入 Git 忽略，不提交到 Skill 仓库。
