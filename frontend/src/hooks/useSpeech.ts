import { useState, useCallback, useEffect, useRef } from 'react';

const LANGUAGE_BCP47: Record<string, string> = {
  ru: 'ru-RU',
  en: 'en-US',
  kz: 'kk-KZ',
};

export function useSpeech() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported] = useState(() => 'speechSynthesis' in window);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Keep speaking state in sync with the browser's synthesis state.
  useEffect(() => {
    if (!isSupported) return;
    const onEnd = () => setIsSpeaking(false);
    const onError = () => setIsSpeaking(false);
    window.speechSynthesis.addEventListener('end' as never, onEnd);
    window.speechSynthesis.addEventListener('error' as never, onError);
    return () => {
      window.speechSynthesis.removeEventListener('end' as never, onEnd);
      window.speechSynthesis.removeEventListener('error' as never, onError);
    };
  }, [isSupported]);

  const speak = useCallback(
    (text: string, language = 'ru') => {
      if (!isSupported || !text.trim()) return;

      // Cancel any ongoing speech first.
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = LANGUAGE_BCP47[language] ?? 'ru-RU';
      utterance.rate = 0.95;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    },
    [isSupported],
  );

  const stop = useCallback(() => {
    if (!isSupported) return;
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, [isSupported]);

  return { speak, stop, isSpeaking, isSupported };
}
