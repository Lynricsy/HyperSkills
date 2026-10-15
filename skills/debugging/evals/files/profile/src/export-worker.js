import { getSession } from './session-cache.js';
import { renderExport } from './render.js';

const inFlight = new Set();

export async function runExport(job) {
  inFlight.add(job.id);
  try {
    const session = await getSession(job.sessionId);
    return await renderExport(session, job);
  } finally {
    inFlight.delete(job.id);
  }
}
