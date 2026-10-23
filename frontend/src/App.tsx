import React, { useState, useEffect } from 'react';
import { Role, User } from './types';
import { api, setAuthToken, getAuthToken } from './services/api';
import { Header } from './components/Header';
import { PatientPortal } from './components/PatientPortal';
import { AshaPortal } from './components/AshaPortal';
import { DoctorPortal } from './components/DoctorPortal';
import { FacilityPortal } from './components/FacilityPortal';
import { AdminDashboard } from './components/AdminDashboard';
import { ScenarioRunnerModal } from './components/ScenarioRunnerModal';
import { RegisterModal } from './components/RegisterModal';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [patientUsername, setPatientUsername] = useState<string>('ramesh');
  const [language, setLanguage] = useState<'hi' | 'en'>('hi');
  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState<boolean>(false);
  const [isRegisterOpen, setIsRegisterOpen] = useState<boolean>(false);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  const signIn = async (username: string) => {
    try {
      const data = await api.login(username);
      setAuthToken(data.access_token);
      setCurrentUser(data.user);
      setLoginError(null);
      if (data.user.role === 'PATIENT') setPatientUsername(data.user.username);
    } catch (err: any) {
      setLoginError(`Could not sign in as "${username}": ${err.message}. Is the backend running on port 8000?`);
    }
  };

  useEffect(() => {
    signIn(getAuthToken() || 'ramesh');
  }, []);

  const handleRegistered = (token: string, user: User) => {
    setAuthToken(token);
    setCurrentUser(user);
    setPatientUsername(user.username);
    setIsRegisterOpen(false);
  };

  const handleDemoReset = () => {
    setPatientUsername('ramesh');
    setRefreshKey(prev => prev + 1);
    const keep = currentUser && currentUser.role !== 'PATIENT' ? currentUser.username : 'ramesh';
    signIn(keep);
  };

  const role: Role | null = currentUser?.role ?? null;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      <Header
        currentUser={currentUser}
        patientUsername={patientUsername}
        onSignIn={signIn}
        language={language}
        onLanguageChange={setLanguage}
        onOpenScenarioModal={() => setIsScenarioModalOpen(true)}
        onOpenRegister={() => setIsRegisterOpen(true)}
        onDemoReset={handleDemoReset}
      />

      <div className="bg-amber-50 border-b border-amber-200 text-amber-900 text-[11px] px-4 py-1.5 text-center">
        {language === 'hi'
          ? 'डेमो प्रोटोटाइप: सभी मरीज़, डॉक्टर और स्टॉक डेटा काल्पनिक है। ABHA, eSanjeevani, SMS एकीकरण सिम्युलेटेड हैं। आपात स्थिति में 112 डायल करें।'
          : 'Demo prototype: all patients, doctors and stock data are fictional. ABHA, eSanjeevani and SMS integrations are simulated. In a real emergency dial 112.'}
      </div>

      <main className="flex-1 pb-12" key={`${refreshKey}-${currentUser?.username ?? 'none'}`}>
        {loginError && (
          <div className="max-w-3xl mx-auto mt-8 bg-rose-50 border border-rose-300 text-rose-900 text-sm rounded-xl p-4">{loginError}</div>
        )}
        {!currentUser && !loginError && (
          <div className="max-w-3xl mx-auto mt-8 text-sm text-slate-500 text-center">Signing in…</div>
        )}
        {currentUser && role === 'PATIENT' && (
          <PatientPortal language={language} user={currentUser} onRegister={() => setIsRegisterOpen(true)} />
        )}
        {currentUser && role === 'ASHA' && <AshaPortal language={language} user={currentUser} />}
        {currentUser && role === 'DOCTOR' && <DoctorPortal language={language} user={currentUser} />}
        {currentUser && role === 'FACILITY_ADMIN' && <FacilityPortal language={language} user={currentUser} />}
        {currentUser && role === 'SUPER_ADMIN' && <AdminDashboard language={language} user={currentUser} />}
      </main>

      <ScenarioRunnerModal
        isOpen={isScenarioModalOpen}
        onClose={() => setIsScenarioModalOpen(false)}
        onSelectScenario={(_id, _role, defaultUser) => signIn(defaultUser)}
      />

      {isRegisterOpen && (
        <RegisterModal language={language} onClose={() => setIsRegisterOpen(false)} onRegistered={handleRegistered} />
      )}

      <footer className="bg-slate-900 text-slate-400 text-xs border-t border-slate-800 py-6 px-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-white font-bold">SwasthyaSetu AI • स्वास्थ्यसेतु</div>
            <p className="text-slate-400 text-[11px]">
              Team AI Avengers: Rishabh, Sanay Prabhat, Ambuj Kumar (GL Bajaj Institute of Technology & Management)
            </p>
            <p className="text-slate-500 text-[10px]">
              “Doctor tak pahunchna hi nahi, poori healthcare journey ko complete karna.”
            </p>
          </div>
          <div className="text-right space-y-1">
            <div className="text-slate-300 font-semibold text-[11px]">Reference programmes</div>
            <div className="flex flex-wrap items-center gap-3 text-[10px] text-teal-400">
              <a href="https://mohfw.gov.in" target="_blank" rel="noreferrer" className="hover:underline">MoHFW</a>
              <a href="https://abdm.gov.in" target="_blank" rel="noreferrer" className="hover:underline">ABDM</a>
              <a href="https://esanjeevani.mohfw.gov.in" target="_blank" rel="noreferrer" className="hover:underline">eSanjeevani</a>
              <a href="https://www.who.int/health-topics/digital-health" target="_blank" rel="noreferrer" className="hover:underline">WHO Digital Health</a>
            </div>
            <p className="text-[10px] text-slate-500">
              Safety rules run before any AI • Clinical decisions stay with qualified clinicians
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default App;
