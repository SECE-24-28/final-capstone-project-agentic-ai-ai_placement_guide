# 🚀 Local Development Setup (uv)

Docker illai — uv vechu run pannrom.

---

## Prerequisites

| Tool | Install |
|------|---------|
| Python 3.10+ | python.org |
| uv | `pip install uv` or `winget install astral-sh.uv` |
| Node.js 20+ | nodejs.org |
| PostgreSQL 16+ with pgvector | See below |

---

## 1. PostgreSQL + pgvector

pgvector support ullavai use pannanum. Two options:

### Option A: pgvector Windows Installer (Easiest)
```
1. Download PostgreSQL 16 from postgresql.org
2. Download pgvector from: https://github.com/pgvector/pgvector/releases
   → pgvector-pg16-windows.zip
3. Extract and copy files to your PostgreSQL install folder
4. psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
5. psql -U postgres -c "CREATE DATABASE placement_ai;"
```

### Option B: Already have PostgreSQL — just enable pgvector
```sql
-- psql -U postgres -d placement_ai
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 2. Backend Setup (uv)

```bash
cd backend

# uv will auto-create virtualenv and install all deps from pyproject.toml
uv sync

# spaCy model download
uv run python -m spacy download en_core_web_sm

# .env file create pannunga
copy .env.example .env
# .env file open panni GEMINI_API_KEY add pannunga

# Database tables create
uv run alembic upgrade head

# 25 jobs seed pannunga (backend/ folder la irundhu run pannunga)
uv run python ../database/seed.py

# Backend start
uv run uvicorn app.main:app --reload --port 8000
```

✅ API running at: http://localhost:8000  
✅ Swagger docs: http://localhost:8000/docs

---

## 3. Frontend Setup

```bash
cd frontend

npm install

# .env.local create pannunga
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local

npm run dev
```

✅ Frontend running at: http://localhost:3000

---

## 4. .env file contents (backend/.env)

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/placement_ai
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/placement_ai
SECRET_KEY=your-super-secret-32-character-key-here
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash
DEBUG=true
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=10
```

---

## 5. Gemini API Key எடுக்கணும்

1. https://aistudio.google.com/ → Sign in
2. "Get API key" → "Create API key"
3. Copy panni `.env` la paste pannunga

---

## 6. uv common commands

```bash
# Dependencies add pannanum
uv add fastapi

# Dev dependency add pannanum
uv add --dev pytest

# Script run pannanum
uv run python any_script.py

# Tests run pannanum
uv run pytest tests/ -v

# Virtual env activate (optional, uv run use pannalum)
.venv\Scripts\activate   # Windows
```

---

## 7. Verify

```bash
# Backend health check
curl http://localhost:8000/health
# → {"status":"healthy","service":"AI Placement Preparation Agent"}
```

---

## 8. First Use Flow

1. http://localhost:3000 open pannunga
2. Register → account create pannunga
3. Upload page → resume PDF drag & drop
4. Target role select pannunga
5. "Run Full AI Analysis" click pannunga
6. Dashboard la results parunga 🎉

---

## Common Issues

| Problem | Fix |
|---------|-----|
| `uv: command not found` | `pip install uv` |
| `pgvector not found` | Extension install check pannunga |
| `spacy model missing` | `uv run python -m spacy download en_core_web_sm` |
| `Gemini API error` | `.env` la GEMINI_API_KEY check pannunga |
| `asyncpg connect error` | PostgreSQL running-a check pannunga, port 5432 |
