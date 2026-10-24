import React, { useState, useEffect } from 'react';
import { Appointment, Patient, CareTimelineEvent } from '../types';
import { api } from '../services/api';
import { PatientMasterProfileModal } from './PatientMasterProfileModal';
import { 
  Stethoscope, Users, FileText, CheckCircle2, Clock, 
  AlertTriangle, Pill, Activity, Calendar, ShieldCheck, ArrowRight
} from 'lucide-react';

interface DoctorPortalProps {
  language: 'hi' | 'en';
}

export const DoctorPortal: React.FC<DoctorPortalProps> = ({ language }) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [selectedApt, setSelectedApt] = useState<Appointment | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [timeline, setTimeline] = useState<CareTimelineEvent[]>([]);
  const [masterProfilePatientId, setMasterProfilePatientId] = useState<number | null>(null);

  // Encounter Form State
  const [chiefComplaints, setChiefComplaints] = useState<string>('Chest discomfort on exertion, mild shortness of breath');
  const [clinicalNotes, setClinicalNotes] = useState<string>('Vitals stable. Heart sounds S1, S2 audible. No murmurs. Bilateral vesicular breath sounds.');
  const [diagnosis, setDiagnosis] = useState<string>('Mild Atypical Angina / Exertional Fatigue');
  const [vitalBp, setVitalBp] = useState<string>('130/84');
  const [vitalPulse, setVitalPulse] = useState<number>(76);
  const [vitalTemp, setVitalTemp] = useState<number>(98.4);
  const [vitalSpo2, setVitalSpo2] = useState<number>(98);
  const [riskFlag, setRiskFlag] = useState<string>('MODERATE_RISK');

  // Prescriptions & Diagnostics
  const [prescribeMedicine, setPrescribeMedicine] = useState<string>('Paracetamol 500mg');
  const [orderDiagnostics, setOrderDiagnostics] = useState<string[]>(['Electrocardiogram (ECG)']);
  const [followUpDays, setFollowUpDays] = useState<number>(7);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [encounterDone, setEncounterDone] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const apts = await api.getAppointments();
      setAppointments(apts);
      if (apts.length > 0 && !selectedApt) {
        setSelectedApt(apts[0]);
        loadPatientDetails(apts[0].patient_id);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const loadPatientDetails = async (patientId: number) => {
    try {
      const pat = await api.getPatient(patientId, 'dr_deshmukh');
      setPatient(pat);
      const tl = await api.getTimeline(patientId);
      setTimeline(tl);
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectAppointment = (apt: Appointment) => {
    setSelectedApt(apt);
    loadPatientDetails(apt.patient_id);
    setEncounterDone(false);
  };

  const handleToggleDiagnostic = (testName: string) => {
    if (orderDiagnostics.includes(testName)) {
      setOrderDiagnostics(orderDiagnostics.filter(t => t !== testName));
    } else {
      setOrderDiagnostics([...orderDiagnostics, testName]);
    }
  };

  const handleSubmitEncounter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApt || !patient) return;

    setIsSubmitting(true);
    try {
      await api.createEncounter({
        appointment_id: selectedApt.id,
        patient_id: patient.id,
        doctor_id: 1, // Dr. Deshmukh
        facility_id: 1, // Paud CHC
        chief_complaints: chiefComplaints,
        clinical_notes: clinicalNotes,
        diagnosis: diagnosis,
        vital_bp: vitalBp,
        vital_pulse: vitalPulse,
        vital_temp: vitalTemp,
        vital_spo2: vitalSpo2,
        clinician_risk_flag: riskFlag,
        prescriptions: [
          {
            medicine_name: prescribeMedicine,
            dosage: prescribeMedicine.includes('Paracetamol') ? '500mg' : '5mg',
            frequency: 'Twice daily after food',
            duration_days: 5,
            instructions: 'Take with warm water'
          }
        ],
        diagnostic_test_names: orderDiagnostics,
        follow_up_days: followUpDays,
        follow_up_instructions: `Review in ${followUpDays} days with completed reports.`
      }, 'dr_deshmukh');

      setEncounterDone(true);
      await loadData();
      alert('Consultation encounter, digital prescription & follow-up saved to patient timeline!');
    } catch (err: any) {
      alert('Failed to save encounter: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Doctor Header Banner */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-xl border border-teal-200">
            D
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">Dr. Anand Deshmukh, MD</h2>
              <span className="bg-teal-100 text-teal-900 text-xs px-2.5 py-0.5 rounded-full font-semibold border border-teal-200">
                Medical Officer / Physician
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Paud Community Health Centre (CHC) • OPD Hours: 08:30 AM - 02:00 PM • Teleconsult Available
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-600">
          <ShieldCheck className="text-teal-700" size={16} />
          <span>ABDM Clinician Registration: <strong className="text-slate-800">MCI-MH-49201</strong></span>
        </div>
      </div>

      {/* Main Grid: Queue on Left, Encounter on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Daily Consultation Queue */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Clock className="text-teal-700" size={18} />
              {language === 'hi' ? 'दैनिक ओपीडी कतार' : 'Today\'s OPD Queue'}
            </h3>
            <span className="text-xs font-semibold bg-teal-50 text-teal-800 px-2.5 py-0.5 rounded border border-teal-200">
              {appointments.length} Registered
            </span>
          </div>

          <div className="space-y-2.5">
            {appointments.map((apt) => {
              const isSelected = selectedApt?.id === apt.id;
              return (
                <div
                  key={apt.id}
                  onClick={() => handleSelectAppointment(apt)}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition space-y-1.5 ${
                    isSelected ? 'border-teal-600 bg-teal-50/60 shadow-sm' : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{apt.patient_name || 'Patient'}</span>
                    <span className="bg-teal-700 text-white font-mono font-bold text-[10px] px-2 py-0.5 rounded">
                      {apt.queue_token}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Reason: {apt.reason || 'General Health Consultation'}
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span>{apt.scheduled_date} ({apt.scheduled_time})</span>
                    <span className={`font-semibold ${apt.status === 'COMPLETED' ? 'text-emerald-700' : 'text-amber-700'}`}>
                      {apt.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right 2 Columns: Clinical Encounter Workspace */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
            <div>
              <span className="text-[10px] bg-slate-100 text-slate-600 font-bold uppercase px-2 py-0.5 rounded">
                Active Consultation Record
              </span>
              <h3 className="text-lg font-bold text-slate-900 mt-1">
                {patient ? `${patient.name} (${patient.age}y / ${patient.gender})` : 'Select a patient'}
              </h3>
              <p className="text-xs text-slate-500 font-mono">
                ABHA ID: {patient?.abha_id} • Village: {patient?.village}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs bg-emerald-50 text-emerald-800 font-semibold px-2.5 py-1 rounded border border-emerald-200">
                ✓ Consent Authorized
              </span>
              {patient && (
                <button
                  type="button"
                  onClick={() => setMasterProfilePatientId(patient.id)}
                  className="flex items-center gap-1.5 px-3 py-1 bg-teal-700 hover:bg-teal-800 text-white rounded-lg text-xs font-semibold shadow-sm transition"
                >
                  <FileText size={13} />
                  <span>{language === 'hi' ? 'संपूर्ण मास्टर प्रोफाइल एवं लैब्स' : 'Master Profile & Lab Reports'}</span>
                </button>
              )}
            </div>
          </div>

          {/* AI Intake Summary Banner */}
          <div className="bg-teal-50/80 border border-teal-200 rounded-xl p-3.5 space-y-1 text-xs">
            <div className="font-bold text-teal-900 flex items-center gap-1.5">
              <Activity size={14} />
              AI Assistant Structured Intake Summary:
            </div>
            <p className="text-slate-700 leading-relaxed font-mono text-[11px] bg-white/80 p-2 rounded border border-teal-100">
              "Patient Ramesh Kumar (48y/M) presented with acute chest heaviness on walking with dyspnea. Duration: 1-2 days. Triage screened: ECG evaluation recommended. Mild hypertension history."
            </p>
          </div>

          {/* Clinical Encounter Form */}
          <form onSubmit={handleSubmitEncounter} className="space-y-4">
            {/* Vitals Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
              <div>
                <label className="text-slate-500 font-medium">Blood Pressure:</label>
                <input
                  type="text"
                  value={vitalBp}
                  onChange={(e) => setVitalBp(e.target.value)}
                  className="w-full font-mono font-bold text-slate-900 bg-white border border-slate-300 rounded px-2 py-1 mt-0.5"
                />
              </div>
              <div>
                <label className="text-slate-500 font-medium">Pulse (bpm):</label>
                <input
                  type="number"
                  value={vitalPulse}
                  onChange={(e) => setVitalPulse(Number(e.target.value))}
                  className="w-full font-mono font-bold text-slate-900 bg-white border border-slate-300 rounded px-2 py-1 mt-0.5"
                />
              </div>
              <div>
                <label className="text-slate-500 font-medium">Temp (°F):</label>
                <input
                  type="number"
                  step="0.1"
                  value={vitalTemp}
                  onChange={(e) => setVitalTemp(Number(e.target.value))}
                  className="w-full font-mono font-bold text-slate-900 bg-white border border-slate-300 rounded px-2 py-1 mt-0.5"
                />
              </div>
              <div>
                <label className="text-slate-500 font-medium">SpO2 (%):</label>
                <input
                  type="number"
                  value={vitalSpo2}
                  onChange={(e) => setVitalSpo2(Number(e.target.value))}
                  className="w-full font-mono font-bold text-slate-900 bg-white border border-slate-300 rounded px-2 py-1 mt-0.5"
                />
              </div>
            </div>

            {/* Diagnosis & Risk Flag */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2 space-y-1">
                <label className="text-xs font-bold text-slate-700">Diagnosis / Clinical Impression:</label>
                <input
                  type="text"
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  required
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-xl outline-none focus:border-teal-600 font-medium"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-700">Clinician Risk Flag:</label>
                <select
                  value={riskFlag}
                  onChange={(e) => setRiskFlag(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-xl outline-none focus:border-teal-600 bg-white font-semibold"
                >
                  <option value="NORMAL">Normal / Low Risk</option>
                  <option value="MODERATE_RISK">Moderate Risk (Follow-up)</option>
                  <option value="HIGH_RISK">High Risk (Escalate)</option>
                </select>
              </div>
            </div>

            {/* Examination Notes */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-700">Clinical Examination & Doctor's Notes:</label>
              <textarea
                rows={2}
                value={clinicalNotes}
                onChange={(e) => setClinicalNotes(e.target.value)}
                className="w-full text-xs p-2.5 border border-slate-300 rounded-xl outline-none focus:border-teal-600"
              />
            </div>

            {/* Digital Prescription (with stock verification) */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <Pill size={14} className="text-teal-700" />
                  Digital Prescription Entry
                </span>
                <span className="text-[11px] text-slate-500">
                  Linked to Paud CHC Dispensary
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <select
                  value={prescribeMedicine}
                  onChange={(e) => setPrescribeMedicine(e.target.value)}
                  className="text-xs p-2 border border-slate-300 rounded-lg outline-none bg-white font-medium"
                >
                  <option value="Paracetamol 500mg">Paracetamol 500mg (In Stock ✓)</option>
                  <option value="Metformin 500mg">Metformin 500mg (In Stock ✓)</option>
                  <option value="Amlodipine 5mg">Amlodipine 5mg (OUT OF STOCK - Scenario C)</option>
                  <option value="Oral Rehydration Salts (ORS)">Oral Rehydration Salts (In Stock ✓)</option>
                </select>

                {prescribeMedicine.includes('Amlodipine') && (
                  <span className="text-xs text-rose-700 font-bold bg-rose-50 border border-rose-200 px-2 py-1 rounded">
                    ⚠ Warning: Amlodipine 5mg currently out-of-stock at Paud CHC. Available at Aundh DH (26 km).
                  </span>
                )}
              </div>
            </div>

            {/* Diagnostics Orders (with facility availability check) */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <Activity size={14} className="text-teal-700" />
                  Order Diagnostic Investigations
                </span>
                <span className="text-[11px] text-slate-500">
                  Scenario B: USG requires District referral
                </span>
              </div>

              <div className="flex flex-wrap gap-2 text-xs">
                {['Electrocardiogram (ECG)', 'Complete Blood Count (CBC)', 'Fasting Blood Sugar (FBS)', 'Ultrasound Abdomen (USG)'].map((test) => {
                  const isChecked = orderDiagnostics.includes(test);
                  const isMissingAtChc = test.includes('Ultrasound');
                  return (
                    <button
                      key={test}
                      type="button"
                      onClick={() => handleToggleDiagnostic(test)}
                      className={`px-3 py-1.5 rounded-lg border font-medium transition flex items-center gap-1.5 ${
                        isChecked 
                          ? 'bg-teal-700 text-white border-teal-700 shadow-sm' 
                          : 'bg-white text-slate-700 border-slate-300 hover:border-slate-400'
                      }`}
                    >
                      <span>{isChecked ? '✓' : '+'}</span>
                      <span>{test}</span>
                      {isMissingAtChc && (
                        <span className="text-[9px] bg-rose-100 text-rose-800 px-1 rounded ml-1 font-bold">
                          DH Referral
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Follow-up Scheduling */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-teal-50/60 p-3 rounded-xl border border-teal-200">
              <div className="flex items-center gap-2 text-xs">
                <Calendar size={15} className="text-teal-700" />
                <span className="font-bold text-teal-950">Schedule Follow-up Review:</span>
                <select
                  value={followUpDays}
                  onChange={(e) => setFollowUpDays(Number(e.target.value))}
                  className="p-1 border border-teal-300 rounded bg-white text-xs font-semibold"
                >
                  <option value={7}>After 7 Days (Review ECG & BP)</option>
                  <option value={14}>After 14 Days (Routine Check)</option>
                  <option value={30}>After 30 Days (Chronic Diabetic Panel)</option>
                </select>
              </div>
              <span className="text-[11px] text-teal-800">
                Missed review triggers automatic ASHA home-visit task
              </span>
            </div>

            {/* Submit Button */}
            <div className="pt-2 flex items-center justify-end">
              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-teal-700 hover:bg-teal-800 text-white font-bold text-sm px-6 py-2.5 rounded-xl transition shadow-sm flex items-center gap-2"
              >
                <CheckCircle2 size={16} />
                <span>{isSubmitting ? 'Recording Encounter...' : 'Complete Consultation & Issue Orders'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      {masterProfilePatientId && (
        <PatientMasterProfileModal
          patientId={masterProfilePatientId}
          onClose={() => setMasterProfilePatientId(null)}
          language={language}
        />
      )}
    </div>
  );
};
