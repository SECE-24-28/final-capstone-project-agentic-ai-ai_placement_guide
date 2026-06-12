# 🎯 AI Placement Preparation Agent

An enterprise-grade **Multi-Agent AI System** helping students become placement-ready through automated resume analysis, skill gap detection, personalized learning roadmaps, and intelligent job matching.

---

## ✨ System Overview

```
Resume Upload → Agent 1 → Agent 2 → Agent 3 → Agent 4 → Unified Dashboard
                Resume    Skill Gap  Roadmap    Job
                Analyzer  Analyzer   Generator  Matcher
```

All 4 agents run automatically when a student uploads their resume. No hardcoded data — everything is extracted dynamically from the uploaded resume using AI.

---

## 🤖 The 4 Agents

### Agent 1 — Resume Analyzer
- Parses PDF & DOCX using PyMuPDF + python-docx
- Extracts: Name, Email, Phone, Skills, Education, Experience, Projects, Certifications
  - Resume text truncation increased to 6000 chars to prevent cutting off Projects/Experience
  - Groq max_tokens increased to 4096 to handle full structured extraction
- Calculates **ATS Score (0–100)** using 7 measurable signals (no LLM opinion scoring):

| Signal | Weight | How it's measured |
|--------|--------|-------------------|
| Keyword Match Rate | 25% | Dynamic NLP extraction from target role/JD via spaCy — matched / total JD keywords × 100 |
| Parseability Score | 15% | Clean text extraction check — penalizes non-ASCII, garbled text, long unbroken lines |
| Section Detection | 15% | Detects: Summary, Skills, Experience, Education, Projects, Certifications |
| Quantified Achievements | 20% | Counts numbers/metrics (%, $, counts) in resume bullets |
| Action Verb Density | 10% | Checks for strong verbs: Led, Built, Reduced, Increased, Deployed, etc. |
| Relevance Score | 10% | Cosine similarity between resume embedding and target role description |
| Format Compliance | 5% | ATS-friendly format check — file type, word count, table borders |

- Calculates **Readiness Score (0–100)** using:
  ```
  Readiness = (KeywordMatch × 0.35) + (ParseScore × 0.20)
             + (QuantifiedAchievements × 0.20) + (SectionCompleteness × 0.15)
             + (FormatScore × 0.10)
  ```
- Keyword matching is fully dynamic — extracted from the job description/target role using spaCy NLP, not a hardcoded skill list
- Generates 384-dim resume embedding using sentence-transformers → stored in MongoDB

### Agent 2 — Skill Gap Analyzer
- Queries Groq (Llama 3.3 70B) for 15–25 required skills for any target role
- Uses cosine similarity (sentence-transformers) for semantic skill matching
- Calculates gap percentage and prioritizes missing skills by market demand

### Agent 3 — Roadmap Generator
- Estimates personalized duration based on skill count, hours/day, student level
- Generates detailed daily plan + weekly plan + monthly milestones
- Recommends real resources (Coursera, YouTube, LeetCode) per skill
- Creates mock interview schedule

### Agent 4 — Job Matching Agent (Dynamic Scoring + Bug Fixes)
- Semantic job search using sentence-transformer embeddings
- **6 scoring criteria** with dynamic weight engine:

| Criterion | How it's scored |
|-----------|-----------------|
| Skill Score | Sentence-transformer cosine similarity ≥ 0.72 → hard match (full credit). Below threshold → soft match: best_cosine × 0.5 as partial credit |
| Resume Score | 60% section completeness + 40% keyword density vs this job's required skills |
| CGPA Score | candidate ≥ required → 100. Else: max(0, (1 − deficit/min_cgpa) × 100) — clamped, cannot go negative |
| Experience Score | candidate_months / required_months × 100, capped at 100. No requirement → excluded |
| Certification Score | Fuzzy match via rapidfuzz token_set_ratio ≥ 85. Falls back to exact match if unavailable |
| Batch Score | Graduation year in allowed years → 100, else 0. Unknown year → excluded (not 50) |

- **Dynamic weight re-normalization**: criteria returning `None` are dropped and remaining weights re-normalize to exactly 100%
  - Skills only → skill: 70%, resume: 30%
  - Skills + CGPA → skill: 56%, resume: 22%, cgpa: 21% *(re-normalized from raw 0.50/0.20/0.15)*
  - All criteria present → weights split from raw: skill: 0.50, resume: 0.20, cgpa: 0.15, exp: 0.15, certs: 0.10, batch: 0.10

- **Placement prediction** thresholds:

| Score | Prediction |
|-------|------------|
| ≥ 80 | Highly Likely |
| ≥ 65 | Likely |
| ≥ 50 | Possible |
| ≥ 35 | Unlikely |
| < 35 | Not Ready |

---

## 🏗️ Project Structure

```
final-capstone-project-agentic-ai-ai_placement_guide/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── resume_analyzer/agent.py    ← Agent 1 (ATS + Readiness scoring)
│   │   │   ├── skill_gap/agent.py          ← Agent 2
│   │   │   ├── roadmap/agent.py            ← Agent 3
│   │   │   └── job_matching/agent.py       ← Agent 4 (dynamic scoring engine)
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py
│   │   │   ├── resume.py
│   │   │   ├── skill_gap.py
│   │   │   ├── roadmap.py
│   │   │   ├── jobs.py
│   │   │   ├── pipeline.py                 ← Full pipeline endpoint
│   │   │   └── students.py
│   │   ├── core/
│   │   │   ├── config.py                   ← Settings from .env
│   │   │   ├── embedder.py                 ← sentence-transformers singleton
│   │   │   └── security.py                 ← JWT + RBAC
│   │   ├── db/session.py                   ← Async Motor + MongoDB init
│   │   ├── models/models.py                ← MongoDB document builders
│   │   ├── schemas/schemas.py              ← All Pydantic schemas
│   │   ├── repositories/
│   │   │   ├── user_repo.py
│   │   │   ├── resume_repo.py
│   │   │   └── job_repo.py
│   │   └── main.py                         ← FastAPI app entry point
│   ├── uploads/                            ← Uploaded resume files
│   ├── .env                                ← Environment variables
│   ├── .env.example
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx                    ← Landing page → redirects to /login
│       │   ├── (auth)/login/page.tsx
│       │   ├── (auth)/register/page.tsx
│       │   └── (dashboard)/
│       │       ├── layout.tsx              ← Sidebar nav (logo click → /dashboard)
│       │       ├── dashboard/page.tsx      ← Stats + charts + readiness banner
│       │       ├── upload/page.tsx         ← Drag-drop + agent progress
│       │       ├── analysis/page.tsx       ← Resume analysis + ATS tips panel
│       │       ├── history/page.tsx        ← Resume version history
│       │       ├── roadmap/page.tsx        ← Tabbed roadmap view
│       │       ├── jobs/page.tsx           ← Job matches + rankings
│       │       └── profile/page.tsx        ← Student profile
│       ├── components/
│       │   ├── DashboardCharts.tsx         ← Recharts (SSR-disabled) for dashboard
│       │   └── AnalysisCharts.tsx          ← Recharts (SSR-disabled) for analysis
│       └── lib/
│           ├── api.ts                      ← Axios API client
│           ├── store.ts                    ← Zustand state
│           └── utils.ts                   ← Utility functions
├── database/seed.py                        ← Seed jobs with embeddings
├── shared/utils.py                         ← Shared utilities
├── tests/test_agents.py                    ← Pytest test suite
├── docs/
│   ├── ARCHITECTURE.md                     ← Full architecture docs
│   └── SETUP.md                            ← Local dev setup guide
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 (async) |
| AI/ML | Groq (Llama 3.3 70B), sentence-transformers (all-MiniLM-L6-v2) |
| NLP | spaCy (en_core_web_sm), scikit-learn cosine similarity |
| Fuzzy Matching | rapidfuzz (certification matching, token_set_ratio ≥ 85) |
| PDF/DOCX | PyMuPDF, python-docx |
| Database | MongoDB + Motor (async) |
| Auth | JWT (python-jose) + bcrypt |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Charts | Recharts (dynamic import, ssr:false — fixes hydration mismatch) |
| State | Zustand |
| Package Manager | uv (Astral) |

---

## 🚀 Quick Start (uv)

```bash
# Backend
cd backend
uv sync
uv run python -m spacy download en_core_web_sm
copy .env.example .env   # Add GROQ_API_KEY — get free key at https://console.groq.com
uv run uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Make sure MongoDB is running locally on `mongodb://localhost:27017` before starting the backend.

See [docs/SETUP.md](docs/SETUP.md) for detailed instructions.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login → JWT |
| POST | `/api/v1/analyze/full` | **Upload resume → All 4 agents** |
| POST | `/api/v1/resume/analyze` | Agent 1 only |
| POST | `/api/v1/skill-gap/analyze` | Agent 2 only |
| POST | `/api/v1/roadmap/generate` | Agent 3 only |
| POST | `/api/v1/jobs/match` | Agent 4 only |
| GET  | `/api/v1/students/me` | Profile |

Interactive docs: http://localhost:8000/docs

### `/api/v1/jobs/match` Request Body

```json
{
  "skills": ["Python", "FastAPI", "MongoDB"],
  "resume_score": 72.5,
  "resume_raw_text": "full resume text here...",
  "cgpa": 8.2,
  "graduation_year": 2025,
  "experience_months": 3,
  "certifications": ["AWS Cloud Practitioner"],
  "target_role": "Backend Developer"
}
```

---

## 🔧 Environment Variables

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=placement_ai
SECRET_KEY=your-super-secret-32-character-key-here
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
DEBUG=true
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=10
```

---

## 👥 Team

| Member | Responsibility |
|--------|----------------|
| Member 1 | Agent 1 (Resume Analyzer) + Database + Auth API |
| Member 2 | Agent 2 (Skill Gap) + Agent 3 (Roadmap) + Pipeline |
| Member 3 | Agent 4 (Job Matching) + Frontend + Deployment |

---

## 🖥️ Frontend Features

- **Landing page** — auto-redirects unauthenticated users to `/login`, authenticated to `/dashboard`
- **Sidebar logo** — clicking the AI Placement logo navigates back to `/dashboard`
- **Readiness banner badges** — target role and student level badges only appear after a resume is uploaded (not shown at 0/100)
- **ATS Improvement Tips panel** — shown in Analysis page after upload; lists actionable fixes with category tags (KEYWORDS / IMPACT / STYLE / STRUCTURE / FORMAT), estimated point gains per fix, and FIX → buttons
- **Resume Version Comparison** — side-by-side diff of two resume versions with ATS score delta, added/removed items per section
- **Recharts hydration fix** — all chart components dynamically imported with `ssr: false` to prevent `recharts1-clip` vs `recharts2-clip` ID mismatch on page reload

---

## 📖 Documentation

- [Architecture & Diagrams](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP.md)
- API Docs: http://localhost:8000/docs (when running)
