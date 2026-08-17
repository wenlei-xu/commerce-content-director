# 英文字幕

从已对齐的原片转写、OCR 与用户明确提供文案中生成 `subtitles.en.srt`。将内容译为自然、简短、可读的英文，保留事实，不增加功效、价格、品牌承诺或 CTA。

每条字幕独立覆盖其真实语音/文字时间，不因母版切格而强拆。口播和屏幕文字发生重叠时优先口播；只有屏幕文字时可生成一条简短英文字幕。没有可靠可翻译内容时创建零字节 `subtitles.en.srt` 并在质量报告标注 `No verified dialogue or on-screen copy`。

示例：

```srt
1
00:00:00,000 --> 00:00:01,770
Looking for a brighter smile?
```

