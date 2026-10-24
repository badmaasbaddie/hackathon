import React, { useEffect, useState } from 'react';
import { FileSearch, AlertTriangle } from 'lucide-react';
import { CaseReviewSummary, Lang } from '../types';
import { api } from '../services/api';
import { makeT } from '../i18n';

// District view of the 100 synthetic case reviews: what went wrong, and how ready today's facilities are.
export const CaseReviewPanel: React.FC<{ language: Lang }> = ({ language }) => {
  const t = makeT(language);
  const [data, setData] = useState<CaseReviewSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getCaseReviews().then(setData).catch(err => setError(err.message));
  }, []);

  if (error) return <div className="text-xs bg-rose-50 border border-rose-300 text-rose-900 rounded-xl p-3">{error}</div>;
  if (!data) return null;

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <FileSearch className="text-teal-700" size={18} /> {t('100 केस समीक्षाओं से सीख', 'Lessons from 100 case reviews')}
          </h3>
          <p className="text-xs text-slate-500">
            {t('हर स्थिति को क्या चाहिए था, और आज कितने केंद्र वह दे सकते हैं।', 'What each condition needed, and how many facilities can provide it today.')}
          </p>
        </div>
        <span className="text-[11px] bg-amber-100 text-amber-900 border border-amber-300 font-bold px-2 py-1 rounded">
          {t('काल्पनिक डेटा', 'Synthetic data')}
        </span>
      </div>

      <div className="text-[11px] bg-amber-50 border border-amber-200 text-amber-900 rounded-lg p-2.5 flex items-start gap-1.5">
        <AlertTriangle size={13} className="mt-0.5 shrink-0" /> {data.notice}
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-slate-50 rounded-xl p-3 border border-slate-200"><div className="text-xl font-black">{data.total_cases}</div><div className="text-[11px] text-slate-500">{t('केस समीक्षाएं', 'case reviews')}</div></div>
        <div className="bg-slate-50 rounded-xl p-3 border border-slate-200"><div className="text-xl font-black">{data.median_distance_km} km</div><div className="text-[11px] text-slate-500">{t('औसत दूरी', 'median distance')}</div></div>
        <div className="bg-slate-50 rounded-xl p-3 border border-slate-200"><div className="text-xl font-black">{data.median_delay_hrs} h</div><div className="text-[11px] text-slate-500">{t('औसत देरी', 'median delay')}</div></div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-slate-500 border-b border-slate-200">
              <th className="py-1.5 pr-2">{t('स्थिति', 'Condition')}</th>
              <th className="py-1.5 pr-2">{t('ज़रूरत', 'Needs')}</th>
              <th className="py-1.5 pr-2">{t('मुख्य बाधा', 'Main barrier')}</th>
              <th className="py-1.5">{t('तैयार केंद्र', 'Facilities ready today')}</th>
            </tr>
          </thead>
          <tbody>
            {data.conditions.map(c => {
              const share = c.facilities_ready / Math.max(c.facilities_total, 1);
              return (
                <tr key={c.condition} className="border-b border-slate-100 align-top">
                  <td className="py-1.5 pr-2 font-semibold text-slate-900">{c.condition}<div className="font-normal text-slate-400">{c.cases} {t('केस', 'cases')}</div></td>
                  <td className="py-1.5 pr-2 text-slate-600">{c.needs_tests} • {c.needs_specialist}</td>
                  <td className="py-1.5 pr-2 text-slate-600">{c.main_barrier}</td>
                  <td className="py-1.5">
                    <span className={`font-bold px-1.5 py-0.5 rounded ${share < 0.34 ? 'bg-rose-100 text-rose-800' : share < 0.75 ? 'bg-amber-100 text-amber-900' : 'bg-emerald-100 text-emerald-800'}`}>
                      {c.facilities_ready} / {c.facilities_total}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="space-y-1.5">
        <h4 className="text-xs font-bold text-slate-800">{t('बाधाएं और SwasthyaSetu का जवाब', 'Barriers, and how SwasthyaSetu responds')}</h4>
        {data.barriers.map(b => (
          <div key={b.barrier} className="text-xs flex flex-wrap gap-x-2 border-b border-slate-100 pb-1">
            <span className="font-semibold text-slate-900 capitalize">{b.barrier}</span>
            <span className="text-slate-400">({b.cases} {t('केस', 'cases')})</span>
            {b.how_swasthyasetu_helps && <span className="text-teal-800">→ {b.how_swasthyasetu_helps}</span>}
          </div>
        ))}
      </div>

      <p className="text-[11px] text-slate-500">
        {t('उपयोग नहीं किया गया', 'Not used')}: {Object.values(data.excluded_fields).join(' ')}
      </p>
    </section>
  );
};
