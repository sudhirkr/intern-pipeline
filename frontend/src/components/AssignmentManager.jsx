import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  fetchAssignments, createAssignment, updateAssignment, deleteAssignment,
  assignToCandidate, fetchAdminCandidates,
} from '../api/client';

const DIFFICULTY_CONFIG = {
  easy: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', label: 'Easy' },
  medium: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400', label: 'Medium' },
  hard: { bg: 'bg-rose-500/10', border: 'border-rose-500/20', text: 'text-rose-400', label: 'Hard' },
};

function DifficultyBadge({ difficulty }) {
  const c = DIFFICULTY_CONFIG[difficulty] || DIFFICULTY_CONFIG.medium;
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium ${c.bg} ${c.text} border ${c.border}`}>
      {c.label}
    </span>
  );
}

const EMPTY_FORM = {
  title: '',
  description: '',
  tech_stack: '',
  difficulty: 'medium',
  expected_outcome: '',
};

export default function AssignmentManager() {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editing, setEditing] = useState(null); // null=hidden, 'create'=creating, {..}=editing
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Assign-to-candidate modal state
  const [assignTarget, setAssignTarget] = useState(null); // assignment object
  const [candidates, setCandidates] = useState([]);
  const [assigning, setAssigning] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    if (!localStorage.getItem('admin_token')) {
      navigate('/login');
    }
  }, [navigate]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchAssignments();
      setAssignments(data.assignments);
    } catch (err) {
      console.error('Failed to load assignments:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => {
    setEditing('create');
    setForm(EMPTY_FORM);
    setError('');
  };

  const openEdit = (a) => {
    setEditing(a);
    setForm({
      title: a.title,
      description: a.description,
      tech_stack: a.tech_stack || '',
      difficulty: a.difficulty || 'medium',
      expected_outcome: a.expected_outcome || '',
    });
    setError('');
  };

  const closeForm = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setError('');
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (editing && editing !== 'create') {
        await updateAssignment(editing.id, form);
      } else {
        await createAssignment(form);
      }
      setForm(EMPTY_FORM);
      setEditing(null);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this assignment? This will also remove all candidate links.')) return;
    try {
      await deleteAssignment(id);
      load();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const openAssignModal = async (assignment) => {
    setAssignTarget(assignment);
    setSelectedCandidateId('');
    try {
      const data = await fetchAdminCandidates({ limit: 100 });
      setCandidates(data.candidates);
    } catch (err) {
      console.error('Failed to load candidates:', err);
    }
  };

  const handleAssign = async () => {
    if (!selectedCandidateId || !assignTarget) return;
    setAssigning(true);
    try {
      await assignToCandidate(assignTarget.id, parseInt(selectedCandidateId));
      setAssignTarget(null);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setAssigning(false);
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
              <p className="text-xs text-slate-500">Assignment Manager</p>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <nav className="flex items-center gap-4 mr-4">
              <Link to="/admin" className="text-sm text-slate-400 hover:text-white transition-colors">Candidates</Link>
              <Link to="/admin/assignments" className="text-sm text-white font-medium">Assignments</Link>
            </nav>
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
          {/* Assignment list */}
          <div className={`${editing ? 'w-1/2' : 'w-full'} transition-all duration-300`}>
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">Assignments ({assignments.length})</h2>
              <button
                onClick={openCreate}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl transition-colors"
              >
                + Create Assignment
              </button>
            </div>

            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-5 animate-pulse">
                    <div className="h-4 bg-slate-800 rounded w-1/3 mb-2" />
                    <div className="h-3 bg-slate-800 rounded w-2/3" />
                  </div>
                ))}
              </div>
            ) : assignments.length === 0 ? (
              <div className="text-center py-16">
                <h3 className="text-lg font-semibold text-slate-300 mb-1">No assignments yet</h3>
                <p className="text-sm text-slate-500">Create your first assignment to get started</p>
              </div>
            ) : (
              <div className="space-y-4">
                {assignments.map((a) => (
                  <div key={a.id} className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-5 hover:border-slate-700/50 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-base font-semibold text-white">{a.title}</h3>
                          <DifficultyBadge difficulty={a.difficulty} />
                        </div>
                        <p className="text-sm text-slate-400 mb-2 line-clamp-2">{a.description}</p>
                        {a.tech_stack && (
                          <p className="text-xs text-slate-500">
                            <span className="text-slate-400 font-medium">Tech:</span> {a.tech_stack}
                          </p>
                        )}
                        {a.expected_outcome && (
                          <p className="text-xs text-slate-500 mt-1">
                            <span className="text-slate-400 font-medium">Expected:</span> {a.expected_outcome}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-800/50">
                      <button
                        onClick={() => openEdit(a)}
                        className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => openAssignModal(a)}
                        className="px-3 py-1.5 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border border-blue-500/20 text-xs font-medium rounded-lg transition-colors"
                      >
                        Assign to Candidate
                      </button>
                      <button
                        onClick={() => handleDelete(a.id)}
                        className="px-3 py-1.5 bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/20 text-xs font-medium rounded-lg transition-colors ml-auto"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Create/Edit form panel */}
          {editing ? (
            <div className="w-1/2 sticky top-24 self-start">
              <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">
                    {editing === 'create' ? 'Create Assignment' : 'Edit Assignment'}
                  </h3>
                  <button
                    onClick={() => { setEditing(null); setForm(EMPTY_FORM); setError(''); }}
                    className="text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {error && (
                  <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-sm text-rose-400">
                    {error}
                  </div>
                )}

                <form onSubmit={handleSave} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Title *</label>
                    <input
                      type="text"
                      value={form.title}
                      onChange={(e) => setForm({ ...form, title: e.target.value })}
                      required
                      className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                      placeholder="Assignment title"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Description *</label>
                    <textarea
                      value={form.description}
                      onChange={(e) => setForm({ ...form, description: e.target.value })}
                      required
                      rows={3}
                      className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all resize-none"
                      placeholder="Describe the assignment task"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Tech Stack</label>
                    <input
                      type="text"
                      value={form.tech_stack}
                      onChange={(e) => setForm({ ...form, tech_stack: e.target.value })}
                      className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                      placeholder="e.g. Python, FastAPI, React"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Difficulty</label>
                    <select
                      value={form.difficulty}
                      onChange={(e) => setForm({ ...form, difficulty: e.target.value })}
                      className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Expected Outcome</label>
                    <textarea
                      value={form.expected_outcome}
                      onChange={(e) => setForm({ ...form, expected_outcome: e.target.value })}
                      rows={2}
                      className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all resize-none"
                      placeholder="What should the candidate deliver?"
                    />
                  </div>
                  <div className="flex gap-3 pt-2">
                    <button
                      type="submit"
                      disabled={saving}
                      className="flex-1 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-colors"
                    >
                      {saving ? 'Saving...' : editing === 'create' ? 'Create Assignment' : 'Update Assignment'}
                    </button>
                    <button
                      type="button"
                      onClick={() => { setEditing(null); setForm(EMPTY_FORM); setError(''); }}
                      className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          ) : null}
        </div>
      </main>

      {/* Assign to Candidate Modal */}
      {assignTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800/50 rounded-2xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-bold text-white mb-1">Assign to Candidate</h3>
            <p className="text-sm text-slate-400 mb-4">
              Assigning: <span className="text-white font-medium">{assignTarget.title}</span>
            </p>

            {error && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-sm text-rose-400">
                {error}
              </div>
            )}

            <div className="mb-4">
              <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Select Candidate</label>
              <select
                value={selectedCandidateId}
                onChange={(e) => setSelectedCandidateId(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
              >
                <option value="">— Choose a candidate —</option>
                {candidates.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.email})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleAssign}
                disabled={!selectedCandidateId || assigning}
                className="flex-1 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-colors"
              >
                {assigning ? 'Assigning...' : 'Assign'}
              </button>
              <button
                onClick={() => { setAssignTarget(null); setError(''); }}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
