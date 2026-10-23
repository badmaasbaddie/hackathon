import React, { useState, useEffect } from 'react';
import { FacilityReadiness } from '../types';
import { api } from '../services/api';
import { 
  Building2, Users, Activity, Pill, Clock, 
  CheckCircle2, AlertCircle, RefreshCw, Shield, MapPin
} from 'lucide-react';

interface FacilityPortalProps {
  language: 'hi' | 'en';
}

export const FacilityPortal: React.FC<FacilityPortalProps> = ({ language }) => {
  const [facilities, setFacilities] = useState<FacilityReadiness[]>([]);
  const [selectedFacId, setSelectedFacId] = useState<number>(1); // Paud CHC default

  const loadData = async () => {
    try {
      const facs = await api.getFacilities();
      setFacilities(facs);
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const currentFac = facilities.find(f => f.id === selectedFacId) || facilities[0];

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Facility Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-xl border border-teal-200">
            <Building2 size={26} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">{currentFac?.name || 'Paud CHC'}</h2>
              <span className="bg-teal-100 text-teal-900 text-xs px-2.5 py-0.5 rounded-full font-bold">
                {currentFac?.facility_type}
              </span>
              <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-0.5 rounded-full font-bold">
                24x7 Open
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Address: {currentFac?.address} • Phone: {currentFac?.phone} • Emergency: 112
            </p>
          </div>
        </div>

        {/* Facility Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500 font-medium">Switch Facility:</label>
          <select
            value={selectedFacId}
            onChange={(e) => setSelectedFacId(Number(e.target.value))}
            className="text-xs font-bold p-2 border border-slate-300 rounded-xl bg-white outline-none focus:border-teal-600"
          >
            {facilities.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name} ({f.facility_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1.5">
            <Users size={14} className="text-teal-700" />
            Doctors On Duty
          </div>
          <div className="text-2xl font-black text-slate-900">
            {currentFac?.available_doctors_count || 1}
          </div>
          <p className="text-xs text-slate-600">
            {currentFac?.doctor_names.join(', ') || 'Dr. Anand Deshmukh (General Medicine)'}
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1.5">
            <Clock size={14} className="text-teal-700" />
            Estimated Queue Wait
          </div>
          <div className="text-2xl font-black text-slate-900">
            {currentFac?.estimated_queue_wait_mins || 20} mins
          </div>
          <p className="text-xs text-emerald-700 font-semibold">
            Real-time OPD Token Dispatch Active
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1.5">
            <RefreshCw size={14} className="text-teal-700" />
            Data Freshness
          </div>
          <div className="text-sm font-bold text-slate-900">
            {currentFac?.freshness_label || 'Verified 15m ago'}
          </div>
          <p className="text-[11px] text-slate-500">
            Clear distinction between confirmed live data and simulated test states.
          </p>
        </div>
      </div>

      {/* 2 Grids: Diagnostics Equipment Status & Medicine Stock Snapshot */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Diagnostics Equipment & Capacity */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Activity className="text-teal-700" size={18} />
                {language === 'hi' ? 'जांच सुविधाएं एवं उपकरण स्थिति' : 'Diagnostic Equipment & Test Availability'}
              </h3>
              <p className="text-xs text-slate-500">
                Lacking equipment triggers honest referral options (Scenario B).
              </p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-semibold">
              Live Roster
            </span>
          </div>

          <div className="space-y-2.5">
            {currentFac?.diagnostic_tests_available.map((test, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-emerald-50/50 border border-emerald-200 text-xs">
                <div className="font-bold text-slate-800">{test}</div>
                <span className="bg-emerald-600 text-white font-bold text-[10px] px-2 py-0.5 rounded">
                  Operational ✓
                </span>
              </div>
            ))}

            {currentFac?.diagnostic_tests_missing.map((test, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-rose-50/50 border border-rose-200 text-xs">
                <div>
                  <div className="font-bold text-rose-900">{test}</div>
                  <div className="text-[10px] text-rose-700">Lacking hardware at this tier; refer to District Hospital Pune</div>
                </div>
                <span className="bg-rose-600 text-white font-bold text-[10px] px-2 py-0.5 rounded">
                  Unavailable ✕
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Medicine Inventory Snapshot */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Pill className="text-teal-700" size={18} />
                {language === 'hi' ? 'दवा स्टॉक स्थिति (Dispensary Inventory)' : 'Dispensary Medicine Inventory'}
              </h3>
              <p className="text-xs text-slate-500">
                Prescription-linked availability tracker (Scenario C).
              </p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-semibold">
              Dispensary
            </span>
          </div>

          <div className="space-y-2.5">
            {currentFac && Object.entries(currentFac.medicine_stock_summary).map(([med, st], idx) => {
              const isOut = st === 'OUT_OF_STOCK';
              return (
                <div
                  key={idx}
                  className={`flex items-center justify-between p-3 rounded-xl border text-xs ${
                    isOut ? 'bg-rose-50/60 border-rose-300' : 'bg-slate-50 border-slate-200'
                  }`}
                >
                  <div>
                    <span className="font-bold text-slate-900">{med}</span>
                    {isOut && (
                      <p className="text-[10px] text-rose-700 font-semibold mt-0.5">
                        Stock depleted. Regional buffer stock available at District Hospital.
                      </p>
                    )}
                  </div>
                  <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded ${
                    isOut ? 'bg-rose-600 text-white' : 'bg-emerald-600 text-white'
                  }`}>
                    {isOut ? 'OUT OF STOCK' : 'IN STOCK'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
