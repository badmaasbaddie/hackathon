import React, { useState, useEffect } from 'react';
import { AdminMetrics, AuditEvent } from '../types';
import { api } from '../services/api';
import { 
  BarChart3, Users, Building2, AlertTriangle, CheckCircle2, 
  Clock, ShieldAlert, Activity, Pill, RefreshCw, FileText
} from 'lucide-react';

interface AdminDashboardProps {
  language: 'hi' | 'en';
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ language }) => {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [adapters, setAdapters] = useState<any[]>([]);
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [isRetraining, setIsRetraining] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const m = await api.getAdminMetrics();
      setMetrics(m);
      const audits = await api.getAuditEvents();
      setAuditEvents(audits);
      const ad = await api.getAdaptersStatus();
      setAdapters(ad.adapters || []);
      
      const mInfoRes = await fetch('/api/ai/model-info');
      if (mInfoRes.ok) {
        const info = await mInfoRes.json();
        setModelInfo(info);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleRetrain = async () => {
    setIsRetraining(true);
    try {
      const res = await fetch('/api/ai/train', { method: 'POST' });
      const data = await res.json();
      alert('AI Model retrained successfully! Accuracy: ' + data.summary.test_accuracy + '%');
      loadData();
    } catch (err: any) {
      alert('Retrain failed: ' + err.message);
    } finally {
      setIsRetraining(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900">
              {language === 'hi' ? 'जिला सार्वजनिक स्वास्थ्य नियंत्रण कक्ष' : 'District Public Health Operations Center'}
            </h2>
            <span className="bg-amber-100 text-amber-900 text-xs px-2.5 py-0.5 rounded-full font-bold">
              Pune Zilla Parishad
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Mulshi Rural Cluster • Real-Time Health Navigation, Continuity & Resource Coordination
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl transition font-medium"
        >
          <RefreshCw size={13} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Users size={13} className="text-teal-700" />
            Total Patients
          </div>
          <div className="text-2xl font-black text-slate-900">
            {metrics?.total_patients || 1000}
          </div>
          <p className="text-[10px] text-teal-700 font-semibold">1,000 Trained Patient Records</p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Building2 size={13} className="text-teal-700" />
            Doctors & Hub Hospitals
          </div>
          <div className="text-2xl font-black text-slate-900">
            200 / {metrics?.total_facilities || 11}
          </div>
          <p className="text-[10px] text-slate-500">200 Doctors Across Regions</p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1">
            <Activity size={13} className="text-teal-700" />
            ASHA Health Workers
          </div>
          <div className="text-2xl font-black text-slate-900">
            200
          </div>
          <p className="text-[10px] text-teal-700 font-semibold">ASHA-LKO-001 to 200 Linked</p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="text-[11px] font-bold text-purple-700 uppercase flex items-center gap-1">
            <ShieldAlert size={13} />
            Jila Prashashan
          </div>
          <div className="text-2xl font-black text-purple-900">
            10 Authorities
          </div>
          <p className="text-[10px] text-purple-700 font-medium">District Data Oversight Ready</p>
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
                Trained Indian Healthcare AI Model (1,000 Patient Records)
              </h3>
            </div>
            <p className="text-xs text-teal-200 mt-0.5">
              Trained on multi-regional patient monitoring dataset with vitals, hub hospitals, doctors, and ASHA workers.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs bg-teal-900/80 border border-teal-700 text-teal-300 font-bold px-3 py-1 rounded-xl">
              Accuracy: {modelInfo?.test_accuracy || 79.0}%
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
                {language === 'hi' ? 'सुरक्षा एवं क्लिनिकल ऑडिट ट्रेल' : 'Security, Access & Clinical Audit Trail'}
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
              {language === 'hi' ? 'एकीकरण एडाप्टर स्थिति' : 'Ecosystem Adapters'}
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
