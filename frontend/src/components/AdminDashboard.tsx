import { makeT } from '../i18n';
import React, { useState, useEffect, useRef } from 'react';
import { AdminMetrics, AuditEvent, AdminActivity, User, Lang } from '../types';
import { api } from '../services/api';
import {
  BarChart3, Users, Building2, AlertTriangle, CheckCircle2,
  Clock, ShieldAlert, Activity, Pill, RefreshCw, FileText, Calendar
} from 'lucide-react';

interface AdminDashboardProps {
  language: Lang;
  user: User;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ language, user }) => {
  const t = makeT(language);
  const [activity, setActivity] = useState<AdminActivity | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [continuityMsg, setContinuityMsg] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [adapters, setAdapters] = useState<any[]>([]);
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [isRetraining, setIsRetraining] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [m, audits, ad, act, info] = await Promise.all([
        api.getAdminMetrics(), api.getAuditEvents(100), api.getAdaptersStatus(), api.getAdminActivity(), api.getModelInfo()
      ]);
      setMetrics(m);
      setAuditEvents(audits);
      setAdapters(ad.adapters || []);
      setActivity(act);
      setModelInfo(info);
      setLoadError(null);
    } catch (err: any) {
      setLoadError(err.message);
    }
  };

  const handleRetrain = async () => {
    setIsRetraining(true);
    try {
      const data = await api.retrainModel();
      alert('Care-pathway model retrained. Test accuracy: ' + data.summary.test_accuracy + '%');
      loadData();
    } catch (err: any) {
      alert('Retrain failed: ' + err.message);
    } finally {
      setIsRetraining(false);
    }
  };

  const runContinuity = async () => {
    try {
      const r = await api.runContinuityEngine();
      setContinuityMsg(`Continuity check done: ${r.newly_overdue} newly overdue, ${r.tasks_created} ASHA tasks created, ${r.reminders_sent} reminders sent.`);
      loadData();
    } catch (err: any) {
      setContinuityMsg(err.message);
    }
  };

  const demoRef = useRef<(detail: any) => void>(() => {});
  demoRef.current = (detail: any) => {
    if (detail.action === 'continuity') runContinuity();
  };
  useEffect(() => {
    const onDemo = (e: Event) => demoRef.current((e as CustomEvent).detail);
    window.addEventListener('swasthyasetu-demo', onDemo);
    return () => window.removeEventListener('swasthyasetu-demo', onDemo);
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900">
              {t('जिला सार्वजनिक स्वास्थ्य नियंत्रण कक्ष', 'District Public Health Operations Center')}
            </h2>
            <span className="bg-amber-100 text-amber-900 text-xs px-2.5 py-0.5 rounded-full font-bold">
              Demo data
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {user.full_name} • Appointments, continuity of care and platform activity
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={runContinuity}
            className="flex items-center gap-1.5 text-xs bg-teal-700 hover:bg-teal-800 text-white px-3 py-1.5 rounded-xl transition font-medium"
          >
            <Clock size={13} />
            <span>Run missed-care check</span>
          </button>
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl transition font-medium"
          >
            <RefreshCw size={13} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {loadError && <div className="text-xs bg-rose-50 border border-rose-300 text-rose-900 rounded-xl p-3">{loadError}</div>}
      {continuityMsg && <div className="text-xs bg-teal-50 border border-teal-200 text-teal-900 rounded-xl p-3">{continuityMsg}</div>}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Users size={13} className="text-teal-700" />
            Total Patients
          </div>
          <div className="text-2xl font-black text-slate-900">
            {metrics?.total_patients ?? '–'}
          </div>
          <p className="text-[10px] text-teal-700 font-semibold">{activity?.registrations_last_24h ?? 0} registered in last 24h</p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Building2 size={13} className="text-teal-700" />
            Doctors & Hub Hospitals
          </div>
          <div className="text-2xl font-black text-slate-900">
            {metrics?.total_doctors ?? '–'} / {metrics?.total_facilities ?? '–'}
          </div>
          <p className="text-[10px] text-slate-500">Doctors / facilities</p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Activity size={13} className="text-teal-700" />
            ASHA Health Workers
          </div>
          <div className="text-2xl font-black text-slate-900">
            {metrics?.total_asha_workers ?? '–'}
          </div>
          <p className="text-[10px] text-teal-700 font-semibold">{metrics?.open_asha_tasks ?? 0} open / {metrics?.resolved_asha_tasks ?? 0} resolved tasks</p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="text-[11px] font-bold text-purple-700 uppercase flex items-center gap-1">
            <ShieldAlert size={13} />
            Emergency alerts
          </div>
          <div className="text-2xl font-black text-purple-900">
            {metrics?.critical_emergency_alerts_count ?? 0}
          </div>
          <p className="text-[10px] text-purple-700 font-medium">{activity?.access_denials_total ?? 0} access denials audited</p>
        </div>
      </div>

      {/* IMPACT */}
      <div className="bg-gradient-to-r from-teal-800 to-teal-900 text-white rounded-2xl p-5 shadow-sm space-y-3">
        <div>
          <h3 className="text-base font-bold">{t('इस डेमो में प्रभाव', 'Impact in this demo')}</h3>
          <p className="text-xs text-teal-100">{t('हर संख्या प्लेटफ़ॉर्म पर दर्ज वास्तविक घटनाओं से गिनी गई है।', 'Every number is counted from events recorded on the platform.')}</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: t('छूटे फॉलो-अप फिर से जुड़े', 'Missed follow-ups recovered'), value: activity?.impact.missed_follow_ups_recovered, note: t('आशा घर भ्रमण से', 'via ASHA home visits') },
            { label: t('आपात स्थिति में 112 की सलाह', 'Emergencies sent to 112'), value: activity?.impact.emergencies_directed_to_112, note: t('LLM से पहले, तुरंत', 'instantly, before any LLM') },
            { label: t('बेकार यात्राएं टलीं', 'Wasted trips avoided'), value: activity?.impact.wasted_trips_avoided, note: t('जांच/दवा न होने की पहले से जानकारी', 'test or medicine unavailable, known in advance') },
            { label: t('SMS भेजे गए', 'SMS sent'), value: activity?.impact.sms_reminders_sent, note: t('पुष्टि और रिमाइंडर', 'confirmations & reminders') },
            { label: t('सहमति वापसी का पालन', 'Consent withdrawals honoured'), value: activity?.impact.consent_withdrawals_honoured, note: t('मरीज़ का नियंत्रण', 'patient in control') },
          ].map(k => (
            <div key={k.label} className="bg-white/10 rounded-xl p-3 border border-white/10">
              <div className="text-2xl font-black">{k.value ?? '–'}</div>
              <div className="text-[11px] font-bold text-teal-50">{k.label}</div>
              <div className="text-[10px] text-teal-200">{k.note}</div>
            </div>
          ))}
        </div>
      </div>

      {/* APPOINTMENT MONITORING */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total appointments', value: metrics?.total_appointments },
          { label: 'Pending / in queue', value: metrics?.pending_appointments },
          { label: 'Completed', value: metrics?.completed_appointments },
          { label: 'Overdue follow-ups', value: metrics?.overdue_followups_count },
          { label: 'Diagnostic orders', value: metrics?.diagnostic_tests_ordered },
          { label: 'Stock alerts (low/out)', value: metrics?.medicine_stock_alerts_count },
          { label: 'Logins (24h)', value: activity?.logins_last_24h },
          { label: 'Facility data fresh (<24h)', value: metrics ? `${metrics.data_freshness_pct}%` : undefined },
        ].map(k => (
          <div key={k.label} className="bg-white p-3 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-[11px] font-bold text-slate-500 uppercase">{k.label}</div>
            <div className="text-xl font-black text-slate-900">{k.value ?? '–'}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-3">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2"><Calendar className="text-teal-700" size={18} /> Recent appointments</h3>
          <div className="overflow-x-auto max-h-[360px] overflow-y-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="py-1.5 pr-2">Code</th><th className="py-1.5 pr-2">Patient</th><th className="py-1.5 pr-2">Facility / doctor</th>
                  <th className="py-1.5 pr-2">When</th><th className="py-1.5">Status</th>
                </tr>
              </thead>
              <tbody>
                {(activity?.recent_appointments || []).map(a => (
                  <tr key={a.id} className="border-b border-slate-100">
                    <td className="py-1.5 pr-2 font-mono">{a.appointment_code}</td>
                    <td className="py-1.5 pr-2 font-semibold">{a.patient_name}</td>
                    <td className="py-1.5 pr-2">{a.facility_name}<div className="text-slate-500">{a.doctor_name}</div></td>
                    <td className="py-1.5 pr-2">{a.scheduled_date} {a.scheduled_time}</td>
                    <td className="py-1.5">{a.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-4 text-xs">
          <div>
            <h3 className="text-sm font-bold text-slate-900 mb-2">Appointments by status</h3>
            {Object.entries(activity?.appointments_by_status || {}).map(([k, v]) => (
              <div key={k} className="flex justify-between border-b border-slate-100 py-1"><span>{k}</span><strong>{v}</strong></div>
            ))}
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 mb-2">Busiest facilities</h3>
            {(activity?.appointments_by_facility || []).map(f => (
              <div key={f.facility} className="flex justify-between gap-2 border-b border-slate-100 py-1"><span className="truncate">{f.facility}</span><strong>{f.count}</strong></div>
            ))}
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 mb-2">AI symptom checks by triage level</h3>
            {Object.entries(activity?.intakes_by_triage_level || {}).map(([k, v]) => (
              <div key={k} className="flex justify-between border-b border-slate-100 py-1"><span>{k}</span><strong>{v}</strong></div>
            ))}
          </div>
        </div>
      </div>

      {/* AI MODEL TRAINING & DATASET SHOWCASE */}
      <div className="bg-gradient-to-br from-slate-900 via-teal-950 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-teal-800 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-teal-800/80 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-emerald-500 text-slate-950 text-[10px] font-black uppercase px-2 py-0.5 rounded tracking-wide">
                MODEL TRAINED
              </span>
              <h3 className="text-base font-bold text-white">
                Care-pathway classifier (trained on {modelInfo?.dataset_size ?? 1000} fictional records)
              </h3>
            </div>
            <p className="text-xs text-teal-200 mt-0.5">
              Supporting analytics only. The patient-facing assistant uses an existing LLM with approved references - it is not trained here.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs bg-teal-900/80 border border-teal-700 text-teal-300 font-bold px-3 py-1 rounded-xl">
              Test accuracy: {modelInfo?.test_accuracy ?? '–'}%
            </span>
            <button
              onClick={handleRetrain}
              disabled={isRetraining}
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold px-3 py-1.5 rounded-xl transition flex items-center gap-1.5 shadow"
            >
              <RefreshCw size={13} className={isRetraining ? 'animate-spin' : ''} />
              <span>{isRetraining ? 'Training...' : 'Retrain Model'}</span>
            </button>
          </div>
        </div>

        {/* 4 Care Pathways Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-white/10 p-3 rounded-xl border border-white/10 space-y-1">
            <span className="text-[10px] uppercase font-bold text-teal-300">Care Pathway 1</span>
            <div className="font-bold text-white">High-Risk Maternal Care</div>
            <p className="text-[11px] text-slate-300">Hb & Weight tracking, gestational alert protocol.</p>
          </div>
          <div className="bg-white/10 p-3 rounded-xl border border-white/10 space-y-1">
            <span className="text-[10px] uppercase font-bold text-teal-300">Care Pathway 2</span>
            <div className="font-bold text-white">Chronic Disease Mgmt</div>
            <p className="text-[11px] text-slate-300">Hypertension, Diabetes, and Heart Rate monitoring.</p>
          </div>
          <div className="bg-white/10 p-3 rounded-xl border border-white/10 space-y-1">
            <span className="text-[10px] uppercase font-bold text-teal-300">Care Pathway 3</span>
            <div className="font-bold text-white">Post-Op Connected Care</div>
            <p className="text-[11px] text-slate-300">SpO2 and Body Temperature connected sensor protocol.</p>
          </div>
          <div className="bg-white/10 p-3 rounded-xl border border-white/10 space-y-1">
            <span className="text-[10px] uppercase font-bold text-teal-300">Care Pathway 4</span>
            <div className="font-bold text-white">Daily SMS / Weekly Visit</div>
            <p className="text-[11px] text-slate-300">ASHA field visit reminders & mobile SMS dispatch.</p>
          </div>
        </div>

        {/* 10 Jila Prashashan Authorities Details */}
        <div className="bg-black/30 p-3.5 rounded-xl border border-teal-800/60 space-y-2">
          <div className="text-xs font-bold text-amber-300 uppercase tracking-wide">
            10 Jila Prashashan (District Administration) Authorities with Data Checking Access:
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-[11px] text-slate-200">
            <div>• DHO Lucknow Central</div>
            <div>• DHO Lucknow Rural</div>
            <div>• CMO Mohanlalganj</div>
            <div>• DHO Malihabad</div>
            <div>• DHO Bakshi Ka Talab</div>
            <div>• DHO Kakori & Chinhat</div>
            <div>• DHO Gosainganj</div>
            <div>• DHO Itaunja</div>
            <div>• DHO Amethi Rural</div>
            <div>• State Quality Inspector</div>
          </div>
        </div>
      </div>

      {/* 2 Columns: Audit Events Viewer & Integrations Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Audit Events Viewer (Left 2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileText className="text-teal-700" size={18} />
                {t('सुरक्षा एवं क्लिनिकल ऑडिट ट्रेल', 'Security, Access & Clinical Audit Trail')}
              </h3>
              <p className="text-xs text-slate-500">
                Immutable chronological log of patient record accesses, consultations, and permission checks.
              </p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-700 font-mono px-2.5 py-0.5 rounded">
              Live Stream
            </span>
          </div>

          <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
            {auditEvents.map((ev) => {
              const isDenied = ev.outcome === 'DENIED';
              return (
                <div
                  key={ev.id}
                  className={`p-3 rounded-xl border text-xs space-y-1 ${
                    isDenied ? 'bg-rose-50/60 border-rose-300' : 'bg-slate-50 border-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 flex items-center gap-1.5">
                      {isDenied ? <ShieldAlert size={14} className="text-rose-600" /> : <CheckCircle2 size={14} className="text-teal-700" />}
                      {ev.action}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {new Date(ev.created_at).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-600 flex items-center gap-2">
                    <span>Actor: <strong className="text-slate-800">{ev.user_name} ({ev.role})</strong></span>
                    <span>•</span>
                    <span>Resource: {ev.resource_type} ({ev.resource_id || 'N/A'})</span>
                    <span>•</span>
                    <span className={`font-bold ${isDenied ? 'text-rose-700' : 'text-emerald-700'}`}>
                      {ev.outcome}
                    </span>
                  </div>

                  {ev.details_json && ev.details_json !== '{}' && (
                    <div className="text-[10px] text-slate-500 font-mono bg-white/70 p-1.5 rounded border border-slate-200 truncate">
                      {ev.details_json}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Integration Adapters Status (Right col) */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
          <div className="border-b border-slate-200 pb-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <RefreshCw className="text-teal-700" size={18} />
              {t('एकीकरण एडाप्टर स्थिति', 'Ecosystem Adapters')}
            </h3>
            <p className="text-xs text-slate-500">
              Clear distinction between genuinely integrated services and simulated mock adapters.
            </p>
          </div>

          <div className="space-y-3">
            {adapters.map((ad, idx) => (
              <div key={idx} className="p-3 rounded-xl border border-slate-200 bg-slate-50 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">{ad.name}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    ad.status === 'ACTIVE_DIRECT'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-amber-100 text-amber-900 border border-amber-300'
                  }`}>
                    {ad.status}
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  {ad.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
