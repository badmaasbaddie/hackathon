import { Lang } from '../types';
import { speechLang } from '../i18n';
import { authHeaders } from '../services/api';

export type SpeakResult = 'ok' | 'no-voice' | 'unsupported';

const browserCanSpeak = () => typeof window !== 'undefined' && 'speechSynthesis' in window;
export const canSpeak = () => typeof window !== 'undefined' && (browserCanSpeak() || typeof Audio !== 'undefined');

// ElevenLabs voices are used when the server has an API key; otherwise the browser's own voices.
let providerPromise: Promise<'elevenlabs' | 'browser'> | null = null;
const getProvider = () => {
  if (!providerPromise) {
    providerPromise = fetch('/api/tts/status')
      .then(r => (r.ok ? r.json() : { provider: 'browser' }))
      .then(d => (d.provider === 'elevenlabs' ? 'elevenlabs' : 'browser'))
      .catch(() => 'browser' as const);
  }
  return providerPromise;
};

let currentAudio: HTMLAudioElement | null = null;
let currentUrl: string | null = null;

const stopAudio = () => {
  if (currentAudio) currentAudio.pause();
  if (currentUrl) URL.revokeObjectURL(currentUrl);
  currentAudio = null;
  currentUrl = null;
};

// The server returns a single-use link; the <audio> element streams it, so playback starts
// while ElevenLabs is still generating the rest of the answer.
const speakWithElevenLabs = async (text: string, language: Lang): Promise<boolean> => {
  try {
    const res = await fetch('/api/tts/prepare', { method: 'POST', headers: authHeaders(), body: JSON.stringify({ text, language }) });
    if (!res.ok) return false;
    const { url } = await res.json();
    stopAudio();
    currentAudio = new Audio(url);
    await currentAudio.play();
    return true;
  } catch {
    return false;
  }
};

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
  stopSpeaking();
  if ((await getProvider()) === 'elevenlabs' && (await speakWithElevenLabs(text, language))) return 'ok';
  if (!browserCanSpeak()) return 'unsupported';
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
  stopAudio();
  if (browserCanSpeak()) window.speechSynthesis.cancel();
};
