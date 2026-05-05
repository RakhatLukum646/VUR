import { useState, useCallback, useEffect, useMemo, useRef } from 'react';

const LANGUAGE_BCP47: Record<string, string> = {
  ru: 'ru-RU',
  en: 'en-US',
  kz: 'kk-KZ',
};

type SpeechBoundary = {
  charIndex: number;
  charLength: number;
  name?: string;
};

export function useSpeech() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSupported] = useState(() => 'speechSynthesis' in window);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoiceURI, setSelectedVoiceURI] = useState<string | null>(() => {
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
    if (!isSupported) return;
    const updateVoices = () => setVoices(window.speechSynthesis.getVoices());

    updateVoices();
    const prev = window.speechSynthesis.onvoiceschanged;
    window.speechSynthesis.onvoiceschanged = () => {
      updateVoices();
      if (typeof prev === 'function') {
        prev.call(window.speechSynthesis, new Event('voiceschanged'));
      }
    };

    return () => {
      window.speechSynthesis.onvoiceschanged = prev ?? null;
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

  const bcp47ForLanguage = useCallback(
    (language: string) => LANGUAGE_BCP47[language] ?? 'ru-RU',
    []
  );

  const autoVoiceForLanguage = useCallback(
    (language: string) => {
      const target = bcp47ForLanguage(language);
      const targetPrefix = target.split('-')[0]?.toLowerCase() ?? '';

      const exact = voices.find((v) => v.lang.toLowerCase() === target.toLowerCase());
      if (exact) return exact;

      const prefix = voices.find(
        (v) => v.lang.toLowerCase().startsWith(`${targetPrefix}-`) || v.lang.toLowerCase() === targetPrefix
      );
      if (prefix) return prefix;

      return voices[0] ?? null;
    },
    [bcp47ForLanguage, voices]
  );

  const selectedVoice = useMemo(() => {
    if (!selectedVoiceURI) return null;
    return voices.find((v) => v.voiceURI === selectedVoiceURI) ?? null;
  }, [selectedVoiceURI, voices]);

  const activeVoice = useMemo(() => {
    if (!activeVoiceURI) return null;
    return voices.find((v) => v.voiceURI === activeVoiceURI) ?? null;
  }, [activeVoiceURI, voices]);

  const speak = useCallback(
    (text: string, language = 'ru') => {
      if (!isSupported || !text.trim()) return;

      // Cancel any ongoing speech first.
      window.speechSynthesis.cancel();
      setActiveBoundary(null);
      setActiveVoiceURI(null);

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = bcp47ForLanguage(language);
      utterance.rate = 0.95;
      utterance.voice = selectedVoice ?? autoVoiceForLanguage(language);
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
    [autoVoiceForLanguage, bcp47ForLanguage, isSupported, selectedVoice]
  );

  const pause = useCallback(() => {
    if (!isSupported) return;
    if (!window.speechSynthesis.speaking) return;
    window.speechSynthesis.pause();
    setIsPaused(true);
  }, [isSupported]);

  const resume = useCallback(() => {
    if (!isSupported) return;
    if (!window.speechSynthesis.paused) return;
    window.speechSynthesis.resume();
    setIsPaused(false);
  }, [isSupported]);

  const stop = useCallback(() => {
    if (!isSupported) return;
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
