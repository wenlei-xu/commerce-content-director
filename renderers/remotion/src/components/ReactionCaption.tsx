import React from 'react';
import {interpolate, spring, useCurrentFrame} from 'remotion';

export type ReactionCaptionProps = {
  text: string;
  top: number;
  left?: number;
  right?: number;
  rotate?: number;
  fontSize?: number;
  color?: string;
};

/**
 * Petopia reaction-caption preset:
 * enter from below, pop upward quickly, overshoot slightly, then settle.
 */
export const ReactionCaption: React.FC<ReactionCaptionProps> = ({
  text,
  top,
  left,
  right,
  rotate = 0,
  fontSize = 50,
  color = '#F7D96A',
}) => {
  const frame = useCurrentFrame();
  const pop = spring({
    frame,
    fps: 24,
    config: {damping: 8, mass: 0.24, stiffness: 560},
    durationInFrames: 6,
  });
  const translateY = interpolate(pop, [0, 0.68, 1], [280, -24, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scale = interpolate(pop, [0, 0.68, 1], [0.76, 1.12, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top,
        left,
        right,
        color,
        fontFamily: "'ZiZhiQuXiMaiTi', sans-serif",
        fontWeight: 400,
        fontSize,
        lineHeight: 1.2,
        whiteSpace: 'nowrap',
        WebkitTextStroke: '3px #050505',
        paintOrder: 'stroke fill',
        transform: `translateY(${translateY}px) scale(${scale}) rotate(${rotate}deg)`,
        transformOrigin: 'center bottom',
        opacity: 1,
      }}
    >
      {text}
    </div>
  );
};
