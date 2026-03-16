import { useState, useEffect, useMemo } from 'react';
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
  if (!value) return <span className="text-slate-600 text-xs">—</span>;
  const lower = value.toLowerCase();
  if (lower === 'present') {
    return <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Present</span>;
  }
  if (lower === 'absent') {
    return <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">Absent</span>;
  }
  return <span className="text-slate-400 text-xs">{value}</span>;
}

function AttendanceStats({ rows }) {
  let present = 0, absent = 0, noData = 0;
  rows.forEach(r => {
    const v = (r.attendance || '').toLowerCase();
    if (v === 'present') present++;
    else if (v === 'absent') absent++;
    else noData++;
  });
  return (
    <div className="flex flex-wrap gap-4 sm:gap-6 mb-6">
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
        <p className="text-2xl font-bold text-blue-400">{rows.length}</p>
        <p className="text-xs text-blue-500/80">Total</p>
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (!localStorage.getItem('admin_token')) {
      navigate('/login');
      return;
    }
    fetch('/api/admin/projects/sheet', {
      headers: { Authorization: `Bearer ${localStorage.getItem('admin_token')}` },
    })
      .then(res => {
        if (!res.ok) throw new Error(res.status === 401 ? 'Not authenticated' : 'Failed to fetch projects');
        return res.json();
      })
      .then(data => setProjects(Array.isArray(data) ? data : []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [navigate]);

  const filtered = useMemo(() => {
    if (!search) return projects;
    const q = search.toLowerCase();
    return projects.filter(r =>
      (r.student_name || '').toLowerCase().includes(q) ||
      (r.project_name || '').toLowerCase().includes(q) ||
      (r.email || '').toLowerCase().includes(q)
    );
  }, [projects, search]);

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
          <button onClick={() => window.location.reload()} className="text-sm text-blue-400 hover:text-blue-300">Retry</button>
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
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-xl font-bold text-white">Student Projects</h2>
            <p className="text-sm text-slate-400">Attendance, dashboard links &amp; GitHub repos</p>
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

        <AttendanceStats rows={projects} />

        {/* Desktop table */}
        <div className="hidden md:block bg-slate-900/50 border border-slate-800/50 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800/50">
                  <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Student Name</th>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Email</th>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Project Name</th>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Attendance</th>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Dashboard</th>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">GitHub Repo</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => (
                  <tr key={i} className="border-b border-slate-800/30 hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-white whitespace-nowrap">{row.student_name || '—'}</td>
                    <td className="px-4 py-3 text-sm text-slate-400 whitespace-nowrap">{row.email || '—'}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{row.project_name || '—'}</td>
                    <td className="px-4 py-3"><AttendanceBadge value={row.attendance} /></td>
                    <td className="px-4 py-3"><ExternalLink href={row.dashboard_link} /></td>
                    <td className="px-4 py-3"><ExternalLink href={row.github_repo_link} /></td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-sm text-slate-500">
                      {search ? 'No results match your search' : 'No data available'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden space-y-3">
          {filtered.map((row, i) => (
            <div key={i} className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-4">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-sm font-semibold text-white">{row.student_name || '—'}</h3>
                <AttendanceBadge value={row.attendance} />
              </div>
              <p className="text-xs text-slate-400 mb-1">{row.email || '—'}</p>
              <p className="text-sm text-slate-300 mb-3">{row.project_name || '—'}</p>
              <div className="flex flex-wrap gap-3">
                <ExternalLink href={row.dashboard_link}>Dashboard</ExternalLink>
                <ExternalLink href={row.github_repo_link}>GitHub</ExternalLink>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center py-8 text-sm text-slate-500">
              {search ? 'No results match your search' : 'No data available'}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
