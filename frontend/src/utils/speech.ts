import { Lang } from '../types';
import { speechLang } from '../i18n';

export const canSpeak = () => typeof window !== 'undefined' && 'speechSynthesis' in window;

// Read text aloud with the browser's built-in voices. Marathi voices are missing on
// many devices, so fall back to a Hindi voice (same script) and then to the default.
export const speak = (text: string, language: Lang) => {
  if (!canSpeak()) return false;
  const synth = window.speechSynthesis;
  synth.cancel();
  const clean = text.split('\n').filter(line => !/^(Sources|स्रोत):/.test(line.trim())).join(' ');
  const utter = new SpeechSynthesisUtterance(clean);
  const wanted = speechLang(language);
  const voices = synth.getVoices();
  const voice = voices.find(v => v.lang === wanted)
    || voices.find(v => v.lang.startsWith(wanted.slice(0, 2)))
    || (language === 'mr' ? voices.find(v => v.lang.startsWith('hi')) : undefined);
  utter.lang = voice?.lang || wanted;
  if (voice) utter.voice = voice;
  utter.rate = 0.95;
  synth.speak(utter);
  return true;
};

export const stopSpeaking = () => {
  if (canSpeak()) window.speechSynthesis.cancel();
};
