# Remotion rendering contract

Remotion is an optional, code-driven MP4 renderer for final-video post-production. It is not a replacement for the Omni segment-generation workflow, the Feishu content authority, or the existing FFmpeg validation path.

Use this contract when the task needs automated final MP4 output with reusable visual templates such as:

- animated spoken subtitles;
- dog inner-voice bubbles;
- monitoring/timestamp overlays;
- product reveal cards;
- reaction words, scale, shake or pop animations;
- Petopia end cards and repeatable branded layouts.

Do not use Computer Use, desktop Jianying control, mouse/keyboard simulation or a Jianying export button in this route. Jianying drafts are optional review artifacts only and are never the required rendering step.

## Backend selection

Every final-video run must record one `render_backend` in its local execution manifest:

- `ffmpeg` — use the existing `scripts/assemble_final_video.py` path when the video only needs concatenation, audio mixing, static ASS subtitles or simple overlays.
- `remotion` — use a verified local Remotion project when animated subtitles, bubbles, product cards or other reusable React compositions are part of the requested output. Remotion owns the visual composition and MP4 render.
- `hybrid` — use Remotion for visual composition and animated text, then FFmpeg for final audio muxing, loudness normalization, codec normalization or final container checks. Use this when the Remotion composition intentionally does not own the final audio mix.

Default to `ffmpeg` when the user has not requested a Remotion composition and no verified Remotion project is available. Never silently fall back from a selected `remotion` or `hybrid` backend to Jianying or another renderer.

## Rough and fine edit passes

Treat the first render as a **rough cut** unless the user explicitly asks for a finished edit:

- Rough cut: picture edit, clip order, duration, voiceover/original sound and basic subtitles only. Do not add sound effects, animated captions, reaction words, decorative transitions or other motion polish.
- Fine cut: after the rough cut is accepted, add subtitle motion, bubbles, reaction words, transitions, background-music balancing and sound effects.

Sound effects are a separate fine-cut layer. Prefer the categorized assets under `assets/audio/jianying-sfx/`. Choose a sound by the visible event it supports: appearance, discovery, pickup, jump, failure, reward or return. Place the sound at the visual action peak, normally within about 80 ms of the motion peak, rather than at the start of a subtitle cue. For a 20–30 second pet video, use roughly 3–5 meaningful effects; do not attach a sound to every subtitle. Keep effects below the voiceover and preserve the original/environmental sound.

When a Remotion composition needs synchronized effects, record them as explicit cue data instead of scattering timing constants through JSX:

```ts
{
  time: 10.3,
  sound: '03_惊讶与发现/综艺好奇.mp3',
  volume: 0.18,
  event: '狗狗发现漏食'
}
```

For a rough render, omit the cue list. For a fine render, render or mix the cue list only after the visual timing is locked. If Remotion owns the visual composition and FFmpeg owns final audio mixing, use the `hybrid` backend and keep the sound-effect cue manifest with the render specification.

## Required inputs

The selected renderer receives a single render specification saved under the active run directory, normally at `renders/render-spec.json`:

```json
{
  "schema": "commerce-remotion-render-v1",
  "render_backend": "remotion",
  "composition_id": "PetopiaShortVideo",
  "width": 720,
  "height": 1280,
  "fps": 30,
  "duration_seconds": 15,
  "segments": [
    {"path": "segments/01.mp4", "start": 0, "duration": 4},
    {"path": "segments/02.mp4", "start": 4, "duration": 6}
  ],
  "voiceover": "audio/voiceover.mp3",
  "background_music": "audio/background-music.mp3",
  "subtitles": "subtitles/subtitles.json",
  "screen_texts": [],
  "template": "dog-reaction"
}
```

The render specification is an execution artifact, not a second script. The workbook remains the authority for spoken copy, segment order, product facts and screen-text intent. The renderer must use the exact approved spoken copy and the already-locked ASR timing map.

## Runtime checks

Before a Remotion render:

1. Verify `node` and `npx` are available.
2. Verify the selected `project_dir` contains `package.json` and declares `remotion` or `@remotion/cli`.
3. Use the project's installed Remotion version; do not silently install or upgrade dependencies during a production run.
4. Run the project-level composition discovery or a short still-frame render before the full render when the project has not been used in the current run.
5. Write the exact project path, composition ID, Remotion command, package-lock digest when available, output path and render result into the run manifest.

The skill helper `scripts/render_remotion.py` only invokes an already-installed local Remotion project. It must fail clearly when Node, the project, the composition or the local Remotion dependency is unavailable.

## Subtitle rules

Remotion subtitles follow the same content and timing contract as FFmpeg subtitles:

- render only approved spoken copy in the subtitle layer;
- keep independent `screen_texts` separate from spoken subtitles;
- use final TTS ASR timing, never estimated timings;
- preserve the 720x1280 safe rectangle and scale it proportionally for other 9:16 output;
- keep cues to one or two visible lines;
- run frame-level visual QA after rendering.

Remotion may animate a subtitle, but animation must not change the words, order, timing evidence or product claims.

## Failure and fallback

If a selected Remotion render fails, preserve the failed command and logs under the current run. Do not silently switch to Jianying, Computer Use or a different visual template. A user-approved rerun may select `ffmpeg` if the requested visual treatment can be represented by the existing FFmpeg subtitle contract; otherwise stop with the missing dependency or composition error.
