const API_BASE = '/api';

export async function fetchCandidates({ skip = 0, limit = 50, search = '' } = {}) {
  const params = new URLSearchParams({ skip, limit });
  if (search) params.set('search', search);
  const res = await fetch(`${API_BASE}/candidates?${params}`);
  if (!res.ok) throw new Error('Failed to fetch candidates');
  return res.json();
}

export async function fetchCandidate(id) {
  const res = await fetch(`${API_BASE}/candidates/${id}`);
  if (!res.ok) throw new Error('Candidate not found');
  return res.json();
}

export async function createCandidate(formData) {
  // formData should be a FormData object (supports file uploads)
  const res = await fetch(`${API_BASE}/candidates`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to create candidate');
  }
  return res.json();
}

export async function parseResume({ file, resumeUrl }) {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  }
  if (resumeUrl) {
    formData.append('resume_url', resumeUrl);
  }

  const res = await fetch(`${API_BASE}/candidates/parse-resume`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to parse resume');
  }
  return res.json();
}
