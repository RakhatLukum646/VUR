import type { TranslationResponse, SessionContext } from '../types';

const LLM_API_URL = 'http://localhost:8002';
const API_GATEWAY_URL = 'http://localhost:8000';

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

// Health check
export async function checkHealth(): Promise<{
  status: string;
  timestamp: string;
  services: {
    api_gateway: string;
    media_pipe: string;
    llm: string;
  };
}> {
  const response = await fetch(`${API_GATEWAY_URL}/api/v1/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}

// Check MediaPipe service health
export async function checkMediaPipeHealth(): Promise<{ status: string }> {
  const response = await fetch('http://localhost:8001/api/v1/health', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`MediaPipe health check failed: ${response.status}`);
  }

  return response.json();
}

// Check LLM service health
export async function checkLLMHealth(): Promise<{ status: string }> {
  const response = await fetch(`${LLM_API_URL}/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`LLM health check failed: ${response.status}`);
  }

  return response.json();
}
