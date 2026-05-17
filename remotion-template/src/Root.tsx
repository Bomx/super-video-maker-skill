import React from "react";
import { Composition } from "remotion";
import {
  CaptionedTalkingHead,
  captionedTalkingHeadSchema,
} from "./CaptionedTalkingHead";

const captionDemoWords = [
  { word: "This", start: 0.0, end: 0.25 },
  { word: "template", start: 0.25, end: 0.65 },
  { word: "renders", start: 0.65, end: 1.0 },
  { word: "captioned", start: 1.0, end: 1.45 },
  { word: "talking", start: 1.45, end: 1.8 },
  { word: "head", start: 1.8, end: 2.15 },
  { word: "videos.", start: 2.15, end: 2.7 },
];

export const RemotionRoot: React.FC = () => {
  const captionDefaults = captionedTalkingHeadSchema.parse({
    durationInSeconds: 3,
    mainVideoSrc: "source/main.mp4",
    words: captionDemoWords,
    fps: 30,
    width: 1920,
    height: 1080,
    accentHex: "#FF6B2C",
    maxWordsPerLine: 6,
    maxCharsPerLine: 42,
    bRollClips: [],
  });

  return (
    <Composition
      id="CaptionedTalkingHead"
      component={CaptionedTalkingHead}
      schema={captionedTalkingHeadSchema}
      defaultProps={captionDefaults}
      calculateMetadata={async ({ props }) => {
        const p = captionedTalkingHeadSchema.parse(props);
        return {
          durationInFrames: Math.max(1, Math.ceil(p.durationInSeconds * p.fps)),
          fps: p.fps,
          width: p.width,
          height: p.height,
        };
      }}
    />
  );
};
