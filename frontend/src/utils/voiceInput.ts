import { Lang } from '../types';
import { speechLang } from '../i18n';
import { getAuthToken } from '../services/api';

export type VoiceState = 'idle' | 'listening' | 'transcribing';
export type VoiceError = 'blocked' | 'no-mic' | 'network' | 'no-speech' | 'language' | 'unsupported' | 'failed';

export interface VoiceHandlers {
  onState: (state: VoiceState) => void;
  onText: (text: string) => void;
  onError: (error: VoiceError) => void;
}

export interface VoiceSession {
  stop: () => void;
}

const MAX_RECORDING_MS = 15000;

// The server transcribes recordings with ElevenLabs Scribe (when the key allows it) or with
// Whisper running on the server's computer; otherwise the browser's own recognition is used.
let providerPromise: Promise<'server' | 'browser'> | null = null;
let checkedAt = 0;
const getProvider = () => {
  // Re-check now and then, so turning on the permission at ElevenLabs takes effect without a reload.
  if (!providerPromise || Date.now() - checkedAt > 60000) {
    checkedAt = Date.now();
    providerPromise = fetch('/api/stt/status')
      .then(r => (r.ok ? r.json() : { provider: 'browser' }))
      .then(d => (d.provider === 'elevenlabs' || d.provider === 'local' ? 'server' : 'browser'))
      .catch(() => 'browser' as const);
  }
  return providerPromise;
};

const canRecord = () => typeof MediaRecorder !== 'undefined' && !!navigator.mediaDevices?.getUserMedia;
const browserRecognition = () => (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

const recordForServer = async (language: Lang, h: VoiceHandlers): Promise<VoiceSession | null> => {
  let stream: MediaStream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err: any) {
    h.onError(err?.name === 'NotFoundError' ? 'no-mic' : 'blocked');
    return null;
  }
  const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'].find(m => MediaRecorder.isTypeSupported(m));
  const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
  const parts: Blob[] = [];
  recorder.ondataavailable = e => { if (e.data.size) parts.push(e.data); };
  recorder.onstop = async () => {
    stream.getTracks().forEach(t => t.stop());
    clearTimeout(timer);
    h.onState('transcribing');
    try {
      const blob = new Blob(parts, { type: recorder.mimeType || 'audio/webm' });
      const res = await fetch(`/api/stt?language=${language}`, {
        method: 'POST',
        headers: { 'Content-Type': blob.type, Authorization: `Bearer ${getAuthToken() ?? ''}` },
        body: blob,
      });
      if (!res.ok) {
        providerPromise = null; // re-check; the server may have switched to browser recognition
        h.onError(res.status === 502 ? 'failed' : 'network');
      } else {
        const { text } = await res.json();
        if (text) h.onText(text);
        else h.onError('no-speech');
      }
    } catch {
      h.onError('network');
    } finally {
      h.onState('idle');
    }
  };
  recorder.start();
  h.onState('listening');
  const timer = setTimeout(() => recorder.state === 'recording' && recorder.stop(), MAX_RECORDING_MS);
  return { stop: () => recorder.state === 'recording' && recorder.stop() };
};

const ERROR_MAP: Record<string, VoiceError> = {
  'not-allowed': 'blocked',
  'service-not-allowed': 'blocked',
  'audio-capture': 'no-mic',
  network: 'network',
  'no-speech': 'no-speech',
  'language-not-supported': 'language',
};

const recognizeInBrowser = (language: Lang, h: VoiceHandlers): VoiceSession | null => {
  const SpeechRecognition = browserRecognition();
  if (!SpeechRecognition) {
    h.onError('unsupported');
    return null;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = speechLang(language);
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  let gotText = false;
  let failed = false;
  recognition.onresult = (event: any) => {
    gotText = true;
    h.onText(event.results[0][0].transcript);
  };
  recognition.onerror = (event: any) => {
    if (event.error === 'aborted') return;
    failed = true;
    h.onError(ERROR_MAP[event.error] || 'failed');
  };
  recognition.onend = () => {
    if (!gotText && !failed) h.onError('no-speech');
    h.onState('idle');
  };
  try {
    recognition.start();
  } catch {
    h.onError('failed');
    return null;
  }
  h.onState('listening');
  return { stop: () => recognition.stop() };
};

export const startVoiceInput = async (language: Lang, handlers: VoiceHandlers): Promise<VoiceSession | null> => {
  if ((await getProvider()) === 'server' && canRecord()) return recordForServer(language, handlers);
  return recognizeInBrowser(language, handlers);
};
