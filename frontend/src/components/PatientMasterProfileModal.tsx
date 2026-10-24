import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  X, User, ShieldCheck, HeartPulse, Activity, AlertCircle, FileText, 
  Calendar, CheckCircle2, Clock, Sparkles, Stethoscope, Pill, MapPin
} from 'lucide-react';

interface PatientMasterProfileModalProps {
  patientId: number | null;
  onClose: () => void;
  language: 'hi' | 'en';
}

export const PatientMasterProfileModal: React.FC<PatientMasterProfileModalProps> = ({
  patientId,
  onClose,
  language
}) => {
  const [profile, setProfile] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'appointments' | 'reports' | 'followups' | 'ai_summary'>('timeline');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [aiSummary, setAiSummary] = useState<any>(null);
  const [isGeneratingAi, setIsGeneratingAi] = useState<boolean>(false);
  const [reportExplanation, setReportExplanation] = useState<{ [key: number]: any }>({});
  const [explainingReportId, setExplainingReportId] = useState<number | null>(null);

  useEffect(() => {
    if (!patientId) return;
    setIsLoading(true);
    api.getPatientMasterProfile(patientId)
      .then((data) => {
        setProfile(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load profile:', err);
        setIsLoading(false);
      });
  }, [patientId]);

  if (!patientId) return null;

  const handleGenerateAiBrief = async () => {
    setIsGeneratingAi(true);
    try {
      const res = await api.getAIPatientSummary(patientId);
      setAiSummary(res);
      setActiveTab('ai_summary');
    } catch (err: any) {
      alert('Failed to generate AI brief: ' + err.message);
    } finally {
      setIsGeneratingAi(false);
    }
  };

  const handleExplainReport = async (reportId: number, audience: string) => {
    setExplainingReportId(reportId);
    try {
      const res = await api.explainReport(reportId, audience);
      setReportExplanation((prev) => ({ ...prev, [reportId]: res }));
    } catch (err: any) {
      alert('Failed to explain report: ' + err.message);
    } finally {
      setExplainingReportId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden border border-slate-200">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-teal-900 via-teal-800 to-emerald-900 text-white p-6 flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-teal-700/80 border border-teal-500/40 flex items-center justify-center text-white text-2xl font-black shadow-inner">
              {profile?.patient?.name?.charAt(0) || 'P'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-black tracking-tight">{profile?.patient?.name || 'Loading Patient...'}</h2>
                <span className="text-xs font-mono bg-white/20 px-2 py-0.5 rounded text-teal-100">
                  {profile?.external_id || profile?.patient?.abha_id || 'ID'}
                </span>
                <span className="text-xs bg-emerald-400 text-emerald-950 font-bold px-2 py-0.5 rounded-full">
                  {profile?.patient?.care_status || 'ROUTINE'}
                </span>
              </div>
              <p className="text-xs text-teal-200 flex items-center gap-3 mt-1">
                <span>{profile?.patient?.age} Yrs, {profile?.patient?.gender}</span>
                <span>•</span>
                <span className="flex items-center gap-1"><MapPin size={12} /> {profile?.patient?.village}</span>
                <span>•</span>
                <span>Blood: <strong>{profile?.blood_group || 'O+'}</strong></span>
                <span>•</span>
                <span>Phone: {profile?.patient?.phone}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleGenerateAiBrief}
              disabled={isGeneratingAi}
              className="text-xs bg-amber-400 hover:bg-amber-300 text-amber-950 font-bold px-3 py-1.5 rounded-xl shadow-md transition flex items-center gap-1.5"
            >
              <Sparkles size={14} className={isGeneratingAi ? 'animate-spin' : ''} />
              {isGeneratingAi ? 'Generating...' : 'AI Care Brief'}
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Provenance & Medical Conditions Ribbon */}
        <div className="bg-slate-50 border-b border-slate-200 px-6 py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-500 font-semibold">Conditions:</span>
            <span className="font-bold text-slate-800 bg-white px-2 py-0.5 rounded border border-slate-200">
              {profile?.conditions || 'None'}
            </span>
            <span className="text-slate-500 font-semibold ml-2">Meds:</span>
            <span className="font-medium text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">
              {profile?.current_medication || 'None'}
            </span>
            <span className="text-slate-500 font-semibold ml-2">Allergies:</span>
            <span className="text-rose-700 font-medium bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
              {profile?.allergies || 'No known allergies'}
            </span>
          </div>

          {/* Provenance Indicators */}
          <div className="flex items-center gap-2 font-mono text-[11px]">
            <span className="bg-sky-100 text-sky-800 px-2 py-0.5 rounded border border-sky-200 font-semibold">
              📁 {profile?.provenance_counts?.imported_records || 0} Imported Records
            </span>
            <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
              🩺 {profile?.provenance_counts?.clinician_entered || 0} Clinician Notes
            </span>
            <span className="bg-purple-100 text-purple-800 px-2 py-0.5 rounded border border-purple-200 font-semibold">
              🤖 {profile?.provenance_counts?.ai_summaries || 0} AI Syntheses
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 px-6 bg-white gap-4 text-xs font-bold">
          <button
            onClick={() => setActiveTab('timeline')}
            className={`py-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'timeline'
                ? 'border-teal-700 text-teal-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Clock size={14} /> Care Timeline ({profile?.timeline_events?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('appointments')}
            className={`py-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'appointments'
                ? 'border-teal-700 text-teal-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Calendar size={14} /> Appointments ({profile?.appointments?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('reports')}
            className={`py-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'reports'
                ? 'border-teal-700 text-teal-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <FileText size={14} /> Diagnostic Reports ({profile?.reports?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('followups')}
            className={`py-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'followups'
                ? 'border-teal-700 text-teal-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Activity size={14} /> Follow-ups & Alerts ({profile?.follow_up_plans?.length || 0})
          </button>
          {aiSummary && (
            <button
              onClick={() => setActiveTab('ai_summary')}
              className={`py-3 border-b-2 transition flex items-center gap-1.5 ${
                activeTab === 'ai_summary'
                  ? 'border-amber-600 text-amber-800'
                  : 'border-transparent text-amber-600 hover:text-amber-800'
              }`}
            >
              <Sparkles size={14} /> Grounded AI Summary
            </button>
          )}
        </div>

        {/* Tab Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {isLoading ? (
            <div className="text-center py-12 text-slate-500">Loading master patient record...</div>
          ) : (
            <>
              {/* TAB 1: CARE TIMELINE */}
              {activeTab === 'timeline' && (
                <div className="space-y-3">
                  {profile?.timeline_events?.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No timeline events recorded yet.</p>
                  ) : (
                    profile?.timeline_events?.map((ev: any) => (
                      <div key={ev.id} className="p-3.5 rounded-2xl border border-slate-200 bg-slate-50/60 flex items-start gap-3">
                        <div className="w-8 h-8 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                          {ev.event_type === 'INTAKE' && '📝'}
                          {ev.event_type === 'APPOINTMENT' && '📅'}
                          {ev.event_type === 'CONSULTATION' && '🩺'}
                          {ev.event_type === 'DIAGNOSTIC' && '🔬'}
                          {ev.event_type === 'FOLLOW_UP' && '🔔'}
                          {ev.event_type === 'HOME_VISIT' && '🏠'}
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-900 text-xs">{ev.title}</span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              {new Date(ev.created_at).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600">{ev.description}</p>
                          <div className="text-[10px] text-slate-400 flex items-center gap-2">
                            <span>Recorded by: <strong>{ev.actor_name}</strong></span>
                            <span>•</span>
                            <span className="bg-slate-200 text-slate-700 px-1.5 py-0.2 rounded font-mono">{ev.actor_role}</span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* TAB 2: APPOINTMENTS */}
              {activeTab === 'appointments' && (
                <div className="space-y-3">
                  {profile?.appointments?.map((apt: any) => (
                    <div key={apt.id} className="p-4 rounded-2xl border border-slate-200 bg-white flex items-center justify-between shadow-sm">
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-black text-slate-900">{apt.appointment_code}</span>
                          <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                            apt.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' :
                            apt.status === 'CANCELLED' ? 'bg-rose-100 text-rose-800' :
                            'bg-amber-100 text-amber-800'
                          }`}>
                            {apt.status}
                          </span>
                          <span className="text-[10px] font-mono bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded">
                            Token: {apt.queue_token}
                          </span>
                        </div>
                        <p className="text-slate-600">Date: <strong>{apt.scheduled_date}</strong> at {apt.scheduled_time} • {apt.consultation_type}</p>
                        <p className="text-slate-500">Reason: {apt.reason || 'General checkup'}</p>
                      </div>
                      <div className="text-right text-xs">
                        <span className="text-slate-400 block text-[10px]">ID: {apt.external_id || apt.id}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* TAB 3: DIAGNOSTIC REPORTS */}
              {activeTab === 'reports' && (
                <div className="space-y-4">
                  {profile?.reports?.map((rep: any) => (
                    <div key={rep.id} className="p-4 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-sm">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-black text-slate-900 text-sm">{rep.report_type}</span>
                            <span className="text-[10px] font-mono bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded">
                              {rep.external_id}
                            </span>
                            {rep.is_abnormal && (
                              <span className="bg-rose-100 text-rose-800 text-[10px] font-bold px-2 py-0.5 rounded">
                                ⚠️ Abnormal Finding
                              </span>
                            )}
                            {rep.doctor_reviewed ? (
                              <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded">
                                ✓ Clinician Reviewed
                              </span>
                            ) : (
                              <span className="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded">
                                Review Pending
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">Report Date: {rep.report_date}</p>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleExplainReport(rep.id, 'PATIENT')}
                            disabled={explainingReportId === rep.id}
                            className="text-[11px] bg-teal-50 hover:bg-teal-100 text-teal-800 font-bold px-2.5 py-1 rounded-lg border border-teal-200 transition"
                          >
                            {explainingReportId === rep.id ? 'Explaining...' : '🗣️ Hindi/Easy Explanation'}
                          </button>
                        </div>
                      </div>

                      <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
                        <strong className="text-slate-800 block mb-0.5">Laboratory Findings:</strong>
                        <p className="text-slate-700 font-mono text-[11px]">{rep.findings}</p>
                        <p className="text-[11px] text-amber-800 mt-1.5">Action Note: {rep.ai_action_note}</p>
                      </div>

                      {/* Display AI Explanation if generated */}
                      {reportExplanation[rep.id] && (
                        <div className="bg-amber-50/70 p-3.5 rounded-xl border border-amber-300 text-xs space-y-1.5">
                          <div className="flex items-center justify-between text-amber-900 font-bold">
                            <span className="flex items-center gap-1.5"><Sparkles size={14} /> AI Patient Explanation</span>
                            <span className="text-[10px] font-mono text-amber-700">Grounded Citation: {reportExplanation[rep.id].citations?.join(', ')}</span>
                          </div>
                          <p className="text-slate-800 whitespace-pre-line text-[11px] leading-relaxed">
                            {reportExplanation[rep.id].content}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* TAB 4: FOLLOW-UPS & ALERTS */}
              {activeTab === 'followups' && (
                <div className="space-y-4">
                  {/* Active Alerts */}
                  {profile?.alerts?.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-rose-900 uppercase tracking-wide flex items-center gap-1.5">
                        <AlertCircle size={14} className="text-rose-600" /> Active Continuity Monitoring Alerts
                      </h4>
                      {profile?.alerts?.map((al: any) => (
                        <div key={al.id} className="p-3 rounded-xl border border-rose-200 bg-rose-50/70 text-xs space-y-1">
                          <div className="flex items-center justify-between font-bold">
                            <span className="text-rose-900">{al.title}</span>
                            <span className="px-2 py-0.5 rounded text-[10px] bg-rose-600 text-white font-mono">
                              {al.priority} • {al.status}
                            </span>
                          </div>
                          <p className="text-rose-800 text-[11px]">{al.description}</p>
                          <p className="text-[10px] text-rose-600 font-mono">Rule: {al.triggering_rule}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Follow-up Plans */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                      Scheduled Follow-up Care Plans
                    </h4>
                    {profile?.follow_up_plans?.map((fup: any) => (
                      <div key={fup.id} className="p-3.5 rounded-xl border border-slate-200 bg-white text-xs flex items-center justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">{fup.care_type}</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              fup.status === 'OVERDUE' || fup.status === 'MISSED' ? 'bg-rose-100 text-rose-800' :
                              fup.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                            }`}>
                              {fup.status}
                            </span>
                          </div>
                          <p className="text-slate-600">Due Date: <strong>{fup.due_date}</strong></p>
                          <p className="text-slate-500 text-[11px]">{fup.instructions}</p>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">{fup.external_id}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 5: GROUNDED AI SUMMARY */}
              {activeTab === 'ai_summary' && aiSummary && (
                <div className="bg-gradient-to-br from-teal-50 to-emerald-50 p-5 rounded-2xl border border-teal-200 space-y-3">
                  <div className="flex items-center justify-between border-b border-teal-200 pb-2">
                    <div className="flex items-center gap-2">
                      <Sparkles size={16} className="text-teal-700" />
                      <h4 className="text-sm font-bold text-teal-950">Grounded Patient Care Brief</h4>
                    </div>
                    <span className="text-[10px] font-mono bg-teal-100 text-teal-800 px-2 py-0.5 rounded">
                      Model: SwasthyaSetu-GroundedRAG-v1.0
                    </span>
                  </div>

                  <p className="text-xs text-slate-800 whitespace-pre-line leading-relaxed font-sans">
                    {aiSummary.content}
                  </p>

                  <div className="bg-white p-3 rounded-xl border border-teal-200 text-[11px] space-y-1">
                    <strong className="text-teal-900 block font-mono">Source Provenance Record Citations:</strong>
                    <div className="flex flex-wrap gap-1.5">
                      {aiSummary.citations?.map((cit: string, idx: number) => (
                        <span key={idx} className="bg-slate-100 text-slate-700 border border-slate-300 px-2 py-0.5 rounded text-[10px] font-mono">
                          {cit}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">
            Authorized Medical Record Access • Audited Access Logged
          </span>
          <button
            onClick={onClose}
            className="text-xs bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold px-4 py-2 rounded-xl transition"
          >
            Close Profile
          </button>
        </div>

      </div>
    </div>
  );
};
