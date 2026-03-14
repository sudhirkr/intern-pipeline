const API_BASE = '/api';

// ── Token helpers ──
function getAdminToken() {
  return localStorage.getItem('admin_token');
}

function authHeaders() {
  const token = getAdminToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Public / candidate endpoints ──

export async function fetchCandidateByToken(token) {
  const res = await fetch(`${API_BASE}/candidates/by-token/${token}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Application not found');
  }
  return res.json();
}

export async function updateCandidateByToken(token, data) {
  const res = await fetch(`${API_BASE}/candidates/by-token/${token}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update application');
  }
  return res.json();
}

export async function createCandidate(formData) {
  const res = await fetch(`${API_BASE}/candidates`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create candidate');
  }
  return res.json();
}

export async function parseResume({ file, resumeUrl }) {
  const formData = new FormData();
  if (file) formData.append('file', file);
  if (resumeUrl) formData.append('resume_url', resumeUrl);

  const res = await fetch(`${API_BASE}/candidates/parse-resume`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to parse resume');
  }
  return res.json();
}

// ── Admin auth ──

export async function adminLogin(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }
  return res.json();
}

// ── Admin endpoints ──

export async function fetchAdminCandidates({ skip = 0, limit = 50, search = '', status = '' } = {}) {
  const params = new URLSearchParams({ skip, limit });
  if (search) params.set('search', search);
  if (status) params.set('status', status);
  const res = await fetch(`${API_BASE}/admin/candidates?${params}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch candidates');
  return res.json();
}

export async function fetchAdminCandidate(id) {
  const res = await fetch(`${API_BASE}/admin/candidates/${id}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Candidate not found');
  return res.json();
}

export async function updateCandidateStatus(id, status) {
  const res = await fetch(`${API_BASE}/admin/candidates/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update status');
  }
  return res.json();
}

// ── Persona endpoints ──

export async function generatePersona(candidateId) {
  const res = await fetch(`${API_BASE}/candidates/${candidateId}/generate-persona`, {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to generate persona');
  }
  return res.json();
}

export async function fetchPersona(candidateId, token = null) {
  const params = token ? `?token=${token}` : '';
  const headers = token
    ? { Authorization: `Bearer ${token}` }
    : authHeaders();
  const res = await fetch(`${API_BASE}/candidates/${candidateId}/persona${params}`, {
    headers,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch persona');
  }
  return res.json();
}
