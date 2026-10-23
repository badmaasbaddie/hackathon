import React from 'react';
import { Role } from '../types';
import { PlayCircle, ShieldCheck, CheckCircle2, AlertTriangle, WifiOff, Users, Pill, Activity } from 'lucide-react';

interface ScenarioRunnerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectScenario: (scenarioId: string, role: Role, defaultUser: string) => void;
}

export const ScenarioRunnerModal: React.FC<ScenarioRunnerModalProps> = ({
  isOpen,
  onClose,
  onSelectScenario
}) => {
  if (!isOpen) return null;

  const scenarios = [
    {
      id: 'SCENARIO_A',
      title: 'Scenario A: Successful Routine Care',
      role: 'PATIENT' as Role,
      user: 'ramesh',
      tag: 'Routine Care Flow',
      icon: CheckCircle2,
      color: 'border-emerald-200 bg-emerald-50/50 text-emerald-800',
      description: 'Fictional patient Ramesh Kumar reports mild symptoms in Hindi, receives triage recommendation for Paud CHC, books demo appointment, and receives consultation & follow-up.'
    },
    {
      id: 'SCENARIO_B',
      title: 'Scenario B: Diagnostic Test Unavailable',
      role: 'FACILITY_ADMIN' as Role,
      user: 'admin_paud',
      tag: 'Hardware Readiness',
      icon: Activity,
      color: 'border-blue-200 bg-blue-50/50 text-blue-800',
      description: 'Paud CHC displays ECG operational but Ultrasound (USG) hardware missing at CHC tier, offering honest fallback to Aundh District Hospital.'
    },
    {
      id: 'SCENARIO_C',
      title: 'Scenario C: Medicine Out-of-Stock Limitation',
      role: 'DOCTOR' as Role,
      user: 'dr_deshmukh',
      tag: 'Prescription Safety',
      icon: Pill,
      color: 'border-amber-200 bg-amber-50/50 text-amber-800',
      description: 'Prescribing Amlodipine 5mg displays dispensary stockout warning at Paud CHC with regional stock visible at District Hospital, without AI altering the prescription.'
    },
    {
      id: 'SCENARIO_D',
      title: 'Scenario D: Missed Follow-up & ASHA Escalation',
      role: 'ASHA' as Role,
      user: 'asha_kavita',
      tag: 'Continuous Care',
      icon: Users,
      color: 'border-purple-200 bg-purple-50/50 text-purple-800',
      description: 'Chronic patient Sunita Devi passes due date without review. System creates high-priority ASHA task; worker visits home, enters notes, and resolves the case.'
    },
    {
      id: 'SCENARIO_E',
      title: 'Scenario E: Conservative Emergency Warning',
      role: 'PATIENT' as Role,
      user: 'ramesh',
      tag: 'Emergency Triage',
      icon: AlertTriangle,
      color: 'border-rose-200 bg-rose-50/50 text-rose-800',
      description: 'Patient reports severe chest pain and acute breathlessness. Immediate 112 emergency banner triggers prominently without waiting for questionnaires or LLMs.'
    },
    {
      id: 'SCENARIO_F',
      title: 'Scenario F: Offline Queue & Idempotent Sync',
      role: 'PATIENT' as Role,
      user: 'ramesh',
      tag: 'Low Connectivity',
      icon: WifiOff,
      color: 'border-teal-200 bg-teal-50/50 text-teal-800',
      description: 'User toggles offline simulation, queues an appointment booking, restores connectivity, and synchronizes idempotently without duplicate records.'
    },
    {
      id: 'SCENARIO_G',
      title: 'Scenario G: Role-Based Access Control Denial',
      role: 'ASHA' as Role,
      user: 'asha_kavita',
      tag: 'ABDM Privacy & RBAC',
      icon: ShieldCheck,
      color: 'border-slate-300 bg-slate-50 text-slate-800',
      description: 'ASHA Kavita attempts to access Anita More (from Kamshet village outside her catchment). Backend blocks with 403 Forbidden and writes audit log.'
    }
  ];

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between border-b border-slate-200 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <PlayCircle className="text-teal-700" size={20} />
              <h3 className="text-lg font-bold text-slate-900">
                Evaluation Scenarios Guide (Section 13)
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Select any scenario below to automatically switch to the designated portal role and verify the end-to-end workflow.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 font-bold text-sm p-1"
          >
            ✕
          </button>
        </div>

        <div className="space-y-3">
          {scenarios.map((sc) => {
            const Icon = sc.icon;
            return (
              <div
                key={sc.id}
                onClick={() => {
                  onSelectScenario(sc.id, sc.role, sc.user);
                  onClose();
                }}
                className={`p-4 rounded-xl border cursor-pointer transition hover:shadow-md space-y-1.5 ${sc.color}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 font-bold text-sm">
                    <Icon size={16} />
                    <span>{sc.title}</span>
                  </div>
                  <span className="text-[10px] uppercase font-black px-2 py-0.5 rounded bg-white/80 border border-current">
                    {sc.tag}
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {sc.description}
                </p>
              </div>
            );
          })}
        </div>

        <div className="pt-2 text-right">
          <button
            onClick={onClose}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-4 py-2 rounded-xl transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
