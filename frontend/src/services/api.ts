import {
  Patient, FacilityReadiness, Appointment, SymptomIntakeResponse,
  DiagnosticOrder, FollowUpPlan, HealthWorkerTask, CareTimelineEvent,
  AdminMetrics, User, ChatTurn, ChatResponse, PatientRecord, RegisterPayload,
  Doctor, FacilityManage, FacilityService, InventoryItem, ScheduleSlot,
  AdminActivity, FamilyMember, AuditEvent, Lang, NotificationItem, CareTeamMember
} from '../types';
import { getOfflineMode, enqueueOfflineAction } from './offlineQueue';

const API_BASE = '/api';
const TOKEN_KEY = 'swasthyasetu_token';

// Demo session token (the username returned by /api/auth/login). Kept in
// sessionStorage so a refresh keeps the persona; wrapped because storage can be blocked.
let authToken: string | null = (() => {
  try { return sessionStorage.getItem(TOKEN_KEY); } catch { return null; }
})();

export const setAuthToken = (token: string | null) => {
  authToken = token;
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch { /* storage unavailable */ }
};

export const getAuthToken = () => authToken;

export const authHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
  return headers;
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers: { ...authHeaders(), ...(init.headers || {}) } });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === 'string') detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: any) => d.msg).join('; ');
    } catch { /* non-JSON error */ }
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

const get = <T>(path: string) => request<T>(path);
const send = <T>(method: string, path: string, body?: unknown) =>
  request<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });

const qs = (params: Record<string, string | number | undefined | null>) => {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '');
  return entries.length ? '?' + entries.map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&') : '';
};

export const api = {
  // System
  resetDemo: () => send<any>('POST', '/demo/reset'),
  getHealth: () => get<any>('/health'),
  getAdaptersStatus: () => get<{ adapters: any[] }>('/adapters/status'),

  // Auth
  login: (username: string) => send<{ access_token: string; user: User }>('POST', '/auth/login', { username }),
  register: (payload: RegisterPayload) => send<{ access_token: string; user: User }>('POST', '/auth/register', payload),

  // Patients
  getMyPatient: () => get<Patient>('/patients/me'),
  addFamilyMember: (m: Omit<FamilyMember, 'id'>) => send<FamilyMember>('POST', '/patients/me/family', m),
  getCareTeam: () => get<CareTeamMember[]>('/patients/me/care-team'),
  setConsent: (userId: number, granted: boolean) => send<CareTeamMember[]>('PUT', '/patients/me/consents', { user_id: userId, granted }),
  getMyNotifications: () => get<NotificationItem[]>('/notifications/me'),
  getPatients: (village?: string) => get<Patient[]>(`/patients${qs({ village })}`),
  getPatient: (id: number) => get<Patient>(`/patients/${id}`),
  getPatientRecord: (id: number) => get<PatientRecord>(`/patients/${id}/record`),
  getTimeline: (patientId: number) => get<CareTimelineEvent[]>(`/timeline/${patientId}`),

  // AI assistant
  submitIntake: (patientId: number, rawInput: string, language = 'hi') =>
    send<SymptomIntakeResponse>('POST', '/symptom-intake', { patient_id: patientId, raw_input: rawInput, language, duration_days: 2 }),
  chat: (messages: ChatTurn[], language: Lang, patientId?: number) =>
    send<ChatResponse>('POST', '/ai/chat', { messages, language, patient_id: patientId }),

  // Facilities & doctors
  getFacilities: (district?: string) => get<FacilityReadiness[]>(`/facilities${qs({ district })}`),
  getDoctors: (facilityId?: number) => get<Doctor[]>(`/doctors${qs({ facility_id: facilityId })}`),
  getFacilityManage: (facilityId: number) => get<FacilityManage>(`/facilities/${facilityId}/manage`),
  updateDoctor: (doctorId: number, body: { is_available_today?: boolean; schedule?: ScheduleSlot[] }) =>
    send<Doctor>('PATCH', `/doctors/${doctorId}`, body),
  updateService: (facilityId: number, serviceId: number, body: { is_available: boolean; notes?: string | null }) =>
    send<FacilityService>('PATCH', `/facilities/${facilityId}/services/${serviceId}`, body),
  updateInventory: (facilityId: number, itemId: number, quantity: number) =>
    send<InventoryItem>('PATCH', `/facilities/${facilityId}/inventory/${itemId}`, { quantity_in_stock: quantity }),

  // Appointments
  async bookAppointment(payload: {
    patient_id: number;
    doctor_id: number;
    facility_id: number;
    scheduled_date: string;
    scheduled_time?: string;
    consultation_type?: string;
    reason?: string;
  }): Promise<Appointment> {
    if (getOfflineMode()) {
      enqueueOfflineAction('BOOK_APPOINTMENT', payload);
      return {
        id: -Date.now(),
        appointment_code: 'QUEUED-OFFLINE',
        patient_id: payload.patient_id,
        doctor_id: payload.doctor_id,
        facility_id: payload.facility_id,
        scheduled_date: payload.scheduled_date,
        scheduled_time: payload.scheduled_time || '10:30 AM',
        consultation_type: payload.consultation_type || 'IN_PERSON',
        status: 'QUEUED_OFFLINE',
        reason: payload.reason,
        queue_token: 'pending sync',
        is_simulated: true,
        created_at: new Date().toISOString()
      };
    }
    return send<Appointment>('POST', '/appointments', payload);
  },
  getAppointments: (params: { patient_id?: number; status?: string } = {}) => get<Appointment[]>(`/appointments${qs(params)}`),
  setAppointmentStatus: (id: number, status: string) => send<Appointment>('PATCH', `/appointments/${id}`, { status }),

  // Clinical
  createEncounter: (payload: any) => send<any>('POST', '/encounters', payload),
  getDiagnosticOrders: (patientId?: number) => get<DiagnosticOrder[]>(`/diagnostics/orders${qs({ patient_id: patientId })}`),
  getFollowUps: (patientId?: number) => get<FollowUpPlan[]>(`/follow-ups${qs({ patient_id: patientId })}`),

  // ASHA tasks
  getTasks: (status?: string) => get<HealthWorkerTask[]>(`/tasks${qs({ status })}`),
  async updateTask(
    taskId: number,
    payload: { status: string; visit_notes: string; outcome?: string; escalated_to_doctor_id?: number }
  ): Promise<HealthWorkerTask | null> {
    if (getOfflineMode()) {
      enqueueOfflineAction('RESOLVE_TASK', { task_id: taskId, ...payload });
      return null;
    }
    return send<HealthWorkerTask>('PATCH', `/tasks/${taskId}`, payload);
  },

  // Admin
  getAuditEvents: (limit = 50) => get<AuditEvent[]>(`/audit-events${qs({ limit })}`),
  getAdminMetrics: () => get<AdminMetrics>('/admin/metrics'),
  getAdminActivity: () => get<AdminActivity>('/admin/activity'),
  runContinuityEngine: () => send<{ newly_overdue: number; tasks_created: number; reminders_sent: number }>('POST', '/continuity/run'),
  getModelInfo: () => get<any>('/ai/model-info'),
  retrainModel: () => send<any>('POST', '/ai/train'),
};
