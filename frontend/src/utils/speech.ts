import { Lang } from '../types';
import { speechLang } from '../i18n';

export type SpeakResult = 'ok' | 'no-voice' | 'unsupported';

export const canSpeak = () => typeof window !== 'undefined' && 'speechSynthesis' in window;

// Browsers load their voice list asynchronously: the first getVoices() call is often
// empty, so wait briefly for 'voiceschanged' before choosing a voice.
const loadVoices = (): Promise<SpeechSynthesisVoice[]> =>
  new Promise(resolve => {
    const synth = window.speechSynthesis;
    const now = synth.getVoices();
    if (now.length) return resolve(now);
    const done = () => {
      synth.removeEventListener('voiceschanged', done);
      resolve(synth.getVoices());
    };
    synth.addEventListener('voiceschanged', done);
    setTimeout(done, 1500);
  });

// Prefer natural/online voices (Edge "Natural", Chrome "Google") over basic ones.
const rank = (v: SpeechSynthesisVoice) => (/natural|online|google/i.test(v.name) ? 0 : 1);

export const findVoice = (voices: SpeechSynthesisVoice[], language: Lang): SpeechSynthesisVoice | undefined => {
  const prefixes = language === 'mr' ? ['mr', 'hi'] : language === 'hi' ? ['hi'] : ['en-IN', 'en'];
  for (const prefix of prefixes) {
    const matches = voices.filter(v => v.lang.replace('_', '-').toLowerCase().startsWith(prefix.toLowerCase()));
    if (matches.length) return matches.sort((a, b) => rank(a) - rank(b))[0];
  }
  return undefined;
};

// Reference titles in parentheses and the "Sources:" line are English; skip them when speaking.
const speakableText = (text: string) =>
  text
    .split('\n')
    .filter(line => !/^(Sources|स्रोत):/.test(line.trim()))
    .join(' ')
    .replace(/\([A-Za-z0-9 :,&'/-]+\)/g, '');

/**
 * Read text aloud in the chosen language. For Hindi and Marathi we never fall back to an
 * English voice: it would skip all Devanagari and read only the English words.
 */
export const speak = async (text: string, language: Lang): Promise<SpeakResult> => {
  if (!canSpeak()) return 'unsupported';
  const synth = window.speechSynthesis;
  synth.cancel();
  const voice = findVoice(await loadVoices(), language);
  if (!voice && language !== 'en') return 'no-voice';

  const utter = new SpeechSynthesisUtterance(speakableText(text));
  utter.lang = voice?.lang || speechLang(language);
  if (voice) utter.voice = voice;
  utter.rate = 0.95;
  synth.speak(utter);
  return 'ok';
};

export const stopSpeaking = () => {
  if (canSpeak()) window.speechSynthesis.cancel();
};
