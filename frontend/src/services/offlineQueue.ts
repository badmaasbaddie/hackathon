import { OfflineAction } from '../types';

const QUEUE_KEY = 'swasthyasetu_offline_queue';
const OFFLINE_TOGGLE_KEY = 'swasthyasetu_offline_mode';

export const getOfflineMode = (): boolean => {
  return localStorage.getItem(OFFLINE_TOGGLE_KEY) === 'true';
};

export const setOfflineMode = (val: boolean): void => {
  localStorage.setItem(OFFLINE_TOGGLE_KEY, val ? 'true' : 'false');
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
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
  window.dispatchEvent(new Event('offline-queue-updated'));
  return newAction;
};

export const clearOfflineQueue = (): void => {
  localStorage.removeItem(QUEUE_KEY);
  window.dispatchEvent(new Event('offline-queue-updated'));
};

export const syncOfflineBatch = async (userId: number = 1): Promise<{ synced_count: number; results: any[] }> => {
  const queue = getOfflineQueue().filter(item => item.status === 'QUEUED');
  if (queue.length === 0) {
    return { synced_count: 0, results: [] };
  }

  const res = await fetch('/api/sync/batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
  clearOfflineQueue();
  return data;
};
