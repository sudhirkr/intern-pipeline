import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchCandidateByToken, updateCandidateByToken, fetchPersona } from '../api/client';
import PersonaCard from './PersonaCard';
import AssignmentView from './AssignmentView';

const LEARNING_STYLES = [
  { value: 'visual', label: 'Visual' },
  { value: 'hands_on', label: 'Hands-On' },
  { value: 'reading', label: 'Reading' },
  { value: 'mixed', label: 'Mixed' },
];

const AVAILABILITIES = [
  { value: 'full_time', label: 'Full Time' },
  { value: 'part_time', label: 'Part Time' },
  { value: 'flexible', label: 'Flexible' },
];

const STATUS_CONFIG = {
  submitted: { bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-400', label: 'Submitted' },
  reviewing: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400', label: 'Under Review' },
  accepted: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', label: 'Accepted' },
  rejected: { bg: 'bg-rose-500/10', border: 'border-rose-500/20', text: 'text-rose-400', label: 'Rejected' },
};

function DetailField({ label, value }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">{label}</dt>
      <dd className="text-sm text-white">{value || <span className="text-slate-600">—</span>}</dd>
    </div>
  );
}

function EditField({ label, value, onChange, type = 'text', options }) {
  if (options) {
    return (
      <div>
        <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">{label}</label>
        <select
          value={value || ''}
          onChange={onChange}
          className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
        >
          {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
    );
  }
  if (type === 'textarea') {
    return (
      <div>
        <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">{label}</label>
        <textarea
          value={value || ''}
          onChange={onChange}
          rows={3}
          className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 resize-y"
        />
      </div>
    );
  }
  return (
    <div>
      <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">{label}</label>
      <input
        type={type}
        value={value || ''}
        onChange={onChange}
        className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
      />
    </div>
  );
}

export default function ApplicationView() {
  const { token } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({});
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');
  const [persona, setPersona] = useState(null);
  const [personaGenerated, setPersonaGenerated] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchCandidateByToken(token);
        setCandidate(data);
        // Try loading persona
        try {
          const p = await fetchPersona(data.id, token);
          setPersona(p.persona);
          setPersonaGenerated(p.persona_generated);
        } catch {
          // Persona not available yet
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [token]);

  const startEdit = () => {
    setEditData({
      name: candidate.name || '',
      phone: candidate.phone || '',
      college: candidate.college || '',
      degree: candidate.degree || '',
      year: candidate.year || '',
      skills: candidate.skills || '',
      projects: candidate.projects || '',
      work_experience: candidate.work_experience || '',
      interests: candidate.interests || '',
      learning_style: candidate.learning_style || 'mixed',
      availability: candidate.availability || 'flexible',
      motivation: candidate.motivation || '',
      portfolio_links: candidate.portfolio_links || '',
      preferred_tech_stack: candidate.preferred_tech_stack || '',
      ai_tool_usage: candidate.ai_tool_usage || '',
      challenge_solved: candidate.challenge_solved || '',
    });
    setEditMode(true);
    setSaveMsg('');
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveMsg('');
    try {
      const updated = await updateCandidateByToken(token, editData);
      setCandidate(updated);
      setEditMode(false);
      setSaveMsg('Application updated successfully!');
    } catch (err) {
      setSaveMsg(`Error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const updateField = (field) => (e) => {
    setEditData({ ...editData, [field]: e.target.value });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-925 flex items-center justify-center">
        <div className="w-12 h-12 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-925 flex items-center justify-center">
        <div className="max-w-md text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
            <svg className="w-8 h-8 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Application Not Found</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <Link to="/apply" className="text-blue-400 hover:text-blue-300 underline underline-offset-4">
            Submit a new application
          </Link>
        </div>
      </div>
    );
  }

  const statusInfo = STATUS_CONFIG[candidate.status] || STATUS_CONFIG.submitted;

  return (
    <div className="min-h-screen bg-slate-925">
      {/* Header */}
      <header className="border-b border-slate-800/50 bg-slate-925/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <Link to="/apply" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">Intern Pipeline</h1>
              <p className="text-xs text-slate-500">Your Application</p>
            </div>
          </Link>
          <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${statusInfo.bg} ${statusInfo.text} border ${statusInfo.border}`}>
            {statusInfo.label}
          </span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Title */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">{candidate.name}</h2>
            <p className="text-sm text-slate-400 mt-1">Application submitted • Save this link to view/edit later</p>
          </div>
          {!editMode ? (
            <button
              onClick={startEdit}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors"
            >
              Edit Application
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={() => setEditMode(false)}
                className="px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 text-white font-medium rounded-xl transition-colors"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </div>

        {saveMsg && (
          <div className={`mb-6 px-4 py-3 rounded-xl text-sm ${saveMsg.startsWith('Error') ? 'bg-rose-500/10 border border-rose-500/20 text-rose-400' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'}`}>
            {saveMsg}
          </div>
        )}

        {/* Share link */}
        <div className="mb-8 bg-slate-900/50 border border-slate-800/50 rounded-2xl p-4 flex items-center gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-slate-500 mb-1">Your application link</p>
            <p className="text-sm text-slate-300 truncate font-mono">{window.location.href}</p>
          </div>
          <button
            onClick={() => { navigator.clipboard.writeText(window.location.href); }}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/50 text-slate-300 text-sm rounded-xl transition-colors flex-shrink-0"
          >
            Copy Link
          </button>
        </div>

        {/* Content */}
        {!editMode ? (
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">Basic Information</h3>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <DetailField label="Full Name" value={candidate.name} />
                <DetailField label="Email" value={candidate.email} />
                <DetailField label="Phone" value={candidate.phone} />
                <DetailField label="College" value={candidate.college} />
                <DetailField label="Degree" value={candidate.degree} />
                <DetailField label="Year" value={candidate.year} />
              </dl>
            </div>

            {/* Skills & Experience */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">Skills & Experience</h3>
              <dl className="space-y-4">
                <DetailField label="Skills" value={candidate.skills} />
                <DetailField label="Projects" value={candidate.projects} />
                <DetailField label="Work Experience" value={candidate.work_experience} />
              </dl>
            </div>

            {/* Preferences */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">Preferences & Personality</h3>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <DetailField label="Learning Style" value={LEARNING_STYLES.find(l => l.value === candidate.learning_style)?.label || candidate.learning_style} />
                <DetailField label="Availability" value={AVAILABILITIES.find(a => a.value === candidate.availability)?.label || candidate.availability} />
                <DetailField label="Interests" value={candidate.interests} />
                <DetailField label="Motivation" value={candidate.motivation} />
              </dl>
            </div>

            {/* Links & Tech */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">Links & Tech Stack</h3>
              <dl className="space-y-4">
                <DetailField label="Portfolio Links" value={candidate.portfolio_links} />
                <DetailField label="Preferred Tech Stack" value={candidate.preferred_tech_stack} />
              </dl>
            </div>

            {/* AI & Challenges */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">AI & Problem Solving</h3>
              <dl className="space-y-4">
                <DetailField label="AI Tool Usage" value={candidate.ai_tool_usage} />
                <DetailField label="Challenge Solved" value={candidate.challenge_solved} />
              </dl>
            </div>

            {/* Persona */}
            <PersonaCard
              candidateId={candidate.id}
              persona={persona}
              personaGenerated={personaGenerated}
              isAdmin={false}
            />

            {/* Assigned Project */}
            <div className="mt-6">
              <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                Assigned Project
              </h3>
              <AssignmentView token={token} />
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Edit: Basic Info */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">Basic Information</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <EditField label="Full Name" value={editData.name} onChange={updateField('name')} />
                <div>
                  <dt className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Email</dt>
                  <dd className="text-sm text-slate-500 bg-slate-800/50 rounded-xl px-4 py-2.5">{candidate.email} (cannot be changed)</dd>
                </div>
                <EditField label="Phone" value={editData.phone} onChange={updateField('phone')} />
                <EditField label="College" value={editData.college} onChange={updateField('college')} />
                <EditField label="Degree" value={editData.degree} onChange={updateField('degree')} />
                <EditField label="Year" value={editData.year} onChange={updateField('year')} />
              </div>
            </div>

            {/* Edit: Skills */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">Skills & Experience</h3>
              <div className="space-y-4">
                <EditField label="Skills" value={editData.skills} onChange={updateField('skills')} />
                <EditField label="Projects" value={editData.projects} onChange={updateField('projects')} type="textarea" />
                <EditField label="Work Experience" value={editData.work_experience} onChange={updateField('work_experience')} type="textarea" />
              </div>
            </div>

            {/* Edit: Preferences */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">Preferences & Personality</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <EditField label="Learning Style" value={editData.learning_style} onChange={updateField('learning_style')} options={LEARNING_STYLES} />
                <EditField label="Availability" value={editData.availability} onChange={updateField('availability')} options={AVAILABILITIES} />
                <EditField label="Interests" value={editData.interests} onChange={updateField('interests')} />
                <EditField label="Motivation" value={editData.motivation} onChange={updateField('motivation')} type="textarea" />
              </div>
            </div>

            {/* Edit: Links */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">Links & Tech Stack</h3>
              <div className="space-y-4">
                <EditField label="Portfolio Links" value={editData.portfolio_links} onChange={updateField('portfolio_links')} />
                <EditField label="Preferred Tech Stack" value={editData.preferred_tech_stack} onChange={updateField('preferred_tech_stack')} />
              </div>
            </div>

            {/* Edit: AI */}
            <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
              <h3 className="text-base font-semibold text-white mb-4">AI & Problem Solving</h3>
              <div className="space-y-4">
                <EditField label="AI Tool Usage" value={editData.ai_tool_usage} onChange={updateField('ai_tool_usage')} type="textarea" />
                <EditField label="Challenge Solved" value={editData.challenge_solved} onChange={updateField('challenge_solved')} type="textarea" />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
