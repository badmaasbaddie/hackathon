import { makeT } from '../i18n';
import React, { useState, useEffect } from 'react';
import { Role, User, Lang } from '../types';
import { getOfflineMode, setOfflineMode, getOfflineQueue, syncOfflineBatch } from '../services/offlineQueue';
import { api } from '../services/api';
import { 
  Wifi, WifiOff, RefreshCw, RotateCcw, PlayCircle, ShieldCheck, 
  UserCheck, Stethoscope, Building2, BarChart3, User as UserIcon
} from 'lucide-react';

interface HeaderProps {
  currentUser: User | null;
  patientUsername: string;
  onSignIn: (username: string) => void;
  language: Lang;
  onLanguageChange: (lang: Lang) => void;
  onOpenScenarioModal: () => void;
  onOpenGuidedDemo: () => void;
  onOpenRegister: () => void;
  onDemoReset: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  patientUsername,
  onSignIn,
  language,
  onLanguageChange,
  onOpenScenarioModal,
  onOpenGuidedDemo,
  onOpenRegister,
  onDemoReset,
}) => {
  const t = makeT(language);
  const currentRole: Role | undefined = currentUser?.role;
  const [isOffline, setIsOffline] = useState<boolean>(getOfflineMode());
  const [queueCount, setQueueCount] = useState<number>(getOfflineQueue().length);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [resetting, setResetting] = useState<boolean>(false);

  useEffect(() => {
    const handleQueueUpdate = () => {
      setQueueCount(getOfflineQueue().length);
    };
    const handleModeUpdate = () => {
      setIsOffline(getOfflineMode());
    };

    window.addEventListener('offline-queue-updated', handleQueueUpdate);
    window.addEventListener('offline-mode-changed', handleModeUpdate);
    return () => {
      window.removeEventListener('offline-queue-updated', handleQueueUpdate);
      window.removeEventListener('offline-mode-changed', handleModeUpdate);
    };
  }, []);

  const handleToggleOffline = () => {
    const nextVal = !isOffline;
    setIsOffline(nextVal);
    setOfflineMode(nextVal);
  };

  const handleManualSync = async () => {
    setIsSyncing(true);
    try {
      const res = await syncOfflineBatch(currentUser?.id || 0);
      const failed = res.results.filter((r: any) => r.status === 'FAILED');
      alert(failed.length
        ? `Synced ${res.synced_count} action(s). ${failed.length} failed: ${failed.map((f: any) => f.message).join('; ')}`
        : `Synced ${res.synced_count} queued action(s) with the SwasthyaSetu server.`);
      window.dispatchEvent(new Event('swasthyasetu-data-changed'));
    } catch (err: any) {
      alert('Sync failed: ' + err.message);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleResetClick = async () => {
    if (confirm('Reset the demo database to the clean fictional baseline? All changes made in this demo will be lost.')) {
      setResetting(true);
      try {
        await api.resetDemo();
        onDemoReset();
      } catch (err: any) {
        alert('Reset failed: ' + err.message);
      } finally {
        setResetting(false);
      }
    }
  };

  const roles: { role: Role; labelHi: string; labelEn: string; icon: any; defaultUser: string }[] = [
    { role: 'PATIENT', labelHi: 'मरीज़ / परिवार', labelEn: 'Patient / Family', icon: UserIcon, defaultUser: patientUsername },
    { role: 'ASHA', labelHi: 'आशा कार्यकर्ता', labelEn: 'ASHA / ANM', icon: UserCheck, defaultUser: 'asha_kavita' },
    { role: 'DOCTOR', labelHi: 'डॉक्टर पोर्टल', labelEn: 'Doctor', icon: Stethoscope, defaultUser: 'dr_deshmukh' },
    { role: 'FACILITY_ADMIN', labelHi: 'अस्पताल / CHC', labelEn: 'Facility / CHC', icon: Building2, defaultUser: 'admin_paud' },
    { role: 'SUPER_ADMIN', labelHi: 'जिला प्रशासन', labelEn: 'Admin Analytics', icon: BarChart3, defaultUser: 'admin_district' },
  ];

  return (
    <header className="bg-gradient-to-r from-teal-900 via-teal-800 to-teal-950 text-white shadow-lg md:sticky md:top-0 z-40">
      {/* Top Banner / Hackathon Context */}
      <div className="bg-teal-950/80 border-b border-teal-800/60 px-4 py-1.5 text-xs flex flex-wrap justify-between items-center gap-2">
        <div className="flex items-center gap-2">
          <span className="text-teal-200 font-medium">
            “Doctor tak pahunchna hi nahi, poori healthcare journey ko complete karna.”
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {/* Offline Simulation Control */}
          <div className="flex items-center gap-2 bg-teal-900/90 px-2 py-0.5 rounded border border-teal-700">
            <button
              onClick={handleToggleOffline}
              className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium transition ${
                isOffline ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-teal-700 text-teal-100 hover:bg-teal-600'
              }`}
              title="Toggle simulated rural network disconnection"
              aria-pressed={isOffline}
            >
              {isOffline ? <WifiOff size={13} /> : <Wifi size={13} />}
              {isOffline ? 'Simulating Offline' : 'Online'}
            </button>
            {queueCount > 0 && (
              <span className="bg-amber-400 text-slate-900 text-[11px] font-bold px-1.5 py-0.2 rounded-full">
                {queueCount} queued
              </span>
            )}
            {queueCount > 0 && !isOffline && (
              <button
                onClick={handleManualSync}
                disabled={isSyncing}
                className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-500 text-white px-2 py-0.5 rounded text-[11px] font-semibold transition"
              >
                <RefreshCw size={11} className={isSyncing ? 'animate-spin' : ''} />
                Sync
              </button>
            )}
          </div>

          {/* Language Switch */}
          <div className="flex items-center bg-teal-900 rounded border border-teal-700 overflow-hidden text-xs" role="group" aria-label="Language">
            {([['hi', 'हिन्दी'], ['mr', 'मराठी'], ['en', 'English']] as [Lang, string][]).map(([code, label]) => (
              <button
                key={code}
                onClick={() => onLanguageChange(code)}
                aria-pressed={language === code}
                className={`px-2 py-0.5 transition ${language === code ? 'bg-teal-600 font-bold text-white' : 'text-teal-200 hover:bg-teal-800'}`}
              >
                {label}
              </button>
            ))}
          </div>

          <button
            onClick={onOpenGuidedDemo}
            className="flex items-center gap-1 bg-white hover:bg-amber-100 text-teal-950 font-bold px-2.5 py-0.5 rounded transition shadow-sm"
          >
            <PlayCircle size={13} />
            <span>{t('मार्गदर्शित डेमो', 'Guided demo')}</span>
          </button>

          {/* Quick Scenario Runner */}
          <button
            onClick={onOpenScenarioModal}
            className="flex items-center gap-1 bg-amber-500 hover:bg-amber-400 text-teal-950 font-bold px-2.5 py-0.5 rounded transition shadow-sm"
          >
            <PlayCircle size={13} />
            <span>Judge Scenarios</span>
          </button>

          <button
            onClick={onOpenRegister}
            className="flex items-center gap-1 bg-teal-600 hover:bg-teal-500 text-white font-semibold px-2.5 py-0.5 rounded transition"
          >
            <ShieldCheck size={13} />
            <span>{t('नया पंजीकरण', 'Register')}</span>
          </button>

          {/* Reset Demo */}
          <button
            onClick={handleResetClick}
            disabled={resetting}
            className="flex items-center gap-1 text-teal-300 hover:text-white px-1.5 py-0.5 rounded text-xs transition"
            title="Reset database to fresh demo baseline"
          >
            <RotateCcw size={12} className={resetting ? 'animate-spin' : ''} />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Main Bar */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-600 border border-teal-400 flex items-center justify-center shadow-md">
            <span className="text-2xl font-black text-amber-300">स्</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                SwasthyaSetu AI
                <span className="text-sm font-normal text-teal-200">| स्वास्थ्यसेतु</span>
              </h1>
              <span className="hidden lg:inline bg-teal-800/80 text-teal-200 text-[10px] font-semibold px-2 py-0.5 rounded border border-teal-700">
                Understand • Navigate • Coordinate • Continue
              </span>
            </div>
            <p className="text-xs text-teal-200">
              {t('ग्रामीण स्वास्थ्य सेवा नेविगेशन एवं निरंतरता प्लेटफ़ॉर्म', 'Rural Healthcare Navigation, Coordination & Continuity Platform')}
            </p>
          </div>
        </div>

        {/* Current Active Persona & Switcher */}
        <div className="flex flex-wrap items-center gap-2 bg-teal-950/60 p-1 rounded-xl border border-teal-800/80">
          <div className="text-right px-2 hidden md:block">
            <div className="text-[11px] text-teal-300">{t('साइन इन', 'Signed in as')} (demo)</div>
            <div className="text-xs font-semibold text-white truncate max-w-[150px]">
              {currentUser?.full_name || 'Guest'}
            </div>
          </div>
            <div className="flex flex-wrap items-center gap-1">
            {roles.map((r) => {
              const Icon = r.icon;
              const isActive = currentRole === r.role;
              return (
                <button
                  key={r.role}
                  onClick={() => onSignIn(r.defaultUser)}
                  aria-pressed={isActive}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    isActive
                      ? 'bg-teal-500 text-teal-950 font-bold shadow-md'
                      : 'text-teal-200 hover:bg-teal-800/60 hover:text-white'
                  }`}
                >
                  <Icon size={14} />
                  <span>{t(r.labelHi, r.labelEn)}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </header>
  );
};
