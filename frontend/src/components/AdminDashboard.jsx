import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { fetchAdminCandidates, fetchAdminCandidate, updateCandidateStatus, fetchPersona } from '../api/client';
import PersonaCard from './PersonaCard';

const STATUS_OPTIONS = ['submitted', 'reviewing', 'accepted', 'rejected'];

const STATUS_CONFIG = {
  submitted: { bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-400', label: 'Submitted' },
  reviewing: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400', label: 'Reviewing' },
  accepted: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', label: 'Accepted' },
  rejected: { bg: 'bg-rose-500/10', border: 'border-rose-500/20', text: 'text-rose-400', label: 'Rejected' },
};

function StatusBadge({ status }) {
  const c = STATUS_CONFIG[status] || STATUS_CONFIG.submitted;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${c.bg} ${c.text} border ${c.border}`}>
      {c.label}
    </span>
  );
}

function DetailField({ label, value }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">{label}</dt>
      <dd className="text-sm text-white">{value || <span className="text-slate-600">—</span>}</dd>
    </div>
  );
}

export default function AdminDashboard() {
  const [candidates, setCandidates] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [selectedPersonaLoading, setSelectedPersonaLoading] = useState(false);
  const navigate = useNavigate();

  // Check auth
  useEffect(() => {
    if (!localStorage.getItem('admin_token')) {
      navigate('/login');
    }
  }, [navigate]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchAdminCandidates({ search, status: statusFilter, limit: 100 });
      setCandidates(data.candidates);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load:', err);
      if (err.message.includes('401') || err.message.includes('Not authenticated')) {
        localStorage.removeItem('admin_token');
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, navigate]);

  useEffect(() => {
    load();
  }, [load]);

  const selectCandidate = async (id) => {
    setDetailLoading(true);
    setSelectedPersonaLoading(true);
    try {
      const [data, personaData] = await Promise.all([
        fetchAdminCandidate(id),
        fetchPersona(id).catch(() => ({ persona: null, persona_generated: false })),
      ]);
      setSelected(data);
      setSelectedPersona(personaData);
    } catch (err) {
      console.error('Failed to load candidate:', err);
    } finally {
      setDetailLoading(false);
      setSelectedPersonaLoading(false);
    }
  };

  const handleStatusUpdate = async (newStatus) => {
    if (!selected) return;
    setUpdating(true);
    try {
      await updateCandidateStatus(selected.id, newStatus);
      setSelected({ ...selected, status: newStatus });
      load(); // refresh list
    } catch (err) {
      console.error('Failed to update status:', err);
    } finally {
      setUpdating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_email');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-925">
      {/* Header */}
      <header className="border-b border-slate-800/50 bg-slate-925/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <Link to="/admin" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">Intern Pipeline</h1>
              <p className="text-xs text-slate-500">Admin Dashboard</p>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">{localStorage.getItem('admin_email')}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/50 text-slate-300 text-sm rounded-xl transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Candidate list */}
          <div className={`${selected ? 'w-1/2' : 'w-full'} transition-all duration-300`}>
            {/* Filters */}
            <div className="mb-6 flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="Search by name, email, or college..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 pl-10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                />
                <svg className="absolute left-3 top-3 w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
              >
                <option value="">All Statuses</option>
                {STATUS_OPTIONS.map(s => (
                  <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <p className="text-sm text-slate-400">
                <span className="font-semibold text-slate-200">{total}</span> candidate{total !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Table */}
            {loading ? (
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-4 animate-pulse">
                    <div className="h-4 bg-slate-800 rounded w-1/3 mb-2" />
                    <div className="h-3 bg-slate-800 rounded w-1/2" />
                  </div>
                ))}
              </div>
            ) : candidates.length === 0 ? (
              <div className="text-center py-16">
                <h3 className="text-lg font-semibold text-slate-300 mb-1">No candidates found</h3>
                <p className="text-sm text-slate-500">Try adjusting your search or filters</p>
              </div>
            ) : (
              <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-800/50">
                      <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Name</th>
                      <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Email</th>
                      <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">College</th>
                      <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Availability</th>
                      <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Persona</th>
                      <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.map((c) => (
                      <tr
                        key={c.id}
                        onClick={() => selectCandidate(c.id)}
                        className={`border-b border-slate-800/30 cursor-pointer hover:bg-slate-800/30 transition-colors ${selected?.id === c.id ? 'bg-blue-500/5' : ''}`}
                      >
                        <td className="px-4 py-3 text-sm font-medium text-white">{c.name}</td>
                        <td className="px-4 py-3 text-sm text-slate-400">{c.email}</td>
                        <td className="px-4 py-3 text-sm text-slate-400">{c.college || '—'}</td>
                        <td className="px-4 py-3 text-sm text-slate-400 capitalize">{c.availability?.replace('_', ' ') || '—'}</td>
                        <td className="px-4 py-3">
                          {c.persona ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
                              ✓ Generated
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium bg-slate-800 text-slate-500 border border-slate-700/50">
                              — Pending
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Detail panel */}
          {selected && (
            <div className="w-1/2 sticky top-24 self-start">
              <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">{selected.name}</h3>
                  <button
                    onClick={() => setSelected(null)}
                    className="text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {detailLoading ? (
                  <div className="flex justify-center py-8">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : (
                  <>
                    {/* Status update buttons */}
                    <div className="mb-6">
                      <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Update Status</p>
                      <div className="flex flex-wrap gap-2">
                        {STATUS_OPTIONS.map(s => (
                          <button
                            key={s}
                            onClick={() => handleStatusUpdate(s)}
                            disabled={updating || selected.status === s}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                              selected.status === s
                                ? `${STATUS_CONFIG[s].bg} ${STATUS_CONFIG[s].text} border ${STATUS_CONFIG[s].border} cursor-default`
                                : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/50'
                            }`}
                          >
                            {STATUS_CONFIG[s].label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Details */}
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <DetailField label="Email" value={selected.email} />
                        <DetailField label="Phone" value={selected.phone} />
                        <DetailField label="College" value={selected.college} />
                        <DetailField label="Degree" value={selected.degree} />
                        <DetailField label="Year" value={selected.year} />
                        <DetailField label="Availability" value={selected.availability?.replace('_', ' ')} />
                        <DetailField label="Learning Style" value={selected.learning_style} />
                      </div>
                      <DetailField label="Skills" value={selected.skills} />
                      <DetailField label="Projects" value={selected.projects} />
                      <DetailField label="Work Experience" value={selected.work_experience} />
                      <DetailField label="Interests" value={selected.interests} />
                      <DetailField label="Motivation" value={selected.motivation} />
                      <DetailField label="Portfolio Links" value={selected.portfolio_links} />
                      <DetailField label="Preferred Tech Stack" value={selected.preferred_tech_stack} />
                      <DetailField label="AI Tool Usage" value={selected.ai_tool_usage} />
                      <DetailField label="Challenge Solved" value={selected.challenge_solved} />
                    </div>

                    {/* Persona */}
                    <div className="mt-6">
                      {selectedPersonaLoading ? (
                        <div className="flex justify-center py-4">
                          <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                        </div>
                      ) : (
                        <PersonaCard
                          candidateId={selected.id}
                          persona={selectedPersona?.persona}
                          personaGenerated={selectedPersona?.persona_generated}
                          isAdmin={true}
                          onPersonaGenerated={(newPersona) => {
                            setSelectedPersona({ persona: newPersona, persona_generated: true });
                            load(); // refresh list to show persona indicator
                          }}
                        />
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
