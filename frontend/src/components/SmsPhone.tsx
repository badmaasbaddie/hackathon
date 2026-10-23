import React, { useEffect, useState } from 'react';
import { Smartphone } from 'lucide-react';
import { Lang, NotificationItem } from '../types';
import { api } from '../services/api';
import { makeT } from '../i18n';

// A phone mock-up showing the simulated SMS the platform has "sent" to this patient.
export const SmsPhone: React.FC<{ language: Lang }> = ({ language }) => {
  const t = makeT(language);
  const [messages, setMessages] = useState<NotificationItem[]>([]);

  const load = () => api.getMyNotifications().then(setMessages).catch(() => {});

  useEffect(() => {
    load();
    const onChange = () => load();
    window.addEventListener('swasthyasetu-data-changed', onChange);
    const timer = setInterval(load, 10000);
    return () => {
      window.removeEventListener('swasthyasetu-data-changed', onChange);
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="mx-auto w-full max-w-[260px] rounded-[2rem] border-[6px] border-slate-800 bg-slate-800 shadow-lg">
      <div className="rounded-[1.5rem] bg-slate-50 overflow-hidden">
        <div className="bg-slate-800 text-white text-[11px] px-4 py-2 flex items-center gap-1.5">
          <Smartphone size={12} /> {t('आपके फोन पर SMS (डेमो)', 'SMS on your phone (demo)')}
        </div>
        <div className="h-64 overflow-y-auto p-2.5 space-y-2" aria-live="polite">
          {messages.length === 0 && <p className="text-[11px] text-slate-400 text-center mt-8">{t('अभी कोई संदेश नहीं', 'No messages yet')}</p>}
          {messages.map(m => (
            <div key={m.id} className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-3 py-2 text-[11px] text-slate-700 shadow-sm">
              <div className="font-bold text-teal-800">VM-SWSTHY • {m.title}</div>
              <div>{m.message}</div>
              <div className="text-[9px] text-slate-400 text-right mt-0.5">{new Date(m.created_at).toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
