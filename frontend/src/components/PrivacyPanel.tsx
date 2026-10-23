import React, { useEffect, useRef, useState } from 'react';
import { Lock, ShieldCheck, ShieldOff } from 'lucide-react';
import { CareTeamMember, Lang } from '../types';
import { api } from '../services/api';
import { makeT } from '../i18n';

// Patient-controlled consent: which doctors / ASHA workers may open the health record.
export const PrivacyPanel: React.FC<{ language: Lang }> = ({ language }) => {
  const t = makeT(language);
  const [team, setTeam] = useState<CareTeamMember[]>([]);
  const [busy, setBusy] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.getCareTeam().then(setTeam).catch(err => setError(err.message));

  useEffect(() => {
    load();
    const onChange = () => load();
    window.addEventListener('swasthyasetu-data-changed', onChange);
    return () => window.removeEventListener('swasthyasetu-data-changed', onChange);
  }, []);

  const toggle = async (m: CareTeamMember) => {
    setBusy(m.user_id);
    try {
      setTeam(await api.setConsent(m.user_id, m.consent_status !== 'GRANTED'));
      window.dispatchEvent(new Event('swasthyasetu-data-changed'));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  };

  const demoRef = useRef<(detail: any) => void>(() => {});
  demoRef.current = (detail: any) => {
    if (detail.action !== 'revoke-doctor') return;
    const doctor = team.find(m => m.role === 'DOCTOR' && m.consent_status === 'GRANTED');
    if (doctor) toggle(doctor);
  };
  useEffect(() => {
    const onDemo = (e: Event) => demoRef.current((e as CustomEvent).detail);
    window.addEventListener('swasthyasetu-demo', onDemo);
    return () => window.removeEventListener('swasthyasetu-demo', onDemo);
  }, []);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
      <div>
        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2"><Lock className="text-teal-700" size={20} /> {t('मेरा स्वास्थ्य रिकॉर्ड कौन देख सकता है', 'Who can see my health record')}</h3>
        <p className="text-xs text-slate-500">{t('आप तय करते हैं कि कौन से डॉक्टर और आशा कार्यकर्ता आपका रिकॉर्ड खोल सकते हैं। बदलाव तुरंत लागू होते हैं और दर्ज किए जाते हैं।', 'You decide which doctors and ASHA workers can open your record. Changes take effect immediately and are recorded.')}</p>
      </div>
      {error && <div className="text-xs text-rose-800 bg-rose-50 border border-rose-200 rounded-lg p-2">{error}</div>}
      {team.length === 0 && <p className="text-xs text-slate-400">{t('अभी कोई डॉक्टर या आशा कार्यकर्ता आपसे जुड़ा नहीं है।', 'No doctors or ASHA workers are linked to you yet.')}</p>}
      <div className="space-y-3">
        {team.map(m => {
          const allowed = m.consent_status === 'GRANTED';
          return (
            <div key={m.user_id} className={`flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border ${allowed ? 'border-emerald-200 bg-emerald-50/50' : 'border-rose-200 bg-rose-50/50'}`}>
              <div className="flex items-center gap-3">
                {allowed ? <ShieldCheck className="text-emerald-700" size={22} /> : <ShieldOff className="text-rose-700" size={22} />}
                <div>
                  <div className="text-sm font-bold text-slate-900">{m.name} <span className="text-[10px] font-semibold bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded">{m.role}</span></div>
                  <div className="text-xs text-slate-500">{m.detail}</div>
                  <div className={`text-[11px] font-bold ${allowed ? 'text-emerald-700' : 'text-rose-700'}`}>{allowed ? t('अनुमति है', 'Allowed') : t('बंद', 'Blocked')}</div>
                </div>
              </div>
              <button onClick={() => toggle(m)} disabled={busy === m.user_id}
                className={`text-xs font-bold px-3 py-1.5 rounded-lg disabled:opacity-50 ${allowed ? 'bg-rose-600 hover:bg-rose-700 text-white' : 'bg-emerald-600 hover:bg-emerald-700 text-white'}`}>
                {allowed ? t('अनुमति हटाएं', 'Withdraw access') : t('अनुमति दें', 'Allow access')}
              </button>
            </div>
          );
        })}
      </div>
      <p className="text-[11px] text-slate-500">{t('आपात स्थिति में अस्पताल स्टाफ फिर भी इलाज कर सकता है; यह केवल डिजिटल रिकॉर्ड की पहुंच नियंत्रित करता है।', 'In an emergency, hospital staff can still treat you; this controls access to your digital record.')}</p>
    </div>
  );
};
