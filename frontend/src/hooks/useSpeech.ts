import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import type { Language } from '../types';

const LANGUAGE_BCP47: Record<Language, string> = {
  ru: 'ru-RU',
  en: 'en-US',
  kz: 'kk-KZ',
};

type SpeechBoundary = {
  charIndex: number;
  charLength: number;
  name?: string;
};

function appLanguageToBcp47(language: string): string {
  if (language === 'en' || language === 'ru' || language === 'kz') {
    return LANGUAGE_BCP47[language];
  }
  return 'ru-RU';
}

export function useSpeech() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSupported] = useState(
    () => typeof window !== 'undefined' && 'speechSynthesis' in window,
  );
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoiceURI, setSelectedVoiceURI] = useState<string | null>(() => {
    if (typeof window === 'undefined') {
      return null;
    }
    try {
      return localStorage.getItem('tts.voiceURI');
    } catch {
      return null;
    }
  });
  const [activeBoundary, setActiveBoundary] = useState<SpeechBoundary | null>(null);
  const [speakingText, setSpeakingText] = useState<string>('');
  const [activeVoiceURI, setActiveVoiceURI] = useState<string | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    if (!isSupported) {
      return;
    }
    const updateVoices = () => setVoices(window.speechSynthesis.getVoices());

    updateVoices();
    window.speechSynthesis.addEventListener('voiceschanged', updateVoices);

    return () => {
      window.speechSynthesis.removeEventListener('voiceschanged', updateVoices);
    };
  }, [isSupported]);

  useEffect(() => {
    try {
      if (selectedVoiceURI) {
        localStorage.setItem('tts.voiceURI', selectedVoiceURI);
      } else {
        localStorage.removeItem('tts.voiceURI');
      }
    } catch {
      // Ignore storage failures (private mode / blocked storage).
    }
  }, [selectedVoiceURI]);

  const autoVoiceForLanguage = useCallback(
    (language: string) => {
      const target = appLanguageToBcp47(language);
      const targetPrefix = target.split('-')[0]?.toLowerCase() ?? '';

      const exact = voices.find((v) => v.lang.toLowerCase() === target.toLowerCase());
      if (exact) {
        return exact;
      }

      const prefix = voices.find(
        (v) =>
          v.lang.toLowerCase().startsWith(`${targetPrefix}-`) ||
          v.lang.toLowerCase() === targetPrefix,
      );
      if (prefix) {
        return prefix;
      }

      return voices[0] ?? null;
    },
    [voices],
  );

  const selectedVoice = useMemo(() => {
    if (!selectedVoiceURI) {
      return null;
    }
    return voices.find((v) => v.voiceURI === selectedVoiceURI) ?? null;
  }, [selectedVoiceURI, voices]);

  const activeVoice = useMemo(() => {
    if (!activeVoiceURI) {
      return null;
    }
    return voices.find((v) => v.voiceURI === activeVoiceURI) ?? null;
  }, [activeVoiceURI, voices]);

  const speak = useCallback(
    (text: string, language: Language | string = 'ru') => {
      if (!isSupported || !text.trim()) {
        return;
      }

      window.speechSynthesis.cancel();
      setActiveBoundary(null);
      setActiveVoiceURI(null);

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = appLanguageToBcp47(language);
      utterance.rate = 0.95;
      const chosen = selectedVoice ?? autoVoiceForLanguage(language);
      if (chosen) {
        utterance.voice = chosen;
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
        setIsPaused(false);
        setSpeakingText(text);
        setActiveVoiceURI(utterance.voice?.voiceURI ?? null);
      };
      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPaused(false);
        setActiveBoundary(null);
        setActiveVoiceURI(null);
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
        setIsPaused(false);
        setActiveBoundary(null);
        setActiveVoiceURI(null);
      };
      utterance.onboundary = (event) => {
        setActiveBoundary({
          charIndex: event.charIndex,
          charLength: typeof event.charLength === 'number' ? event.charLength : 0,
          name: event.name,
        });
      };

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    },
    [autoVoiceForLanguage, isSupported, selectedVoice],
  );

  const pause = useCallback(() => {
    if (!isSupported) {
      return;
    }
    if (!window.speechSynthesis.speaking) {
      return;
    }
    window.speechSynthesis.pause();
    setIsPaused(true);
  }, [isSupported]);

  const resume = useCallback(() => {
    if (!isSupported) {
      return;
    }
    if (!window.speechSynthesis.paused) {
      return;
    }
    window.speechSynthesis.resume();
    setIsPaused(false);
  }, [isSupported]);

  const stop = useCallback(() => {
    if (!isSupported) {
      return;
    }
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
    setActiveBoundary(null);
    setActiveVoiceURI(null);
  }, [isSupported]);

  return {
    speak,
    stop,
    pause,
    resume,
    isSpeaking,
    isPaused,
    isSupported,
    voices,
    selectedVoiceURI,
    setSelectedVoiceURI,
    activeBoundary,
    speakingText,
    activeVoice,
  };
}
