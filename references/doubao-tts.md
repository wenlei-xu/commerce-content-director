# Doubao TTS 2.0

Use this provider for external voiceover in the final-video workflow when `audio_mode` is `spoken` or `sparse_spoken`.

- Endpoint: `wss://openspeech.bytedance.com/api/v3/tts/bidirection`
- Authentication: local `DOUBAO_TTS_API_KEY`; never copy it into prompts, manifests, reports, or Feishu.
- Resource ID: `seed-tts-2.0`.
- Supported workflow languages: `zh-CN` and `th`. Send `explicit_language=zh-cn` or `explicit_language=th` through `additions` according to the immutable language lock.
- Default speaker configuration is in `config/doubao-tts.json`: the official Chinese sample voice for `zh-CN`, and the official Mildred neutral Thai 2.0 voice for `th`. Override it with `DOUBAO_TTS_SPEAKER_ZH_CN`, `DOUBAO_TTS_SPEAKER_TH`, or the CLI `--speaker` argument only when the selected voice is a Doubao TTS 2.0 voice that supports the locked language.
- Keep generated audio and the non-secret report inside the current run package. Never log request headers or the API key.

Synthesize one approved dialogue line at a time so every artifact retains its `line_id`, then align those clips to the locked dialogue windows before assembly:

```powershell
python scripts/synthesize_doubao_tts.py --language zh-CN --text "审核通过的逐字台词" --output audio/LINE-01.mp3 --report audio/LINE-01.json
```

Run `--dry-run` to validate local configuration without submitting a billable synthesis request. A real smoke test must produce readable audio and a report with `resource_id=seed-tts-2.0` before the provider is considered ready.
