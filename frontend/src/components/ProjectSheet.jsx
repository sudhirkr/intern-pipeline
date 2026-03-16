import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';

function LinkIcon() {
  return (
    <svg className="w-3.5 h-3.5 inline ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
    </svg>
  );
}

function ExternalLink({ href, children }) {
  if (!href) return <span className="text-slate-600">—</span>;
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-blue-400 hover:text-blue-300 underline underline-offset-2 inline-flex items-center"
    >
      {children || 'View'}
      <LinkIcon />
    </a>
  );
}

function AttendanceBadge({ value }) {
  if (!value) return null;
  const lower = value.toLowerCase();
  if (lower === 'present') {
    return <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Present</span>;
  }
  if (lower === 'absent') {
    return <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">Absent</span>;
  }
  return <span className="text-slate-400 text-xs">{value}</span>;
}

function AttendanceStats({ projects }) {
  let present = 0, absent = 0, noData = 0, total = 0;
  projects.forEach(p => {
    p.students.forEach(s => {
      total++;
      const v = (s.attendance || '').toLowerCase();
      if (v === 'present') present++;
      else if (v === 'absent') absent++;
      else noData++;
    });
  });
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6">
      <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3">
        <p className="text-2xl font-bold text-emerald-400">{present}</p>
        <p className="text-xs text-emerald-500/80">Present</p>
      </div>
      <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl px-4 py-3">
        <p className="text-2xl font-bold text-rose-400">{absent}</p>
        <p className="text-xs text-rose-500/80">Absent</p>
      </div>
      <div className="bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-3">
        <p className="text-2xl font-bold text-slate-400">{noData}</p>
        <p className="text-xs text-slate-500">No Data</p>
      </div>
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl px-4 py-3">
        <p className="text-2xl font-bold text-blue-400">{projects.length}</p>
        <p className="text-xs text-blue-500/80">Projects</p>
      </div>
    </div>
  );
}

function ProjectCard({ project, evaluation, onEvaluate }) {
  const [editing, setEditing] = useState(false);
  const [marks, setMarks] = useState(evaluation?.marks ?? '');
  const [feedback, setFeedback] = useState(evaluation?.feedback ?? '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    const m = parseInt(marks, 10);
    if (isNaN(m) || m < 0 || m > 10) return;
    setSaving(true);
    try {
      await onEvaluate(project.project_name, m, feedback);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const scoreColor = (s) => {
    if (s >= 8) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (s >= 5) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    if (s >= 3) return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl overflow-hidden hover:border-slate-700/50 transition-colors">
      {/* Project header */}
      <div className="px-4 sm:px-5 py-3 sm:py-4 border-b border-slate-800/50 bg-slate-800/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-3 min-w-0">
            <h3 className="text-base font-semibold text-white">{project.project_name}</h3>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            {/* Score badge */}
            {!editing ? (
              <button
                onClick={() => setEditing(true)}
                className={`shrink-0 inline-flex items-center px-2.5 py-1 rounded-lg text-sm font-bold border cursor-pointer hover:ring-2 hover:ring-blue-500/40 transition-all ${
                  evaluation?.marks != null
                    ? scoreColor(evaluation.marks)
                    : 'text-slate-500 bg-slate-800/60 border-slate-700/40'
                }`}
                title="Click to evaluate"
              >
                {evaluation?.marks != null ? `${evaluation.marks}/10` : '—/10'}
              </button>
            ) : null}
            {project.project_link && (
              <ExternalLink href={project.project_link}>ChatGPT</ExternalLink>
            )}
            {project.dashboard_link && (
              <ExternalLink href={project.dashboard_link}>Dashboard</ExternalLink>
            )}
            {project.github_repo_link && (
              <ExternalLink href={project.github_repo_link}>GitHub</ExternalLink>
            )}
          </div>
        </div>

        {/* Inline evaluation form */}
        {editing && (
          <div className="mt-3 p-3 bg-slate-950/50 rounded-lg border border-slate-700/30">
            <div className="flex items-center gap-3 mb-2">
              <label className="text-sm text-slate-400">Marks:</label>
              <input
                type="number"
                min="0"
                max="10"
                value={marks}
                onChange={e => setMarks(e.target.value)}
                className="w-16 bg-slate-800 border border-slate-700/50 rounded-lg px-2 py-1 text-white text-center text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                autoFocus
              />
              <span className="text-xs text-slate-500">/10</span>
            </div>
            <textarea
              placeholder="Feedback (optional)..."
              value={feedback}
              onChange={e => setFeedback(e.target.value)}
              rows={2}
              className="w-full bg-slate-800 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none mb-2"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => { setEditing(false); setMarks(evaluation?.marks ?? ''); setFeedback(evaluation?.feedback ?? ''); }}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        )}

        {/* Feedback display */}
        {!editing && evaluation?.feedback && (
          <p className="mt-2 text-xs text-slate-400 italic">{evaluation.feedback}</p>
        )}
      </div>

      {/* Students */}
      <div className="divide-y divide-slate-800/30">
        {project.students.map((student, i) => (
          <div key={i} className="px-4 sm:px-5 py-3 flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <span className="text-sm font-medium text-white truncate">{student.student_name || '—'}</span>
              <p className="text-xs text-slate-400 truncate mt-0.5">{student.email || '—'}</p>
            </div>
            <AttendanceBadge value={student.attendance} />
          </div>
        ))}
        {project.students.length === 0 && (
          <div className="px-4 sm:px-5 py-3 text-sm text-slate-500">No students listed</div>
        )}
      </div>
    </div>
  );
}

function MobileNav({ current }) {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_email');
    navigate('/login');
  };

  return (
    <div className="relative sm:hidden">
      <button
        onClick={() => setOpen(!open)}
        className="p-2 text-slate-400 hover:text-white transition-colors"
        aria-label="Menu"
      >
        {open ? (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-2 w-56 bg-slate-900 border border-slate-700/50 rounded-xl shadow-2xl shadow-black/40 overflow-hidden z-50">
          <Link
            to="/admin"
            onClick={() => setOpen(false)}
            className={`block px-4 py-3 text-sm transition-colors ${current === 'candidates' ? 'text-white bg-blue-500/10 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
          >
            Candidates
          </Link>
          <Link
            to="/admin/assignments"
            onClick={() => setOpen(false)}
            className={`block px-4 py-3 text-sm transition-colors ${current === 'assignments' ? 'text-white bg-blue-500/10 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
          >
            Assignments
          </Link>
          <Link
            to="/admin/projects"
            onClick={() => setOpen(false)}
            className={`block px-4 py-3 text-sm transition-colors ${current === 'projects' ? 'text-white bg-blue-500/10 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
          >
            Projects
          </Link>
          <div className="border-t border-slate-800/50" />
          <div className="px-4 py-2 text-xs text-slate-500">{localStorage.getItem('admin_email')}</div>
          <button
            onClick={handleLogout}
            className="block w-full text-left px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            Logout
          </button>
        </div>
      )}
    </div>
  );
}

function DesktopNav() {
  return (
    <nav className="hidden sm:flex items-center gap-4 mr-4">
      <Link to="/admin" className="text-sm text-slate-400 hover:text-white transition-colors">Candidates</Link>
      <Link to="/admin/assignments" className="text-sm text-slate-400 hover:text-white transition-colors">Assignments</Link>
      <Link to="/admin/projects" className="text-sm text-white font-medium">Projects</Link>
    </nav>
  );
}

export default function ProjectSheet() {
  const [projects, setProjects] = useState([]);
  const [evaluations, setEvaluations] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [sheetUrl, setSheetUrl] = useState('');
  const [activeUrl, setActiveUrl] = useState('');
  const navigate = useNavigate();

  const fetchEvaluations = useCallback(() => {
    fetch('/api/admin/projects/evaluations', {
      headers: { Authorization: `Bearer ${localStorage.getItem('admin_token')}` },
    })
      .then(res => res.ok ? res.json() : {})
      .then(data => setEvaluations(data || {}))
      .catch(() => {});
  }, []);

  const handleEvaluate = useCallback(async (projectName, marks, feedback) => {
    const res = await fetch(`/api/admin/projects/evaluations/${encodeURIComponent(projectName)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
      },
      body: JSON.stringify({ marks, feedback: feedback || null }),
    });
    if (!res.ok) throw new Error('Failed to save evaluation');
    const saved = await res.json();
    setEvaluations(prev => ({ ...prev, [projectName]: saved }));
  }, []);

  const fetchProjects = useCallback((url) => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (url) params.set('sheet_url', url);

    fetch(`/api/admin/projects/sheet?${params.toString()}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('admin_token')}` },
    })
      .then(res => {
        if (!res.ok) throw new Error(res.status === 401 ? 'Not authenticated' : 'Failed to fetch projects');
        return res.json();
      })
      .then(data => setProjects(Array.isArray(data) ? data : []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!localStorage.getItem('admin_token')) {
      navigate('/login');
      return;
    }
    fetchProjects('');
    fetchEvaluations();
  }, [navigate, fetchProjects, fetchEvaluations]);

  const handleLoadSheet = (e) => {
    e.preventDefault();
    setActiveUrl(sheetUrl);
    fetchProjects(sheetUrl);
  };

  const handleUseDefault = () => {
    setSheetUrl('');
    setActiveUrl('');
    fetchProjects('');
  };

  const filtered = search
    ? projects.filter(p =>
        (p.project_name || '').toLowerCase().includes(search.toLowerCase()) ||
        p.students.some(s =>
          (s.student_name || '').toLowerCase().includes(search.toLowerCase()) ||
          (s.email || '').toLowerCase().includes(search.toLowerCase())
        )
      )
    : projects;

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_email');
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-925 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-925 flex items-center justify-center">
        <div className="text-center">
          <p className="text-rose-400 mb-2">{error}</p>
          <button onClick={() => fetchProjects(activeUrl)} className="text-sm text-blue-400 hover:text-blue-300">Retry</button>
        </div>
      </div>
    );
  }

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
            <DesktopNav />
            <MobileNav current="projects" />
            <span className="hidden sm:inline text-sm text-slate-400">{localStorage.getItem('admin_email')}</span>
            <button
              onClick={handleLogout}
              className="hidden sm:block px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/50 text-slate-300 text-sm rounded-xl transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        {/* Google Sheet URL input */}
        <form onSubmit={handleLoadSheet} className="mb-6 flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Paste Google Sheet URL to load custom data..."
              value={sheetUrl}
              onChange={e => setSheetUrl(e.target.value)}
              className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              className="px-5 py-3 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl transition-colors shadow-lg shadow-blue-500/20"
            >
              Load Sheet
            </button>
            {activeUrl && (
              <button
                type="button"
                onClick={handleUseDefault}
                className="px-5 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700/50 text-slate-300 text-sm rounded-xl transition-colors"
              >
                Use Default
              </button>
            )}
          </div>
        </form>

        {activeUrl && (
          <div className="mb-4 text-xs text-slate-500 truncate">
            Loaded from: {activeUrl}
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-xl font-bold text-white">Student Projects</h2>
            <p className="text-sm text-slate-400">{projects.length} projects, grouped by team</p>
          </div>
          <div className="relative w-full sm:w-72">
            <input
              type="text"
              placeholder="Search by name, email, or project..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-3 pl-10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
            />
            <svg className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        <AttendanceStats projects={projects} />

        {/* Project cards grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filtered.map((project, i) => (
            <ProjectCard key={i} project={project} evaluation={evaluations[project.project_name]} onEvaluate={handleEvaluate} />
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-12 text-sm text-slate-500">
            {search ? 'No projects match your search' : 'No projects available'}
          </div>
        )}
      </main>
    </div>
  );
}
