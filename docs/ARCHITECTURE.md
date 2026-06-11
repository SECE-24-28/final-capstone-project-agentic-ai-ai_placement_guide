# 🏗️ AI Placement Preparation Agent — Complete Architecture

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  Login │ Register │ Dashboard │ Upload │ Analysis │ Roadmap     │
│  Jobs  │ Profile  │ (Tailwind CSS + Recharts)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (JSON)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                         │
│                                                                 │
│  /api/v1/auth         JWT Authentication + RBAC                 │
│  /api/v1/resume       Agent 1 — Resume Analyzer                 │
│  /api/v1/skill-gap    Agent 2 — Skill Gap Analyzer              │
│  /api/v1/roadmap      Agent 3 — Roadmap Generator               │
│  /api/v1/jobs         Agent 4 — Job Matching                    │
│  /api/v1/analyze      Full Pipeline (all 4 agents)              │
└────────┬─────────────┬────────────────┬───────────┬────────────┘
         │             │                │           │
         ▼             ▼                ▼           ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Agent 1  │  │ Agent 2  │  │ Agent 3  │  │ Agent 4  │
   │ Resume   │  │ Skill    │  │ Roadmap  │  │ Job      │
   │ Analyzer │  │ Gap      │  │ Gen      │  │ Matching │
   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                                │
                                ▼
              ┌─────────────────────────────────┐
              │    PostgreSQL 16 + pgvector      │
              │  ┌─────────────┐ ┌────────────┐ │
              │  │ Relational  │ │  Vector    │ │
              │  │ Tables      │ │  Embeddings│ │
              │  └─────────────┘ └────────────┘ │
              └─────────────────────────────────┘
```

---

## 2. Multi-Agent Architecture

```
Resume Upload (PDF/DOCX)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 1: RESUME ANALYZER                                       │
│                                                                 │
│  PyMuPDF/python-docx → Text Extraction                         │
│         ↓                                                       │
│  Gemini API → Structured JSON (skills, education, exp, etc)    │
│         ↓                                                       │
│  Gemini API → ATS Score (0-100) + Feedback                     │
│         ↓                                                       │
│  sentence-transformers → 384-dim embedding → PostgreSQL        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ {skills[], cgpa, graduation_year...}
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 2: SKILL GAP ANALYZER                                    │
│                                                                 │
│  Gemini API → Role Requirements (15-25 skills for target role) │
│         ↓                                                       │
│  sentence-transformers → Cosine Similarity (semantic match)    │
│         ↓                                                       │
│  Gemini API → Priority Ranking + Learning Order                │
│  Output: gap_percentage, missing_skills[], priority_skills[]   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ {missing_skills[], learning_order[]}
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 3: ROADMAP GENERATOR                                     │
│                                                                 │
│  Duration Estimator → weeks = ceil(skills × hrs/skill)        │
│         ↓                                                       │
│  Gemini API → Full Roadmap JSON                                │
│  • 14-day daily plan                                           │
│  • Full weekly plan (all N weeks)                              │
│  • Monthly milestones                                          │
│  • 2-3 real resources per skill (Coursera, YouTube, etc)       │
│  • Mock interview schedule                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ {roadmap, resources, schedule}
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 4: JOB MATCHING AGENT                                    │
│                                                                 │
│  pgvector Semantic Search → Top-30 relevant jobs               │
│         ↓                                                       │
│  Dynamic Scoring Engine:                                       │
│    • Skill Score (50%) — always present                        │
│    • Resume Score (20%) — always present                       │
│    • Remaining 30% → split equally among:                      │
│      CGPA Score | Experience Score | Cert Score | Batch Score  │
│      (only if job has those criteria)                          │
│         ↓                                                       │
│  Company Rankings + Placement Prediction                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                   Unified Dashboard
```

---

## 3. Database ER Diagram

```
users (1) ──── (1) students (1) ──── (N) resumes
                    │                      │
                    │              ┌───────┼───────┐
                    │              │       │       │
                    │           skills  education  experience
                    │           certifications  projects
                    │           resume_feedback
                    │
                    ├──── (N) skill_gaps
                    ├──── (N) roadmaps
                    └──── (N) job_matches ──── (N) jobs ──── (1) companies
```

---

## 4. Database Schema

```sql
-- users: authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'student',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- students: profile data (populated from resume)
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    target_role VARCHAR(255),
    available_hours_per_day FLOAT DEFAULT 2.0,
    cgpa FLOAT,
    graduation_year INTEGER,
    student_level VARCHAR(50) DEFAULT 'beginner',
    placement_status VARCHAR(50) DEFAULT 'not_ready',
    created_at TIMESTAMP DEFAULT NOW()
);

-- resumes: stores file + AI analysis + 384-dim vector embedding
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    raw_text TEXT,
    resume_score FLOAT DEFAULT 0.0,
    embedding vector(384),            -- pgvector
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- skills, education, experience, projects, certifications, resume_feedback
-- (linked to resumes.id)

-- jobs: stores job postings + role embedding for semantic search
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    role VARCHAR(255),
    required_skills JSON,
    min_cgpa FLOAT,
    required_degree VARCHAR(255),
    batch_years JSON,
    min_experience_months INTEGER DEFAULT 0,
    required_certifications JSON,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    embedding vector(384),            -- pgvector semantic search
    created_at TIMESTAMP DEFAULT NOW()
);

-- job_matches: dynamic score per student per job
CREATE TABLE job_matches (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    job_id INTEGER REFERENCES jobs(id),
    match_score FLOAT,
    score_breakdown JSON,             -- which criteria used + individual scores
    missing_skills JSON,
    placement_prediction VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, job_id)
);
```

---

## 5. API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/auth/register | ❌ | Register new user |
| POST | /api/v1/auth/login | ❌ | Login, get JWT |
| GET | /api/v1/students/me | ✅ | Get student profile |
| PATCH | /api/v1/students/me | ✅ | Update profile |
| POST | /api/v1/resume/analyze | ✅ | Upload resume → Agent 1 |
| GET | /api/v1/resume/latest | ✅ | Get latest analysis |
| POST | /api/v1/skill-gap/analyze | ✅ | Skills + role → Agent 2 |
| POST | /api/v1/roadmap/generate | ✅ | Missing skills → Agent 3 |
| GET | /api/v1/roadmap/latest | ✅ | Get latest roadmap |
| POST | /api/v1/jobs/match | ✅ | Profile → Agent 4 |
| POST | /api/v1/analyze/full | ✅ | Upload → All 4 agents |
| GET | /health | ❌ | Health check |

---

## 6. Dynamic Scoring Logic (Agent 4)

```
Job A: Skills + CGPA
  → skill_score(50%) + resume_score(20%) + cgpa_score(30%)

Job B: Skills + Experience
  → skill_score(50%) + resume_score(20%) + experience_score(30%)

Job C: Skills Only
  → skill_score(50%) + resume_score(20%) + [remaining 30% to skill]
  → effectively: skill_score(70%) + resume_score(30%)

Job D: Skills + Degree + Batch + CGPA
  → skill_score(50%) + resume_score(20%) + cgpa(10%) + batch(10%) + [10% leftover → skill]

Rule: weights always normalize to 100%. No criteria is ever forced.
```

---

## 7. pgvector Semantic Search

```python
# Jobs are embedded when seeded:
embedding = sentence_transformer.encode(
    f"{company} {role} {' '.join(required_skills)}"
)  # → vector(384)

# At query time, semantic search:
SELECT * FROM jobs
ORDER BY embedding <=> query_embedding  -- cosine distance
LIMIT 30;

# Resume embeddings stored similarly for future matching
```

---

## 8. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend Framework | FastAPI | Async REST API |
| ORM | SQLAlchemy 2.0 (async) | Database operations |
| Migrations | Alembic | Schema versioning |
| Database | PostgreSQL 16 | Relational data |
| Vector Search | pgvector | Semantic job search |
| AI API | Gemini 1.5 Flash | Extraction, scoring, roadmap |
| NLP | spaCy (en_core_web_sm) | Text processing |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 (384-dim) |
| Similarity | scikit-learn cosine | Skill matching |
| PDF Parsing | PyMuPDF | PDF text extraction |
| DOCX Parsing | python-docx | Word doc extraction |
| Auth | JWT (python-jose) + bcrypt | Secure auth |
| Frontend | Next.js 14 + TypeScript | React framework |
| Styling | Tailwind CSS | Utility CSS |
| Charts | Recharts | Data visualization |
| State | Zustand | Global state |
| Forms | React Hook Form + Zod | Form validation |
| HTTP Client | Axios | API calls |
| Containerization | Docker + docker-compose | Deployment |

---

## 9. Agent Communication Flow

```
POST /api/v1/analyze/full
         │
         ├─→ Agent 1: analyze_resume(file_bytes, filename)
         │     └─→ Returns: {skills, education, cgpa, resume_score, embedding, ...}
         │
         ├─→ Agent 2: analyze_skill_gap(skills, target_role)
         │     └─→ Returns: {gap_%, missing_skills, priority_skills, learning_order}
         │
         ├─→ Agent 3: generate_roadmap(missing_skills, level, hours, role)
         │     └─→ Returns: {daily_plan, weekly_plan, milestones, resources, schedule}
         │
         └─→ Agent 4: match_jobs(skills, resume_score, cgpa, year, exp, certs, jobs)
               └─→ Returns: {job_matches, company_rankings, probability, prediction}
```

---

## 10. Development Timeline (3 Team Members)

### Week 1-2: Foundation
| Member | Tasks |
|--------|-------|
| Member 1 | PostgreSQL setup, SQLAlchemy models, Alembic migrations, pgvector |
| Member 2 | FastAPI project structure, JWT auth, User/Student endpoints |
| Member 3 | Frontend setup (Next.js), login/register pages, Zustand store |

### Week 3-4: Agent 1 + Agent 4
| Member | Tasks |
|--------|-------|
| Member 1 | Agent 1: PyMuPDF + python-docx parsing, Gemini extraction prompts |
| Member 2 | Agent 4: Dynamic scoring engine, pgvector semantic search |
| Member 3 | Frontend: Upload page, Analysis page, Job Matches page |

### Week 5-6: Agent 2 + Agent 3
| Member | Tasks |
|--------|-------|
| Member 1 | Agent 2: Gemini role requirements, sentence-transformers semantic matching |
| Member 2 | Agent 3: Duration estimator, Gemini roadmap generation, resource curation |
| Member 3 | Frontend: Roadmap page with tabs, Dashboard with charts |

### Week 7-8: Integration + Testing
| Member | Tasks |
|--------|-------|
| Member 1 | Full pipeline endpoint, agent communication, error handling |
| Member 2 | Database seeder, integration tests, performance optimization |
| Member 3 | Dashboard stats, Profile page, Docker setup, deployment docs |

### Week 9-10: Polish + Documentation
- All: Testing, bug fixes, README, demo video, presentation

---

## 11. Frontend Page Structure

```
/login                  → Auth login
/register               → Auth register
/dashboard              → Stats cards, readiness score, charts
/upload                 → Drag-drop resume + config + agent progress
/analysis               → Resume score, skills pie chart, education/exp/projects
/roadmap                → Tabbed: weekly/daily/milestones/resources/mock interviews
/jobs                   → Company rankings chart, job match cards with score breakdown
/profile                → Student profile view + edit
```

---

## 12. Future Enhancements

1. **LinkedIn Resume Import** — Auto-fill from LinkedIn profile URL
2. **Real Job Scraping** — Naukri/LinkedIn live job postings via API
3. **Mock Interview AI** — Gemini-powered Q&A with scoring
4. **Placement Predictor ML** — Train XGBoost on historical placement data
5. **Peer Benchmarking** — Compare skills vs cohort average
6. **Admin Dashboard** — Track all students, placement rates, company analytics
7. **Email Notifications** — Weekly progress reports, deadline reminders
8. **Resume Builder** — Generate optimized resume from profile data
9. **Multi-language** — Support resumes in regional languages
10. **Mobile App** — React Native companion app
