import { Lang } from './types';
import { MR } from './i18n.mr';

// Components write every label as t(hindi, english). Marathi text is looked up by the
// English string; anything not yet translated falls back to Hindi (also Devanagari).
export const makeT = (language: Lang) => (hi: string, en: string): string =>
  language === 'en' ? en : language === 'mr' ? (MR[en] ?? hi) : hi;

export const speechLang = (language: Lang) => (language === 'mr' ? 'mr-IN' : language === 'hi' ? 'hi-IN' : 'en-IN');
