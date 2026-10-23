import { makeT, speechLang } from '../i18n';
import React, { useState, useEffect, useRef } from 'react';
import {
  Patient, FacilityReadiness, Appointment, CareTimelineEvent, User,
  ChatTurn, ChatResponse, PatientRecord, Lang } from '../types';
import { api } from '../services/api';
import { localDate } from '../utils/date';
import {
  AlertTriangle, PhoneCall, CheckCircle2, Clock, MapPin, Shield, Mic, Send,
  Activity, Info, Pill, FileText, Calendar, Bell, Users, Stethoscope, XCircle, Volume2, VolumeX
} from 'lucide-react';
import { FacilityMap } from './FacilityMap';
import { PrivacyPanel } from './PrivacyPanel';
import { speak, stopSpeaking, canSpeak } from '../utils/speech';

interface PatientPortalProps {
  language: Lang;
  user: User;
  onRegister: () => void;
}

export type PatientTab = 'ASSISTANT' | 'FACILITIES' | 'RECORDS' | 'TIMELINE' | 'FAMILY' | 'PRIVACY';
type Tab = PatientTab;

interface AssistantMessage extends ChatTurn {
  meta?: ChatResponse;
}

const TIME_SLOTS = ['09:00 AM', '09:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM', '01:00 PM', '01:30 PM'];

const statusColor = (s: string) =>
  s === 'COMPLETED' || s === 'SENT' || s === 'ORDERED' ? 'bg-emerald-100 text-emerald-800'
    : s === 'CANCELLED' || s === 'OVERDUE' || s === 'UNAVAILABLE' || s === 'OUT_OF_STOCK' ? 'bg-rose-100 text-rose-800'
      : 'bg-amber-100 text-amber-900';

export const PatientPortal: React.FC<PatientPortalProps> = ({ language, user, onRegister }) => {
  const t = makeT(language);

  const [patient, setPatient] = useState<Patient | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('ASSISTANT');

  // Assistant
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [readAloud, setReadAloud] = useState<boolean>(() => {
    try { return localStorage.getItem('swasthyasetu_read_aloud') === 'true'; } catch { return false; }
  });
  const chatEndRef = useRef<HTMLDivElement>(null);
  const lastMeta = [...messages].reverse().find(m => m.meta)?.meta;

  // Facilities & booking
  const [facilities, setFacilities] = useState<FacilityReadiness[]>([]);
  const [showAllDistricts, setShowAllDistricts] = useState(false);
  const [bookFacilityId, setBookFacilityId] = useState<number | null>(null);
  const [bookDoctorId, setBookDoctorId] = useState<number | null>(null);
  const [bookDate, setBookDate] = useState(localDate(1));
  const [bookTime, setBookTime] = useState('10:30 AM');
  const [bookType, setBookType] = useState('IN_PERSON');
  const [bookReason, setBookReason] = useState('');
  const [booking, setBooking] = useState(false);
  const [bookingResult, setBookingResult] = useState<{ ok: boolean; text: string } | null>(null);

  // Records
  const [record, setRecord] = useState<PatientRecord | null>(null);
  const [timeline, setTimeline] = useState<CareTimelineEvent[]>([]);

  // Family
  const [familyForm, setFamilyForm] = useState({ full_name: '', relationship_type: 'CHILD', age: '', gender: 'Female', chronic_conditions: '' });
  const [showFamilyForm, setShowFamilyForm] = useState(false);

  const loadFacilities = async (p: Patient | null, all: boolean) => {
    const facs = await api.getFacilities(all || !p ? undefined : p.district);
    setFacilities(facs.length ? facs : await api.getFacilities());
  };

  const loadRecords = async (p: Patient) => {
    const [rec, tl] = await Promise.all([api.getPatientRecord(p.id), api.getTimeline(p.id)]);
    setRecord(rec);
    setTimeline(tl);
  };

  const loadAll = async () => {
    try {
      const p = await api.getMyPatient();
      setPatient(p);
      await Promise.all([loadFacilities(p, showAllDistricts), loadRecords(p)]);
    } catch (err: any) {
      setLoadError(err.message);
    }
  };

  useEffect(() => {
    loadAll();
    const onChange = () => loadAll();
    window.addEventListener('swasthyasetu-data-changed', onChange);
    return () => window.removeEventListener('swasthyasetu-data-changed', onChange);
  }, []);

  useEffect(() => {
    if (patient) loadFacilities(patient, showAllDistricts).catch(() => {});
  }, [showAllDistricts]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [messages]);

  // Pick a sensible default facility/doctor for the booking form.
  useEffect(() => {
    if (!facilities.length) return;
    const fac = facilities.find(f => f.id === bookFacilityId) || facilities[0];
    if (fac.id !== bookFacilityId) setBookFacilityId(fac.id);
    const docs = fac.doctors;
    if (!docs.some(d => d.id === bookDoctorId)) {
      setBookDoctorId((docs.find(d => d.is_available_today) || docs[0])?.id ?? null);
    }
  }, [facilities, bookFacilityId]);

  const handleVoiceInput = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert(t('आपके ब्राउज़र में वॉइस इनपुट समर्थित नहीं है। कृपया टाइप करें।', 'Speech recognition is not supported in this browser. Please type your symptoms.'));
      return;
    }
    try {
      const recognition = new SpeechRecognition();
      recognition.lang = speechLang(language);
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      setIsListening(true);
      recognition.onresult = (event: any) => setDraft(prev => (prev ? prev + ' ' : '') + event.results[0][0].transcript);
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  const toggleReadAloud = () => {
    const next = !readAloud;
    setReadAloud(next);
    if (!next) stopSpeaking();
    try { localStorage.setItem('swasthyasetu_read_aloud', String(next)); } catch { /* storage unavailable */ }
  };

  const [voiceWarning, setVoiceWarning] = useState<string | null>(null);

  const listen = async (text: string) => {
    const result = await speak(text, language);
    if (result === 'unsupported') {
      setVoiceWarning(t('इस ब्राउज़र में पढ़कर सुनाने की सुविधा नहीं है।', 'Text-to-speech is not supported in this browser.'));
    } else if (result === 'no-voice') {
      setVoiceWarning(t(
        'इस ब्राउज़र में हिंदी आवाज़ इंस्टॉल नहीं है, इसलिए यह हिंदी नहीं पढ़ सकता। ऐप को Microsoft Edge में खोलें (हिंदी और मराठी आवाज़ें पहले से हैं) या Google Chrome में (हिंदी), या Windows सेटिंग्स > भाषा में हिंदी का स्पीच पैक जोड़ें।',
        'No voice for this language is installed in this browser.'
      ));
    } else {
      setVoiceWarning(null);
    }
  };

  const sendMessage = async (e?: React.FormEvent, override?: string, fresh = false) => {
    e?.preventDefault();
    const text = (override ?? draft).trim();
    if (!text || sending) return;
    // The whole conversation is safety-screened, so a new topic needs a fresh conversation.
    const history: AssistantMessage[] = [...(fresh ? [] : messages), { role: 'user', content: text }];
    setMessages(history);
    setDraft('');
    setSending(true);
    try {
      const res = await api.chat(history.map(({ role, content }) => ({ role, content })).slice(-20), language);
      setMessages([...history, { role: 'assistant', content: res.reply, meta: res }]);
      if (readAloud) listen(res.reply);
      setBookReason(text.slice(0, 200));
      window.dispatchEvent(new Event('swasthyasetu-data-changed'));
      if (patient) loadRecords(patient).catch(() => {});
    } catch (err: any) {
      setMessages([...history, { role: 'assistant', content: t('क्षमा करें, सहायक अभी उपलब्ध नहीं है: ', 'Sorry, the assistant is unavailable right now: ') + err.message }]);
    } finally {
      setSending(false);
    }
  };

  const handleBook = async (e?: React.FormEvent, override?: { facilityId: number; doctorId: number; reason: string }) => {
    e?.preventDefault();
    const facilityId = override?.facilityId ?? bookFacilityId;
    const doctorId = override?.doctorId ?? bookDoctorId;
    if (!patient || !facilityId || !doctorId) return;
    setBooking(true);
    setBookingResult(null);
    try {
      const apt = await api.bookAppointment({
        patient_id: patient.id, doctor_id: doctorId, facility_id: facilityId,
        scheduled_date: bookDate, scheduled_time: bookTime, consultation_type: bookType,
        reason: override?.reason || bookReason || lastMeta?.triage.primary_complaint || 'General consultation'
      });
      setBookingResult({
        ok: true,
        text: apt.status === 'QUEUED_OFFLINE'
          ? t('आप ऑफ़लाइन हैं - अनुरोध सहेजा गया है और कनेक्शन आने पर भेजा जाएगा।', 'You are offline - the request is saved and will be sent when you reconnect (use Sync in the top bar).')
          : `${t('अपॉइंटमेंट बुक हो गया', 'Appointment booked')}: ${apt.appointment_code} • ${t('टोकन', 'Token')} ${apt.queue_token} • ${apt.facility_name} • ${apt.doctor_name} • ${apt.scheduled_date} ${apt.scheduled_time}`
      });
      await loadAll();
      window.dispatchEvent(new Event('swasthyasetu-data-changed'));
    } catch (err: any) {
      setBookingResult({ ok: false, text: err.message });
    } finally {
      setBooking(false);
    }
  };

  const demoRef = useRef<(detail: any) => void>(() => {});
  demoRef.current = (detail: any) => {
    if (detail.action === 'tab') setActiveTab(detail.tab);
    if (detail.action === 'chat') {
      setActiveTab('ASSISTANT');
      sendMessage(undefined, detail.text, Boolean(detail.fresh));
    }
    if (detail.action === 'book') {
      const fac = facilities.find(f => f.facility_type === 'CHC') || facilities[0];
      const doc = fac?.doctors.find(d => d.is_available_today) || fac?.doctors[0];
      if (!fac || !doc) return;
      setBookFacilityId(fac.id);
      setBookDoctorId(doc.id);
      setActiveTab('FACILITIES');
      handleBook(undefined, { facilityId: fac.id, doctorId: doc.id, reason: detail.reason });
      setTimeout(() => document.getElementById('booking-form')?.scrollIntoView({ behavior: 'smooth' }), 300);
    }
  };
  useEffect(() => {
    const onDemo = (e: Event) => demoRef.current((e as CustomEvent).detail);
    window.addEventListener('swasthyasetu-demo', onDemo);
    return () => window.removeEventListener('swasthyasetu-demo', onDemo);
  }, []);

  const startBookingAt = (facId: number) => {
    setBookFacilityId(facId);
    setActiveTab('FACILITIES');
    setTimeout(() => document.getElementById('booking-form')?.scrollIntoView({ behavior: 'smooth' }), 50);
  };

  const cancelAppointment = async (apt: Appointment) => {
    if (!confirm(t(`अपॉइंटमेंट ${apt.appointment_code} रद्द करें?`, `Cancel appointment ${apt.appointment_code}?`))) return;
    try {
      await api.setAppointmentStatus(apt.id, 'CANCELLED');
      await loadAll();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const addFamily = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.addFamilyMember({ ...familyForm, age: Number(familyForm.age), chronic_conditions: familyForm.chronic_conditions || 'None' });
      setFamilyForm({ full_name: '', relationship_type: 'CHILD', age: '', gender: 'Female', chronic_conditions: '' });
      setShowFamilyForm(false);
      setPatient(await api.getMyPatient());
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loadError) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-10 text-center space-y-3">
        <p className="text-sm text-rose-800">{loadError}</p>
        <button onClick={onRegister} className="bg-teal-700 text-white text-sm font-bold px-4 py-2 rounded-xl">{t('पंजीकरण करें', 'Register as a patient')}</button>
      </div>
    );
  }

  const selectedFacility = facilities.find(f => f.id === bookFacilityId);
  const emergencyFacility = facilities
    .filter(f => f.facility_type !== 'PHC' && f.diagnostic_tests_available.includes('Electrocardiogram (ECG)'))
    .sort((a, b) => a.distance_km - b.distance_km)[0];
  const upcoming = (record?.appointments || []).filter(a => a.status === 'BOOKED' || a.status === 'IN_QUEUE');
  const pendingFollowUps = (record?.follow_ups || []).filter(f => f.status === 'SCHEDULED' || f.status === 'OVERDUE');

  const samplePrompts = [
    { label: t('सीने में दर्द व सांस में तकलीफ (आपातकाल)', 'Chest pain & breathlessness (emergency)'), text: 'Mujhe chest mein severe pain aur saans lene mein dikkat ho rahi hai pichle 2 ghante se.' },
    { label: t('बुखार और शरीर दर्द', 'Fever & body pain'), text: t('मुझे कल रात से हल्का बुखार और बदन दर्द है, क्या करूं?', 'I have had a mild fever and body pain since last night. What should I do?') },
    { label: t('बीपी की दवा और फॉलो-अप', 'My BP medicine & follow-up'), text: t('मेरी बीपी की दवा और अगला फॉलो-अप कब है?', 'Which BP medicines am I on and when is my next follow-up?') },
  ];

  const tabs: { id: Tab; label: string }[] = [
    { id: 'ASSISTANT', label: t('१. एआई स्वास्थ्य सहायक', '1. AI Health Assistant') },
    { id: 'FACILITIES', label: t('२. अस्पताल व अपॉइंटमेंट', '2. Facilities & Booking') },
    { id: 'RECORDS', label: t('३. मेरा स्वास्थ्य रिकॉर्ड', '3. My Health Record') },
    { id: 'TIMELINE', label: t('४. टाइमलाइन', '4. Timeline') },
    { id: 'FAMILY', label: t('५. परिवार', '5. Family') },
    { id: 'PRIVACY', label: t('६. गोपनीयता', '6. Privacy') },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Profile */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4 min-w-0">
          <div className="w-14 h-14 shrink-0 rounded-2xl bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-xl border border-teal-200">
            {(patient?.name || user.full_name).charAt(0)}
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">{patient?.name || user.full_name}</h2>
              <span className="bg-slate-100 text-slate-700 text-[11px] px-2 py-0.5 rounded-full font-semibold border border-slate-200">
                {t('डेमो ABHA', 'Demo ABHA')}: <span className="font-mono">{patient?.abha_id}</span>
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {patient?.village}, {patient?.block}, {patient?.district} • {patient?.age}y / {patient?.gender} • {t('ब्लड ग्रुप', 'Blood')}: {patient?.blood_group}
            </p>
            <p className="text-xs text-teal-700 font-medium mt-1">
              {t('पुरानी बीमारी', 'Conditions')}: {patient?.chronic_conditions}
              {pendingFollowUps.length > 0 && <> • <Bell size={11} className="inline" /> {t('अगला फॉलो-अप', 'Next follow-up')}: {pendingFollowUps[pendingFollowUps.length - 1].due_date}</>}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center bg-slate-100 p-1 rounded-xl text-xs font-medium border border-slate-200" role="tablist">
          {tabs.map(tab => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-lg transition ${activeTab === tab.id ? 'bg-teal-700 text-white font-bold shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ASSISTANT */}
      {activeTab === 'ASSISTANT' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-4">
            <div>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="text-teal-700" size={20} />
                  {t('स्वास्थ्य सहायक से बात करें', 'Talk to the health assistant')}
                </h3>
                <div className="flex items-center gap-2">
                {messages.length > 0 && (
                  <button type="button" onClick={() => { stopSpeaking(); setMessages([]); }}
                    className="text-xs font-semibold px-2.5 py-1 rounded-lg border bg-white text-slate-600 border-slate-300 hover:bg-slate-50">
                    {t('नई बातचीत', 'New conversation')}
                  </button>
                )}
                {canSpeak() && (
                  <button type="button" onClick={toggleReadAloud} aria-pressed={readAloud}
                    className={`text-xs font-semibold px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${readAloud ? 'bg-teal-700 text-white border-teal-700' : 'bg-white text-slate-600 border-slate-300'}`}>
                    {readAloud ? <Volume2 size={14} /> : <VolumeX size={14} />} {t('जवाब पढ़कर सुनाएं', 'Read answers aloud')}
                  </button>
                )}
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {t('हिंदी, मराठी या अंग्रेज़ी में लिखें या बोलें। आपातकालीन संकेत मिलने पर तुरंत 112 की सलाह दी जाती है। यह डॉक्टर का विकल्प नहीं है।',
                  'Type or speak in Hindi, Marathi or English. Emergency signs always trigger 112 advice first. This is not a substitute for a doctor.')}
              </p>
            </div>

            {voiceWarning && (
              <div className="text-xs bg-amber-50 border border-amber-300 text-amber-900 rounded-xl p-3 flex items-start justify-between gap-2" role="status">
                <span>{voiceWarning}</span>
                <button type="button" onClick={() => setVoiceWarning(null)} aria-label="Dismiss" className="font-bold">✕</button>
              </div>
            )}

            {/* Emergency banner */}
            {lastMeta?.triage.is_emergency && (
              <div className="bg-red-50 border-2 border-red-500 rounded-2xl p-4 space-y-3" role="alert">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-red-600 text-white flex items-center justify-center shrink-0">
                    <AlertTriangle size={24} />
                  </div>
                  <div>
                    <div className="text-[11px] font-black uppercase text-red-700">{t('आपातकाल - तुरंत कार्रवाई करें', 'Emergency - act now')}</div>
                    <p className="text-sm font-semibold text-red-900 leading-relaxed">{lastMeta.triage.emergency_advice}</p>
                    {canSpeak() && (
                      <button type="button" onClick={() => listen(lastMeta.triage.emergency_advice || '')} className="mt-1 text-xs font-bold text-red-800 underline flex items-center gap-1">
                        <Volume2 size={13} /> {t('सुनें', 'Listen')}
                      </button>
                    )}
                  </div>
                </div>
                <div className="bg-white/80 rounded-xl p-3 border border-red-200 flex flex-wrap items-center justify-between gap-3">
                  <a href="tel:112" className="text-2xl font-black text-red-600 flex items-center gap-2">
                    <PhoneCall size={22} /> 112 / 108
                  </a>
                  {emergencyFacility && (
                    <div className="text-right text-xs">
                      <div className="text-slate-600">{t('निकटतम आपातकालीन केंद्र', 'Nearest emergency-ready facility')}:</div>
                      <div className="font-bold text-slate-900">{emergencyFacility.name} ({emergencyFacility.distance_km} km, ~{emergencyFacility.travel_time_mins} min) • {emergencyFacility.emergency_contact}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Conversation */}
            <div className="border border-slate-200 rounded-xl bg-slate-50 p-3 h-[360px] overflow-y-auto space-y-3" aria-live="polite">
              {messages.length === 0 && (
                <div className="space-y-2">
                  <p className="text-xs text-slate-500">{t('उदाहरण के लिए क्लिक करें:', 'Try one of these:')}</p>
                  <div className="flex flex-wrap gap-2">
                    {samplePrompts.map((p, idx) => (
                      <button key={idx} type="button" onClick={() => setDraft(p.text)}
                        className="text-xs bg-white hover:bg-teal-50 border border-slate-200 hover:border-teal-300 rounded-lg px-2.5 py-1 text-slate-700 text-left">
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((m, idx) => (
                <div key={idx} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm whitespace-pre-line ${
                    m.role === 'user' ? 'bg-teal-700 text-white'
                      : m.meta?.triage.is_emergency ? 'bg-red-100 border border-red-300 text-red-950'
                        : 'bg-white border border-slate-200 text-slate-800'}`}>
                    {m.content}
                    {m.meta && (
                      <div className="mt-2 pt-2 border-t border-slate-200/70 text-[10px] text-slate-500 space-y-0.5">
                        <div>
                          <span className={`font-bold px-1.5 rounded ${statusColor(m.meta.triage.triage_level === 'ROUTINE' ? 'COMPLETED' : m.meta.triage.triage_level === 'EMERGENCY' ? 'CANCELLED' : 'BOOKED')}`}>
                            {m.meta.triage.triage_level}
                          </span>{' '}
                          {m.meta.mode === 'LLM' ? `AI: ${m.meta.model}` : m.meta.mode === 'SAFETY_RULES' ? t('सुरक्षा नियम', 'Safety rules') : t('डेमो मोड (बिना LLM)', 'Demo mode (no LLM key)')}
                        </div>
                        {m.meta.sources.length > 0 && <div>{t('स्रोत', 'Sources')}: {m.meta.sources.map(s => s.title).join('; ')}</div>}
                      </div>
                    )}
                    {m.role === 'assistant' && canSpeak() && (
                      <button type="button" onClick={() => listen(m.content)} className="mt-1 text-[11px] font-semibold text-teal-800 flex items-center gap-1" aria-label={t('सुनें', 'Listen')}>
                        <Volume2 size={12} /> {t('सुनें', 'Listen')}
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {sending && <div className="text-xs text-slate-500 flex items-center gap-1"><Clock size={12} className="animate-spin" /> {t('सोच रहा है…', 'Thinking…')}</div>}
              <div ref={chatEndRef} />
            </div>

            <form onSubmit={sendMessage} className="flex items-end gap-2">
              <label htmlFor="symptom-input" className="sr-only">{t('अपने लक्षण लिखें', 'Describe your symptoms')}</label>
              <textarea
                id="symptom-input"
                rows={2}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                placeholder={t('उदा. "मुझे 2 दिन से बुखार है..."', 'e.g. "I have had a fever for 2 days..."')}
                className="flex-1 rounded-xl border border-slate-300 p-3 text-sm focus:border-teal-600 focus:ring-1 focus:ring-teal-600 outline-none"
              />
              <button type="button" onClick={handleVoiceInput} aria-label={t('बोलकर बताएं', 'Speak')}
                className={`p-3 rounded-xl transition ${isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-slate-100 text-slate-600 hover:bg-teal-100'}`}>
                <Mic size={18} />
              </button>
              <button type="submit" disabled={sending || !draft.trim()} aria-label={t('भेजें', 'Send')}
                className="bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white p-3 rounded-xl">
                <Send size={18} />
              </button>
            </form>
            <div className="text-[11px] text-slate-500 flex items-center gap-1">
              <Shield size={12} className="text-teal-700" />
              {t('आपके रिकॉर्ड का उपयोग केवल आपकी सहायता के लिए किया जाता है और हर पहुंच ऑडिट होती है।', 'Your own record is used only to answer you, and every access is audited.')}
            </div>
          </div>

          {/* Right rail */}
          <div className="space-y-4">
            {lastMeta && !lastMeta.triage.is_emergency && (
              <div className="bg-teal-50 border border-teal-200 rounded-2xl p-4 space-y-2">
                <div className="text-xs font-bold text-teal-900">{t('सुझाया गया अगला कदम', 'Suggested next step')}</div>
                <p className="text-xs text-slate-700">{lastMeta.triage.explanation_patient}</p>
                <div className="text-[11px] text-slate-600">
                  {t('सुविधा', 'Facility')}: <strong>{lastMeta.triage.recommended_facility_type}</strong> • {t('विशेषज्ञता', 'Specialty')}: <strong>{lastMeta.triage.recommended_specialty}</strong>
                </div>
                <button onClick={() => setActiveTab('FACILITIES')} className="w-full bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-2 rounded-xl">
                  {t('अस्पताल चुनें और अपॉइंटमेंट बुक करें', 'Choose a facility & book')}
                </button>
              </div>
            )}

            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 space-y-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Calendar className="text-teal-700" size={16} /> {t('आगामी अपॉइंटमेंट', 'Upcoming appointments')}
              </h3>
              {upcoming.length === 0 ? (
                <p className="text-xs text-slate-400">{t('कोई अपॉइंटमेंट नहीं', 'None booked')}</p>
              ) : upcoming.map(a => (
                <div key={a.id} className="text-xs border border-slate-200 rounded-lg p-2.5 space-y-0.5">
                  <div className="font-bold text-slate-900">{a.scheduled_date} • {a.scheduled_time} • {t('टोकन', 'Token')} {a.queue_token}</div>
                  <div className="text-slate-600">{a.doctor_name}, {a.facility_name}</div>
                </div>
              ))}
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 space-y-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <MapPin className="text-teal-700" size={16} /> {t('निकटतम स्वास्थ्य केंद्र', 'Nearby facilities')}
              </h3>
              {facilities.slice(0, 3).map(fac => (
                <button key={fac.id} onClick={() => startBookingAt(fac.id)} className="w-full text-left p-2.5 rounded-xl border border-slate-200 hover:border-teal-500 text-xs space-y-1">
                  <div className="flex justify-between gap-2">
                    <span className="font-bold text-slate-900">{fac.name}</span>
                    <span className="bg-teal-100 text-teal-800 text-[10px] font-bold px-1.5 rounded shrink-0 h-fit">{fac.facility_type}</span>
                  </div>
                  <div className="text-slate-500">{fac.distance_km} km (~{fac.travel_time_mins} min) • {fac.available_doctors_count} {t('डॉक्टर उपलब्ध', 'doctors on duty')}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* FACILITIES & BOOKING */}
      {activeTab === 'FACILITIES' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">{t('स्वास्थ्य केंद्र और उपलब्ध सेवाएं', 'Healthcare facilities & available services')}</h3>
                <p className="text-xs text-slate-500">{t('डॉक्टर रोस्टर, जांच और दवा स्टॉक अस्पताल स्टाफ द्वारा अपडेट किए जाते हैं। अंतिम अपडेट समय दिखाया गया है।', 'Doctor rosters, tests and medicine stock are updated by facility staff; the last update time is shown on each card.')}</p>
              </div>
              <label className="text-xs text-slate-600 flex items-center gap-2">
                <input type="checkbox" checked={showAllDistricts} onChange={e => setShowAllDistricts(e.target.checked)} />
                {t('सभी ज़िले दिखाएं', 'Show all districts')}
              </label>
            </div>

            <FacilityMap facilities={facilities} selectedId={bookFacilityId} onSelect={startBookingAt} language={language} />

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {facilities.map(f => (
                <div key={f.id} className={`border rounded-2xl p-4 space-y-3 ${bookFacilityId === f.id ? 'border-teal-600 ring-1 ring-teal-600' : 'border-slate-200'}`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-bold">{f.facility_type}</span>
                      <h4 className="text-sm font-bold text-slate-900 mt-1">{f.name}</h4>
                      <p className="text-[11px] text-slate-500">{f.address}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-sm font-bold text-teal-800">{f.distance_km} km</div>
                      <div className="text-[11px] text-slate-400">~{f.travel_time_mins} min</div>
                    </div>
                  </div>
                  <div className="bg-slate-50 rounded-xl p-2.5 space-y-1 text-[11px]">
                    <div className="flex justify-between gap-2"><span className="text-slate-500">{t('समय', 'Hours')}</span><span className="font-semibold text-right">{f.operating_hours}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">{t('डॉक्टर ड्यूटी पर', 'Doctors on duty')}</span><span className="font-semibold text-emerald-700">{f.available_doctors_count}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">{t('आज की अनुमानित प्रतीक्षा', "Est. wait today")}</span><span className="font-semibold">{f.estimated_queue_wait_mins} min</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">{t('फ़ोन', 'Phone')}</span><span className="font-semibold">{f.phone}</span></div>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {f.diagnostic_tests_available.map(test => (
                      <span key={test} className="bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] px-1.5 py-0.5 rounded">✓ {test.split(' (')[0]}</span>
                    ))}
                    {f.diagnostic_tests_missing.map(test => (
                      <span key={test} className="bg-rose-50 text-rose-700 border border-rose-200 text-[10px] px-1.5 py-0.5 rounded">✕ {test.split(' (')[0]}</span>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-1 text-[10px]">
                    {Object.entries(f.medicine_stock_summary).map(([med, st]) => (
                      <div key={med} className="flex justify-between bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200">
                        <span className="truncate">{med}</span>
                        <span className={`font-bold ${st === 'IN_STOCK' ? 'text-emerald-700' : st === 'LOW_STOCK' ? 'text-amber-700' : 'text-rose-600'}`}>
                          {st === 'IN_STOCK' ? t('उपलब्ध', 'In stock') : st === 'LOW_STOCK' ? t('कम', 'Low') : t('खत्म', 'Out')}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-slate-400">{f.freshness_label}</span>
                    <button onClick={() => startBookingAt(f.id)} className="bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg">
                      {t('यहां बुक करें', 'Book here')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Booking form */}
          <form id="booking-form" onSubmit={handleBook} className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Calendar className="text-teal-700" size={20} /> {t('अपॉइंटमेंट का अनुरोध', 'Request an appointment')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
              <label className="space-y-1">
                <span className="text-xs font-semibold text-slate-700">{t('स्वास्थ्य केंद्र', 'Facility')}</span>
                <select value={bookFacilityId ?? ''} onChange={e => { setBookFacilityId(Number(e.target.value)); setBookDoctorId(null); }} className="w-full p-2 border border-slate-300 rounded-lg bg-white">
                  {facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
                </select>
              </label>
              <label className="space-y-1">
                <span className="text-xs font-semibold text-slate-700">{t('डॉक्टर', 'Doctor')}</span>
                <select value={bookDoctorId ?? ''} onChange={e => setBookDoctorId(Number(e.target.value))} className="w-full p-2 border border-slate-300 rounded-lg bg-white">
                  {(selectedFacility?.doctors || []).map(d => (
                    <option key={d.id} value={d.id}>
                      {d.name} - {d.specialty}{d.is_available_today ? '' : ` (${t('आज छुट्टी', 'off today')})`}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-1">
                <span className="text-xs font-semibold text-slate-700">{t('परामर्श प्रकार', 'Consultation')}</span>
                <select value={bookType} onChange={e => setBookType(e.target.value)} className="w-full p-2 border border-slate-300 rounded-lg bg-white">
                  <option value="IN_PERSON">{t('अस्पताल में', 'In person')}</option>
                  <option value="TELEMEDICINE">{t('टेली-परामर्श (डेमो)', 'Teleconsultation (demo)')}</option>
                </select>
              </label>
              <label className="space-y-1">
                <span className="text-xs font-semibold text-slate-700">{t('तारीख', 'Date')}</span>
                <input type="date" min={localDate(0)} value={bookDate} onChange={e => setBookDate(e.target.value)} required className="w-full p-2 border border-slate-300 rounded-lg" />
              </label>
              <label className="space-y-1">
                <span className="text-xs font-semibold text-slate-700">{t('समय', 'Time')}</span>
                <select value={bookTime} onChange={e => setBookTime(e.target.value)} className="w-full p-2 border border-slate-300 rounded-lg bg-white">
                  {TIME_SLOTS.map(s => <option key={s}>{s}</option>)}
                </select>
              </label>
              <label className="space-y-1">
                <span className="text-xs font-semibold text-slate-700">{t('कारण', 'Reason')}</span>
                <input value={bookReason} onChange={e => setBookReason(e.target.value)} maxLength={200} placeholder={t('जैसे: बुखार', 'e.g. fever')} className="w-full p-2 border border-slate-300 rounded-lg" />
              </label>
            </div>
            {(() => {
              const doc = selectedFacility?.doctors.find(d => d.id === bookDoctorId);
              return doc && doc.schedule.length > 0 ? (
                <p className="text-[11px] text-slate-500">
                  {t('ओपीडी समय', 'OPD schedule')}: {doc.schedule.map(s => `${s.day_of_week.slice(0, 3)} ${s.start_time}-${s.end_time}`).join(', ')}
                </p>
              ) : null;
            })()}
            {bookingResult && (
              <div className={`text-xs rounded-lg p-3 border flex items-center gap-2 ${bookingResult.ok ? 'bg-emerald-50 border-emerald-300 text-emerald-900' : 'bg-rose-50 border-rose-300 text-rose-900'}`}>
                {bookingResult.ok ? <CheckCircle2 size={16} /> : <XCircle size={16} />} {bookingResult.text}
              </div>
            )}
            <div className="flex justify-end">
              <button type="submit" disabled={booking || !bookDoctorId} className="bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white text-sm font-bold px-5 py-2.5 rounded-xl">
                {booking ? t('बुक हो रहा है…', 'Booking…') : t('अपॉइंटमेंट बुक करें', 'Book appointment')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* HEALTH RECORD */}
      {activeTab === 'RECORDS' && record && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2"><Bell className="text-teal-700" size={18} /> {t('फॉलो-अप और रिमाइंडर', 'Follow-ups & reminders')}</h3>
            {record.follow_ups.length === 0 && <p className="text-xs text-slate-400">{t('कोई फॉलो-अप नहीं', 'No follow-ups')}</p>}
            {record.follow_ups.map(f => (
              <div key={f.id} className="text-xs border border-slate-200 rounded-lg p-2.5 flex justify-between gap-3">
                <div><div className="font-bold text-slate-900">{t('देय तिथि', 'Due')} {f.due_date}</div><div className="text-slate-600">{f.instructions}</div></div>
                <span className={`h-fit text-[10px] font-bold px-2 py-0.5 rounded ${statusColor(f.status)}`}>{f.status}</span>
              </div>
            ))}
            {record.reminders.map(r => (
              <div key={r.id} className="text-[11px] bg-slate-50 border border-slate-200 rounded-lg p-2 flex justify-between gap-3">
                <span>{r.channel}: {r.message}</span>
                <span className="shrink-0 text-slate-500">{r.status === 'SENT' ? t('भेजा गया', 'Sent') : `${t('निर्धारित', 'Scheduled')} ${new Date(r.scheduled_time).toLocaleDateString()}`}</span>
              </div>
            ))}
          </section>

          <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2"><Calendar className="text-teal-700" size={18} /> {t('अपॉइंटमेंट', 'Appointments')}</h3>
            {record.appointments.length === 0 && <p className="text-xs text-slate-400">{t('कोई अपॉइंटमेंट नहीं', 'No appointments')}</p>}
            {record.appointments.map(a => (
              <div key={a.id} className="text-xs border border-slate-200 rounded-lg p-2.5 flex justify-between gap-3">
                <div>
                  <div className="font-bold text-slate-900">{a.scheduled_date} {a.scheduled_time} • {a.appointment_code} • {t('टोकन', 'Token')} {a.queue_token}</div>
                  <div className="text-slate-600">{a.doctor_name}, {a.facility_name} • {a.consultation_type}</div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${statusColor(a.status)}`}>{a.status}</span>
                  {a.status === 'BOOKED' && <button onClick={() => cancelAppointment(a)} className="text-[10px] text-rose-700 underline">{t('रद्द करें', 'Cancel')}</button>}
                </div>
              </div>
            ))}
          </section>

          <section className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2"><Stethoscope className="text-teal-700" size={18} /> {t('परामर्श और पर्चे', 'Consultations & prescriptions')}</h3>
            {record.encounters.length === 0 && <p className="text-xs text-slate-400">{t('अभी कोई परामर्श नहीं', 'No consultations yet')}</p>}
            {record.encounters.map(e => (
              <div key={e.id} className="border border-slate-200 rounded-xl p-3 text-xs space-y-1.5">
                <div className="flex flex-wrap justify-between gap-2">
                  <span className="font-bold text-slate-900">{e.diagnosis}</span>
                  <span className="text-slate-500">{new Date(e.encounter_date).toLocaleDateString()} • {e.doctor_name} • {e.facility_name}</span>
                </div>
                <div className="text-slate-600">BP {e.vital_bp} • {t('नाड़ी', 'Pulse')} {e.vital_pulse} • {t('तापमान', 'Temp')} {e.vital_temp}°F • SpO2 {e.vital_spo2}%</div>
                {e.prescriptions.flatMap(rx => rx.items.map(item => (
                  <div key={item.id} className="flex flex-wrap justify-between gap-2 bg-slate-50 rounded p-1.5">
                    <span><Pill size={11} className="inline text-teal-700" /> {item.medicine_name} {item.dosage} • {item.frequency} • {item.duration_days} {t('दिन', 'days')}</span>
                    {item.collected_status === 'OUT_OF_STOCK' && <span className="text-[10px] font-bold text-rose-700">{t('इस केंद्र पर स्टॉक नहीं', 'Not in stock at this facility')}</span>}
                  </div>
                )))}
              </div>
            ))}
          </section>

          <section className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2"><FileText className="text-teal-700" size={18} /> {t('जांच', 'Diagnostic tests')}</h3>
            {record.diagnostic_orders.length === 0 && <p className="text-xs text-slate-400">{t('कोई जांच नहीं', 'No tests ordered')}</p>}
            {record.diagnostic_orders.map(o => (
              <div key={o.id} className="text-xs border border-slate-200 rounded-lg p-2.5 flex justify-between gap-3">
                <span>{o.test_name} • {o.facility_name} • {o.scheduled_date}</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${statusColor(o.status)}`}>{o.status === 'UNAVAILABLE' ? t('यहां उपलब्ध नहीं - रेफ़र', 'Not available here - referral') : o.status}</span>
              </div>
            ))}
          </section>
        </div>
      )}

      {/* TIMELINE */}
      {activeTab === 'TIMELINE' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
          <div>
            <h3 className="text-lg font-bold text-slate-900">{t('डिजिटल स्वास्थ्य टाइमलाइन', 'Care journey timeline')}</h3>
            <p className="text-xs text-slate-500">{t('परामर्श, जांच, पर्चे और फॉलो-अप का क्रमवार रिकॉर्ड', 'Chronological record of consultations, tests, prescriptions and follow-ups')}</p>
          </div>
          <div className="relative border-l-2 border-teal-600 ml-4 space-y-6 pl-6">
            {timeline.length === 0 ? (
              <p className="text-xs text-slate-400 italic">{t('अभी कोई घटना नहीं', 'No events yet')}</p>
            ) : timeline.map(ev => (
              <div key={ev.id} className="relative space-y-1">
                <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-teal-600 border-2 border-white" />
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-bold text-teal-900 uppercase">{ev.event_type} • {ev.actor_name}</span>
                  <span className="text-[11px] text-slate-400 font-mono">{new Date(ev.created_at).toLocaleString()}</span>
                </div>
                <h4 className="text-sm font-bold text-slate-800">{ev.title}</h4>
                <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-200">{ev.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FAMILY */}
      {activeTab === 'FAMILY' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2"><Users className="text-teal-700" size={20} /> {t('परिवार के सदस्य', 'Family members')}</h3>
            <button onClick={() => setShowFamilyForm(v => !v)} className="bg-teal-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-teal-800">
              + {t('सदस्य जोड़ें', 'Add family member')}
            </button>
          </div>
          {showFamilyForm && (
            <form onSubmit={addFamily} className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs bg-slate-50 p-3 rounded-xl border border-slate-200">
              <input required placeholder={t('नाम', 'Name')} value={familyForm.full_name} onChange={e => setFamilyForm({ ...familyForm, full_name: e.target.value })} className="p-2 border rounded-lg col-span-2 md:col-span-1" />
              <select value={familyForm.relationship_type} onChange={e => setFamilyForm({ ...familyForm, relationship_type: e.target.value })} className="p-2 border rounded-lg bg-white">
                <option value="SPOUSE">{t('पति/पत्नी', 'Spouse')}</option><option value="CHILD">{t('बच्चा', 'Child')}</option>
                <option value="PARENT">{t('माता/पिता', 'Parent')}</option><option value="SIBLING">{t('भाई/बहन', 'Sibling')}</option>
              </select>
              <input required type="number" min={0} max={120} placeholder={t('उम्र', 'Age')} value={familyForm.age} onChange={e => setFamilyForm({ ...familyForm, age: e.target.value })} className="p-2 border rounded-lg" />
              <select value={familyForm.gender} onChange={e => setFamilyForm({ ...familyForm, gender: e.target.value })} className="p-2 border rounded-lg bg-white">
                <option value="Female">{t('महिला', 'Female')}</option><option value="Male">{t('पुरुष', 'Male')}</option>
              </select>
              <input placeholder={t('बीमारी (यदि कोई)', 'Conditions (if any)')} value={familyForm.chronic_conditions} onChange={e => setFamilyForm({ ...familyForm, chronic_conditions: e.target.value })} className="p-2 border rounded-lg" />
              <button type="submit" className="col-span-2 md:col-span-5 bg-teal-700 text-white font-bold py-2 rounded-lg">{t('सहेजें', 'Save')}</button>
            </form>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(patient?.family_members || []).length === 0 && <p className="text-xs text-slate-400">{t('अभी कोई सदस्य नहीं जोड़ा गया', 'No family members added yet')}</p>}
            {(patient?.family_members || []).map(m => (
              <div key={m.id} className="border border-slate-200 rounded-xl p-4 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">{m.full_name}</span>
                  <span className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-semibold">{m.relationship_type} ({m.age}y, {m.gender})</span>
                </div>
                <p className="text-xs text-slate-500">{t('बीमारी', 'Conditions')}: {m.chronic_conditions}</p>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-slate-500 flex items-center gap-1"><Info size={12} /> {t('परिवार के सदस्यों के लिए अलग पंजीकरण बाद के चरण में आएगा।', 'Separate health records for family members are planned for a later phase.')}</p>
        </div>
      )}
      {activeTab === 'PRIVACY' && <PrivacyPanel language={language} />}
    </div>
  );
};
