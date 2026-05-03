import { useState, useCallback, useEffect, useRef } from 'react';
import type { Language } from '../types';

const LANGUAGE_BCP47: Record<Language, string> = {
  ru: 'ru-RU',
  en: 'en-US',
  kz: 'kk-KZ',
};

function normalizeLangTag(tag: string): string {
  return tag.replace('_', '-').toLowerCase();
}

function bestVoiceForLang(bcp47: string): SpeechSynthesisVoice | undefined {
  const voices = window.speechSynthesis.getVoices();
  if (voices.length === 0) {
    return undefined;
  }
  const target = normalizeLangTag(bcp47);
  const primary = target.split('-')[0] ?? target;

  const exact = voices.find((v) => normalizeLangTag(v.lang) === target);
  if (exact) {
    return exact;
  }

  const withPrimary = voices.find((v) =>
    normalizeLangTag(v.lang).startsWith(`${primary}-`),
  );
  if (withPrimary) {
    return withPrimary;
  }

  return voices.find((v) => normalizeLangTag(v.lang).startsWith(primary));
}

export function useSpeech() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported] = useState(
    () => typeof window !== 'undefined' && 'speechSynthesis' in window,
  );
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    if (!isSupported) {
      return;
    }
    const primeVoices = () => {
      window.speechSynthesis.getVoices();
    };
    primeVoices();
    window.speechSynthesis.addEventListener('voiceschanged', primeVoices);
    return () => {
      window.speechSynthesis.removeEventListener('voiceschanged', primeVoices);
    };
  }, [isSupported]);

  const speakWithVoices = useCallback((utterance: SpeechSynthesisUtterance) => {
    const voice = bestVoiceForLang(utterance.lang);
    if (voice) {
      utterance.voice = voice;
    }
    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, []);

  const speak = useCallback(
    (text: string, language: Language = 'ru') => {
      if (!isSupported || !text.trim()) {
        return;
      }

      window.speechSynthesis.cancel();

      const bcp47 = LANGUAGE_BCP47[language];
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = bcp47;
      utterance.rate = 0.95;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      const start = () => {
        if (window.speechSynthesis.getVoices().length > 0) {
          speakWithVoices(utterance);
          return;
        }
        const onVoicesChanged = () => {
          window.speechSynthesis.removeEventListener(
            'voiceschanged',
            onVoicesChanged,
          );
          speakWithVoices(utterance);
        };
        window.speechSynthesis.addEventListener(
          'voiceschanged',
          onVoicesChanged,
        );
        window.speechSynthesis.getVoices();
      };

      queueMicrotask(start);
    },
    [isSupported, speakWithVoices],
  );

  const stop = useCallback(() => {
    if (!isSupported) {
      return;
    }
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, [isSupported]);

  return { speak, stop, isSpeaking, isSupported };
}
