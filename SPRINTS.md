# Intern Pipeline — Improvement Sprints

## Sprint 1: Caching & Smart Invalidation
**Goal:** Avoid re-processing resume/persona when data hasn't changed. Regenerate only when needed.

### Backend
- [ ] Add `resume_parsed` JSON column to Candidate model (stores LLM-extracted resume fields)
- [ ] Add `resume_hash` column (SHA-256 of uploaded file bytes) to detect file changes
- [ ] On resume upload: check hash match → skip LLM if same file
- [ ] Store parsed resume data in DB after first parse
- [ ] Cache persona: return existing persona if already generated, add `?force=true` to regenerate
- [ ] Smart invalidation: if resume changes OR candidate updates skills/projects/experience → mark persona stale
- [ ] Use faster/cheaper model for resume parsing (it's simpler extraction, doesn't need hunter-alpha)
- [ ] Add `persona_generated_at` timestamp column

### Frontend
- [ ] Show "Persona already generated" with timestamp, "Regenerate" button
- [ ] Show cache indicator when resume was already parsed

---

## Sprint 2: Logging
**Goal:** Proper logging for debugging production issues.

### Backend
- [ ] Add Python `logging` module with structured format
- [ ] Log API calls: model, latency, token count
- [ ] Log errors with full context (candidate_id, operation, error details)
- [ ] Log resume parse and persona generation events
- [ ] Write to both console (uvicorn) and `logs/app.log`
- [ ] Add request ID middleware for tracing

---

## Sprint 3: Loading Indicators & Status
**Goal:** Users always know what's happening during long operations.

### Frontend
- [x] Create toast notification system (Toast.jsx) with success/error/info/warning types, auto-dismiss, manual dismiss, stacking, slide-in animation
- [x] Resume parsing: show "Extracting text... → Analyzing with AI... → Done" with 3-step progress indicator (dots + labels)
- [x] Persona generation: show "Analyzing candidate profile..." with elapsed seconds counter + progress bar + pulse animation
- [x] Form submission: toast on success/error, disable entire form during submission to prevent double-submit
- [x] Admin dashboard: toast on status update ("Status updated to {status}"), toast on error, toast on persona generation
- [x] ToastProvider wraps entire app in App.jsx
- [x] All components use `useToast` hook for notifications

---

## Sprint 4: Responsive UI
**Goal:** Works well on mobile, tablet, and desktop.

### Frontend
- [x] Admin dashboard: stack list/detail panels on mobile (lg breakpoint: `flex-col lg:flex-row`, detail shows full-width with "← Back" button)
- [x] Tables → card layout on small screens (md breakpoint: `hidden md:block` table + `md:hidden` card list)
- [x] Form: verified `grid-cols-1 md:grid-cols-2`, drop zone `min-h-[120px]`, step indicator stacks on mobile, success screen full-width buttons
- [x] Navigation: hamburger menu on mobile (sm breakpoint: `MobileNav` component in AdminDashboard + AssignmentManager)
- [x] Touch-friendly tap targets (min 44px via `min-h-[44px]` / `py-3` on all buttons and interactive elements)
- [x] Tested: build succeeds with `npm run build`
