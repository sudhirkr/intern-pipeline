import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchCandidateByToken } from '../api/client';

const API_BASE = '/api';

const DIFFICULTY_CONFIG = {
  easy: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', label: 'Easy' },
  medium: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', label: 'Medium' },
  hard: { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20', label: 'Hard' },
};

const STATUS_CONFIG = {
  assigned: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20', label: 'Assigned' },
  submitted: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', label: 'Submitted' },
  graded: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', label: 'Graded' },
};

export default function AssignmentView({ token: propToken }) {
  const { token: urlToken } = useParams();
  const token = propToken || urlToken;

  const [assignment, setAssignment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API_BASE}/candidates/by-token/${token}/assignment`);
        if (!res.ok) {
          if (res.status === 404) {
            setError('No assignment found yet. An admin will assign you a project soon.');
          } else {
            throw new Error('Failed to load assignment');
          }
          return;
        }
        const data = await res.json();
        setAssignment(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    if (token) load();
  }, [token]);

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 text-center">
        <p className="text-sm text-slate-400">{error}</p>
      </div>
    );
  }

  if (!assignment) return null;

  const diffConfig = DIFFICULTY_CONFIG[assignment.assignment?.difficulty] || DIFFICULTY_CONFIG.medium;
  const statusConfig = STATUS_CONFIG[assignment.status] || STATUS_CONFIG.assigned;

  return (
    <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Your Assigned Project
        </h3>
        <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium ${statusConfig.bg} ${statusConfig.text} border ${statusConfig.border}`}>
          {statusConfig.label}
        </span>
      </div>

      <div className="space-y-4">
        <div>
          <h4 className="text-lg font-bold text-white">{assignment.assignment?.title}</h4>
          <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium mt-2 ${diffConfig.bg} ${diffConfig.text} border ${diffConfig.border}`}>
            {diffConfig.label}
          </span>
        </div>

        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Description</p>
          <p className="text-sm text-slate-300 leading-relaxed">{assignment.assignment?.description}</p>
        </div>

        {assignment.assignment?.tech_stack && (
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Tech Stack</p>
            <p className="text-sm text-slate-300">{assignment.assignment.tech_stack}</p>
          </div>
        )}

        {assignment.assignment?.expected_outcome && (
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Expected Outcome</p>
            <p className="text-sm text-slate-300">{assignment.assignment.expected_outcome}</p>
          </div>
        )}

        {assignment.github_repo_url && (
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">GitHub Repository</p>
            <a href={assignment.github_repo_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-400 hover:text-blue-300 underline">
              {assignment.github_repo_url}
            </a>
          </div>
        )}

        {assignment.deployed_url && (
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Deployed URL</p>
            <a href={assignment.deployed_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-400 hover:text-blue-300 underline">
              {assignment.deployed_url}
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
