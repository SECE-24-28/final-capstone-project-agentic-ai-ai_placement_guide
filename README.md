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
- Calculates ATS Score (0–100) with detailed feedback via Gemini API
- Generates 384-dim resume embedding using sentence-transformers → stored in pgvector

### Agent 2 — Skill Gap Analyzer
- Queries Gemini API for 15-25 required skills for any target role
- Uses cosine similarity (sentence-transformers) for semantic skill matching
- Calculates gap percentage and prioritizes missing skills by market demand

### Agent 3 — Roadmap Generator
- Estimates personalized duration based on skill count, hours/day, student level
- Generates detailed 14-day daily plan + full weekly plan + monthly milestones
- Recommends real resources (Coursera, YouTube, LeetCode) per skill
- Creates mock interview schedule

### Agent 4 — Job Matching Agent (Dynamic Scoring)
- Uses pgvector semantic search to find relevant jobs
- **Dynamic scoring**: weights auto-adjust based on criteria in each job posting
  - Job with only Skills → skill(70%) + resume(30%)
  - Job with Skills + CGPA → skill(50%) + resume(20%) + cgpa(30%)
  - Job with 4 criteria → weights split equally among available criteria
- Predicts: Highly Likely / Likely / Possible / Unlikely / Not Ready

---

## 🏗️ Project Structure

```
placement_ai_system/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── resume_analyzer/agent.py    ← Agent 1
│   │   │   ├── skill_gap/agent.py          ← Agent 2
│   │   │   ├── roadmap/agent.py            ← Agent 3
│   │   │   └── job_matching/agent.py       ← Agent 4 (+ existing scoring.py)
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
│   │   │   └── security.py                 ← JWT + RBAC
│   │   ├── db/session.py                   ← Async SQLAlchemy + pgvector init
│   │   ├── models/models.py                ← All SQLAlchemy models
│   │   ├── schemas/schemas.py              ← All Pydantic schemas
│   │   ├── repositories/
│   │   │   ├── user_repo.py
│   │   │   ├── resume_repo.py
│   │   │   └── job_repo.py
│   │   └── main.py                         ← FastAPI app entry point
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/001_initial.py
│   ├── pyproject.toml
│   ├── uv.lock
│   └── alembic.ini
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── (auth)/login/page.tsx
│       │   ├── (auth)/register/page.tsx
│       │   └── (dashboard)/
│       │       ├── layout.tsx              ← Sidebar nav
│       │       ├── dashboard/page.tsx      ← Stats + charts
│       │       ├── upload/page.tsx         ← Drag-drop + agent progress
│       │       ├── analysis/page.tsx       ← Resume analysis results
│       │       ├── roadmap/page.tsx        ← Tabbed roadmap view
│       │       ├── jobs/page.tsx           ← Job matches + rankings
│       │       └── profile/page.tsx        ← Student profile
│       └── lib/
│           ├── api.ts                      ← Axios API client
│           ├── store.ts                    ← Zustand state
│           └── utils.ts                   ← Utility functions
├── database/seed.py                        ← Seed 25 jobs with embeddings
├── shared/utils.py                         ← Shared utilities
├── tests/test_agents.py                    ← Pytest test suite
├── docs/
│   ├── ARCHITECTURE.md                     ← Full architecture docs
│   └── SETUP.md                           ← Local dev setup guide
└── docs/
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 (async) |
| AI/ML | Gemini 1.5 Flash, sentence-transformers (all-MiniLM-L6-v2) |
| NLP | spaCy (en_core_web_sm), scikit-learn cosine similarity |
| PDF/DOCX | PyMuPDF, python-docx |
| Database | PostgreSQL 16 + pgvector |
| Auth | JWT (python-jose) + bcrypt |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Charts | Recharts |
| State | Zustand |
| Package Manager | uv (Astral) |

---

## 🚀 Quick Start (uv)

```bash
# Backend
cd backend
uv sync
uv run python -m spacy download en_core_web_sm
copy .env.example .env   # GEMINI_API_KEY add pannunga
uv run alembic upgrade head
uv run python ../database/seed.py
uv run uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

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

---

## 👥 Team

| Member | Responsibility |
|--------|----------------|
| Member 1 | Agent 1 (Resume Analyzer) + Database + Auth API |
| Member 2 | Agent 2 (Skill Gap) + Agent 3 (Roadmap) + Pipeline |
| Member 3 | Agent 4 (Job Matching) + Frontend + Deployment |

---

## 📖 Documentation

- [Architecture & Diagrams](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP.md)
- API Docs: http://localhost:8000/docs (when running)
