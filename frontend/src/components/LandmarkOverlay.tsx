import { useEffect, useRef } from 'react';
import type { Landmark } from '../types';

interface LandmarkOverlayProps {
  landmarks: Landmark[] | null | undefined;
  width: number;
  height: number;
}

// MediaPipe hand skeleton connections
const CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],           // thumb
  [0, 5], [5, 6], [6, 7], [7, 8],            // index
  [0, 9], [9, 10], [10, 11], [11, 12],       // middle
  [0, 13], [13, 14], [14, 15], [15, 16],     // ring
  [0, 17], [17, 18], [18, 19], [19, 20],     // pinky
  [5, 9], [9, 13], [13, 17],                 // knuckle bar
];

// Finger tip indices
const FINGERTIPS = [4, 8, 12, 16, 20];

export function LandmarkOverlay({ landmarks, width, height }: LandmarkOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!landmarks || landmarks.length < 21) return;

    // Draw connections
    ctx.strokeStyle = 'rgba(99, 179, 237, 0.85)';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';

    for (const [start, end] of CONNECTIONS) {
      const s = landmarks[start];
      const e = landmarks[end];
      if (!s || !e) continue;

      ctx.beginPath();
      ctx.moveTo(s[0] * canvas.width, s[1] * canvas.height);
      ctx.lineTo(e[0] * canvas.width, e[1] * canvas.height);
      ctx.stroke();
    }

    // Draw all joints
    for (let i = 0; i < landmarks.length; i++) {
      const lm = landmarks[i];
      const x = lm[0] * canvas.width;
      const y = lm[1] * canvas.height;
      const isTip = FINGERTIPS.includes(i);
      const isWrist = i === 0;

      ctx.beginPath();
      ctx.arc(x, y, isTip ? 6 : isWrist ? 7 : 4, 0, Math.PI * 2);
      ctx.fillStyle = isTip
        ? 'rgba(252, 129, 74, 0.95)'
        : isWrist
        ? 'rgba(255, 255, 255, 0.9)'
        : 'rgba(99, 179, 237, 0.9)';
      ctx.fill();

      if (isTip || isWrist) {
        ctx.strokeStyle = 'rgba(255,255,255,0.7)';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    }
  }, [landmarks, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      className="absolute inset-0 w-full h-full pointer-events-none"
    />
  );
}
