import React, { useState } from 'react';
import { PlayCircle, ChevronLeft, ChevronRight, Wand2, X, Minimize2, Maximize2 } from 'lucide-react';
import { Lang, User } from '../types';
import { api } from '../services/api';
import { makeT } from '../i18n';

interface GuidedDemoProps {
  language: Lang;
  currentUser: User | null;
  onSignIn: (username: string) => Promise<void> | void;
  onReset: () => void;
  onClose: () => void;
}

type DemoAction = { action: string; delay?: number; [key: string]: unknown };

interface Step {
  user: string;
  who: string;
  title: string;
  show: string;
  actions: DemoAction[];
}

const fire = (actions: DemoAction[]) => {
  let wait = 0;
  actions.forEach(a => {
    wait += a.delay ?? 0;
    setTimeout(() => window.dispatchEvent(new CustomEvent('swasthyasetu-demo', { detail: a })), wait);
  });
};

export const GuidedDemo: React.FC<GuidedDemoProps> = ({ language, currentUser, onSignIn, onReset, onClose }) => {
  const t = makeT(language);
  const [index, setIndex] = useState(-1);
  const [resetFirst, setResetFirst] = useState(true);
  const [busy, setBusy] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const say = (hi: string, mr: string, en: string) => (language === 'en' ? en : language === 'mr' ? mr : hi);

  const steps: Step[] = [
    {
      user: 'ramesh', who: t('मरीज़ - रमेश', 'Patient - Ramesh'),
      title: t('आपात स्थिति, अपनी भाषा में', 'An emergency, in his own language'),
      show: t('रमेश सीने में दर्द लिखते हैं। सुरक्षा नियम तुरंत 112/108 और निकटतम आपातकालीन केंद्र बताते हैं - कोई AI मॉडल इंतज़ार नहीं कराता।',
        'Ramesh describes chest pain. Safety rules answer instantly with 112/108 and the nearest emergency-ready centre - no AI model is waited on.'),
      actions: [{ action: 'chat', fresh: true, text: say('मुझे सीने में दर्द है और सांस लेने में तकलीफ हो रही है', 'मला छातीत दुखत आहे आणि श्वास घ्यायला त्रास होत आहे', 'I have chest pain and difficulty breathing') }],
    },
    {
      user: 'ramesh', who: t('मरीज़ - रमेश', 'Patient - Ramesh'),
      title: t('रोज़मर्रा का सवाल, भरोसेमंद जवाब', 'An everyday question, a grounded answer'),
      show: t('जवाब स्वीकृत संदर्भ सामग्री और रमेश के अपने रिकॉर्ड से बनता है, स्रोत दिखाए जाते हैं। "सुनें" से जवाब पढ़कर सुनाया जाता है।',
        'The answer is built from approved reference material and Ramesh\'s own record, with sources shown. "Listen" reads it aloud.'),
      actions: [{ action: 'chat', fresh: true, text: say('मुझे कल रात से हल्का बुखार और बदन दर्द है, क्या करूं?', 'मला काल रात्रीपासून हलका ताप आणि अंगदुखी आहे, मी काय करू?', 'I have had a mild fever and body pain since last night. What should I do?') }],
    },
    {
      user: 'ramesh', who: t('मरीज़ - रमेश', 'Patient - Ramesh'),
      title: t('अस्पताल की तैयारी देखकर बुकिंग', 'Check hospital readiness, then book'),
      show: t('नक्शे और कार्ड पर दिखता है कि पौड CHC में अल्ट्रासाउंड नहीं है और अम्लोडिपिन खत्म है - जाने से पहले। बुकिंग पर टोकन मिलता है और फोन पर SMS आता है (टैब 1)।',
        'The map and cards show Paud CHC has no ultrasound and is out of Amlodipine - before he travels. Booking gives a token and an SMS arrives on his phone (tab 1).'),
      actions: [{ action: 'book', reason: say('सीने में भारीपन - बीपी जांच', 'छातीत जडपणा - रक्तदाब तपासणी', 'Chest heaviness - BP review') }],
    },
    {
      user: 'dr_deshmukh', who: t('डॉक्टर - डॉ. देशमुख', 'Doctor - Dr. Deshmukh'),
      title: t('परामर्श, स्टॉक जांच के साथ', 'Consultation with a live stock check'),
      show: t('डॉक्टर अपनी कतार और AI इनटेक सारांश देखते हैं। अम्लोडिपिन पर स्टॉक चेतावनी आती है, अल्ट्रासाउंड रेफ़रल बनता है, 7 दिन का फॉलो-अप और SMS रिमाइंडर तय होता है।',
        'The doctor sees his own queue and the AI intake summary. Amlodipine gets a stock warning, ultrasound becomes a referral, and a 7-day follow-up with SMS reminder is scheduled.'),
      actions: [{ action: 'consult' }],
    },
    {
      user: 'admin_paud', who: t('अस्पताल - पौड CHC', 'Hospital - Paud CHC'),
      title: t('अस्पताल अपनी जानकारी अपडेट करता है', 'The hospital updates its readiness'),
      show: t('स्टाफ अम्लोडिपिन का स्टॉक भरता है और अल्ट्रासाउंड उपलब्ध करता है। मरीज़ों को यह तुरंत दिखता है।',
        'Staff restock Amlodipine and mark ultrasound available. Patients see the change immediately.'),
      actions: [{ action: 'restock' }],
    },
    {
      user: 'asha_kavita', who: t('आशा - कविता ताई', 'ASHA - Kavita Tai'),
      title: t('छूटा फॉलो-अप → घर भ्रमण', 'Missed follow-up → home visit'),
      show: t('सुनीता देवी का फॉलो-अप छूट गया था; सिस्टम ने अपने आप आशा को कार्य दिया। कविता ताई घर भ्रमण दर्ज करती हैं और मरीज़ को SMS जाता है।',
        'Sunita Devi missed her follow-up, so the system automatically created a task for her ASHA. Kavita Tai records the home visit and the patient gets an SMS.'),
      actions: [{ action: 'visit', notes: 'Visited at home. Random blood sugar 164 mg/dL. Missed review because there was no bus; arranged to accompany her to the CHC tomorrow.' }],
    },
    {
      user: 'asha_kavita', who: t('आशा - कविता ताई', 'ASHA - Kavita Tai'),
      title: t('गोपनीयता: दूसरे क्षेत्र का रिकॉर्ड बंद', 'Privacy: another area\'s record stays closed'),
      show: t('कविता ताई दूसरे गांव की मरीज़ (#3) का रिकॉर्ड खोलने की कोशिश करती हैं। सर्वर रोकता है और ऑडिट में दर्ज करता है।',
        'Kavita Tai tries to open a patient from another village (#3). The server blocks it and writes it to the audit trail.'),
      actions: [{ action: 'access-test' }],
    },
    {
      user: 'ramesh', who: t('मरीज़ - रमेश', 'Patient - Ramesh'),
      title: t('मरीज़ का अपने डेटा पर नियंत्रण', 'The patient controls his data'),
      show: t('रमेश गोपनीयता टैब में डॉ. देशमुख की अनुमति हटाते हैं। अब डॉक्टर उनका रिकॉर्ड नहीं खोल सकते (डॉक्टर पोर्टल में जांचें)।',
        'In the Privacy tab Ramesh withdraws Dr. Deshmukh\'s access. The doctor can no longer open his record (check the Doctor portal).'),
      actions: [{ action: 'tab', tab: 'PRIVACY' }, { action: 'revoke-doctor', delay: 1200 }],
    },
    {
      user: 'admin_district', who: t('ज़िला प्रशासन', 'District administration'),
      title: t('ज़िले को पूरी तस्वीर', 'The district sees the whole picture'),
      show: t('अपॉइंटमेंट, छूटे फॉलो-अप, प्रभाव के आंकड़े और ऑडिट ट्रेल - जिसमें पहुंच रोकना और सहमति वापसी शामिल है।',
        'Appointments, missed follow-ups, impact numbers and the audit trail - including the blocked access and the consent withdrawal.'),
      actions: [{ action: 'continuity' }],
    },
  ];

  const goTo = async (i: number) => {
    setIndex(i);
    if (currentUser?.username !== steps[i].user) await onSignIn(steps[i].user);
  };

  const start = async () => {
    setBusy(true);
    try {
      if (resetFirst) {
        await api.resetDemo();
        onReset();
      }
      await goTo(0);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setBusy(false);
    }
  };

  const step = index >= 0 ? steps[index] : null;

  return (
    <div className="fixed z-50 bottom-3 left-3 right-3 sm:left-auto sm:w-[360px] bg-white rounded-2xl shadow-2xl border-2 border-amber-400" role="dialog" aria-label={t('मार्गदर्शित डेमो', 'Guided demo')}>
      <div className="flex items-center justify-between px-4 py-2 bg-amber-400 rounded-t-xl text-slate-900">
        <div className="flex items-center gap-2 text-sm font-bold">
          <PlayCircle size={16} /> {t('मार्गदर्शित डेमो', 'Guided demo')} {step && <span className="font-normal">({index + 1}/{steps.length})</span>}
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setCollapsed(c => !c)} aria-label={collapsed ? 'Expand' : 'Collapse'} className="p-1 hover:bg-amber-300 rounded">
            {collapsed ? <Maximize2 size={14} /> : <Minimize2 size={14} />}
          </button>
          <button onClick={onClose} aria-label="Close" className="p-1 hover:bg-amber-300 rounded"><X size={14} /></button>
        </div>
      </div>

      {!collapsed && (
        <div className="p-4 space-y-3">
          {!step ? (
            <>
              <p className="text-sm text-slate-700">
                {t('एक मरीज़ की पूरी यात्रा, हर भूमिका से होकर: आपात स्थिति, बुकिंग, डॉक्टर, अस्पताल, आशा, गोपनीयता और ज़िला। हर चरण पर "मेरे लिए करें" दबाएं।',
                  'One patient\'s whole journey through every role: emergency, booking, doctor, hospital, ASHA, privacy and the district. Press "Do it for me" at each step.')}
              </p>
              <label className="flex items-center gap-2 text-xs text-slate-600">
                <input type="checkbox" checked={resetFirst} onChange={e => setResetFirst(e.target.checked)} />
                {t('पहले डेमो डेटा रीसेट करें (सुझाव)', 'Reset demo data first (recommended)')}
              </label>
              <button onClick={start} disabled={busy} className="w-full bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white text-sm font-bold py-2 rounded-xl">
                {busy ? t('तैयार हो रहा है…', 'Preparing…') : t('डेमो शुरू करें', 'Start the demo')}
              </button>
            </>
          ) : (
            <>
              <div className="text-[11px] font-bold uppercase text-amber-700">{step.who}</div>
              <h4 className="text-base font-bold text-slate-900">{step.title}</h4>
              <p className="text-xs text-slate-600 leading-relaxed">{step.show}</p>
              <button onClick={() => fire(step.actions)} disabled={currentUser?.username !== step.user}
                className="w-full bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 text-sm font-bold py-2 rounded-xl flex items-center justify-center gap-2">
                <Wand2 size={15} /> {t('मेरे लिए करें', 'Do it for me')}
              </button>
              <div className="flex items-center justify-between">
                <button onClick={() => goTo(index - 1)} disabled={index === 0} className="text-xs font-semibold text-slate-600 disabled:opacity-30 flex items-center gap-1">
                  <ChevronLeft size={14} /> {t('पिछला', 'Back')}
                </button>
                {index < steps.length - 1 ? (
                  <button onClick={() => goTo(index + 1)} className="text-xs font-bold text-teal-800 flex items-center gap-1">
                    {t('अगला', 'Next')}: {steps[index + 1].who} <ChevronRight size={14} />
                  </button>
                ) : (
                  <button onClick={onClose} className="text-xs font-bold text-teal-800">{t('डेमो समाप्त', 'Finish demo')}</button>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
