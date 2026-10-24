import React from 'react';
import { MapPin, PhoneCall, AlertTriangle, FileSearch } from 'lucide-react';
import { CarePathway, Lang } from '../types';
import { makeT } from '../i18n';

interface CarePathwayCardProps {
  pathway: CarePathway;
  emergency: boolean;
  language: Lang;
  onBook?: (facilityId: number) => void;
}

// What a recognised condition needs, and which facility can actually provide it -
// built from the synthetic case reviews where delays came from going to the wrong place.
export const CarePathwayCard: React.FC<CarePathwayCardProps> = ({ pathway: p, emergency, language, onBook }) => {
  const t = makeT(language);
  const rec = p.recommended_facility;
  const nearestDiffers = p.nearest_facility && rec && p.nearest_facility.id !== rec.id;

  return (
    <div className={`rounded-xl border p-3 text-xs space-y-2 ${emergency ? 'bg-white border-red-200' : 'bg-white border-teal-200'}`}>
      <div className="font-bold text-slate-900 text-sm">{p.label}</div>
      <div className="text-slate-700">
        <span className="font-semibold">{t('ज़रूरत', 'Needs')}:</span> {p.needs_facility} • {p.needs_tests} • {p.needs_specialist}
      </div>

      {rec ? (
        <div className="flex flex-wrap items-center justify-between gap-2 bg-emerald-50 border border-emerald-200 rounded-lg p-2">
          <div>
            <div className="font-semibold text-emerald-900 flex items-center gap-1"><MapPin size={12} /> {t('यहां जाएं', 'Go to')}: {rec.name}</div>
            <div className="text-emerald-800">{rec.distance_km} km (~{rec.travel_time_mins} min) • {rec.phone}</div>
          </div>
          {emergency ? (
            <a href="tel:108" className="bg-red-600 text-white font-bold px-2.5 py-1 rounded-lg flex items-center gap-1"><PhoneCall size={12} /> 108</a>
          ) : onBook && (
            <button type="button" onClick={() => onBook(rec.id)} className="bg-teal-700 text-white font-bold px-2.5 py-1 rounded-lg">{t('यहां बुक करें', 'Book here')}</button>
          )}
        </div>
      ) : (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-lg p-2 flex items-start gap-1">
          <AlertTriangle size={12} className="mt-0.5 shrink-0" />
          {t('आपके ज़िले में किसी केंद्र पर यह सब उपलब्ध नहीं है। 108 पर कॉल करें - एम्बुलेंस सही अस्पताल तक ले जाएगी।',
            'No facility in your district has all of this. Call 108 - the ambulance team will take you to a hospital that does.')}
        </div>
      )}

      {nearestDiffers && p.nearest_facility_missing.length > 0 && (
        <div className="text-slate-600">
          {t('नज़दीकी', 'The nearer')} {p.nearest_facility!.name} ({p.nearest_facility!.distance_km} km) {t('में नहीं है', 'does not have')}: <span className="font-semibold text-rose-700">{p.nearest_facility_missing.join(', ')}</span>
        </div>
      )}

      {p.case_reviews.cases > 0 && (
        <div className="text-[11px] text-slate-500 flex items-start gap-1">
          <FileSearch size={12} className="mt-0.5 shrink-0" />
          <span>
            {t('ऐसे', 'In')} {p.case_reviews.cases} {t('काल्पनिक केस समीक्षाओं में मुख्य बाधा थी', 'synthetic case reviews like this, the main barrier was')}: “{p.case_reviews.main_barrier}” ({t('औसत', 'median')} {p.case_reviews.median_distance_km} km, {p.case_reviews.median_delay_hrs} {t('घंटे की देरी', 'hrs delay')}).
          </span>
        </div>
      )}
    </div>
  );
};
