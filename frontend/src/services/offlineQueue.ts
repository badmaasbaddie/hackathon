import { OfflineAction } from '../types';
import { authHeaders } from './api';

const QUEUE_KEY = 'swasthyasetu_offline_queue';
const OFFLINE_TOGGLE_KEY = 'swasthyasetu_offline_mode';

export const getOfflineMode = (): boolean => {
  try { return localStorage.getItem(OFFLINE_TOGGLE_KEY) === 'true'; } catch { return false; }
};

export const setOfflineMode = (val: boolean): void => {
  try { localStorage.setItem(OFFLINE_TOGGLE_KEY, val ? 'true' : 'false'); } catch { /* storage unavailable */ }
  window.dispatchEvent(new Event('offline-mode-changed'));
};

export const getOfflineQueue = (): OfflineAction[] => {
  try {
    const data = localStorage.getItem(QUEUE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
};

export const enqueueOfflineAction = (
  action_type: 'BOOK_APPOINTMENT' | 'RESOLVE_TASK',
  payload: any
): OfflineAction => {
  const queue = getOfflineQueue();
  const newAction: OfflineAction = {
    id: 'act-' + Math.random().toString(36).substring(2, 9),
    idempotency_key: 'idem-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7),
    action_type,
    payload,
    created_at: new Date().toISOString(),
    status: 'QUEUED'
  };
  queue.push(newAction);
  try { localStorage.setItem(QUEUE_KEY, JSON.stringify(queue)); } catch { /* storage unavailable */ }
  window.dispatchEvent(new Event('offline-queue-updated'));
  return newAction;
};

export const clearOfflineQueue = (): void => {
  try { localStorage.removeItem(QUEUE_KEY); } catch { /* storage unavailable */ }
  window.dispatchEvent(new Event('offline-queue-updated'));
};

export const syncOfflineBatch = async (userId: number = 1): Promise<{ synced_count: number; results: any[] }> => {
  const queue = getOfflineQueue(); // failed items are retried; idempotency keys make this safe
  if (queue.length === 0) {
    return { synced_count: 0, results: [] };
  }

  const res = await fetch('/api/sync/batch', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      user_id: userId,
      actions: queue.map(q => ({
        idempotency_key: q.idempotency_key,
        action_type: q.action_type,
        payload: q.payload
      }))
    })
  });

  if (!res.ok) {
    throw new Error('Failed to sync offline actions with server');
  }

  const data = await res.json();
  // Keep only actions the server rejected so the user can see and retry them.
  const failed = new Set((data.results || []).filter((r: any) => r.status === 'FAILED').map((r: any) => r.idempotency_key));
  const remaining = getOfflineQueue().filter(q => failed.has(q.idempotency_key)).map(q => ({ ...q, status: 'FAILED' as const }));
  try {
    if (remaining.length) localStorage.setItem(QUEUE_KEY, JSON.stringify(remaining));
    else localStorage.removeItem(QUEUE_KEY);
  } catch { /* storage unavailable */ }
  window.dispatchEvent(new Event('offline-queue-updated'));
  return data;
};
