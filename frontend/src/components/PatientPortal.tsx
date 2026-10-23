import React, { useState, useEffect } from 'react';
import { Patient, FacilityReadiness, SymptomIntakeResponse, Appointment, CareTimelineEvent } from '../types';
import { api } from '../services/api';
import { 
  AlertTriangle, PhoneCall, CheckCircle2, Clock, MapPin, 
  Stethoscope, Pill, FileText, Calendar, Shield, Users, Mic, Send,
  ArrowRight, Activity, Info, AlertCircle
} from 'lucide-react';

interface PatientPortalProps {
  language: 'hi' | 'en';
  onEmergencyTriggered?: () => void;
}

export const PatientPortal: React.FC<PatientPortalProps> = ({ language }) => {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [symptomText, setSymptomText] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [triageResponse, setTriageResponse] = useState<SymptomIntakeResponse | null>(null);
  
  const [facilities, setFacilities] = useState<FacilityReadiness[]>([]);
  const [selectedFacility, setSelectedFacility] = useState<FacilityReadiness | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [timeline, setTimeline] = useState<CareTimelineEvent[]>([]);
  const [activeTab, setActiveTab] = useState<'ASSISTANT' | 'TIMELINE' | 'FACILITIES' | 'FAMILY'>('ASSISTANT');
  const [bookingSuccess, setBookingSuccess] = useState<Appointment | null>(null);
  const [isListening, setIsListening] = useState<boolean>(false);

  // Load patient #1 (Ramesh Kumar)
  const loadData = async () => {
    try {
      const pat = await api.getPatient(1, 'ramesh');
      setPatient(pat);
      const facs = await api.getFacilities();
      setFacilities(facs);
      if (facs.length > 0) setSelectedFacility(facs[0]);
      const apts = await api.getAppointments(1, 'ramesh');
      setAppointments(apts);
      const tl = await api.getTimeline(1);
      setTimeline(tl);
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleVoiceInput = () => {
    // Check SpeechRecognition support
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert(language === 'hi' 
        ? 'आपके ब्राउज़र में वॉइस इनपुट समर्थित नहीं है। कृपया टाइप करें।' 
        : 'Browser speech recognition not supported. Please type your symptoms.'
      );
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = language === 'hi' ? 'hi-IN' : 'en-IN';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      setIsListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setSymptomText(transcript);
        setIsListening(false);
      };
      recognition.onerror = () => {
        setIsListening(false);
      };
      recognition.onend = () => {
        setIsListening(false);
      };
      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  const handleIntakeSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!symptomText.trim()) return;

    setIsSubmitting(true);
    try {
      const res = await api.submitIntake(1, symptomText, language, 'ramesh');
      setTriageResponse(res);
      // Refresh timeline
      const tl = await api.getTimeline(1);
      setTimeline(tl);
    } catch (err: any) {
      alert('Error submitting intake: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBookDemoAppointment = async (facId: number) => {
    try {
      const apt = await api.bookAppointment({
        patient_id: 1,
        doctor_id: 1,
        facility_id: facId,
        scheduled_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
        scheduled_time: '10:30 AM',
        consultation_type: 'IN_PERSON',
        reason: triageResponse?.primary_complaint || 'General Clinical Review'
      }, 'ramesh');
      setBookingSuccess(apt);
      loadData();
    } catch (err: any) {
      alert('Failed to book appointment: ' + err.message);
    }
  };

  const samplePrompts = [
    { label: language === 'hi' ? 'सीने में दर्द व सांस में तकलीफ (आपातकाल)' : 'Severe chest pain & breathlessness (Emergency)', text: 'Mujhe chest mein severe pain aur saans lene mein dikkat ho rahi hai pichle 2 ghante se.' },
    { label: language === 'hi' ? 'बुखार और शरीर दर्द (सामान्य)' : 'Fever & body pain (Routine)', text: 'Halka bukhar aur badan dard hai kal raat se.' },
    { label: language === 'hi' ? 'मधुमेह एवं ब्लड प्रेशर फॉलो-अप' : 'Diabetes & BP checkup', text: 'Mujhe BP aur sugar ki dawaiyan leni hain aur regular follow-up check karwana hai.' }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Patient Profile Card & Health ID */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-xl border border-teal-200">
            {patient?.name?.charAt(0) || 'R'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">{patient?.name || 'Ramesh Kumar'}</h2>
              <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-0.5 rounded-full font-semibold border border-emerald-200">
                ABHA Active
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              ABHA ID: <span className="font-mono text-slate-700 font-medium">{patient?.abha_id || '91-4829-1029-3849'}</span> • 
              Village: <span className="font-medium text-slate-700">{patient?.village || 'Paud'}</span>, Mulshi • 
              Age: <span className="font-medium text-slate-700">{patient?.age || 48}y / {patient?.gender || 'Male'}</span>
            </p>
            <p className="text-xs text-teal-700 font-medium mt-1">
              Assigned ASHA Worker: Kavita Tai Patil (Paud Sub-Centre) • Blood: B+
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-medium border border-slate-200">
          <button
            onClick={() => setActiveTab('ASSISTANT')}
            className={`px-3 py-1.5 rounded-lg transition ${activeTab === 'ASSISTANT' ? 'bg-teal-700 text-white font-bold shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            {language === 'hi' ? '१. एआई स्वास्थ्य सहायक' : '1. AI Health Assistant'}
          </button>
          <button
            onClick={() => setActiveTab('FACILITIES')}
            className={`px-3 py-1.5 rounded-lg transition ${activeTab === 'FACILITIES' ? 'bg-teal-700 text-white font-bold shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            {language === 'hi' ? '२. अस्पताल तैयारी' : '2. Hospital Readiness'}
          </button>
          <button
            onClick={() => setActiveTab('TIMELINE')}
            className={`px-3 py-1.5 rounded-lg transition ${activeTab === 'TIMELINE' ? 'bg-teal-700 text-white font-bold shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            {language === 'hi' ? '३. डिजिटल स्वास्थ्य टाइमलाइन' : '3. Care Timeline'}
          </button>
          <button
            onClick={() => setActiveTab('FAMILY')}
            className={`px-3 py-1.5 rounded-lg transition ${activeTab === 'FAMILY' ? 'bg-teal-700 text-white font-bold shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            {language === 'hi' ? '४. परिवार' : '4. Family'}
          </button>
        </div>
      </div>

      {/* TAB 1: AI ASSISTANT & 10-STEP INTAKE */}
      {activeTab === 'ASSISTANT' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Intake Input Form */}
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5">
            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="text-teal-700" size={20} />
                  {language === 'hi' ? 'लक्षण जांच एवं सुरक्षित ट्राइएज' : 'Symptom Intake & Safety Screening'}
                </h3>
                <span className="text-[11px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200">
                  {language === 'hi' ? 'बोलें या टाइप करें' : 'Voice or Typed Input'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {language === 'hi' 
                  ? 'अपनी भाषा में बताएं कि आपको क्या समस्या है। आपातकालीन स्थिति में तुरंत 112 सहायता मिलेगी।'
                  : 'Describe your symptoms in Hindi or English. Conservative emergency protocols run deterministically.'
                }
              </p>
            </div>

            {/* Quick Sample Chips */}
            <div className="space-y-1.5">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                {language === 'hi' ? 'उदाहरण के लिए क्लिक करें:' : 'Quick Demo Scenarios:'}
              </div>
              <div className="flex flex-wrap gap-2">
                {samplePrompts.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setSymptomText(p.text)}
                    className="text-xs bg-slate-50 hover:bg-teal-50 hover:text-teal-900 hover:border-teal-300 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 transition text-left"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Form */}
            <form onSubmit={handleIntakeSubmit} className="space-y-3">
              <div className="relative">
                <textarea
                  rows={3}
                  value={symptomText}
                  onChange={(e) => setSymptomText(e.target.value)}
                  placeholder={language === 'hi' 
                    ? 'उदा. "मुझे 2 घंटे से सीने में भारीपन लग रहा है और सांस फूल रही है..."' 
                    : 'e.g. "I have severe chest discomfort and feeling breathless for the past 2 hours..."'
                  }
                  className="w-full rounded-xl border border-slate-300 p-3.5 pr-12 text-sm focus:border-teal-600 focus:ring-1 focus:ring-teal-600 outline-none transition"
                />
                <button
                  type="button"
                  onClick={handleVoiceInput}
                  className={`absolute right-3 top-3 p-2 rounded-lg transition ${
                    isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-slate-100 text-slate-600 hover:bg-teal-100 hover:text-teal-700'
                  }`}
                  title={isListening ? 'Listening...' : 'Click to Speak'}
                >
                  <Mic size={18} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-500 flex items-center gap-1">
                  <Shield size={13} className="text-teal-700" />
                  <span>
                    {language === 'hi' ? 'चिकित्सकीय सुरक्षा नियम सक्रिय' : 'Deterministic clinical safety engine active'}
                  </span>
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting || !symptomText.trim()}
                  className="bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-bold text-sm px-5 py-2.5 rounded-xl flex items-center gap-2 transition shadow-sm"
                >
                  {isSubmitting ? (
                    <Clock className="animate-spin" size={16} />
                  ) : (
                    <Send size={16} />
                  )}
                  <span>{language === 'hi' ? 'जांच करें (Triage)' : 'Analyze & Screen'}</span>
                </button>
              </div>
            </form>

            {/* EMERGENCY WARNING BANNER (Scenario E) */}
            {triageResponse && triageResponse.is_emergency && (
              <div className="bg-red-50 border-2 border-red-500 rounded-2xl p-5 space-y-3 animate-fade-in shadow-md">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-red-600 text-white flex items-center justify-center shrink-0">
                    <AlertTriangle size={24} />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="bg-red-600 text-white text-[11px] font-black uppercase px-2 py-0.5 rounded tracking-wide">
                        EMERGENCY PROTOCOL TRIGGERED
                      </span>
                      <span className="text-xs font-bold text-red-900">
                        {language === 'hi' ? 'तत्काल आपातकालीन सहायता' : 'Immediate Emergency Assistance'}
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-red-900 leading-relaxed">
                      {triageResponse.emergency_advice}
                    </p>
                  </div>
                </div>

                <div className="bg-white/80 rounded-xl p-3 border border-red-200 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-xs text-red-700 font-bold uppercase">National Emergency Services (India)</div>
                    <div className="text-2xl font-black text-red-600 flex items-center gap-2">
                      <PhoneCall size={22} />
                      112 / 108
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-600">Nearest Emergency Ready Facility:</div>
                    <div className="text-sm font-bold text-slate-900">
                      Paud CHC (4.2 km - 12 mins) • 24x7 Doctor & ECG Ready
                    </div>
                  </div>
                </div>

                <div className="text-xs text-red-800 bg-red-100/60 p-2.5 rounded-lg border border-red-200">
                  <span className="font-bold">Clinical Advisory:</span> Do not wait for routine OPD appointments. Go directly to emergency casualty or call 112 for rural ambulance dispatch.
                </div>
              </div>
            )}

            {/* ROUTINE / URGENT RECOMMENDATION RESULT */}
            {triageResponse && !triageResponse.is_emergency && (
              <div className="bg-teal-50 border border-teal-200 rounded-2xl p-5 space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center">
                      <CheckCircle2 size={22} />
                    </div>
                    <div>
                      <span className="bg-teal-700 text-white text-[10px] font-bold uppercase px-2 py-0.5 rounded">
                        Triage: {triageResponse.triage_level}
                      </span>
                      <h4 className="text-base font-bold text-slate-900 mt-1">
                        {triageResponse.primary_complaint}
                      </h4>
                    </div>
                  </div>
                  <div className="text-right text-xs">
                    <span className="text-slate-500">Specialty: </span>
                    <span className="font-bold text-teal-800">{triageResponse.recommended_specialty}</span>
                  </div>
                </div>

                <p className="text-sm text-slate-700 bg-white/70 p-3 rounded-xl border border-teal-100 leading-relaxed">
                  {triageResponse.explanation_patient}
                </p>

                {/* Structured Doctor Summary */}
                <div className="bg-white rounded-xl p-3 border border-slate-200 space-y-1">
                  <div className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
                    <Info size={12} className="text-teal-700" />
                    Doctor-Facing Structured Intake Summary:
                  </div>
                  <p className="text-xs font-mono text-slate-700 bg-slate-50 p-2 rounded">
                    {triageResponse.ai_doctor_summary}
                  </p>
                </div>

                {/* Action to book */}
                <div className="pt-2 flex items-center justify-between border-t border-teal-200/60">
                  <div className="text-xs text-teal-900">
                    Recommended: <strong>{triageResponse.recommended_facility_type}</strong>
                  </div>
                  <button
                    onClick={() => handleBookDemoAppointment(1)}
                    className="bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-4 py-2 rounded-xl flex items-center gap-1.5 transition shadow-sm"
                  >
                    <span>{language === 'hi' ? 'CHC पौड में अपॉइंटमेंट बुक करें' : 'Book at Paud CHC'}</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            )}

            {/* Booking Success Toast */}
            {bookingSuccess && (
              <div className="bg-emerald-50 border border-emerald-300 rounded-xl p-4 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="text-emerald-600 shrink-0" size={24} />
                  <div>
                    <div className="text-sm font-bold text-emerald-900">
                      Appointment Booked Successfully! Token: {bookingSuccess.queue_token}
                    </div>
                    <div className="text-xs text-emerald-700 font-mono">
                      Code: {bookingSuccess.appointment_code} • {bookingSuccess.scheduled_date} ({bookingSuccess.scheduled_time})
                    </div>
                  </div>
                </div>
                <span className="text-[11px] bg-emerald-200 text-emerald-900 px-2.5 py-1 rounded-md font-semibold">
                  Saved in Record
                </span>
              </div>
            )}
          </div>

          {/* Right Rail: Verified Facility Readiness Snapshot */}
          <div className="space-y-4">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <MapPin className="text-teal-700" size={18} />
                  {language === 'hi' ? 'निकटतम स्वास्थ्य केंद्र' : 'Nearest Ready Facilities'}
                </h3>
                <span className="text-[11px] text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Live Status
                </span>
              </div>

              <div className="space-y-3">
                {facilities.map((fac) => (
                  <div
                    key={fac.id}
                    onClick={() => setSelectedFacility(fac)}
                    className={`p-3.5 rounded-xl border text-xs cursor-pointer transition space-y-2 ${
                      selectedFacility?.id === fac.id 
                        ? 'border-teal-600 bg-teal-50/60 shadow-sm' 
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-bold text-slate-900 text-sm leading-tight">{fac.name}</span>
                      <span className="bg-teal-100 text-teal-800 text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0">
                        {fac.facility_type}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-slate-500">
                      <span>{fac.distance_km} km ({fac.travel_time_mins} min)</span>
                      <span>•</span>
                      <span className="text-emerald-700 font-semibold">{fac.available_doctors_count} Doctor on Duty</span>
                    </div>

                    {/* Honest Test Availability Indicator (Scenario B) */}
                    <div className="pt-1 border-t border-slate-100 space-y-1">
                      <div className="text-[11px] text-slate-600 flex items-center justify-between">
                        <span>ECG:</span>
                        <span className={fac.diagnostic_tests_available.includes('Electrocardiogram (ECG)') ? 'text-emerald-700 font-bold' : 'text-slate-400'}>
                          {fac.diagnostic_tests_available.includes('Electrocardiogram (ECG)') ? 'Available ✓' : 'Unavailable ✕'}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-600 flex items-center justify-between">
                        <span>Ultrasound (USG):</span>
                        <span className={fac.diagnostic_tests_available.includes('Ultrasound Abdomen (USG)') ? 'text-emerald-700 font-bold' : 'text-amber-700 font-semibold'}>
                          {fac.diagnostic_tests_available.includes('Ultrasound Abdomen (USG)') ? 'Available ✓' : 'Lacking (Referral to DH)'}
                        </span>
                      </div>
                      {/* Medicine Stock (Scenario C) */}
                      <div className="text-[11px] text-slate-600 flex items-center justify-between">
                        <span>Amlodipine (BP):</span>
                        <span className={fac.medicine_stock_summary['Amlodipine'] === 'IN_STOCK' ? 'text-emerald-700 font-bold' : 'text-red-600 font-bold'}>
                          {fac.medicine_stock_summary['Amlodipine'] === 'IN_STOCK' ? 'In Stock' : 'Out of Stock ✕'}
                        </span>
                      </div>
                    </div>

                    <div className="text-[10px] text-slate-400 text-right">
                      {fac.freshness_label}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ABHA Consent & Data Sharing Card */}
            <div className="bg-gradient-to-br from-teal-900 to-teal-950 text-white rounded-2xl p-4 space-y-2.5 shadow-sm">
              <div className="flex items-center gap-2">
                <Shield className="text-teal-300" size={16} />
                <h4 className="text-xs font-bold uppercase tracking-wider text-teal-200">ABDM Consent Architecture</h4>
              </div>
              <p className="text-xs text-teal-100 leading-relaxed">
                Health records are encrypted and shared strictly upon patient-verified consent with assigned ASHA worker & attending MO.
              </p>
              <div className="text-[11px] text-teal-300 flex items-center justify-between pt-1 border-t border-teal-800">
                <span>Active Consents: 2 (Dr. Deshmukh, ASHA Patil)</span>
                <span className="underline cursor-pointer hover:text-white">Manage</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DETAILED HOSPITAL READINESS VIEW */}
      {activeTab === 'FACILITIES' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                {language === 'hi' ? 'अस्पताल संसाधन एवं तैयारी (Hospital Readiness)' : 'Facility Readiness & Resource Availability'}
              </h3>
              <p className="text-xs text-slate-500">
                Transparent verification of doctors, diagnostics, medicine stock, and queue estimates. Never presents fictional data as live.
              </p>
            </div>
            <span className="text-xs font-bold text-teal-800 bg-teal-50 border border-teal-200 px-3 py-1 rounded-lg">
              District: Pune • Taluka: Mulshi
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {facilities.map((f) => (
              <div key={f.id} className="border border-slate-200 rounded-2xl p-5 space-y-4 hover:shadow-md transition">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-bold uppercase">
                      {f.facility_type}
                    </span>
                    <h4 className="text-base font-bold text-slate-900 mt-1">{f.name}</h4>
                    <p className="text-xs text-slate-500">{f.address}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-teal-800">{f.distance_km} km</div>
                    <div className="text-[11px] text-slate-400">~{f.travel_time_mins} mins</div>
                  </div>
                </div>

                <div className="bg-slate-50 rounded-xl p-3 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Operating Hours:</span>
                    <span className="font-semibold text-slate-800">{f.operating_hours}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Est. Queue Wait:</span>
                    <span className="font-semibold text-slate-800">{f.estimated_queue_wait_mins} mins</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Doctors on Duty:</span>
                    <span className="font-semibold text-emerald-700">{f.available_doctors_count} Available</span>
                  </div>
                </div>

                {/* Diagnostics List */}
                <div className="space-y-1.5">
                  <div className="text-xs font-bold text-slate-700">Diagnostic Tests:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {f.diagnostic_tests_available.map((t, idx) => (
                      <span key={idx} className="bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-semibold px-2 py-0.5 rounded">
                        ✓ {t.split('(')[0]}
                      </span>
                    ))}
                    {f.diagnostic_tests_missing.map((t, idx) => (
                      <span key={idx} className="bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-semibold px-2 py-0.5 rounded">
                        ✕ {t.split('(')[0]} (DH Only)
                      </span>
                    ))}
                  </div>
                </div>

                {/* Medicine Stock Status */}
                <div className="space-y-1.5 pt-2 border-t border-slate-100">
                  <div className="text-xs font-bold text-slate-700">Medicine Stock:</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {Object.entries(f.medicine_stock_summary).map(([med, st], idx) => (
                      <div key={idx} className="flex items-center justify-between bg-slate-50 p-1.5 rounded border border-slate-200">
                        <span className="truncate">{med}</span>
                        <span className={`text-[10px] font-bold ${st === 'IN_STOCK' ? 'text-emerald-700' : 'text-rose-600'}`}>
                          {st === 'IN_STOCK' ? 'In Stock' : 'Out'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between text-xs text-slate-400">
                  <span>{f.freshness_label}</span>
                  <button
                    onClick={() => handleBookDemoAppointment(f.id)}
                    className="bg-teal-700 hover:bg-teal-800 text-white font-bold px-3 py-1.5 rounded-lg transition"
                  >
                    Select
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: DIGITAL CARE TIMELINE (Step 9) */}
      {activeTab === 'TIMELINE' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                {language === 'hi' ? 'डिजिटल स्वास्थ्य टाइमलाइन (Digital Health Timeline)' : 'Chronological Care Journey Timeline'}
              </h3>
              <p className="text-xs text-slate-500">
                Audited chronological log of consultations, referrals, orders, prescriptions, and follow-up activities.
              </p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-700 font-semibold px-3 py-1 rounded-lg">
              Patient: Ramesh Kumar ({patient?.abha_id})
            </span>
          </div>

          <div className="relative border-l-2 border-teal-600 ml-4 space-y-6 pl-6">
            {timeline.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No timeline events recorded yet.</p>
            ) : (
              timeline.map((ev) => (
                <div key={ev.id} className="relative space-y-1">
                  <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-teal-600 border-2 border-white shadow-sm" />
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-teal-900 uppercase tracking-wide">
                      {ev.event_type} • {ev.actor_name} ({ev.actor_role})
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {new Date(ev.created_at).toLocaleString()}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-800">{ev.title}</h4>
                  <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                    {ev.description}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 4: FAMILY HEALTH MANAGEMENT */}
      {activeTab === 'FAMILY' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                {language === 'hi' ? 'पारिवारिक स्वास्थ्य प्रबंधन (Family Health)' : 'Family Members & Household Health'}
              </h3>
              <p className="text-xs text-slate-500">
                Manage dependents, elderly parents, and child immunization under unified rural household card.
              </p>
            </div>
            <button className="bg-teal-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-teal-800 transition">
              + Add Family Member
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-slate-200 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900">Meena Kumar</span>
                <span className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-semibold">Spouse (44y)</span>
              </div>
              <p className="text-xs text-slate-500">Chronic Conditions: None reported</p>
              <div className="text-xs text-emerald-700 font-medium">✓ Anemia Screening up to date</div>
            </div>

            <div className="border border-slate-200 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900">Aakash Kumar</span>
                <span className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-semibold">Child (19y)</span>
              </div>
              <p className="text-xs text-slate-500">Chronic Conditions: Asthma (Mild)</p>
              <div className="text-xs text-teal-700 font-medium">Inhaler prescription active</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
