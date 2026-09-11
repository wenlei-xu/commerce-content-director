import React from 'react';
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useVideoConfig,
} from 'remotion';
import {z} from 'zod';
import {ReactionCaption} from './components/ReactionCaption';

export const petopiaShortVideoSchema = z.object({
  videoSrc: z.string(),
  title: z.string(),
  brand: z.string(),
  badge: z.string(),
  actionText: z.string(),
  cta: z.string(),
  durationInSeconds: z.number(),
  fps: z.number(),
});

export type PetopiaShortVideoProps = z.infer<typeof petopiaShortVideoSchema>;

// Soft cream-yellow sampled visually from the reference caption treatment.
const yellow = '#FBE300';
const reactionYellow = '#F7D96A';
const ordinaryCaptionColor = '#FFFFFF';
const ximaiFont = "'ZiZhiQuXiMaiTi', sans-serif";

const ordinaryCaptionText: React.CSSProperties = {
  fontFamily: ximaiFont,
  fontWeight: 400,
  color: ordinaryCaptionColor,
  textShadow: '3.54px -3.54px 15px rgba(0, 0, 0, 0.4)',
  WebkitTextStroke: '4px #111111',
  paintOrder: 'stroke fill',
};

type ReactionCaptionCue = {
  from: number;
  to: number;
  text: string;
  top: number;
  left?: number;
  right?: number;
  rotate: number;
  fontSize: number;
};

type SubtitleCue = {
  from: number;
  to: number;
  text: string;
  highlights: string[];
};

const reactionCaptions: ReactionCaptionCue[] = [
  {from: 0.5, to: 2.8, text: '开啃开啃', top: 300, left: 55, rotate: -4, fontSize: 50},
  {from: 10.3, to: 12.8, text: '里面有吃的', top: 270, left: 58, rotate: 2, fontSize: 50},
  {from: 20.2, to: 22.5, text: '叼走玩去', top: 250, right: 62, rotate: -3, fontSize: 50},
  {from: 24.4, to: 26.5, text: '继续玩', top: 310, left: 100, rotate: 3, fontSize: 50},
];

const subtitleCues: SubtitleCue[] = [
  {from: 0, to: 2.42, text: '淘到一个可以让小狗自己忙活的', highlights: ['自己忙活']},
  {from: 2.42, to: 3.46, text: '金箍棒漏食玩具', highlights: ['金箍棒漏食玩具']},
  {from: 3.46, to: 5.56, text: '这个呢用的是天然橡胶啊', highlights: ['天然橡胶']},
  {from: 5.56, to: 6.38, text: '特别结实', highlights: []},
  {from: 6.38, to: 8.64, text: '那小狗边啃呢是既消耗精力', highlights: ['消耗精力']},
  {from: 8.64, to: 11.16, text: '又能把时间花在这上面一箭双雕', highlights: ['一箭双雕']},
  {from: 11.16, to: 13, text: '而且你看它不同颜色的设计啊', highlights: ['不同颜色']},
  {from: 13, to: 14.76, text: '再加上中间的漏食设计', highlights: ['漏食设计']},
  {from: 14.76, to: 17, text: '就会让小狗咬上去的触感非常丰富', highlights: ['触感丰富']},
  {from: 17, to: 19.14, text: '大大满足它捕猎一般的啃咬欲', highlights: ['啃咬欲']},
  {from: 19.14, to: 21.28, text: '所以家里小狗爱掏棉花爱拔河', highlights: ['掏棉花', '拔河']},
  {from: 21.28, to: 23.06, text: '鬼鬼祟祟还总想拆个小家', highlights: ['拆个小家']},
  {from: 23.06, to: 24.2, text: '你就给它整个这个', highlights: []},
  {from: 24.2, to: 26.02, text: '这么有意思的金箍棒就玩去吧', highlights: ['有意思']},
  {from: 26.02, to: 27.875, text: '非常消耗精力', highlights: ['消耗精力']},
];

const renderHighlightedText = (text: string, highlights: string[]) => {
  const pieces: React.ReactNode[] = [];
  let cursor = 0;
  let pieceKey = 0;
  for (const highlight of highlights) {
    const index = text.indexOf(highlight, cursor);
    if (index < 0) continue;
    if (index > cursor) pieces.push(<span key={`plain-${pieceKey++}`}>{text.slice(cursor, index)}</span>);
    pieces.push(
      <span
        key={`highlight-${pieceKey++}`}
        style={{
          color: yellow,
          fontFamily: ximaiFont,
          fontSize: 58,
          fontWeight: 400,
          display: 'inline-block',
          lineHeight: 1,
          transform: 'translateY(-1px)',
        }}
      >
        {highlight}
      </span>,
    );
    cursor = index + highlight.length;
  }
  if (cursor < text.length) pieces.push(<span key={`tail-${pieceKey++}`}>{text.slice(cursor)}</span>);
  return pieces;
};

const SpokenSubtitle: React.FC<SubtitleCue> = (cue) => {
  const plainLength = cue.text.replace(/\n/g, '').length;
  const highlightedLength = cue.highlights.reduce((total, item) => total + item.length, 0);
  const estimatedWidth = plainLength * 50 + highlightedLength * 8;
  // Keep every cue on one line while leaving a visual safety buffer for the
  // heavier font, thick outline and enlarged keyword spans.
  const scaleX = Math.min(1, 560 / estimatedWidth);
  return (
    <div
      style={{
        ...ordinaryCaptionText,
        position: 'absolute',
        left: 28,
        right: 28,
        bottom: 340,
        fontSize: 50,
        lineHeight: 1,
        letterSpacing: 0,
        textAlign: 'center',
        whiteSpace: 'nowrap',
        transform: `scaleX(${scaleX})`,
        transformOrigin: 'center center',
      }}
    >
      {renderHighlightedText(cue.text, cue.highlights)}
    </div>
  );
};

export const PetopiaShortVideo: React.FC<PetopiaShortVideoProps> = (props) => {
  const {fps, width, height} = useVideoConfig();
  const videoSrc = /^(https?:|file:|data:)/.test(props.videoSrc)
    ? props.videoSrc
    : staticFile(props.videoSrc);
  const smileySansSrc = staticFile('fonts/SmileySans-Oblique.otf');
  const ximaiSrc = staticFile('fonts/ZiZhiQuXiMaiTi.ttf');

  return (
    <>
      <style>{`
        @font-face {
          font-family: 'Smiley Sans Oblique';
          src: url('${smileySansSrc}') format('opentype');
          font-style: normal;
          font-weight: 100 900;
          font-display: block;
        }
        @font-face {
          font-family: 'ZiZhiQuXiMaiTi';
          src: url('${ximaiSrc}') format('truetype');
          font-style: normal;
          font-weight: 400;
          font-display: block;
        }
      `}</style>
      <AbsoluteFill style={{backgroundColor: '#111'}}>
        <OffthreadVideo src={videoSrc} volume={0} style={{width, height, objectFit: 'cover'}} />
        <Audio src={staticFile('golden-staff-v4.mp3')} volume={1} />

        <AbsoluteFill style={{pointerEvents: 'none'}}>
          {reactionCaptions.map((caption) => {
            const from = Math.round(caption.from * fps);
            const durationInFrames = Math.max(1, Math.round((caption.to - caption.from) * fps));
            return (
              <Sequence key={`${caption.from}-${caption.text}`} from={from} durationInFrames={durationInFrames}>
                <ReactionCaption {...caption} color={reactionYellow} />
              </Sequence>
            );
          })}
          {subtitleCues.map((cue) => {
            const from = Math.round(cue.from * fps);
            const durationInFrames = Math.max(1, Math.round((cue.to - cue.from) * fps));
            return (
              <Sequence key={`${cue.from}-${cue.text}`} from={from} durationInFrames={durationInFrames}>
                <SpokenSubtitle {...cue} />
              </Sequence>
            );
          })}
        </AbsoluteFill>
      </AbsoluteFill>
    </>
  );
};
