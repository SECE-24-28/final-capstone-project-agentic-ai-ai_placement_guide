# AI Placement Preparation Agent 🎯

An intelligent multi-agent AI system for student placement preparation with resume analysis, skillgap identification, personalized roadmaps, and job matching.

---

## 📋 Features

- **Resume Analyzer** - ATS scoring (0-100), skill extraction, keyword optimization
- **Skill Gap Analyzer** - Compare skills vs job requirements, gap percentage
- **Roadmap Agent** - Personalized daily/weekly learning plans
- **Job Matching Agent** - Match probability % for companies

---

## 🏗️ System Architecture
Resume Upload → Resume Analyzer → Skill Gap Analyzer → Roadmap Agent → Job Matching Agent

---

## 🤖 The 4 Agents

| Agent | Purpose | Key Tech |
|-------|---------|----------|
| **Resume Analyzer** | Parse PDF/DOCX, ATS scoring | `PyMuPDF`, `spaCy`, GPT-4 |
| **Skill Gap Analyzer** | Compare skills, calculate gap % | `scikit-learn`, Cosine Similarity |
| **Roadmap Agent** | Generate learning plans | GPT-4, PostgreSQL |
| **Job Matching Agent** | Match students to jobs (40% skill + 25% assessment + 20% interview + 15% communication) | Pinecone, XGBoost |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Django |
| **AI/ML** | GPT-4, Gemini, `spaCy`, `scikit-learn`, `sentence-transformers` |
| **Database** | Pinecone (Vector DB) |
| **Frontend** | Next.js / React / Streamlit |

---

## 👥 Team Distribution

| Member | Responsibility |
|--------|----------------|
| **Member 1** | Resume Analyzer Agent (Parser + NLP + ATS scoring + API) |
| **Member 2** | Skill Gap Analyzer + Roadmap Agent (2 agents) |
| **Member 3** | Job Matching Agent + Infrastructure (DB, Auth, Docker, Deployment) |

---

## 📦 Installation

### Prerequisites
- Python 3.13.7
- PostgreSQL 14+
- OpenAI/Gemini API keys

### Setup
```bash
# Clone repository
git clone https://github.com/your-org/ai-placement-agent.git
cd ai-placement-agent

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

### Access
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analyze-resume` | Upload resume → get analysis |
| POST | `/api/v1/skill-gap` | Resume + job desc → gap report |
| POST | `/api/v1/generate-roadmap` | Skill gaps → learning plan |
| POST | `/api/v1/match-jobs` | Student profile → job matches |
| POST | `/api/v1/placement-assistant` | Full analysis (all 4 agents) |

### Example Request
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-resume" \
     -F "resume=@resume.pdf"
```

### Example Response
```json
{
  "resume_score": 85,
  "skill_gap": "15%",
  "roadmap": { "duration": "12 weeks", "weekly_plan": [...] },
  "job_matches": [
    {"company": "TCS", "probability": 84},
    {"company": "Infosys", "probability": 78}
  ]
}
```

---

## 📁 Project Structure

ai-placement-agent/
├── backend/
│ ├── app/
│ │ ├── agents/
│ │ │ ├── resume_analyzer/
│ │ │ ├── skill_gap/
│ │ │ ├── roadmap/
│ │ │ └── job_matching/
│ │ ├── api/v1/endpoints/
│ │ └── main.py
│ ├── requirements.txt
│ └── Dockerfile
├── frontend/
├── docker-compose.yml
└── README.md


---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/name`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push (`git push origin feature/name`)
5. Open Pull Request

---


