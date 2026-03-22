# Requirements Verification Questions — ChronoTrack

**Instructions**: Please fill in each `[Answer]:` tag directly in this file. Use the letter (A, B, C...) or write your own answer after the tag.

---

## Q1: Project Root Directory

The AI-DLC framework places application code in the workspace root. Should ChronoTrack be built directly in `/workspace/trabajo/test-symphony/`?

A) Yes — build ChronoTrack directly in `/workspace/trabajo/test-symphony/` (monorepo root here)
B) No — create a subdirectory `chronotrack/` inside the workspace
C) No — use a different path entirely (specify below)
X) Other (please describe after [Answer]: tag below)

[Answer]:A

---

## Q2: PDF Generation Library

The PRD mentions "WeasyPrint o reportlab" for PDF generation. Which should be used?

A) WeasyPrint (HTML/CSS-based, better looking output, heavier dependency)
B) reportlab (pure Python, lighter, more programmatic)
C) Either — pick whichever is simpler to implement
X) Other (please describe after [Answer]: tag below)

[Answer]:A

---

## Q3: GitHub / CI/CD Setup

The PRD mentions `SYMPHONY_REPO_URL` and GitHub integration. Should the project include:

A) Full CI/CD with GitHub Actions (`.github/workflows/ci.yml`) + remote repo required
B) Docker Compose only — no GitHub Actions, just local infra
C) Docker Compose + GitHub Actions skeletons but no actual repo required now
X) Other (please describe after [Answer]: tag below)

[Answer]:A

---

## Q4: Symphony Integration

The PRD includes Symphony configuration (Section 9). Is this a Symphony-managed project where tickets are tracked in Linear, or should we develop ChronoTrack as a standalone project ignoring Symphony/Linear orchestration?

A) Yes — this IS a Symphony project; generate `WORKFLOW.md` with Symphony config and Linear ticket support
B) No — standalone development only; skip Symphony/WORKFLOW.md setup
C) Generate WORKFLOW.md template but don't configure actual Linear credentials
X) Other (please describe after [Answer]: tag below)

[Answer]:X omitir esto

---

## Q5: Telegram Bot — Default State

The PRD says the bot should start only if `TELEGRAM_TOKEN` is set. For development and testing purposes:

A) Include the bot service fully (code + tests) but skip if token not present at runtime
B) Implement bot as a separate optional unit — can be excluded from initial development
C) Skip bot entirely for now (implement Units 1-4, 6-9 only)
X) Other (please describe after [Answer]: tag below)

[Answer]:A

---

## Q6: Frontend Tooling — Chart Library

The PRD mentions "recharts or chart.js" for bar charts. Which should be used?

A) recharts (React-native, simpler integration)
B) chart.js (more powerful, requires wrapper like react-chartjs-2)
C) Either — pick whichever is simpler
X) Other (please describe after [Answer]: tag below)

[Answer]:A

---

## Q7: Security Baseline Extension

This project will enforce the AI-DLC security baseline (SECURITY-01 through SECURITY-15), which includes requirements for encryption at rest/in transit, access control, input validation, secure auth, logging, and more.

Are there any security requirements from the baseline that should be **disabled** or **modified** for this project?

A) No — enforce all security baseline rules as defined
B) Yes — disable specific rules (specify which ones after [Answer]: tag below)
X) Other (please describe after [Answer]: tag below)

[Answer]:A

---
