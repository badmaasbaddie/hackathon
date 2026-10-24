import React, { useEffect, useRef, useState } from 'react';
import { Upload, FileText, Stethoscope, Clock, IndianRupee, AlertTriangle, PhoneCall, Pill, ScanLine, CheckCircle2 } from 'lucide-react';
import { Lang, ReportAnalysisResult, ReportSummary } from '../types';
import { api } from '../services/api';
import { makeT } from '../i18n';

interface ReportsPanelProps {
  language: Lang;
  history: ReportSummary[];
  onBook: (facilityId: number) => void;
  onAnalysed: () => void;
}

const URGENCY_STYLE: Record<string, string> = {
  EMERGENCY: 'bg-red-50 border-red-500 text-red-900',
  URGENT: 'bg-amber-50 border-amber-500 text-amber-900',
  ROUTINE: 'bg-teal-50 border-teal-400 text-teal-900',
  NORMAL: 'bg-emerald-50 border-emerald-400 text-emerald-900',
};
const STATUS_STYLE: Record<string, string> = {
  normal: 'text-emerald-700', negative: 'text-emerald-700', info: 'text-sky-700',
  low: 'text-amber-700 font-bold', high: 'text-amber-700 font-bold', positive: 'text-rose-700 font-bold',
  critical_low: 'text-red-700 font-black', critical_high: 'text-red-700 font-black',
};

export const ReportsPanel: React.FC<ReportsPanelProps> = ({ language, history, onBook, onAnalysed }) => {
  const t = makeT(language);
  const [file, setFile] = useState<File | null>(null);
  const [pasted, setPasted] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReportAnalysisResult | null>(null);
  const [visionAvailable, setVisionAvailable] = useState<boolean | null>(null);
  const [modelInfo, setModelInfo] = useState<any>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.getReportStatus().then(s => { setVisionAvailable(s.vision_available); setModelInfo(s.model); }).catch(() => {});
  }, []);

  const analyse = async () => {
    setError(null);
    setResult(null);
    if (!file && !pasted.trim()) {
      setError(t('कोई रिपोर्ट फाइल चुनें या उसका टेक्स्ट चिपकाएं।', 'Choose a report file or paste its text.'));
      return;
    }
    setBusy(true);
    try {
      const res = await api.analyzeReport(file ?? new Blob([pasted], { type: 'text/plain' }), file?.name || 'pasted-text.txt', symptoms, language);
      setResult(res);
      onAnalysed();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const openSaved = async (id: number) => {
    setError(null);
    try {
      setResult(await api.getReport(id));
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err: any) {
      setError(err.message);
    }
  };

  const typeLabel = (rt: string) => ({
    lab_report: t('लैब रिपोर्ट', 'Lab report'), imaging_report: t('स्कैन / ईसीजी रिपोर्ट', 'Scan / ECG report'),
    prescription: t('पर्चा', 'Prescription'), other: t('रिपोर्ट', 'Report'),
  } as Record<string, string>)[rt] || rt;

  const urgencyLabel = (u: string) => ({
    EMERGENCY: t('आपातकाल - अभी 112/108 पर कॉल करें', 'Emergency - call 112/108 now'),
    URGENT: t('आज ही डॉक्टर को दिखाएं', 'See a doctor today'),
    ROUTINE: t('डॉक्टर को दिखाएं (अपॉइंटमेंट लें)', 'Show this to a doctor (book a visit)'),
    NORMAL: t('सब मान सामान्य सीमा में हैं', 'All values are in the usual range'),
  } as Record<string, string>)[u] || u;

  const rf = result?.recommended_facility;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-5">
        {/* Upload */}
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2"><ScanLine className="text-teal-700" size={20} /> {t('अपनी रिपोर्ट अपलोड करें', 'Upload your report')}</h3>
            <p className="text-xs text-slate-500">
              {t('खून की जांच, स्कैन/ईसीजी रिपोर्ट या डॉक्टर का पर्चा। AI बताएगा कि किस डॉक्टर को दिखाएं, कितनी जल्दी, और अनुमानित समय व खर्च।',
                'Blood test, scan/ECG report or a doctor\'s prescription. The AI suggests which doctor to see, how soon, and an estimate of time and cost.')}
            </p>
          </div>
          <div className="text-[11px] rounded-lg p-2 border bg-slate-50 border-slate-200 text-slate-600">
            {visionAvailable
              ? t('फोटो, स्कैन और हाथ से लिखे पर्चे AI vision से पढ़े जाते हैं।', 'Photos, scans and handwritten prescriptions are read with AI vision.')
              : t('अभी डिजिटल PDF और टाइप किया टेक्स्ट पढ़ा जा सकता है। फोटो और हाथ से लिखे पर्चे पढ़ने के लिए AI vision कुंजी चाहिए।',
                'Digital PDFs and typed text can be read now. Photos and handwritten prescriptions need the AI vision key.')}
          </div>

          <div
            onClick={() => fileInput.current?.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={e => { e.preventDefault(); if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]); }}
            className="border-2 border-dashed border-teal-300 rounded-xl p-5 text-center cursor-pointer hover:bg-teal-50/50"
            role="button" tabIndex={0}
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') fileInput.current?.click(); }}
          >
            <Upload className="mx-auto text-teal-700" size={26} />
            <div className="text-sm font-semibold text-slate-800 mt-1">{file ? file.name : t('फाइल चुनें या यहां छोड़ें', 'Choose a file or drop it here')}</div>
            <div className="text-[11px] text-slate-500">PDF, JPG, PNG {t('या', 'or')} TXT • {t('अधिकतम 10 MB', 'max 10 MB')}</div>
            <input ref={fileInput} type="file" accept=".pdf,.txt,image/*" className="hidden" onChange={e => setFile(e.target.files?.[0] || null)} />
          </div>
          {file && <button type="button" onClick={() => setFile(null)} className="text-xs text-slate-500 underline">{t('फाइल हटाएं', 'Remove file')}</button>}

          {!file && (
            <label className="block space-y-1">
              <span className="text-xs font-semibold text-slate-700">{t('या रिपोर्ट का टेक्स्ट चिपकाएं', 'Or paste the report text')}</span>
              <textarea rows={4} value={pasted} onChange={e => setPasted(e.target.value)} placeholder={'Haemoglobin 9.2 g/dL\nFBS 168 mg/dL\nTSH 6.8 mIU/L'}
                className="w-full rounded-xl border border-slate-300 p-3 text-sm font-mono" />
            </label>
          )}
          <label className="block space-y-1">
            <span className="text-xs font-semibold text-slate-700">{t('आपके लक्षण (वैकल्पिक)', 'Your symptoms (optional)')}</span>
            <input value={symptoms} onChange={e => setSymptoms(e.target.value)} placeholder={t('जैसे: थकान, चक्कर', 'e.g. tiredness, dizziness')}
              className="w-full rounded-xl border border-slate-300 p-2.5 text-sm" />
          </label>
          {error && <div className="text-xs bg-rose-50 border border-rose-300 text-rose-900 rounded-xl p-3" role="alert">{error}</div>}
          <button onClick={analyse} disabled={busy} className="w-full bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-bold py-2.5 rounded-xl flex items-center justify-center gap-2">
            {busy ? <><Clock size={16} className="animate-spin" /> {t('रिपोर्ट पढ़ी जा रही है…', 'Reading the report…')}</> : <><ScanLine size={16} /> {t('रिपोर्ट जांचें', 'Analyse report')}</>}
          </button>
        </section>

        {/* Result */}
        {result && (
          <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4" aria-live="polite">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-base font-bold text-slate-900">{typeLabel(result.report_type)}{result.filename ? ` • ${result.filename}` : ''}</h3>
              <span className="text-[11px] text-slate-500">
                {result.read_method === 'ai_vision' ? t('AI vision से पढ़ा गया', 'Read with AI vision') : result.read_method === 'pdf_text' ? t('PDF से पढ़ा गया', 'Read from PDF') : t('टाइप किया टेक्स्ट', 'Typed text')}
              </span>
            </div>

            <div className={`border-l-4 rounded-xl p-3 ${URGENCY_STYLE[result.urgency] || ''}`}>
              <div className="font-bold flex items-center gap-2">
                {result.urgency === 'EMERGENCY' ? <AlertTriangle size={18} /> : result.urgency === 'NORMAL' ? <CheckCircle2 size={18} /> : <Clock size={18} />}
                {urgencyLabel(result.urgency)}
              </div>
              {result.urgency_reasons.length > 0 && <ul className="text-xs mt-1 list-disc ml-5">{result.urgency_reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>}
              {result.urgency === 'EMERGENCY' && <a href="tel:112" className="inline-flex items-center gap-1 mt-2 bg-red-600 text-white font-bold text-sm px-3 py-1.5 rounded-lg"><PhoneCall size={14} /> 112 / 108</a>}
            </div>

            {result.specialist && (
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 space-y-2">
                <div className="text-sm font-bold text-slate-900 flex items-center gap-2"><Stethoscope size={16} className="text-teal-700" /> {t('किस डॉक्टर को दिखाएं', 'Doctor to consult')}: {result.specialist.title}</div>
                <p className="text-xs text-slate-600">{result.specialist.why}</p>
                {rf && (
                  <div className="flex flex-wrap items-center justify-between gap-2 bg-white border border-slate-200 rounded-lg p-2 text-xs">
                    <div>
                      <div className="font-semibold">{rf.doctor_name} ({rf.specialty}) • {rf.facility_name}</div>
                      <div className="text-slate-500">{rf.distance_km} km (~{rf.travel_time_mins} min)</div>
                      {!rf.specialist_match && <div className="text-amber-700">{t('पास में यह विशेषज्ञ आज ड्यूटी पर नहीं है - ये डॉक्टर पहले देख सकते हैं और रेफ़र करेंगे।', 'No such specialist is on duty nearby today - this doctor can see you first and refer you.')}</div>}
                    </div>
                    {result.urgency !== 'EMERGENCY' && <button type="button" onClick={() => onBook(rf.facility_id)} className="bg-teal-700 text-white font-bold px-3 py-1.5 rounded-lg">{t('अपॉइंटमेंट बुक करें', 'Book appointment')}</button>}
                  </div>
                )}
              </div>
            )}

            {result.findings.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="text-left text-slate-500 border-b border-slate-200">
                    <th className="py-1.5 pr-2">{t('जांच', 'Test')}</th><th className="py-1.5 pr-2">{t('परिणाम', 'Result')}</th>
                    <th className="py-1.5 pr-2">{t('सामान्य सीमा', 'Usual range')}</th><th className="py-1.5">{t('स्थिति', 'Status')}</th>
                  </tr></thead>
                  <tbody>
                    {result.findings.map((f, i) => (
                      <tr key={i} className="border-b border-slate-100">
                        <td className="py-1.5 pr-2 font-semibold">{f.test}</td>
                        <td className="py-1.5 pr-2">{f.value} {f.unit}</td>
                        <td className="py-1.5 pr-2 text-slate-500">{f.range}</td>
                        <td className={`py-1.5 ${STATUS_STYLE[f.status] || ''}`}>{f.status.replace('_', ' ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {result.imaging && (
              <div className="text-xs bg-slate-50 border border-slate-200 rounded-xl p-3">
                <div className="font-bold">{result.imaging.study}</div>
                <div className="text-slate-700">{t('निष्कर्ष', 'Impression')}: {result.imaging.impression || t('रिपोर्ट में नहीं मिला', 'not found in the report')}</div>
              </div>
            )}

            {result.medicines.length > 0 && (
              <div className="space-y-1.5">
                <div className="text-xs font-bold text-slate-800 flex items-center gap-1"><Pill size={14} className="text-teal-700" /> {t('पर्चे की दवाएं', 'Medicines on the prescription')}</div>
                {result.medicines.map((m, i) => (
                  <div key={i} className="text-xs flex flex-wrap justify-between gap-2 bg-slate-50 border border-slate-200 rounded-lg p-2">
                    <span><span className="font-semibold">{m.name}</span> <span className="text-slate-500">({m.form})</span>{!m.recognised && <span className="text-amber-700"> • {t('नाम की पुष्टि करें', 'check this name')}</span>}</span>
                    <span className="text-slate-600">{m.schedule || ''}{m.duration_days ? ` • ${m.duration_days} ${t('दिन', 'days')}` : ''}</span>
                  </div>
                ))}
              </div>
            )}

            {result.next_steps.length > 0 && (
              <div>
                <div className="text-xs font-bold text-slate-800 mb-1">{t('अगले कदम', 'Next steps')}</div>
                <ul className="text-xs text-slate-700 list-disc ml-5 space-y-0.5">{result.next_steps.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}

            {result.estimates && (
              <div className="bg-sky-50 border border-sky-200 rounded-xl p-3 space-y-1.5 text-xs">
                <div className="font-bold text-sky-900">{t('अनुमान (भविष्यवाणी नहीं)', 'Estimates (not a prediction)')}</div>
                <div className="flex gap-2"><Clock size={14} className="text-sky-700 shrink-0 mt-0.5" /><span><b>{t('ठीक होने का समय', 'Recovery time')}:</b> {result.estimates.recovery}</span></div>
                {result.estimates.cost_private && <div className="flex gap-2"><IndianRupee size={14} className="text-sky-700 shrink-0 mt-0.5" /><span><b>{t('निजी अस्पताल में अनुमानित खर्च', 'Indicative private cost')}:</b> {result.estimates.cost_private}</span></div>}
                <div className="flex gap-2"><IndianRupee size={14} className="text-emerald-700 shrink-0 mt-0.5" /><span><b>{t('सरकारी अस्पताल', 'Government facility')}:</b> {result.estimates.cost_government}</span></div>
                <p className="text-[10px] text-sky-800">{result.estimates.notice}</p>
              </div>
            )}

            {result.symptom_triage && (
              <div className="text-xs bg-slate-50 border border-slate-200 rounded-xl p-2">
                <b>{t('आपके लक्षण', 'Your symptoms')}:</b> {result.symptom_triage.level} - {result.symptom_triage.advice}
              </div>
            )}

            <details className="text-xs">
              <summary className="cursor-pointer font-semibold text-slate-700 flex items-center gap-1"><FileText size={13} /> {t('AI ने क्या पढ़ा (जांच लें)', 'What the AI read (please check)')}</summary>
              <pre className="mt-2 whitespace-pre-wrap bg-slate-50 border border-slate-200 rounded-lg p-2 max-h-64 overflow-auto font-mono text-[11px]">{result.extracted_text}</pre>
            </details>
            <p className="text-[11px] text-slate-500">{result.disclaimer}</p>
          </section>
        )}
      </div>

      {/* History */}
      <aside className="space-y-4">
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 space-y-2">
          <h3 className="text-sm font-bold text-slate-900">{t('पिछली रिपोर्ट', 'Previous reports')}</h3>
          {history.length === 0 && <p className="text-xs text-slate-400">{t('अभी कोई रिपोर्ट नहीं', 'No reports yet')}</p>}
          {history.map(h => (
            <button key={h.id} onClick={() => openSaved(h.id)} className="w-full text-left text-xs border border-slate-200 rounded-lg p-2 hover:border-teal-500">
              <div className="flex justify-between gap-2"><span className="font-semibold">{h.filename || typeLabel(h.report_type)}</span><span className="text-slate-400">{new Date(h.created_at).toLocaleDateString()}</span></div>
              <div className="text-slate-600">{h.summary}</div>
            </button>
          ))}
        </section>
        {modelInfo && (
          <section className="bg-slate-50 rounded-2xl border border-slate-200 p-4 text-[11px] text-slate-600 space-y-1">
            <div className="font-bold text-slate-800">{t('यह कैसे काम करता है', 'How this works')}</div>
            <p>{t('मानों की सामान्य सीमा से तुलना होती है। असामान्य मान होने पर एक मॉडल सुझाता है कि किस विशेषज्ञ को दिखाएं', 'Values are checked against usual ranges. If something is abnormal, a model suggests the specialist')} ({t('प्रशिक्षण', 'trained on')} {modelInfo.dataset_size} {t('काल्पनिक रिपोर्ट', 'synthetic reports')}, {modelInfo.patterns} {t('पैटर्न', 'patterns')}, {t('सटीकता', 'accuracy')} {modelInfo.cv_accuracy_lab_values_only}%).</p>
            <p>{t('असली रिपोर्ट इससे कठिन होती हैं; डॉक्टर ही अंतिम निर्णय लेते हैं।', 'Real reports are harder than the training data; a doctor makes the final decision.')}</p>
          </section>
        )}
      </aside>
    </div>
  );
};
