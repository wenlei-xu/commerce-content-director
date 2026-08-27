# Doubao TTS 2.0

Use this provider as the mandatory Chinese external voiceover route in the final-video workflow when `audio_mode` is `spoken` or `sparse_spoken`. Thai remains on the approved native-Omni route unless a later task explicitly changes that policy.

- Endpoint: `wss://openspeech.bytedance.com/api/v3/tts/bidirection`
- Authentication: local `DOUBAO_TTS_API_KEY`; never copy it into prompts, manifests, reports, or Feishu.
- Resource ID: `seed-tts-2.0`.
- Supported workflow languages: `zh-CN` and `th`. Send `explicit_language=zh-cn` or `explicit_language=th` through `additions` according to the immutable language lock.
- Default speaker configuration is in `config/doubao-tts.json`: `zh_female_qinqienv_uranus_bigtts` for `zh-CN`, and the official Mildred neutral Thai 2.0 voice for `th`. Override it with `DOUBAO_TTS_SPEAKER_ZH_CN`, `DOUBAO_TTS_SPEAKER_TH`, or the CLI `--speaker` argument only when the selected voice is a Doubao TTS 2.0 voice that supports the locked language.
- Keep generated audio and the non-secret report inside the current run package. Never log request headers or the API key.
- Chinese synthesis defaults to `speech_rate=15`. The Thai default remains unchanged.

For continuous Chinese narration, concatenate all exact approved dialogue in chronological order and synthesize it once. Keep a sidecar manifest mapping the complete take back to the ordered `line_id` values and exact texts:

```powershell
python scripts/synthesize_doubao_tts.py --language zh-CN --text-file audio/full-voiceover.txt --speech-rate 15 --output audio/full-voiceover.mp3 --report audio/full-voiceover.json
```

Use separate requests only for genuinely non-contiguous sparse-spoken blocks. Do not split a continuous narration line by line merely to fit planned windows. If the generated take is slightly too long, derive inter-sentence gaps from ASR word timestamps or silence detection and remove only the excess gap duration, retaining at least 80 ms at each sentence boundary. Do not cut phonemes, apply global `atempo`, or silently increase `speech_rate`; if reducing breath gaps is insufficient, revise the copy and obtain approval before synthesizing again.

Run `--dry-run` to validate local configuration without submitting a billable synthesis request. A real smoke test must produce readable audio and a report with `resource_id=seed-tts-2.0` before the provider is considered ready.

For Chinese final assembly, first isolate the BGM from the exact approved reference video and pass the residual-speech gate:

```powershell
python scripts/separate_reference_bgm.py reference.mp4 --background-music audio/reference-bgm.wav --asr-report audio/reference-bgm-asr.json --gate audio/source-bgm-gate.json
python scripts/assemble_final_video.py segment-01.mp4 segment-02.mp4 --subtitles audio/final.srt --voiceover audio/aligned-voiceover.mp3 --background-music audio/reference-bgm.wav --background-music-gate audio/source-bgm-gate.json --audio-policy chinese_external_tts --profile plan/content-system-config-snapshot.json --out final.mp4
```

The final subtitle timing comes from the aligned complete Doubao take. Recover each `line_id` boundary from actual ASR/silence timing and use the exact approved text. Never time subtitles from Omni audio or from unaligned script estimates.
