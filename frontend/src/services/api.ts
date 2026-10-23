import {
  Patient, FacilityReadiness, Appointment, SymptomIntakeResponse,
  DiagnosticOrder, FollowUpPlan, HealthWorkerTask, CareTimelineEvent,
  AdminMetrics, User
} from '../types';
import { getOfflineMode, enqueueOfflineAction } from './offlineQueue';

const API_BASE = '/api';

export const api = {
  // Current user header
  getHeaders(demoUser?: string) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };
    if (demoUser) {
      headers['X-Demo-User'] = demoUser;
    }
    return headers;
  },

  async resetDemo(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/reset`, { method: 'POST' });
    return res.json();
  },

  async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  async getAdaptersStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/adapters/status`);
    return res.json();
  },

  async login(username: string): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username })
    });
    if (!res.ok) throw new Error('Login failed');
    return res.json();
  },

  async getPatients(village?: string, demoUser?: string): Promise<Patient[]> {
    const url = village ? `${API_BASE}/patients?village=${encodeURIComponent(village)}` : `${API_BASE}/patients`;
    const res = await fetch(url, { headers: this.getHeaders(demoUser) });
    if (!res.ok) throw new Error('Failed to fetch patients');
    return res.json();
  },

  async getPatient(id: number, demoUser?: string): Promise<Patient> {
    const res = await fetch(`${API_BASE}/patients/${id}`, { headers: this.getHeaders(demoUser) });
    if (res.status === 403) {
      const err = await res.json();
      throw new Error(err.detail || 'Access Denied: 403 Forbidden');
    }
    if (!res.ok) throw new Error('Failed to fetch patient');
    return res.json();
  },

  async submitIntake(
    patientId: number,
    rawInput: string,
    language: string = 'hi',
    demoUser?: string
  ): Promise<SymptomIntakeResponse> {
    const res = await fetch(`${API_BASE}/symptom-intake`, {
      method: 'POST',
      headers: this.getHeaders(demoUser),
      body: JSON.stringify({
        patient_id: patientId,
        raw_input: rawInput,
        language,
        duration_days: 2
      })
    });
    if (!res.ok) throw new Error('Failed to process symptom intake');
    return res.json();
  },

  async getFacilities(): Promise<FacilityReadiness[]> {
    const res = await fetch(`${API_BASE}/facilities`);
    if (!res.ok) throw new Error('Failed to fetch facilities');
    return res.json();
  },

  async bookAppointment(
    payload: {
      patient_id: number;
      doctor_id: number;
      facility_id: number;
      scheduled_date: string;
      scheduled_time?: string;
      consultation_type?: string;
      reason?: string;
      idempotency_key?: string;
    },
    demoUser?: string
  ): Promise<Appointment> {
    if (getOfflineMode()) {
      enqueueOfflineAction('BOOK_APPOINTMENT', payload);
      // Return optimistic appointment
      return {
        id: Math.floor(Math.random() * 9000) + 1000,
        appointment_code: 'APT-OFFLINE-QUEUED',
        patient_id: payload.patient_id,
        doctor_id: payload.doctor_id,
        facility_id: payload.facility_id,
        scheduled_date: payload.scheduled_date,
        scheduled_time: payload.scheduled_time || '10:30 AM',
        consultation_type: payload.consultation_type || 'IN_PERSON',
        status: 'QUEUED_OFFLINE',
        reason: payload.reason,
        queue_token: 'T-OFFLINE',
        is_simulated: true,
        created_at: new Date().toISOString()
      };
    }

    const res = await fetch(`${API_BASE}/appointments`, {
      method: 'POST',
      headers: this.getHeaders(demoUser),
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to book appointment');
    return res.json();
  },

  async getAppointments(patientId?: number, demoUser?: string): Promise<Appointment[]> {
    const url = patientId ? `${API_BASE}/appointments?patient_id=${patientId}` : `${API_BASE}/appointments`;
    const res = await fetch(url, { headers: this.getHeaders(demoUser) });
    if (!res.ok) throw new Error('Failed to fetch appointments');
    return res.json();
  },

  async createEncounter(payload: any, demoUser?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/encounters`, {
      method: 'POST',
      headers: this.getHeaders(demoUser),
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to create clinical encounter');
    return res.json();
  },

  async getDiagnosticOrders(patientId?: number): Promise<DiagnosticOrder[]> {
    const url = patientId ? `${API_BASE}/diagnostics/orders?patient_id=${patientId}` : `${API_BASE}/diagnostics/orders`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch diagnostic orders');
    return res.json();
  },

  async getFollowUps(patientId?: number): Promise<FollowUpPlan[]> {
    const url = patientId ? `${API_BASE}/follow-ups?patient_id=${patientId}` : `${API_BASE}/follow-ups`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch follow-ups');
    return res.json();
  },

  async getTasks(status?: string): Promise<HealthWorkerTask[]> {
    const url = status ? `${API_BASE}/tasks?status=${status}` : `${API_BASE}/tasks`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch health worker tasks');
    return res.json();
  },

  async updateTask(
    taskId: number,
    payload: { status: string; visit_notes: string; outcome?: string; escalated_to_doctor_id?: number },
    demoUser?: string
  ): Promise<HealthWorkerTask> {
    if (getOfflineMode()) {
      enqueueOfflineAction('RESOLVE_TASK', { task_id: taskId, ...payload });
      return {
        id: taskId,
        patient_id: 2,
        task_type: 'MISSED_FOLLOW_UP',
        priority: 'HIGH',
        due_date: '2026-10-20',
        status: payload.status as any,
        visit_notes: payload.visit_notes + ' (Saved in offline queue)',
        outcome: payload.outcome,
        created_at: new Date().toISOString()
      };
    }

    const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
      method: 'PATCH',
      headers: this.getHeaders(demoUser),
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to update task');
    return res.json();
  },

  async getTimeline(patientId: number): Promise<CareTimelineEvent[]> {
    const res = await fetch(`${API_BASE}/timeline/${patientId}`);
    if (!res.ok) throw new Error('Failed to fetch timeline');
    return res.json();
  },

  async getAuditEvents(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/audit-events`);
    if (!res.ok) throw new Error('Failed to fetch audit events');
    return res.json();
  },

  async getAdminMetrics(): Promise<AdminMetrics> {
    const res = await fetch(`${API_BASE}/admin/metrics`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return res.json();
  }
};
