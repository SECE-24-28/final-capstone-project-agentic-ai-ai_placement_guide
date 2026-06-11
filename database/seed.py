"""
Seed 25 jobs into MongoDB with DIFFERENT criteria combinations.
This demonstrates Agent 4's Dynamic Scoring — each job type uses different fields.

Job Types:
  Type A — Skills Only                    (7 jobs)
  Type B — Skills + CGPA                  (6 jobs)
  Type C — Skills + Experience            (6 jobs)
  Type D — Skills + CGPA + Batch + Certs  (6 jobs)

Run: cd backend && uv run python ../database/seed.py --reset
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from motor.motor_asyncio import AsyncIOMotorClient
from sentence_transformers import SentenceTransformer
from datetime import datetime, timezone

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB",  "placement_ai")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ── TYPE A: Skills Only (no CGPA/batch/exp filter) ───────────────────────────
TYPE_A = [
    {
        "company": "Startup Hub",
        "role": "Full Stack Developer",
        "required_skills": ["React", "Node.js", "MongoDB", "REST APIs", "Git"],
        "job_type": "A",
    },
    {
        "company": "TechMinds",
        "role": "Python Developer",
        "required_skills": ["Python", "Django", "PostgreSQL", "Docker", "Linux"],
        "job_type": "A",
    },
    {
        "company": "CodeFactory",
        "role": "Frontend Developer",
        "required_skills": ["React", "TypeScript", "Tailwind CSS", "JavaScript", "HTML", "CSS"],
        "job_type": "A",
    },
    {
        "company": "DataBridge",
        "role": "Data Analyst",
        "required_skills": ["Python", "SQL", "Pandas", "Excel", "Power BI"],
        "job_type": "A",
    },
    {
        "company": "CloudNine",
        "role": "DevOps Engineer",
        "required_skills": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD", "Terraform"],
        "job_type": "A",
    },
    {
        "company": "OpenLogic",
        "role": "Backend Developer",
        "required_skills": ["Java", "Spring Boot", "MySQL", "REST APIs", "Git"],
        "job_type": "A",
    },
    {
        "company": "NexGen",
        "role": "Mobile Developer",
        "required_skills": ["React Native", "JavaScript", "Firebase", "REST APIs"],
        "job_type": "A",
    },
]

# ── TYPE B: Skills + CGPA ────────────────────────────────────────────────────
TYPE_B = [
    {
        "company": "Google",
        "role": "Software Engineer",
        "required_skills": ["Python", "Data Structures", "Algorithms", "System Design", "SQL"],
        "min_cgpa": 8.0,
        "job_type": "B",
    },
    {
        "company": "Microsoft",
        "role": "Software Development Engineer",
        "required_skills": ["Java", "C++", "Data Structures", "OOP", "SQL", "Azure"],
        "min_cgpa": 7.5,
        "job_type": "B",
    },
    {
        "company": "Adobe",
        "role": "Computer Scientist",
        "required_skills": ["C++", "Python", "Machine Learning", "Data Structures", "Algorithms"],
        "min_cgpa": 8.0,
        "job_type": "B",
    },
    {
        "company": "Oracle",
        "role": "Applications Engineer",
        "required_skills": ["Java", "SQL", "PL/SQL", "Oracle DB", "REST APIs"],
        "min_cgpa": 7.0,
        "job_type": "B",
    },
    {
        "company": "Zoho",
        "role": "Software Engineer",
        "required_skills": ["Java", "Python", "Data Structures", "SQL", "JavaScript"],
        "min_cgpa": 7.0,
        "job_type": "B",
    },
    {
        "company": "Freshworks",
        "role": "Software Engineer",
        "required_skills": ["Ruby on Rails", "Python", "React", "PostgreSQL", "REST APIs"],
        "min_cgpa": 7.5,
        "job_type": "B",
    },
]

# ── TYPE C: Skills + Experience ──────────────────────────────────────────────
TYPE_C = [
    {
        "company": "Swiggy",
        "role": "Backend Engineer",
        "required_skills": ["Python", "Go", "MySQL", "Redis", "Kafka", "Docker"],
        "min_experience_months": 6,
        "job_type": "C",
    },
    {
        "company": "Zomato",
        "role": "Software Engineer",
        "required_skills": ["Python", "Django", "PostgreSQL", "Redis", "AWS"],
        "min_experience_months": 6,
        "job_type": "C",
    },
    {
        "company": "Razorpay",
        "role": "Software Engineer",
        "required_skills": ["Python", "Go", "MySQL", "Redis", "Docker", "Kubernetes"],
        "min_experience_months": 12,
        "job_type": "C",
    },
    {
        "company": "CRED",
        "role": "Software Engineer",
        "required_skills": ["Kotlin", "Python", "PostgreSQL", "Redis", "AWS"],
        "min_experience_months": 12,
        "job_type": "C",
    },
    {
        "company": "Ola",
        "role": "Software Engineer",
        "required_skills": ["Java", "Spring Boot", "MySQL", "Kafka", "AWS"],
        "min_experience_months": 6,
        "job_type": "C",
    },
    {
        "company": "Myntra",
        "role": "Software Engineer",
        "required_skills": ["Java", "Scala", "Spark", "MySQL", "AWS"],
        "min_experience_months": 6,
        "job_type": "C",
    },
]

# ── TYPE D: Skills + CGPA + Batch + Certifications ──────────────────────────
TYPE_D = [
    {
        "company": "Amazon",
        "role": "SDE-1",
        "required_skills": ["Java", "Python", "Data Structures", "Algorithms", "AWS", "REST APIs"],
        "min_cgpa": 7.0,
        "batch_years": [2024, 2025],
        "required_certifications": ["AWS Certified Developer"],
        "job_type": "D",
    },
    {
        "company": "Infosys",
        "role": "Systems Engineer",
        "required_skills": ["Java", "SQL", "HTML", "CSS", "JavaScript"],
        "min_cgpa": 6.5,
        "batch_years": [2024, 2025],
        "required_certifications": None,
        "job_type": "D",
    },
    {
        "company": "TCS",
        "role": "Software Engineer",
        "required_skills": ["Java", "Python", "SQL", "OOP", "Linux"],
        "min_cgpa": 6.0,
        "batch_years": [2024, 2025],
        "required_certifications": None,
        "job_type": "D",
    },
    {
        "company": "Wipro",
        "role": "Software Engineer",
        "required_skills": ["Java", "Python", "SQL", "JavaScript", "Git"],
        "min_cgpa": 6.0,
        "batch_years": [2024, 2025],
        "required_certifications": None,
        "job_type": "D",
    },
    {
        "company": "Salesforce",
        "role": "Associate Software Engineer",
        "required_skills": ["Java", "Apex", "SQL", "JavaScript", "Salesforce CRM"],
        "min_cgpa": 7.5,
        "batch_years": [2024, 2025],
        "required_certifications": ["Salesforce Administrator"],
        "job_type": "D",
    },
    {
        "company": "IBM",
        "role": "Associate Software Engineer",
        "required_skills": ["Java", "Python", "SQL", "Cloud Computing", "REST APIs"],
        "min_cgpa": 6.5,
        "batch_years": [2024, 2025],
        "required_certifications": None,
        "job_type": "D",
    },
]

ALL_JOBS = TYPE_A + TYPE_B + TYPE_C + TYPE_D  # 25 total


async def seed():
    reset = "--reset" in sys.argv
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB]

    existing = await db.jobs.count_documents({})
    if existing >= len(ALL_JOBS) and not reset:
        print(f"[OK] Already have {existing} jobs. Use --reset to re-seed.")
        client.close()
        return

    await db.jobs.delete_many({})
    print(f"[...] Seeding {len(ALL_JOBS)} jobs with dynamic criteria...")

    docs = []
    type_counts = {"A": 0, "B": 0, "C": 0, "D": 0}

    for job in ALL_JOBS:
        text = f"{job['role']} {job['company']} {' '.join(job['required_skills'])}"
        embedding = embedder.encode(text).tolist()
        doc = {
            **job,
            "embedding": embedding,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        docs.append(doc)
        type_counts[job["job_type"]] += 1

    await db.jobs.insert_many(docs)

    print(f"[OK] Seeded {len(docs)} jobs:")
    print(f"     Type A (Skills Only)              : {type_counts['A']} jobs")
    print(f"     Type B (Skills + CGPA)            : {type_counts['B']} jobs")
    print(f"     Type C (Skills + Experience)      : {type_counts['C']} jobs")
    print(f"     Type D (Skills+CGPA+Batch+Certs)  : {type_counts['D']} jobs")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
