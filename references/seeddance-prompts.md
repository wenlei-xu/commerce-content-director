# Seeddance 成片提示词

每个 Segment 输出一份完整的 `seeddance-prompt.md`，不拆续写。用以下顺序组织，并把方括号替换为实际内容：

```text
Generate one continuous [duration]-second [aspect ratio] video. Treat the uploaded replacement dynamic master for [Segment ID] as the authoritative timed sequence: read its frames from left to right and top to bottom, following the exact frame-time map. Preserve its composition, lens distance, lighting, shadow direction, action phase, camera movement, pacing, and transition chain, while rendering a clean continuous video rather than a grid.

Reference visual fingerprint (verbatim):
[style_fingerprint]

Reference anti-style constraints (verbatim):
[anti_style_constraints]

Identity anchors: [all verbatim user subject/hand constraints]. Use the product six-view image as the immutable product identity reference: [product facts]. [If applicable: use the subject six-view image as the immutable identity reference: subject facts.]

Packaging anchors: [verified packaging facts]. Scene and lighting anchors: [user scene constraints].

Timed action and camera sequence:
[For every RF: target time, final replacement frame description, exact action, hand/contact state, product state, lighting, camera movement, and transition_to_next.]

Generate only the finished video. Never show the dynamic-master grid, frame borders, frame numbers, timecodes, source frames, UI, watermarks, subtitles, captions, voice-over text, or unverified on-screen claims. Do not use, infer from, upload, or reference the original video, original frames, original product, or any source asset. Use only this replacement dynamic master, the supplied six-view references, and this prompt.
```

The supplied constraints must be copied exactly unless they conflict with visible product facts. Resolve conflicts in this order: explicit user requirement, visible asset fact, product/subject fact table, reference action. Record each necessary deviation in `quality-report.md`.

