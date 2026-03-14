import { useState, useRef, useCallback } from 'react';
import { createCandidate, parseResume } from '../api/client';

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

const initialForm = {
  name: '',
  email: '',
  phone: '',
  college: '',
  degree: '',
  year: '',
  skills: '',
  projects: '',
  work_experience: '',
  interests: '',
  learning_style: 'mixed',
  availability: 'flexible',
  motivation: '',
  portfolio_links: '',
  preferred_tech_stack: '',
  ai_tool_usage: '',
  challenge_solved: '',
  resume_url: '',
};

// Fields extracted from resume (auto-filled, read-only)
const AUTO_FIELDS = ['name', 'email', 'phone', 'college', 'degree', 'year', 'skills', 'projects', 'work_experience'];

// ── UI Components ──

function FieldLabel({ label, required }) {
  return (
    <label className="block text-sm font-semibold text-slate-300 mb-1.5 tracking-wide">
      {label} {required && <span className="text-rose-400">*</span>}
    </label>
  );
}

function Input({ autoFilled, ...props }) {
  return (
    <input
      {...props}
      className={`w-full bg-slate-800/80 border rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-200 ${
        autoFilled
          ? 'field-auto-filled border-blue-500/30 bg-blue-500/5'
          : 'border-slate-700/50 hover:border-slate-600'
      }`}
    />
  );
}

function Textarea({ autoFilled, ...props }) {
  return (
    <textarea
      {...props}
      className={`w-full bg-slate-800/80 border rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 resize-y transition-all duration-200 ${
        autoFilled
          ? 'field-auto-filled border-blue-500/30 bg-blue-500/5'
          : 'border-slate-700/50 hover:border-slate-600'
      }`}
    />
  );
}

function Select({ options, ...props }) {
  return (
    <select
      {...props}
      className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 hover:border-slate-600 transition-all duration-200"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function SectionHeader({ icon, title, subtitle }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/20 flex items-center justify-center text-blue-400">
        {icon}
      </div>
      <div>
        <h3 className="text-base font-semibold text-white">{title}</h3>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>
    </div>
  );
}

// ── Resume Upload Component ──

function ResumeUpload({ onParsed, parsing, setParsing }) {
  const [dragging, setDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [urlMode, setUrlMode] = useState(false);
  const [resumeUrl, setResumeUrl] = useState('');
  const [error, setError] = useState('');
  const [progress, setProgress] = useState('');
  const fileInputRef = useRef(null);

  const handleFile = useCallback(async (file) => {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'doc'].includes(ext)) {
      setError('Please upload a PDF or DOCX file');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large (max 10MB)');
      return;
    }
    setError('');
    setUploadedFile(file);
    setParsing(true);
    setProgress('Parsing resume...');

    try {
      const result = await parseResume({ file });
      setProgress('Resume parsed successfully!');
      onParsed(result.extracted, file);
    } catch (err) {
      setError(err.message);
      setProgress('');
    } finally {
      setParsing(false);
    }
  }, [onParsed, setParsing]);

  const handleUrlParse = async () => {
    if (!resumeUrl.trim()) {
      setError('Please enter a resume URL');
      return;
    }
    setError('');
    setParsing(true);
    setProgress('Fetching and parsing resume...');

    try {
      const result = await parseResume({ resumeUrl: resumeUrl.trim() });
      setProgress('Resume parsed successfully!');
      onParsed(result.extracted, null);
    } catch (err) {
      setError(err.message);
      setProgress('');
    } finally {
      setParsing(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  return (
    <div className="space-y-4">
      {!urlMode ? (
        <>
          {/* Drag & Drop Zone */}
          <div
            className={`drop-zone ${dragging ? 'dragging' : ''} ${uploadedFile ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.doc"
              className="hidden"
              onChange={(e) => handleFile(e.target.files[0])}
            />
            {parsing ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-12 h-12 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-blue-400 font-medium">{progress}</p>
              </div>
            ) : uploadedFile ? (
              <div className="flex flex-col items-center gap-2">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
                  <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-emerald-400 font-medium">{uploadedFile.name}</p>
                <p className="text-xs text-slate-500">Click to replace</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 rounded-2xl bg-slate-800 border border-slate-700/50 flex items-center justify-center">
                  <svg className="w-7 h-7 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <p className="text-slate-300 font-medium">Drop your resume here</p>
                  <p className="text-sm text-slate-500 mt-1">or click to browse — PDF or DOCX</p>
                </div>
              </div>
            )}
          </div>

          {/* URL Mode Toggle */}
          <div className="text-center">
            <button
              type="button"
              onClick={() => setUrlMode(true)}
              className="text-sm text-slate-400 hover:text-blue-400 transition-colors underline underline-offset-4 decoration-slate-700 hover:decoration-blue-400"
            >
              Or paste a resume URL instead
            </button>
          </div>
        </>
      ) : (
        <>
          {/* URL Input Mode */}
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
            <FieldLabel label="Resume URL" />
            <div className="flex gap-3">
              <Input
                placeholder="https://drive.google.com/your-resume.pdf"
                value={resumeUrl}
                onChange={(e) => setResumeUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleUrlParse()}
              />
              <button
                type="button"
                onClick={handleUrlParse}
                disabled={parsing}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors whitespace-nowrap"
              >
                {parsing ? 'Parsing...' : 'Parse'}
              </button>
            </div>
          </div>
          <div className="text-center">
            <button
              type="button"
              onClick={() => setUrlMode(false)}
              className="text-sm text-slate-400 hover:text-blue-400 transition-colors underline underline-offset-4 decoration-slate-700 hover:decoration-blue-400"
            >
              Or upload a file instead
            </button>
          </div>
        </>
      )}

      {/* Error / Progress */}
      {error && (
        <div className="flex items-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-4 py-3 text-sm">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}
      {progress && !error && !parsing && (
        <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3 text-sm">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {progress}
        </div>
      )}
    </div>
  );
}

// ── Skip Resume Option ──

function SkipResumeButton({ onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full py-3 text-sm text-slate-400 hover:text-slate-200 bg-slate-800/30 hover:bg-slate-800/60 border border-slate-700/30 hover:border-slate-600/50 rounded-xl transition-all duration-200"
    >
      Skip resume upload — fill form manually
    </button>
  );
}

// ── Main Form ──

export default function CandidateForm({ onSuccess }) {
  const [step, setStep] = useState(1); // 1 = resume upload, 2 = form, 3 = success
  const [form, setForm] = useState(initialForm);
  const [autoFilled, setAutoFilled] = useState(new Set());
  const [resumeFile, setResumeFile] = useState(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);

  const update = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value });
    // Clear auto-filled indicator when user edits
    if (autoFilled.has(field)) {
      setAutoFilled((prev) => {
        const next = new Set(prev);
        next.delete(field);
        return next;
      });
    }
  };

  const handleResumeParsed = (extracted, file) => {
    setResumeFile(file);
    const newAutoFilled = new Set();
    const updatedForm = { ...form };

    for (const [key, value] of Object.entries(extracted)) {
      if (value && key in initialForm) {
        updatedForm[key] = value;
        newAutoFilled.add(key);
      }
    }

    setForm(updatedForm);
    setAutoFilled(newAutoFilled);
    // Auto-advance to form step
    setTimeout(() => setStep(2), 800);
  };

  const handleSkipResume = () => {
    setStep(2);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const formData = new FormData();

      // Add all non-empty fields
      for (const [k, v] of Object.entries(form)) {
        if (v !== '' && v !== null && v !== undefined) {
          formData.append(k, v);
        }
      }

      // Attach resume file if uploaded
      if (resumeFile) {
        formData.append('resume_file', resumeFile);
      }

      const result = await createCandidate(formData);
      setSubmissionResult(result);
      setStep(3); // success screen
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // ── Step 3: Success ──
  if (step === 3 && submissionResult) {
    const appUrl = `${window.location.origin}/application/${submissionResult.submission_token}`;
    return (
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-6 sm:p-8 shadow-2xl shadow-black/20 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
          <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-2xl font-bold text-white mb-2">Application Submitted!</h3>
        <p className="text-slate-400 mb-6">Your application has been received. Save the link below to view or edit your application later.</p>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 mb-6">
          <p className="text-xs text-slate-500 mb-2">Your Application Link</p>
          <p className="text-sm text-blue-400 font-mono break-all mb-3">{appUrl}</p>
          <button
            onClick={() => { navigator.clipboard.writeText(appUrl); }}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
          >
            Copy Link
          </button>
        </div>

        <a
          href={`/application/${submissionResult.submission_token}`}
          className="inline-block px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-blue-500/25"
        >
          View Your Application →
        </a>
      </div>
    );
  }

  // ── Step 1: Resume Upload ──
  if (step === 1) {
    return (
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-6 sm:p-8 shadow-2xl shadow-black/20">
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold text-blue-400 bg-blue-500/10 border border-blue-500/20 rounded-full px-2.5 py-0.5">Step 1 of 2</span>
          </div>
          <h3 className="text-xl font-bold text-white">Upload Your Resume</h3>
          <p className="text-sm text-slate-400 mt-1">We'll extract your details automatically</p>
        </div>
        <ResumeUpload onParsed={handleResumeParsed} parsing={parsing} setParsing={setParsing} />
        <div className="mt-6">
          <SkipResumeButton onClick={handleSkipResume} />
        </div>
      </div>
    );
  }

  // ── Step 2: Application Form ──
  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="flex items-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-4 py-3 text-sm">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {/* Step indicator + back */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setStep(1)}
          className="text-sm text-slate-400 hover:text-blue-400 transition-colors flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to resume upload
        </button>
        <span className="text-xs font-bold text-blue-400 bg-blue-500/10 border border-blue-500/20 rounded-full px-2.5 py-0.5">
          Step 2 of 2
        </span>
      </div>

      {autoFilled.size > 0 && (
        <div className="flex items-center gap-2 text-blue-400 bg-blue-500/5 border border-blue-500/20 rounded-xl px-4 py-2.5 text-xs">
          <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Fields with blue highlight were extracted from your resume. You can edit them.
        </div>
      )}

      {/* Basic Info */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
        <SectionHeader
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>}
          title="Basic Information"
          subtitle="Your personal and contact details"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <FieldLabel label="Full Name" required />
            <Input required placeholder="Priya Sharma" value={form.name} onChange={update('name')} autoFilled={autoFilled.has('name')} />
          </div>
          <div>
            <FieldLabel label="Email" required />
            <Input required type="email" placeholder="priya@example.com" value={form.email} onChange={update('email')} autoFilled={autoFilled.has('email')} />
          </div>
          <div>
            <FieldLabel label="Phone" />
            <Input placeholder="+91-9876543210" value={form.phone} onChange={update('phone')} autoFilled={autoFilled.has('phone')} />
          </div>
          <div>
            <FieldLabel label="College" />
            <Input placeholder="IIT Bombay" value={form.college} onChange={update('college')} autoFilled={autoFilled.has('college')} />
          </div>
          <div>
            <FieldLabel label="Degree" />
            <Input placeholder="B.Tech Computer Science" value={form.degree} onChange={update('degree')} autoFilled={autoFilled.has('degree')} />
          </div>
          <div>
            <FieldLabel label="Year" />
            <Input placeholder="3rd Year" value={form.year} onChange={update('year')} autoFilled={autoFilled.has('year')} />
          </div>
        </div>
      </div>

      {/* Skills & Experience */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
        <SectionHeader
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>}
          title="Skills & Experience"
          subtitle="Your technical skills and background"
        />
        <div className="space-y-4">
          <div>
            <FieldLabel label="Skills" />
            <Input placeholder="Python, React, PostgreSQL, Docker..." value={form.skills} onChange={update('skills')} autoFilled={autoFilled.has('skills')} />
          </div>
          <div>
            <FieldLabel label="Projects" />
            <Textarea rows={3} placeholder="Describe your notable projects..." value={form.projects} onChange={update('projects')} autoFilled={autoFilled.has('projects')} />
          </div>
          <div>
            <FieldLabel label="Work Experience" />
            <Textarea rows={2} placeholder="Internships, part-time jobs..." value={form.work_experience} onChange={update('work_experience')} autoFilled={autoFilled.has('work_experience')} />
          </div>
        </div>
      </div>

      {/* Preferences */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
        <SectionHeader
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>}
          title="Preferences & Personality"
          subtitle="Help us understand how you work"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <FieldLabel label="Learning Style" />
            <Select options={LEARNING_STYLES} value={form.learning_style} onChange={update('learning_style')} />
          </div>
          <div>
            <FieldLabel label="Availability" />
            <Select options={AVAILABILITIES} value={form.availability} onChange={update('availability')} />
          </div>
        </div>
        <div className="mt-4 space-y-4">
          <div>
            <FieldLabel label="Interests" />
            <Input placeholder="AI/ML, Web Development, Data Science..." value={form.interests} onChange={update('interests')} />
          </div>
          <div>
            <FieldLabel label="Motivation" />
            <Textarea rows={2} placeholder="Why do you want this internship?" value={form.motivation} onChange={update('motivation')} />
          </div>
        </div>
      </div>

      {/* Links & Tech */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
        <SectionHeader
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>}
          title="Links & Tech Stack"
          subtitle="Show us what you've built"
        />
        <div className="space-y-4">
          <div>
            <FieldLabel label="Portfolio Links" />
            <Input placeholder="https://github.com/you, https://yourportfolio.dev" value={form.portfolio_links} onChange={update('portfolio_links')} />
          </div>
          <div>
            <FieldLabel label="Preferred Tech Stack" />
            <Input placeholder="Python, FastAPI, React, PostgreSQL" value={form.preferred_tech_stack} onChange={update('preferred_tech_stack')} />
          </div>
        </div>
      </div>

      {/* AI & Challenges */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-2xl p-5 sm:p-6">
        <SectionHeader
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>}
          title="AI & Problem Solving"
          subtitle="Your experience with AI tools"
        />
        <div className="space-y-4">
          <div>
            <FieldLabel label="AI Tool Usage" />
            <Textarea rows={2} placeholder="How have you used AI tools (ChatGPT, Copilot, etc.)?" value={form.ai_tool_usage} onChange={update('ai_tool_usage')} />
          </div>
          <div>
            <FieldLabel label="Challenge Solved" />
            <Textarea rows={2} placeholder="Describe a technical challenge you solved..." value={form.challenge_solved} onChange={update('challenge_solved')} />
          </div>
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={submitting}
        className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-[1.01] active:scale-[0.99]"
      >
        {submitting ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Submitting...
          </span>
        ) : (
          'Submit Application'
        )}
      </button>
    </form>
  );
}
