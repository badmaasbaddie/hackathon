import React, { useState, useEffect } from 'react';
import { FacilityManage, User, Doctor, ScheduleSlot, Appointment } from '../types';
import { api } from '../services/api';
import { localDate } from '../utils/date';
import { Building2, Users, Activity, Pill, Clock, RefreshCw, Calendar, Save } from 'lucide-react';

interface FacilityPortalProps {
  language: 'hi' | 'en';
  user: User;
}

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export const FacilityPortal: React.FC<FacilityPortalProps> = ({ language, user }) => {
  const hi = language === 'hi';
  const t = (h: string, e: string) => (hi ? h : e);

  const [data, setData] = useState<FacilityManage | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [editingDoctor, setEditingDoctor] = useState<Doctor | null>(null);
  const [scheduleDraft, setScheduleDraft] = useState<ScheduleSlot[]>([]);
  const [stockDraft, setStockDraft] = useState<Record<number, string>>({});

  const facilityId = user.facility_id;

  const load = async () => {
    if (!facilityId) {
      setError(t('इस खाते से कोई अस्पताल जुड़ा नहीं है', 'No facility is linked to this account'));
      return;
    }
    try {
      const [m, apts] = await Promise.all([api.getFacilityManage(facilityId), api.getAppointments()]);
      setData(m);
      setAppointments(apts);
      setStockDraft(Object.fromEntries(m.inventory.map(i => [i.id, String(i.quantity_in_stock)])));
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => { load(); }, []);

  const flash = (text: string) => {
    setNotice(text);
    setTimeout(() => setNotice(null), 3500);
  };

  const run = async (fn: () => Promise<unknown>, okText: string) => {
    try {
      await fn();
      await load();
      flash(okText);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const toggleDuty = (d: Doctor) =>
    run(() => api.updateDoctor(d.id, { is_available_today: !d.is_available_today }),
      `${d.name}: ${!d.is_available_today ? t('आज ड्यूटी पर', 'on duty today') : t('आज छुट्टी पर', 'off duty today')}`);

  const openSchedule = (d: Doctor) => {
    setEditingDoctor(d);
    setScheduleDraft(DAYS.map(day => d.schedule.find(s => s.day_of_week === day) || { day_of_week: day, start_time: '', end_time: '' }));
  };

  const saveSchedule = async () => {
    if (!editingDoctor) return;
    const slots = scheduleDraft.filter(s => s.start_time && s.end_time);
    await run(() => api.updateDoctor(editingDoctor.id, { schedule: slots }), t('ओपीडी समय सहेजा गया', 'OPD schedule saved'));
    setEditingDoctor(null);
  };

  if (error) return <div className="max-w-3xl mx-auto mt-8 text-sm text-rose-800 bg-rose-50 border border-rose-200 rounded-xl p-4">{error}</div>;
  if (!data) return <div className="max-w-3xl mx-auto mt-8 text-sm text-slate-500 text-center">{t('लोड हो रहा है…', 'Loading…')}</div>;

  const fac = data.facility;
  const todayStr = localDate();
  const todays = appointments.filter(a => a.scheduled_date === todayStr);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-teal-100 text-teal-800 flex items-center justify-center border border-teal-200">
            <Building2 size={26} />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">{fac.name}</h2>
              <span className="bg-teal-100 text-teal-900 text-xs px-2.5 py-0.5 rounded-full font-bold">{fac.facility_type}</span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{fac.address} • {fac.phone} • {fac.operating_hours}</p>
            <p className="text-[11px] text-slate-500">{t('प्रबंधक', 'Managed by')}: {user.full_name}</p>
          </div>
        </div>
        <button onClick={load} className="flex items-center gap-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl">
          <RefreshCw size={13} /> {t('रीफ़्रेश', 'Refresh')}
        </button>
      </div>

      {notice && <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs rounded-xl p-3" role="status">{notice}</div>}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: t('ड्यूटी पर डॉक्टर', 'Doctors on duty'), value: `${fac.available_doctors_count} / ${data.doctors.length}`, icon: Users },
          { label: t('आज के अपॉइंटमेंट', "Today's appointments"), value: todays.length, icon: Calendar },
          { label: t('अनुमानित प्रतीक्षा', 'Est. queue wait'), value: `${fac.estimated_queue_wait_mins} min`, icon: Clock },
          { label: t('अंतिम अपडेट', 'Last update'), value: fac.freshness_label.replace(' by facility staff', ''), icon: RefreshCw },
        ].map(card => (
          <div key={card.label} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
            <div className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1.5"><card.icon size={13} className="text-teal-700" /> {card.label}</div>
            <div className="text-lg font-black text-slate-900">{card.value}</div>
          </div>
        ))}
      </div>

      {/* Doctor roster */}
      <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
        <div className="border-b border-slate-200 pb-3">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2"><Users className="text-teal-700" size={18} /> {t('डॉक्टर रोस्टर और ओपीडी समय', 'Doctor roster & OPD schedules')}</h3>
          <p className="text-xs text-slate-500">{t('बदलाव तुरंत मरीज़ों को दिखते हैं और ड्यूटी से बाहर डॉक्टर के लिए आज की बुकिंग रुक जाती है।', 'Changes are visible to patients immediately; off-duty doctors cannot be booked for today.')}</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="py-2 pr-3">{t('डॉक्टर', 'Doctor')}</th>
                <th className="py-2 pr-3">{t('विशेषज्ञता', 'Specialty')}</th>
                <th className="py-2 pr-3">{t('ओपीडी समय', 'OPD schedule')}</th>
                <th className="py-2 pr-3">{t('आज', 'Today')}</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {data.doctors.map(d => (
                <tr key={d.id} className="border-b border-slate-100">
                  <td className="py-2 pr-3 font-bold text-slate-900">{d.name}</td>
                  <td className="py-2 pr-3 text-slate-600">{d.specialty}</td>
                  <td className="py-2 pr-3 text-slate-600">{d.schedule.length ? d.schedule.map(s => `${s.day_of_week.slice(0, 3)} ${s.start_time}-${s.end_time}`).join(', ') : t('तय नहीं', 'Not set')}</td>
                  <td className="py-2 pr-3">
                    <button onClick={() => toggleDuty(d)} aria-pressed={d.is_available_today}
                      className={`px-2.5 py-1 rounded-lg font-bold ${d.is_available_today ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-700'}`}>
                      {d.is_available_today ? t('ड्यूटी पर', 'On duty') : t('छुट्टी', 'Off duty')}
                    </button>
                  </td>
                  <td className="py-2 text-right">
                    <button onClick={() => openSchedule(d)} className="text-teal-800 font-semibold underline">{t('समय बदलें', 'Edit schedule')}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Services */}
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-3">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2"><Activity className="text-teal-700" size={18} /> {t('जांच सेवाएं', 'Diagnostic services')}</h3>
          {data.services.map(svc => (
            <div key={svc.id} className={`flex items-center justify-between gap-3 p-3 rounded-xl border text-xs ${svc.is_available ? 'bg-emerald-50/50 border-emerald-200' : 'bg-rose-50/50 border-rose-200'}`}>
              <div>
                <div className="font-bold text-slate-900">{svc.name}</div>
                <div className="text-[10px] text-slate-500">{svc.notes || `${t('अपडेट', 'Updated')} ${new Date(svc.updated_at).toLocaleString()}`}</div>
              </div>
              <button
                onClick={() => run(() => api.updateService(fac.id, svc.id, {
                  is_available: !svc.is_available,
                  notes: svc.is_available ? 'Temporarily unavailable - refer to District Hospital' : null
                }), `${svc.name}: ${!svc.is_available ? t('उपलब्ध', 'available') : t('अनुपलब्ध', 'unavailable')}`)}
                aria-pressed={svc.is_available}
                className={`shrink-0 px-2.5 py-1 rounded-lg font-bold ${svc.is_available ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white'}`}>
                {svc.is_available ? t('उपलब्ध', 'Available') : t('अनुपलब्ध', 'Unavailable')}
              </button>
            </div>
          ))}
        </section>

        {/* Inventory */}
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2"><Pill className="text-teal-700" size={18} /> {t('दवा स्टॉक', 'Dispensary stock')}</h3>
            <p className="text-[11px] text-slate-500">{t('मैन्युअल प्रविष्टि। रियल-टाइम इन्वेंटरी एकीकरण बाद के चरण में।', 'Manual entry by staff. Real-time inventory integration is planned for a later phase.')}</p>
          </div>
          {data.inventory.map(item => (
            <form key={item.id} className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl border border-slate-200 bg-slate-50 text-xs"
              onSubmit={e => {
                e.preventDefault();
                run(() => api.updateInventory(fac.id, item.id, Math.max(0, Number(stockDraft[item.id] || 0))), `${item.medicine_name} ${t('स्टॉक अपडेट', 'stock updated')}`);
              }}>
              <div>
                <div className="font-bold text-slate-900">{item.medicine_name}</div>
                <div className="text-[10px] text-slate-500">{t('पुनः ऑर्डर स्तर', 'Reorder level')} {item.reorder_level} • {new Date(item.last_verified_at).toLocaleString()}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${item.stock_status === 'IN_STOCK' ? 'bg-emerald-600 text-white' : item.stock_status === 'LOW_STOCK' ? 'bg-amber-500 text-white' : 'bg-rose-600 text-white'}`}>
                  {item.stock_status.replace(/_/g, ' ')}
                </span>
                <input type="number" min={0} value={stockDraft[item.id] ?? ''} aria-label={`${item.medicine_name} quantity`}
                  onChange={e => setStockDraft({ ...stockDraft, [item.id]: e.target.value })}
                  className="w-20 p-1.5 border border-slate-300 rounded-lg" />
                <span className="text-slate-500">{item.unit}</span>
                <button type="submit" className="bg-teal-700 text-white p-1.5 rounded-lg" aria-label="Save stock"><Save size={13} /></button>
              </div>
            </form>
          ))}
        </section>
      </div>

      {/* Today's queue */}
      <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-3">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2"><Calendar className="text-teal-700" size={18} /> {t('अपॉइंटमेंट', 'Appointments at this facility')}</h3>
        {appointments.length === 0 && <p className="text-xs text-slate-400">{t('कोई अपॉइंटमेंट नहीं', 'No appointments')}</p>}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <tbody>
              {appointments.slice(0, 30).map(a => (
                <tr key={a.id} className="border-b border-slate-100">
                  <td className="py-1.5 pr-3 font-mono">{a.queue_token}</td>
                  <td className="py-1.5 pr-3 font-semibold">{a.patient_name}</td>
                  <td className="py-1.5 pr-3">{a.doctor_name}</td>
                  <td className="py-1.5 pr-3">{a.scheduled_date} {a.scheduled_time}</td>
                  <td className="py-1.5 pr-3">{a.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {editingDoctor && (
        <div className="fixed inset-0 bg-slate-900/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-slate-900">{t('ओपीडी समय', 'OPD schedule')}: {editingDoctor.name}</h3>
            <div className="space-y-2 text-xs">
              {scheduleDraft.map((slot, idx) => (
                <div key={slot.day_of_week} className="grid grid-cols-3 gap-2 items-center">
                  <span className="font-semibold">{slot.day_of_week}</span>
                  <input type="time" value={slot.start_time} aria-label={`${slot.day_of_week} start`}
                    onChange={e => setScheduleDraft(scheduleDraft.map((s, i) => i === idx ? { ...s, start_time: e.target.value } : s))} className="p-1.5 border rounded-lg" />
                  <input type="time" value={slot.end_time} aria-label={`${slot.day_of_week} end`}
                    onChange={e => setScheduleDraft(scheduleDraft.map((s, i) => i === idx ? { ...s, end_time: e.target.value } : s))} className="p-1.5 border rounded-lg" />
                </div>
              ))}
              <p className="text-[10px] text-slate-500">{t('खाली दिन = ओपीडी नहीं', 'Leave a day blank for no OPD')}</p>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setEditingDoctor(null)} className="px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl">{t('रद्द करें', 'Cancel')}</button>
              <button onClick={saveSchedule} className="bg-teal-700 text-white text-xs font-bold px-4 py-2 rounded-xl">{t('सहेजें', 'Save')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
