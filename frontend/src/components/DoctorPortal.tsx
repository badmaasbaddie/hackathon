import React, { useState, useEffect } from 'react';
import { Appointment, PatientRecord, User, FacilityReadiness } from '../types';
import { api } from '../services/api';
import { Clock, CheckCircle2, Pill, Activity, Calendar, ShieldCheck, Plus, Trash2, History } from 'lucide-react';

interface DoctorPortalProps {
  language: 'hi' | 'en';
  user: User;
}

interface RxRow {
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration_days: number;
  instructions: string;
}

const MEDICINES = ['Paracetamol 500mg', 'Metformin 500mg', 'Amlodipine 5mg', 'Oral Rehydration Salts (ORS)', 'Amoxicillin 500mg', 'Telmisartan 40mg'];
const emptyRx = (): RxRow => ({ medicine_name: 'Paracetamol 500mg', dosage: '1 tablet', frequency: 'Twice daily after food', duration_days: 5, instructions: '' });

export const DoctorPortal: React.FC<DoctorPortalProps> = ({ language, user }) => {
  const hi = language === 'hi';
  const t = (h: string, e: string) => (hi ? h : e);

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [selectedApt, setSelectedApt] = useState<Appointment | null>(null);
  const [record, setRecord] = useState<PatientRecord | null>(null);
  const [recordError, setRecordError] = useState<string | null>(null);
  const [facility, setFacility] = useState<FacilityReadiness | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);

  const [chiefComplaints, setChiefComplaints] = useState('');
  const [clinicalNotes, setClinicalNotes] = useState('');
  const [diagnosis, setDiagnosis] = useState('');
  const [vitalBp, setVitalBp] = useState('120/80');
  const [vitalPulse, setVitalPulse] = useState(76);
  const [vitalTemp, setVitalTemp] = useState(98.4);
  const [vitalSpo2, setVitalSpo2] = useState(98);
  const [riskFlag, setRiskFlag] = useState('NORMAL');
  const [rxRows, setRxRows] = useState<RxRow[]>([emptyRx()]);
  const [orderDiagnostics, setOrderDiagnostics] = useState<string[]>([]);
  const [followUpDays, setFollowUpDays] = useState(7);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const resetForm = (apt: Appointment | null) => {
    setChiefComplaints(apt?.reason || '');
    setClinicalNotes('');
    setDiagnosis('');
    setVitalBp('120/80'); setVitalPulse(76); setVitalTemp(98.4); setVitalSpo2(98);
    setRiskFlag('NORMAL');
    setRxRows([emptyRx()]);
    setOrderDiagnostics([]);
    setFollowUpDays(7);
  };

  const loadPatient = async (apt: Appointment) => {
    setRecord(null);
    setRecordError(null);
    try {
      setRecord(await api.getPatientRecord(apt.patient_id));
    } catch (err: any) {
      setRecordError(err.message);
    }
  };

  const selectAppointment = (apt: Appointment) => {
    setSelectedApt(apt);
    setMessage(null);
    resetForm(apt);
    loadPatient(apt);
  };

  const loadData = async (keepSelection = true) => {
    const [apts, facs] = await Promise.all([api.getAppointments(), api.getFacilities()]);
    setAppointments(apts);
    setFacility(facs.find(f => f.id === user.facility_id) || null);
    const open = apts.filter(a => a.status === 'BOOKED' || a.status === 'IN_QUEUE');
    if (!keepSelection || !selectedApt) {
      const first = open[open.length - 1] || apts[0];
      if (first) selectAppointment(first);
    }
  };

  useEffect(() => {
    loadData(false).catch(err => setRecordError(err.message));
  }, []);

  const handleSubmitEncounter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApt) return;
    setIsSubmitting(true);
    setMessage(null);
    try {
      await api.createEncounter({
        appointment_id: selectedApt.id,
        patient_id: selectedApt.patient_id,
        chief_complaints: chiefComplaints || 'Not recorded',
        clinical_notes: clinicalNotes || 'Not recorded',
        diagnosis,
        vital_bp: vitalBp, vital_pulse: vitalPulse, vital_temp: vitalTemp, vital_spo2: vitalSpo2,
        clinician_risk_flag: riskFlag,
        prescriptions: rxRows.filter(r => r.medicine_name.trim()).map(r => ({ ...r, instructions: r.instructions || undefined })),
        diagnostic_test_names: orderDiagnostics,
        follow_up_days: followUpDays,
        follow_up_instructions: `Review in ${followUpDays} days${orderDiagnostics.length ? ' with test reports' : ''}.`
      });
      setMessage({ ok: true, text: t('परामर्श, पर्चा और फॉलो-अप मरीज़ के रिकॉर्ड में सहेजे गए।', 'Consultation, prescription and follow-up saved to the patient record. An SMS reminder has been scheduled.') });
      await loadData();
      setSelectedApt({ ...selectedApt, status: 'COMPLETED' });
      await loadPatient(selectedApt);
    } catch (err: any) {
      setMessage({ ok: false, text: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const markNoShow = async () => {
    if (!selectedApt) return;
    try {
      const updated = await api.setAppointmentStatus(selectedApt.id, 'NO_SHOW');
      setSelectedApt(updated);
      await loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const stockOf = (med: string) => facility?.medicine_stock_summary[med.split(' ')[0]];
  const tests = [...(facility?.diagnostic_tests_available || []), ...(facility?.diagnostic_tests_missing || [])];
  const visibleApts = appointments.filter(a => showCompleted || a.status === 'BOOKED' || a.status === 'IN_QUEUE');
  const patient = record?.patient;
  const isOpen = selectedApt && (selectedApt.status === 'BOOKED' || selectedApt.status === 'IN_QUEUE');

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-xl border border-teal-200">
            {user.full_name.replace('Dr. ', '').charAt(0)}
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">{user.full_name}</h2>
            <p className="text-xs text-slate-500 mt-0.5">{facility?.name} • {facility?.operating_hours}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-600">
          <ShieldCheck className="text-teal-700" size={16} />
          <span>{t('केवल आपके मरीज़ों का रिकॉर्ड दिखता है; हर पहुंच ऑडिट होती है', 'You only see patients in your care; every access is audited')}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Queue */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-4 h-fit">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Clock className="text-teal-700" size={18} /> {t('ओपीडी कतार', 'OPD queue')}
            </h3>
            <label className="text-[11px] text-slate-600 flex items-center gap-1">
              <input type="checkbox" checked={showCompleted} onChange={e => setShowCompleted(e.target.checked)} /> {t('सभी', 'Show all')}
            </label>
          </div>
          <div className="space-y-2.5 max-h-[560px] overflow-y-auto pr-1">
            {visibleApts.length === 0 && <p className="text-xs text-slate-400">{t('कतार खाली है', 'No patients waiting')}</p>}
            {visibleApts.map(apt => (
              <button key={apt.id} onClick={() => selectAppointment(apt)}
                className={`w-full text-left p-3 rounded-xl border text-xs transition space-y-1 ${selectedApt?.id === apt.id ? 'border-teal-600 bg-teal-50/60' : 'border-slate-200 hover:border-slate-300'}`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">{apt.patient_name}</span>
                  <span className="bg-teal-700 text-white font-mono font-bold text-[10px] px-2 py-0.5 rounded">{apt.queue_token}</span>
                </div>
                <p className="text-[11px] text-slate-500">{apt.reason || 'General consultation'}</p>
                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span>{apt.scheduled_date} ({apt.scheduled_time}) • {apt.consultation_type}</span>
                  <span className={`font-semibold ${apt.status === 'COMPLETED' ? 'text-emerald-700' : apt.status === 'BOOKED' ? 'text-amber-700' : 'text-slate-500'}`}>{apt.status}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Workspace */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5">
          {!selectedApt && <p className="text-sm text-slate-500">{t('कतार से मरीज़ चुनें', 'Select a patient from the queue')}</p>}
          {recordError && <div className="text-xs bg-rose-50 border border-rose-300 text-rose-900 rounded-lg p-3">{recordError}</div>}

          {patient && (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{patient.name} ({patient.age}y / {patient.gender})</h3>
                  <p className="text-xs text-slate-500 font-mono">ABHA {patient.abha_id} • {patient.village} • {t('ब्लड', 'Blood')} {patient.blood_group}</p>
                  <p className="text-xs text-slate-600 mt-0.5">{t('पुरानी बीमारी', 'Known conditions')}: <strong>{patient.chronic_conditions}</strong></p>
                </div>
                {isOpen && (
                  <button onClick={markNoShow} className="text-xs text-slate-600 border border-slate-300 rounded-lg px-2.5 py-1 hover:bg-slate-50">
                    {t('नहीं आए', 'Mark no-show')}
                  </button>
                )}
              </div>

              {record?.latest_intake ? (
                <div className={`border rounded-xl p-3.5 space-y-1 text-xs ${record.latest_intake.triage_level === 'EMERGENCY' ? 'bg-red-50 border-red-300' : 'bg-teal-50/80 border-teal-200'}`}>
                  <div className="font-bold text-teal-900 flex items-center gap-1.5">
                    <Activity size={14} /> {t('एआई सहायक इनटेक सारांश', 'AI assistant intake summary')} • {record.latest_intake.triage_level} • {new Date(record.latest_intake.created_at).toLocaleString()}
                  </div>
                  <p className="text-slate-700 font-mono text-[11px] bg-white/80 p-2 rounded border border-teal-100">{record.latest_intake.ai_summary_for_doctor}</p>
                  <p className="text-[11px] text-slate-500">{t('मरीज़ के शब्द', "Patient's words")}: “{record.latest_intake.raw_input}”</p>
                </div>
              ) : (
                <p className="text-xs text-slate-400">{t('कोई एआई इनटेक नहीं', 'No AI intake on record for this patient')}</p>
              )}

              {record && record.encounters.length > 0 && (
                <details className="text-xs border border-slate-200 rounded-xl p-3">
                  <summary className="font-bold text-slate-800 cursor-pointer flex items-center gap-1.5"><History size={14} /> {t('पिछला इतिहास', 'Previous consultations')} ({record.encounters.length})</summary>
                  <div className="mt-2 space-y-2">
                    {record.encounters.slice(0, 5).map(e => (
                      <div key={e.id} className="bg-slate-50 rounded p-2">
                        <div className="font-semibold">{new Date(e.encounter_date).toLocaleDateString()} • {e.diagnosis} • {e.doctor_name}</div>
                        <div className="text-slate-600">BP {e.vital_bp}, SpO2 {e.vital_spo2}% • {e.prescriptions.flatMap(p => p.items.map(i => i.medicine_name)).join(', ') || 'No medicines'}</div>
                      </div>
                    ))}
                  </div>
                </details>
              )}

              {message && (
                <div className={`text-xs rounded-lg p-3 border ${message.ok ? 'bg-emerald-50 border-emerald-300 text-emerald-900' : 'bg-rose-50 border-rose-300 text-rose-900'}`}>{message.text}</div>
              )}

              {isOpen ? (
                <form onSubmit={handleSubmitEncounter} className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
                    <label><span className="text-slate-500 font-medium">BP</span>
                      <input value={vitalBp} onChange={e => setVitalBp(e.target.value)} pattern="\d{2,3}/\d{2,3}" title="e.g. 120/80" className="w-full font-mono font-bold bg-white border border-slate-300 rounded px-2 py-1 mt-0.5" /></label>
                    <label><span className="text-slate-500 font-medium">{t('नाड़ी', 'Pulse')} (bpm)</span>
                      <input type="number" min={20} max={250} value={vitalPulse} onChange={e => setVitalPulse(Number(e.target.value))} className="w-full font-mono font-bold bg-white border border-slate-300 rounded px-2 py-1 mt-0.5" /></label>
                    <label><span className="text-slate-500 font-medium">{t('तापमान', 'Temp')} (°F)</span>
                      <input type="number" step="0.1" min={90} max={110} value={vitalTemp} onChange={e => setVitalTemp(Number(e.target.value))} className="w-full font-mono font-bold bg-white border border-slate-300 rounded px-2 py-1 mt-0.5" /></label>
                    <label><span className="text-slate-500 font-medium">SpO2 (%)</span>
                      <input type="number" min={50} max={100} value={vitalSpo2} onChange={e => setVitalSpo2(Number(e.target.value))} className="w-full font-mono font-bold bg-white border border-slate-300 rounded px-2 py-1 mt-0.5" /></label>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <label className="space-y-1"><span className="font-bold text-slate-700">{t('मुख्य शिकायत', 'Chief complaints')}</span>
                      <input value={chiefComplaints} onChange={e => setChiefComplaints(e.target.value)} className="w-full p-2.5 border border-slate-300 rounded-xl" /></label>
                    <label className="space-y-1"><span className="font-bold text-slate-700">{t('निदान', 'Diagnosis / impression')} *</span>
                      <input value={diagnosis} onChange={e => setDiagnosis(e.target.value)} required className="w-full p-2.5 border border-slate-300 rounded-xl" /></label>
                    <label className="space-y-1 md:col-span-2"><span className="font-bold text-slate-700">{t('जांच एवं नोट्स', 'Examination & notes')}</span>
                      <textarea rows={2} value={clinicalNotes} onChange={e => setClinicalNotes(e.target.value)} className="w-full p-2.5 border border-slate-300 rounded-xl" /></label>
                    <label className="space-y-1"><span className="font-bold text-slate-700">{t('जोखिम स्तर', 'Clinician risk flag')}</span>
                      <select value={riskFlag} onChange={e => setRiskFlag(e.target.value)} className="w-full p-2.5 border border-slate-300 rounded-xl bg-white">
                        <option value="NORMAL">Normal / low risk</option>
                        <option value="MODERATE_RISK">Moderate risk</option>
                        <option value="HIGH_RISK">High risk</option>
                      </select></label>
                  </div>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5"><Pill size={14} className="text-teal-700" /> {t('डिजिटल पर्चा', 'Digital prescription')}</span>
                      <button type="button" onClick={() => setRxRows([...rxRows, emptyRx()])} className="text-xs text-teal-800 font-semibold flex items-center gap-1"><Plus size={13} /> {t('दवा जोड़ें', 'Add medicine')}</button>
                    </div>
                    {rxRows.map((row, idx) => {
                      const stock = stockOf(row.medicine_name);
                      const update = (patch: Partial<RxRow>) => setRxRows(rxRows.map((r, i) => i === idx ? { ...r, ...patch } : r));
                      return (
                        <div key={idx} className="grid grid-cols-2 md:grid-cols-12 gap-2 text-xs items-center">
                          <select value={row.medicine_name} onChange={e => update({ medicine_name: e.target.value })} className="md:col-span-4 p-2 border border-slate-300 rounded-lg bg-white">
                            {MEDICINES.map(m => <option key={m}>{m}</option>)}
                          </select>
                          <input value={row.dosage} onChange={e => update({ dosage: e.target.value })} className="md:col-span-2 p-2 border border-slate-300 rounded-lg" aria-label="Dosage" />
                          <input value={row.frequency} onChange={e => update({ frequency: e.target.value })} className="md:col-span-3 p-2 border border-slate-300 rounded-lg" aria-label="Frequency" />
                          <input type="number" min={1} max={365} value={row.duration_days} onChange={e => update({ duration_days: Number(e.target.value) })} className="md:col-span-1 p-2 border border-slate-300 rounded-lg" aria-label="Days" />
                          <span className={`md:col-span-1 text-[10px] font-bold ${stock === 'IN_STOCK' ? 'text-emerald-700' : stock === 'LOW_STOCK' ? 'text-amber-700' : stock === 'OUT_OF_STOCK' ? 'text-rose-700' : 'text-slate-400'}`}>
                            {stock === 'IN_STOCK' ? 'In stock' : stock === 'LOW_STOCK' ? 'Low' : stock === 'OUT_OF_STOCK' ? 'OUT' : 'Not tracked'}
                          </span>
                          <button type="button" onClick={() => setRxRows(rxRows.filter((_, i) => i !== idx))} aria-label="Remove medicine" className="md:col-span-1 text-slate-400 hover:text-rose-600"><Trash2 size={14} /></button>
                        </div>
                      );
                    })}
                    {rxRows.some(r => stockOf(r.medicine_name) === 'OUT_OF_STOCK') && (
                      <p className="text-[11px] text-rose-700 font-semibold">
                        ⚠ {t('कुछ दवाएं इस केंद्र पर उपलब्ध नहीं हैं; मरीज़ को स्टॉक वाले केंद्र की जानकारी दें।', 'Some medicines are out of stock at this facility; the patient will see which facilities have stock. The prescription is not changed automatically.')}
                      </p>
                    )}
                  </div>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                    <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5"><Activity size={14} className="text-teal-700" /> {t('जांच का आदेश', 'Order diagnostics')}</span>
                    <div className="flex flex-wrap gap-2 text-xs">
                      {tests.map(test => {
                        const checked = orderDiagnostics.includes(test);
                        const unavailable = facility?.diagnostic_tests_missing.includes(test);
                        return (
                          <button key={test} type="button" aria-pressed={checked}
                            onClick={() => setOrderDiagnostics(checked ? orderDiagnostics.filter(x => x !== test) : [...orderDiagnostics, test])}
                            className={`px-3 py-1.5 rounded-lg border font-medium flex items-center gap-1.5 ${checked ? 'bg-teal-700 text-white border-teal-700' : 'bg-white text-slate-700 border-slate-300'}`}>
                            {checked ? '✓' : '+'} {test}
                            {unavailable && <span className="text-[9px] bg-rose-100 text-rose-800 px-1 rounded font-bold">{t('रेफ़रल', 'Referral')}</span>}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-3 bg-teal-50/60 p-3 rounded-xl border border-teal-200 text-xs">
                    <label className="flex items-center gap-2">
                      <Calendar size={15} className="text-teal-700" />
                      <span className="font-bold text-teal-950">{t('फॉलो-अप', 'Follow-up')}:</span>
                      <select value={followUpDays} onChange={e => setFollowUpDays(Number(e.target.value))} className="p-1 border border-teal-300 rounded bg-white font-semibold">
                        <option value={0}>{t('ज़रूरत नहीं', 'Not needed')}</option>
                        <option value={3}>3 {t('दिन', 'days')}</option>
                        <option value={7}>7 {t('दिन', 'days')}</option>
                        <option value={14}>14 {t('दिन', 'days')}</option>
                        <option value={30}>30 {t('दिन', 'days')}</option>
                      </select>
                    </label>
                    <span className="text-[11px] text-teal-800">{t('छूटे फॉलो-अप पर आशा कार्यकर्ता को कार्य मिलता है', 'A missed follow-up automatically creates an ASHA home-visit task')}</span>
                  </div>

                  <div className="flex justify-end">
                    <button type="submit" disabled={isSubmitting} className="bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-bold text-sm px-6 py-2.5 rounded-xl flex items-center gap-2">
                      <CheckCircle2 size={16} /> {isSubmitting ? t('सहेजा जा रहा है…', 'Saving…') : t('परामर्श पूरा करें', 'Complete consultation')}
                    </button>
                  </div>
                </form>
              ) : (
                selectedApt && <p className="text-xs text-slate-500">{t('यह अपॉइंटमेंट', 'This appointment is')} {selectedApt.status}.</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
