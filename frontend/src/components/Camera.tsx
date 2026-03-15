import { useEffect, useImperativeHandle, forwardRef } from 'react';
import { Video, VideoOff, AlertCircle } from 'lucide-react';
import { useCamera } from '../hooks/useCamera';

interface CameraProps {
  isTranslating: boolean;
}

export interface CameraRef {
  captureFrame: () => string | null;
  startCamera: () => Promise<void>;
  stopCamera: () => void;
}

export const Camera = forwardRef<CameraRef, CameraProps>(
  ({ isTranslating }, ref) => {
    const { videoRef, canvasRef, isReady, error, startCamera, stopCamera, captureFrame } = useCamera();

    // Expose captureFrame to parent
    useImperativeHandle(ref, () => ({
      captureFrame,
      startCamera,
      stopCamera,
    }));

    // Auto-start camera when component mounts
    useEffect(() => {
      startCamera();
      
      return () => {
        stopCamera();
      };
    }, []);

    return (
      <div className="relative bg-gray-900 rounded-xl overflow-hidden shadow-lg">
        <div className="relative aspect-video bg-black">
          {/* Video element is always in the DOM so videoRef is available */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`w-full h-full object-cover ${isReady ? '' : 'hidden'}`}
          />

          {/* Overlays */}
          {error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-white p-6">
              <AlertCircle className="w-12 h-12 mb-4 text-red-400" />
              <p className="text-center text-gray-300">{error}</p>
              <button
                onClick={startCamera}
                className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {!error && !isReady && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-white">
              <Video className="w-12 h-12 mb-4 text-gray-400 animate-pulse" />
              <p className="text-gray-400">Initializing camera...</p>
            </div>
          )}

          {isReady && isTranslating && (
            <div className="absolute top-4 right-4 flex items-center gap-2 bg-black/50 px-3 py-1.5 rounded-full">
              <div className="w-3 h-3 bg-red-500 rounded-full recording-indicator" />
              <span className="text-white text-sm font-medium">Recording</span>
            </div>
          )}

          {isReady && (
            <div className="absolute bottom-4 left-4 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-white text-sm bg-black/50 px-2 py-1 rounded">
                Camera ready
              </span>
            </div>
          )}
        </div>

        <canvas ref={canvasRef} className="hidden" />

        <div className="bg-gray-800 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-300">
            {isReady ? (
              <Video className="w-4 h-4 text-green-400" />
            ) : (
              <VideoOff className="w-4 h-4 text-red-400" />
            )}
            <span className="text-sm">
              {isReady ? 'Camera active' : 'Camera inactive'}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            Resolution: 640x480
          </div>
        </div>
      </div>
    );
  }
);

Camera.displayName = 'Camera';
