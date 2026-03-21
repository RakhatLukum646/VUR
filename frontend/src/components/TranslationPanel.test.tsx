import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useAppStore } from '../store/useAppStore';
import { TranslationPanel } from './TranslationPanel';

vi.mock('../hooks/useSpeech', () => ({
  useSpeech: () => ({
    speak: vi.fn(),
    stop: vi.fn(),
    isSpeaking: false,
    isSupported: false,
  }),
}));

describe('TranslationPanel', () => {
  it('shows guidance and low-confidence explanation', () => {
    useAppStore.setState({
      detectedSigns: ['A', 'B'],
      currentSentence: '',
      translationHistory: [],
      language: 'ru',
    });

    render(
      <TranslationPanel
        lastSign="B"
        confidence={0.4}
        guidance="Move your hand closer to the camera."
        frameQuality={0.35}
        stability={0.5}
        sequenceLength={2}
        handDetected
      />
    );

    expect(
      screen.getByText('Move your hand closer to the camera.')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Low confidence. Adjust framing, lighting, or hand shape.')
    ).toBeInTheDocument();
    expect(screen.getByText('Buffered signs in current phrase: 2')).toBeInTheDocument();
  });
});
