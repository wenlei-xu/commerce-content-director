import React from 'react';
import {Composition} from 'remotion';
import {PetopiaShortVideo, petopiaShortVideoSchema} from './PetopiaShortVideo';

const defaultProps = {
  videoSrc: 'golden-staff-clean.mp4',
  title: '金箍棒漏食玩具',
  brand: 'PETOPIA｜建东橡胶专卖店',
  badge: '真实互动记录',
  actionText: '叼｜抛｜拾｜拉',
  cta: '给精力旺的小狗找点事做',
  durationInSeconds: 27.875,
  fps: 24,
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="PetopiaShortVideo"
      component={PetopiaShortVideo}
      durationInFrames={Math.ceil(defaultProps.durationInSeconds * defaultProps.fps)}
      fps={defaultProps.fps}
      width={720}
      height={1280}
      schema={petopiaShortVideoSchema}
      defaultProps={defaultProps}
    />
  );
};
