import React, { useState, useEffect } from 'react';
import { HealthWorkerTask, Patient } from '../types';
import { api } from '../services/api';
import { PatientMasterProfileModal } from './PatientMasterProfileModal';
import { 
  Users, AlertCircle, CheckCircle2, Clock, MapPin, 
  Search, ShieldAlert, FileText, ChevronRight, Check
} from 'lucide-react';

interface AshaPortalProps {
  language: 'hi' | 'en';
}

export const AshaPortal: React.FC<AshaPortalProps> = ({ language }) => {
  const [tasks, setTasks] = useState<HealthWorkerTask[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchVillage, setSearchVillage] = useState<string>('');
  const [selectedTask, setSelectedTask] = useState<HealthWorkerTask | null>(null);
  const [visitNotes, setVisitNotes] = useState<string>('');
  const [outcome, setOutcome] = useState<string>('PATIENT_VISITED_CLINIC');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [accessDeniedMessage, setAccessDeniedMessage] = useState<string | null>(null);
  const [masterProfilePatientId, setMasterProfilePatientId] = useState<number | null>(null);

  const loadData = async () => {
    try {
      const taskList = await api.getTasks();
      setTasks(taskList);
      const patList = await api.getPatients(searchVillage, 'asha_kavita');
      setPatients(patList);
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, [searchVillage]);

  const handleOpenTaskModal = (task: HealthWorkerTask) => {
    setSelectedTask(task);
    setVisitNotes(task.visit_notes || 'Visited patient at home. Checked blood glucose and vital signs.');
  };

  const handleResolveTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask) return;

    setIsSubmitting(true);
    try {
      await api.updateTask(selectedTask.id, {
        status: 'RESOLVED',
        visit_notes: visitNotes,
        outcome: outcome
      }, 'asha_kavita');
      setSelectedTask(null);
      await loadData();
      alert('Task resolved successfully! Dashboard and follow-up records updated.');
    } catch (err: any) {
      alert('Failed to resolve task: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Scenario G: Access Control Test
  const handleTestUnauthorizedAccess = async (targetPatient: Patient) => {
    setAccessDeniedMessage(null);
    try {
      await api.getPatient(targetPatient.id, 'asha_kavita');
      alert('Access granted unexpectedly.');
    } catch (err: any) {
      setAccessDeniedMessage(err.message);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* ASHA Profile & Catchment Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-amber-100 text-amber-800 font-bold flex items-center justify-center text-xl border border-amber-200">
            K
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">Kavita Tai Patil</h2>
              <span className="bg-amber-100 text-amber-900 text-xs px-2.5 py-0.5 rounded-full font-semibold border border-amber-200">
                ASHA Community Health Worker
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Assigned Catchment: <span className="font-semibold text-slate-700">Paud & Pirangut Villages (Mulshi Block)</span> • Sub-Centre: Paud CHC
            </p>
          </div>
        </div>

        {/* Quick Summary Pill */}
        <div className="flex items-center gap-3">
          <div className="bg-rose-50 border border-rose-200 px-3 py-1.5 rounded-xl text-center">
            <div className="text-[10px] uppercase font-bold text-rose-700">Missed Follow-Ups</div>
            <div className="text-lg font-black text-rose-900">
              {tasks.filter(t => t.status === 'OPEN').length}
            </div>
          </div>
          <div className="bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl text-center">
            <div className="text-[10px] uppercase font-bold text-emerald-700">Resolved Visits</div>
            <div className="text-lg font-black text-emerald-900">
              {tasks.filter(t => t.status === 'RESOLVED').length}
            </div>
          </div>
        </div>
      </div>

      {/* ACCESS DENIED ALERT (Scenario G Demo) */}
      {accessDeniedMessage && (
        <div className="bg-rose-50 border-2 border-rose-500 rounded-2xl p-5 space-y-2 shadow-sm animate-fade-in">
          <div className="flex items-center gap-2 text-rose-800 font-bold text-sm">
            <ShieldAlert size={20} className="text-rose-600" />
            <span>Scenario G Demonstration: Access Control & Role Permissions Enforced</span>
          </div>
          <p className="text-xs text-rose-900 font-mono bg-white p-2.5 rounded-lg border border-rose-200">
            {accessDeniedMessage}
          </p>
          <div className="text-[11px] text-rose-700">
            ✓ Security audit event recorded on backend: <code>UNAUTHORIZED_PATIENT_ACCESS_DENIED</code> (Outcome: DENIED).
          </div>
        </div>
      )}

      {/* 2 COLUMN LAYOUT: TASKS & PATIENT ROSTER */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: High Priority Home Visit Tasks (Scenario D) */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <AlertCircle className="text-rose-600" size={18} />
                {language === 'hi' ? 'प्राथमिकता कार्य: छूटे हुए फॉलो-अप (Missed-Care Tasks)' : 'Actionable Missed-Care Tasks'}
              </h3>
              <p className="text-xs text-slate-500">
                Generated automatically when chronic care patients miss their scheduled hospital review.
              </p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-md font-semibold">
              Scenario D
            </span>
          </div>

          <div className="space-y-3">
            {tasks.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No pending tasks.</p>
            ) : (
              tasks.map((task) => (
                <div
                  key={task.id}
                  className={`p-4 rounded-xl border transition space-y-3 ${
                    task.status === 'RESOLVED' 
                      ? 'bg-emerald-50/40 border-emerald-200' 
                      : 'bg-rose-50/30 border-rose-200 hover:border-rose-400'
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${
                          task.status === 'RESOLVED' ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white'
                        }`}>
                          {task.status}
                        </span>
                        <span className="text-sm font-bold text-slate-900">
                          {task.patient_name} ({task.patient_village})
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">
                        Task Type: <span className="font-semibold">{task.task_type}</span> • Due Date: {task.due_date}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setMasterProfilePatientId(task.patient_id)}
                        className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-2.5 py-1.5 rounded-lg transition flex items-center gap-1 border border-slate-300"
                        title="View Master Profile & Grounded AI Care Brief"
                      >
                        <FileText size={12} />
                        <span>Profile & Labs</span>
                      </button>
                      {task.status !== 'RESOLVED' ? (
                        <button
                          onClick={() => handleOpenTaskModal(task)}
                          className="bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition shadow-sm"
                        >
                          Record Home Visit
                        </button>
                      ) : (
                        <span className="text-xs text-emerald-800 font-semibold flex items-center gap-1">
                          <Check size={14} /> Resolved ({task.outcome})
                        </span>
                      )}
                    </div>
                  </div>

                  {task.visit_notes && (
                    <div className="bg-white/80 p-2.5 rounded-lg border border-slate-200 text-xs space-y-1">
                      <span className="font-semibold text-slate-700">Visit Notes:</span>
                      <p className="text-slate-600 italic">{task.visit_notes}</p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Col: Assigned Patients Catchment & Access Control Test */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Users className="text-teal-700" size={18} />
              {language === 'hi' ? 'मरीज़ सूची (Patient Catchment)' : 'Patient Catchment Roster'}
            </h3>
            <p className="text-xs text-slate-500">
              Filter by village or click to test cross-catchment security checks.
            </p>
          </div>

          {/* Village Filter Input */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-slate-400" size={14} />
            <input
              type="text"
              value={searchVillage}
              onChange={(e) => setSearchVillage(e.target.value)}
              placeholder="Filter by village (e.g. Paud, Pirangut)..."
              className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-xl outline-none focus:border-teal-600"
            />
          </div>

          <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
            {patients.map((pat) => {
              const isAssigned = pat.assigned_asha_id === 4; // Kavita's user id is 4
              return (
                <div
                  key={pat.id}
                  className={`p-3 rounded-xl border text-xs space-y-1.5 ${
                    isAssigned ? 'border-slate-200 bg-slate-50/60' : 'border-amber-200 bg-amber-50/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{pat.name}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{pat.village}</span>
                  </div>
                  <p className="text-[11px] text-slate-600">
                    Age: {pat.age}y • Chronic: {pat.chronic_conditions}
                  </p>

                  <div className="pt-1 flex items-center justify-between">
                    <span className={`text-[10px] font-bold ${isAssigned ? 'text-teal-700' : 'text-amber-700'}`}>
                      {isAssigned ? '✓ In Your Catchment' : '⚠ Other Catchment'}
                    </span>
                    {!isAssigned ? (
                      <button
                        onClick={() => handleTestUnauthorizedAccess(pat)}
                        className="bg-amber-600 hover:bg-amber-700 text-white text-[10px] font-bold px-2 py-1 rounded transition"
                        title="Click to trigger Scenario G unauthorized access test"
                      >
                        Test Access (Scenario G)
                      </button>
                    ) : (
                      <button
                        onClick={() => setMasterProfilePatientId(pat.id)}
                        className="text-[10px] text-teal-700 hover:text-teal-900 font-bold underline cursor-pointer"
                      >
                        View Master Record →
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* HOME VISIT RESOLUTION MODAL */}
      {selectedTask && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl border border-slate-200 animate-scale-up">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] bg-rose-100 text-rose-800 font-bold uppercase px-2 py-0.5 rounded">
                  Home Visit Protocol
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1">
                  Record Home Visit: {selectedTask.patient_name}
                </h3>
                <p className="text-xs text-slate-500">
                  Village: {selectedTask.patient_village} • Reason: Missed Chronic Follow-Up
                </p>
              </div>
              <button
                onClick={() => setSelectedTask(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleResolveTask} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-700">Home Visit & Assessment Notes:</label>
                <textarea
                  rows={3}
                  value={visitNotes}
                  onChange={(e) => setVisitNotes(e.target.value)}
                  required
                  placeholder="Record patient condition, reasons for missing appointment, and assistance provided..."
                  className="w-full text-xs p-3 border border-slate-300 rounded-xl outline-none focus:border-teal-600"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-700">Resolution Outcome:</label>
                <select
                  value={outcome}
                  onChange={(e) => setOutcome(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-xl outline-none focus:border-teal-600 bg-white"
                >
                  <option value="PATIENT_VISITED_CLINIC">Accompanied / Patient Visited CHC</option>
                  <option value="HOME_CHECK_COMPLETED">Home Vitals Check Completed (Normal)</option>
                  <option value="MEDICINE_REFILL_ARRANGED">Medicine Refill Arranged via PHC</option>
                  <option value="ESCALATED_TO_MO">Escalated to Medical Officer for Home Visit</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setSelectedTask(null)}
                  className="px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition shadow-sm flex items-center gap-1.5"
                >
                  <CheckCircle2 size={14} />
                  <span>{isSubmitting ? 'Submitting...' : 'Mark Resolved & Synchronize'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
