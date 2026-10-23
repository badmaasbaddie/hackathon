import { makeT } from '../i18n';
import React, { useState } from 'react';
import { User, Lang } from '../types';
import { api } from '../services/api';
import { UserPlus } from 'lucide-react';

interface RegisterModalProps {
  language: Lang;
  onClose: () => void;
  onRegistered: (token: string, user: User) => void;
}

export const RegisterModal: React.FC<RegisterModalProps> = ({ language, onClose, onRegistered }) => {
  const t = makeT(language);
  const [form, setForm] = useState({
    name: '', age: '', gender: 'Female', phone: '', village: '', district: 'Pune', block: 'Mulshi',
    blood_group: 'Unknown', emergency_contact: '', chronic_conditions: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.register({
        name: form.name,
        age: Number(form.age),
        gender: form.gender,
        phone: form.phone,
        village: form.village,
        district: form.district,
        block: form.block,
        blood_group: form.blood_group,
        emergency_contact: form.emergency_contact || undefined,
        chronic_conditions: form.chronic_conditions || 'None'
      });
      onRegistered(res.access_token, res.user);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const input = 'w-full text-sm p-2 border border-slate-300 rounded-lg outline-none focus:border-teal-600';
  const label = 'text-xs font-semibold text-slate-700';

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl border border-slate-200 max-h-[92vh] overflow-y-auto">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <UserPlus className="text-teal-700" size={20} />
              {t('नया मरीज़ पंजीकरण', 'New Patient Registration')}
            </h3>
            <p className="text-xs text-slate-500">
              {t('डेमो: एक काल्पनिक ABHA-प्रारूप आईडी बनाई जाएगी। असली व्यक्तिगत जानकारी न डालें।', 'Demo: a fictional ABHA-format ID is generated. Please do not enter real personal details.')}
            </p>
          </div>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-700 font-bold" aria-label="Close">✕</button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2 space-y-1">
            <label className={label}>{t('पूरा नाम', 'Full name')} *</label>
            <input required minLength={2} value={form.name} onChange={set('name')} className={input} />
          </div>
          <div className="space-y-1">
            <label className={label}>{t('उम्र', 'Age')} *</label>
            <input required type="number" min={0} max={120} value={form.age} onChange={set('age')} className={input} />
          </div>
          <div className="space-y-1">
            <label className={label}>{t('लिंग', 'Gender')} *</label>
            <select value={form.gender} onChange={set('gender')} className={input}>
              <option value="Female">{t('महिला', 'Female')}</option>
              <option value="Male">{t('पुरुष', 'Male')}</option>
              <option value="Other">{t('अन्य', 'Other')}</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className={label}>{t('मोबाइल नंबर', 'Mobile number')} *</label>
            <input required inputMode="numeric" pattern="[0-9]{10}" title="10-digit mobile number" value={form.phone} onChange={set('phone')} className={input} />
          </div>
          <div className="space-y-1">
            <label className={label}>{t('गांव', 'Village')} *</label>
            <input required minLength={2} value={form.village} onChange={set('village')} placeholder="Paud / Pirangut" className={input} />
          </div>
          <div className="space-y-1">
            <label className={label}>{t('ब्लॉक / तालुका', 'Block / Taluka')}</label>
            <input value={form.block} onChange={set('block')} className={input} />
          </div>
          <div className="space-y-1">
            <label className={label}>{t('ज़िला', 'District')}</label>
            <input value={form.district} onChange={set('district')} className={input} />
          </div>
          <div className="space-y-1">
            <label className={label}>{t('ब्लड ग्रुप', 'Blood group')}</label>
            <select value={form.blood_group} onChange={set('blood_group')} className={input}>
              {['Unknown', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'].map(b => <option key={b}>{b}</option>)}
            </select>
          </div>
          <div className="space-y-1">
            <label className={label}>{t('आपातकालीन संपर्क', 'Emergency contact')}</label>
            <input value={form.emergency_contact} onChange={set('emergency_contact')} className={input} />
          </div>
          <div className="col-span-2 space-y-1">
            <label className={label}>{t('पुरानी बीमारियां (यदि कोई)', 'Long-term conditions (if any)')}</label>
            <input value={form.chronic_conditions} onChange={set('chronic_conditions')} placeholder={t('जैसे: मधुमेह, बीपी', 'e.g. diabetes, high BP')} className={input} />
          </div>
        </div>

        {error && <div className="text-xs text-rose-800 bg-rose-50 border border-rose-200 rounded-lg p-2">{error}</div>}

        <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
          <button type="button" onClick={onClose} className="px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl">
            {t('रद्द करें', 'Cancel')}
          </button>
          <button type="submit" disabled={submitting} className="bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white text-xs font-bold px-4 py-2 rounded-xl">
            {submitting ? (t('पंजीकरण हो रहा है…', 'Registering…')) : (t('पंजीकरण करें', 'Register'))}
          </button>
        </div>
      </form>
    </div>
  );
};
