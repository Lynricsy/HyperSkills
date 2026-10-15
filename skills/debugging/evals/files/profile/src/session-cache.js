// In-memory session cache for the export worker.
import { loadSessionFromDb } from './db.js';

const sessionCache = new Map();

export async function getSession(id) {
  if (!sessionCache.has(id)) {
    sessionCache.set(id, await loadSessionFromDb(id));
  }
  return sessionCache.get(id);
}
