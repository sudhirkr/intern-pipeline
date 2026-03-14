import { useState } from 'react';
import { generatePersona } from '../api/client';

const SKILL_LEVEL_CONFIG = {
  Beginner: { bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-400', icon: '🌱' },
  Intermediate: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400', icon: '⚡' },
  Advanced: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', icon: '🚀' },
};

const LEARNING_STYLE_CONFIG = {
  'project-based': { bg: 'bg-purple-500/10', border: 'border-purple-500/20', text: 'text-purple-400', label: 'Project-Based' },
  'classroom': { bg: 'bg-cyan-500/10', border: 'border-cyan-500/20', text: 'text-cyan-400', label: 'Classroom' },
  'self-taught': { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-400', label: 'Self-Taught' },
};

export default function PersonaCard({ candidateId, persona, personaGenerated, isAdmin, onPersonaGenerated }) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      const result = await generatePersona(candidateId);
      if (onPersonaGenerated) {
        onPersonaGenerated(result.persona);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  if (!personaGenerated) {
    return (
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            AI Persona Analysis
          </h3>
        </div>
        <p className="text-sm text-slate-500 mb-4">
          No persona generated yet. {isAdmin ? 'Click below to analyze this candidate with AI.' : 'An admin will generate your persona soon.'}
        </p>
        {error && (
          <div className="mb-4 px-3 py-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            {error}
          </div>
        )}
        {isAdmin && (
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 text-white font-medium rounded-xl transition-colors flex items-center gap-2"
          >
            {generating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Generate Persona
              </>
            )}
          </button>
        )}
      </div>
    );
  }

  const skillConfig = SKILL_LEVEL_CONFIG[persona?.skill_level] || SKILL_LEVEL_CONFIG.Intermediate;
  const learnConfig = LEARNING_STYLE_CONFIG[persona?.learning_style] || LEARNING_STYLE_CONFIG['project-based'];

  return (
    <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          AI Persona Analysis
        </h3>
        {isAdmin && (
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
            title="Regenerate persona"
          >
            {generating ? 'Regenerating...' : '↻ Regenerate'}
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 px-3 py-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Skill Level & Learning Style badges */}
      <div className="flex flex-wrap gap-3 mb-5">
        <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${skillConfig.bg} ${skillConfig.text} border ${skillConfig.border}`}>
          {skillConfig.icon} {persona?.skill_level}
        </span>
        <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${learnConfig.bg} ${learnConfig.text} border ${learnConfig.border}`}>
          📚 {learnConfig.label}
        </span>
      </div>

      {/* Summary */}
      <div className="mb-5">
        <p className="text-sm text-slate-300 leading-relaxed">{persona?.summary}</p>
      </div>

      {/* Strengths */}
      <div className="mb-4">
        <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Strengths</h4>
        <div className="flex flex-wrap gap-2">
          {persona?.strengths?.map((s, i) => (
            <span key={i} className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs rounded-lg border border-emerald-500/20">
              ✓ {s}
            </span>
          ))}
        </div>
      </div>

      {/* Gaps */}
      <div className="mb-4">
        <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Gaps</h4>
        <div className="flex flex-wrap gap-2">
          {persona?.gaps?.map((g, i) => (
            <span key={i} className="px-3 py-1 bg-amber-500/10 text-amber-400 text-xs rounded-lg border border-amber-500/20">
              ○ {g}
            </span>
          ))}
        </div>
      </div>

      {/* Assignment Fit */}
      <div className="mb-4">
        <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Suggested Assignment</h4>
        <div className="px-4 py-3 bg-blue-500/5 border border-blue-500/10 rounded-xl">
          <p className="text-sm text-blue-300">{persona?.assignment_fit}</p>
        </div>
      </div>

      {/* Risk Flags */}
      {persona?.risk_flags?.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Risk Flags</h4>
          <div className="flex flex-wrap gap-2">
            {persona.risk_flags.map((f, i) => (
              <span key={i} className="px-3 py-1 bg-rose-500/10 text-rose-400 text-xs rounded-lg border border-rose-500/20">
                ⚠ {f}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
