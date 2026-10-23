import React, { useState, useEffect } from 'react';
import { Role, User } from './types';
import { api } from './services/api';
import { Header } from './components/Header';
import { PatientPortal } from './components/PatientPortal';
import { AshaPortal } from './components/AshaPortal';
import { DoctorPortal } from './components/DoctorPortal';
import { FacilityPortal } from './components/FacilityPortal';
import { AdminDashboard } from './components/AdminDashboard';
import { ScenarioRunnerModal } from './components/ScenarioRunnerModal';

export const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<Role>('PATIENT');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [language, setLanguage] = useState<'hi' | 'en'>('hi');
  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState<boolean>(false);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  const fetchUser = async (username: string) => {
    try {
      const data = await api.login(username);
      setCurrentUser(data.user);
    } catch {
      // Fallback synthetic user
      setCurrentUser({
        id: 1,
        username,
        full_name: username === 'ramesh' ? 'Ramesh Kumar' : username,
        role: currentRole,
        is_active: true
      });
    }
  };

  useEffect(() => {
    fetchUser('ramesh');
  }, []);

  const handleRoleChange = (role: Role) => {
    setCurrentRole(role);
  };

  const handleUserSwitch = (username: string) => {
    fetchUser(username);
  };

  const handleSelectScenario = (_scenarioId: string, role: Role, defaultUser: string) => {
    setCurrentRole(role);
    fetchUser(defaultUser);
  };

  const handleDemoReset = () => {
    setRefreshKey(prev => prev + 1);
    fetchUser(currentUser?.username || 'ramesh');
    alert('SwasthyaSetu AI database has been reset to baseline synthetic records.');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800" key={refreshKey}>
      {/* Persistent Shell Header */}
      <Header
        currentRole={currentRole}
        onRoleChange={handleRoleChange}
        currentUser={currentUser}
        onUserSwitch={handleUserSwitch}
        language={language}
        onLanguageChange={setLanguage}
        onOpenScenarioModal={() => setIsScenarioModalOpen(true)}
        onDemoReset={handleDemoReset}
      />

      {/* Main Content Area Based on Active Role */}
      <main className="flex-1 pb-12">
        {currentRole === 'PATIENT' && <PatientPortal language={language} />}
        {currentRole === 'ASHA' && <AshaPortal language={language} />}
        {currentRole === 'DOCTOR' && <DoctorPortal language={language} />}
        {currentRole === 'FACILITY_ADMIN' && <FacilityPortal language={language} />}
        {currentRole === 'SUPER_ADMIN' && <AdminDashboard language={language} />}
      </main>

      {/* Scenario Evaluation Modal */}
      <ScenarioRunnerModal
        isOpen={isScenarioModalOpen}
        onClose={() => setIsScenarioModalOpen(false)}
        onSelectScenario={handleSelectScenario}
      />

      {/* Public Health Footer */}
      <footer className="bg-slate-900 text-slate-400 text-xs border-t border-slate-800 py-6 px-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-white font-bold flex items-center gap-2">
              <span>SwasthyaSetu AI • स्वास्थ्यसेतु</span>
            </div>
            <p className="text-slate-400 text-[11px]">
              Team AI Avengers: Rishabh, Sanay Prabhat, Ambuj Kumar (GL Bajaj Institute of Technology & Management)
            </p>
            <p className="text-slate-500 text-[10px]">
              Theme: Healthcare AI + Digital Health (Rural-First) • “Doctor tak pahunchna hi nahi, poori healthcare journey ko complete karna.”
            </p>
          </div>

          <div className="text-right space-y-1">
            <div className="text-slate-300 font-semibold text-[11px]">Research Foundations & Standards</div>
            <div className="flex items-center gap-3 text-[10px] text-teal-400">
              <a href="https://mohfw.gov.in" target="_blank" rel="noreferrer" className="hover:underline">MoHFW</a>
              <span>•</span>
              <a href="https://nha.gov.in" target="_blank" rel="noreferrer" className="hover:underline">NHA</a>
              <span>•</span>
              <a href="https://abdm.gov.in" target="_blank" rel="noreferrer" className="hover:underline">ABDM</a>
              <span>•</span>
              <a href="https://esanjeevani.mohfw.gov.in" target="_blank" rel="noreferrer" className="hover:underline">eSanjeevani</a>
              <span>•</span>
              <a href="https://who.int/health-topics/digital-health" target="_blank" rel="noreferrer" className="hover:underline">WHO Digital Health</a>
            </div>
            <p className="text-[10px] text-slate-500">
              Deterministic emergency safety protocols precedence • Human-in-the-loop qualified clinical oversight
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default App;
