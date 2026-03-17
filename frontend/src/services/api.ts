import type { TranslationResponse, SessionContext } from '../types';

// In Docker (production) the Nginx gateway proxies all traffic through port 80.
// In local dev (npm run dev), set VITE_LLM_URL=http://localhost:8002 in .env.local.
const LLM_API_URL = import.meta.env.VITE_LLM_URL ?? '';

// Translate sign sequence to natural language
export async function translateSigns(
  signSequence: string[],
  sessionId: string,
  context?: string,
  language: string = 'en'
): Promise<TranslationResponse> {
  const response = await fetch(`${LLM_API_URL}/api/v1/translate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      sign_sequence: signSequence,
      session_id: sessionId,
      context,
      language,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Create new session
export async function createSession(): Promise<{ session_id: string; message: string }> {
  const response = await fetch(`${LLM_API_URL}/api/v1/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.status}`);
  }

  return response.json();
}

// Get session context
export async function getSessionContext(sessionId: string): Promise<SessionContext> {
  const response = await fetch(`${LLM_API_URL}/api/v1/context/${sessionId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to get session context: ${response.status}`);
  }

  return response.json();
}

// Clear session
export async function clearSession(sessionId: string): Promise<{ message: string; session_id: string }> {
  const response = await fetch(`${LLM_API_URL}/api/v1/context/${sessionId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to clear session: ${response.status}`);
  }

  return response.json();
}

// Combined health check (goes through gateway /health)
export async function checkHealth(): Promise<{ status: string }> {
  const response = await fetch('/health');
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return response.json();
}

export async function checkMediaPipeHealth(): Promise<{ status: string }> {
  const response = await fetch('/health/mediapipe');
  if (!response.ok) throw new Error(`MediaPipe health check failed: ${response.status}`);
  return response.json();
}

export async function checkLLMHealth(): Promise<{ status: string }> {
  const response = await fetch(`${LLM_API_URL}/health`);
  if (!response.ok) throw new Error(`LLM health check failed: ${response.status}`);
  return response.json();
}
