"""
features.py — 7 Standalone AI Feature Functions
================================================
Feature 1 — Resume Version Compare (diff viewer)
Feature 2 — Resume Strength Meter
Feature 3 — Job-Specific Resume Tailoring
Feature 4 — Match Score Explainability
Feature 5 — Company-wise Best Match Ranking
Feature 6 — Skill Trend Analyzer
Feature 7 — Adzuna Live Job Fetch with Intelligent Fallback

Usage:
    from app.services.features import (
        compare_resume_versions,
        resume_strength_meter,
        tailor_resume_for_job,
        explain_match_score,
        rank_companies,
        analyze_skill_trends,
        get_jobs,
    )
"""

import os
import re
import json
import time
import requests
from collections import Counter
from datetime import datetime, timezone
from typing import List, Optional

import spacy
from groq import Groq
from pymongo import MongoClient

from app.core.config import settings
from app.core.embedder import embedder as _embedder

# ── Shared helpers ────────────────────────────────────────────────────────────

_groq_client = Groq(api_key=settings.GROQ_API_KEY)
_last_groq_call = 0.0


def _groq(prompt: str, max_tokens: int = 2048) -> str:
    """Throttled Groq call — 2s min gap between requests."""
    global _last_groq_call
    gap = time.time() - _last_groq_call
    if gap < 2.0:
        time.sleep(2.0 - gap)
    _last_groq_call = time.time()

    resp = _groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def _parse_json(raw: str) -> dict:
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        raw = m.group(0)
    return json.loads(raw)


try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download as _dl
    _dl("en_core_web_sm")
    _nlp = spacy.load("en_core_web_sm")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 1 — Resume Version Compare (diff viewer)
# ─────────────────────────────────────────────────────────────────────────────

def compare_resume_versions(resume_v1: dict, resume_v2: dict) -> dict:
    """
    Compare two resume version JSONs (from MongoDB resumes collection).

    Args:
        resume_v1: First resume document dict (older version)
        resume_v2: Second resume document dict (newer version)

    Returns:
        {
            "added": [...],            # items in v2 but not v1
            "removed": [...],          # items in v1 but not v2
            "unchanged": [...],        # items in both
            "sections_changed": [...], # which sections differ
            "ats_v1": 62,
            "ats_v2": 84,
            "ats_improvement": +22
        }
    """
    try:
        sections = {
            "Skills":         ("skills",         lambda x: x.get("name", "")),
            "Experience":     ("experience",      lambda x: x.get("company", "") + " - " + x.get("role", "")),
            "Education":      ("education",       lambda x: x.get("institution", "") + " " + x.get("degree", "")),
            "Certifications": ("certifications",  lambda x: x.get("name", "")),
            "Projects":       ("projects",        lambda x: x.get("name", "")),
        }

        added, removed, unchanged = [], [], []
        sections_changed = []

        for section_label, (field, key_fn) in sections.items():
            # Extract string-sets for each section from both versions
            v1_items = {key_fn(i).strip().lower() for i in resume_v1.get(field, []) if key_fn(i).strip()}
            v2_items = {key_fn(i).strip().lower() for i in resume_v2.get(field, []) if key_fn(i).strip()}

            new_items   = v2_items - v1_items
            lost_items  = v1_items - v2_items
            same_items  = v1_items & v2_items

            if new_items or lost_items:
                sections_changed.append(section_label)

            for item in new_items:
                added.append({"section": section_label, "item": item})
            for item in lost_items:
                removed.append({"section": section_label, "item": item})
            for item in same_items:
                unchanged.append({"section": section_label, "item": item})

        ats_v1 = resume_v1.get("resume_score", 0)
        ats_v2 = resume_v2.get("resume_score", 0)

        return {
            "added":            added,
            "removed":          removed,
            "unchanged":        unchanged,
            "sections_changed": sections_changed,
            "ats_v1":           ats_v1,
            "ats_v2":           ats_v2,
            "ats_improvement":  round(ats_v2 - ats_v1, 1),
        }

    except Exception as e:
        return {"error": f"compare_resume_versions failed: {str(e)}"}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 2 — Resume Strength Meter
# ─────────────────────────────────────────────────────────────────────────────

def resume_strength_meter(resume: dict) -> dict:
    """
    Score a parsed resume JSON across 5 criteria (20 pts each = 100 total).

    Criteria:
        skills        — 5+ skills present
        experience    — descriptions with 50+ total words
        summary       — summary/objective present in raw_text
        education     — degree + institution both present
        certifications — at least 1 certification present

    Args:
        resume: Parsed resume dict (from MongoDB or Agent 1 output)

    Returns:
        {
            "overall": 80,
            "breakdown": {
                "skills": 20, "experience": 20, "summary": 20,
                "education": 20, "certifications": 0
            },
            "tips": [...]
        }
    """
    try:
        breakdown = {}
        tips = []

        # ── Skills: 5+ skills = full 20pts ──────────────────────────────────
        skill_count = len(resume.get("skills", []))
        if skill_count >= 5:
            breakdown["skills"] = 20
        elif skill_count > 0:
            breakdown["skills"] = round((skill_count / 5) * 20)
            tips.append(f"Add more skills — you have {skill_count}, aim for 5+")
        else:
            breakdown["skills"] = 0
            tips.append("Skills section is empty — add your technical skills")

        # ── Experience: descriptions totalling 50+ words ────────────────────
        exp_words = sum(
            len((e.get("description") or "").split())
            for e in resume.get("experience", [])
        )
        if exp_words >= 50:
            breakdown["experience"] = 20
        elif exp_words > 0:
            breakdown["experience"] = round((exp_words / 50) * 20)
            tips.append(f"Expand experience descriptions ({exp_words} words) — aim for 50+ words total")
        else:
            breakdown["experience"] = 0
            tips.append("Add internship/work experience with detailed descriptions")

        # ── Summary: detected in raw_text ───────────────────────────────────
        raw = (resume.get("raw_text") or "").lower()
        if re.search(r"\b(summary|objective|profile|about me)\b", raw):
            breakdown["summary"] = 20
        else:
            breakdown["summary"] = 0
            tips.append("Add a professional Summary or Objective section at the top")

        # ── Education: at least one entry with degree + institution ──────────
        edu_complete = any(
            e.get("degree") and e.get("institution")
            for e in resume.get("education", [])
        )
        if edu_complete:
            breakdown["education"] = 20
        elif resume.get("education"):
            breakdown["education"] = 10
            tips.append("Education section incomplete — add degree and institution name")
        else:
            breakdown["education"] = 0
            tips.append("Add your education details (degree, college, year)")

        # ── Certifications: at least 1 ───────────────────────────────────────
        if resume.get("certifications"):
            breakdown["certifications"] = 20
        else:
            breakdown["certifications"] = 0
            tips.append("Add certifications (e.g. AWS, Google, Coursera) to stand out")

        overall = sum(breakdown.values())

        return {
            "overall":   overall,
            "breakdown": breakdown,
            "tips":      tips,
            "grade":     "Excellent" if overall >= 80 else "Good" if overall >= 60 else "Needs Work",
        }

    except Exception as e:
        return {"error": f"resume_strength_meter failed: {str(e)}"}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 3 — Job-Specific Resume Tailoring
# ─────────────────────────────────────────────────────────────────────────────

def tailor_resume_for_job(resume: dict, job_description: str, db=None) -> dict:
    """
    Tailor a candidate's resume for a specific job description using:
      - spaCy → extract key skills/keywords from JD
      - LLaMA 3.3 70B → rewrite resume sections to match JD
      - MongoDB → save original + tailored versions to resume_versions collection

    Args:
        resume:          Parsed resume dict (Agent 1 output)
        job_description: Plain text JD string (no URL fetching)
        db:              Motor/pymongo DB instance (optional — saves to MongoDB if provided)

    Returns:
        {
            "tailored_resume": {...},
            "keywords_added": ["Docker", "Kubernetes"],
            "keywords_already_present": ["Python", "AWS"]
        }
    """
    try:
        # ── Step 1: Extract JD keywords using spaCy ──────────────────────────
        doc = _nlp(job_description.lower())

        # Collect nouns, proper nouns, and noun chunks as keywords
        jd_keywords = set()
        for token in doc:
            if not token.is_stop and not token.is_punct and len(token.text) > 2:
                if token.pos_ in ("NOUN", "PROPN"):
                    jd_keywords.add(token.text.strip())
        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip()
            if 2 < len(phrase) < 40:
                jd_keywords.add(phrase)

        jd_keywords = sorted(jd_keywords)[:30]  # top 30 keywords

        # ── Step 2: Find which keywords candidate already has / missing ──────
        candidate_skill_names = {s.get("name", "").lower() for s in resume.get("skills", [])}
        raw_lower = (resume.get("raw_text") or "").lower()

        already_present = [k for k in jd_keywords if k.lower() in raw_lower or k.lower() in candidate_skill_names]
        missing_kws     = [k for k in jd_keywords if k not in already_present]

        # ── Step 3: Groq — rewrite resume to match JD ────────────────────────
        prompt = f"""You are a professional resume writer. Tailor the candidate's resume to match the job description.

Job Description Keywords to incorporate: {', '.join(jd_keywords[:20])}

Candidate's Current Resume:
- Skills: {[s.get('name') for s in resume.get('skills', [])]}
- Experience: {json.dumps(resume.get('experience', [])[:2], default=str)}
- Projects: {json.dumps(resume.get('projects', [])[:2], default=str)}
- Summary (from raw): {(resume.get('raw_text') or '')[:500]}

Return ONLY valid JSON with this structure:
{{
  "summary": "Rewritten professional summary tailored to the JD",
  "skills": ["skill1", "skill2", ...],
  "experience_highlights": ["bullet 1 rewritten with JD keywords", "bullet 2"],
  "keywords_incorporated": ["keyword1", "keyword2"]
}}"""

        tailored_raw = _groq(prompt, max_tokens=1500)
        tailored_data = _parse_json(tailored_raw)

        # Build tailored resume document
        tailored_resume = {
            **resume,
            "summary":               tailored_data.get("summary", ""),
            "tailored_skills":       [{"name": s, "category": "Other"} for s in tailored_data.get("skills", [])],
            "experience_highlights": tailored_data.get("experience_highlights", []),
            "is_tailored":           True,
            "tailored_for_jd":       job_description[:200],
        }

        # ── Step 4: Save both versions to MongoDB ────────────────────────────
        if db is not None:
            try:
                now = datetime.now(timezone.utc)
                student_id = str(resume.get("student_id", "unknown"))

                # Save original
                db.resume_versions.insert_one({
                    "student_id":   student_id,
                    "version_type": "original",
                    "resume":       {k: v for k, v in resume.items() if k != "_id"},
                    "created_at":   now,
                })
                # Save tailored
                db.resume_versions.insert_one({
                    "student_id":   student_id,
                    "version_type": "tailored",
                    "resume":       {k: v for k, v in tailored_resume.items() if k != "_id"},
                    "jd_snippet":   job_description[:300],
                    "created_at":   now,
                })
            except Exception as db_err:
                # DB save failure is non-fatal — still return result
                tailored_resume["db_save_warning"] = str(db_err)

        return {
            "tailored_resume":         tailored_resume,
            "keywords_added":          missing_kws[:10],
            "keywords_already_present": already_present[:10],
        }

    except Exception as e:
        return {"error": f"tailor_resume_for_job failed: {str(e)}"}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 4 — Match Score Explainability
# ─────────────────────────────────────────────────────────────────────────────

def explain_match_score(
    score_breakdown: dict,
    candidate_skills: List[str],
    job_required_skills: List[str],
) -> dict:
    """
    Human-readable breakdown of Agent 4's final match score.

    Args:
        score_breakdown:      score_breakdown dict from Agent 4 output
                              (has skill_score, cgpa_score, etc. + criteria_used + weights_used)
        candidate_skills:     list of candidate skill names
        job_required_skills:  list of job required skill names

    Returns:
        {
            "final_score": 78,
            "breakdown": {
                "skills":   {"score": 90, "weight": "50%", "matched": [...], "missing": [...]},
                "cgpa":     {"score": 60, "weight": "10%"},
                ...
            },
            "prediction": "Likely",
            "summary": "human readable sentence"
        }
    """
    try:
        from app.agents.job_matching.agent import predict_placement

        weights_used    = score_breakdown.get("weights_used", {})
        criteria_used   = score_breakdown.get("criteria_used", [])

        # Calculate matched vs missing skills using simple lowercase compare
        cand_lower = {s.lower() for s in candidate_skills}
        matched_skills = [s for s in job_required_skills if s.lower() in cand_lower]
        missing_skills = [s for s in job_required_skills if s.lower() not in cand_lower]

        breakdown = {}

        # Build per-criterion explanation
        criterion_labels = {
            "skill_score":         "skills",
            "resume_score":        "resume",
            "cgpa_score":          "cgpa",
            "experience_score":    "experience",
            "certification_score": "certifications",
            "batch_score":         "batch",
        }

        for key, label in criterion_labels.items():
            if key not in criteria_used:
                continue

            score  = score_breakdown.get(key, 0)
            weight = weights_used.get(key, 0)

            entry = {
                "score":  round(score, 1) if score is not None else 0,
                "weight": f"{weight}%",
            }

            # Skills → add matched/missing detail
            if key == "skill_score":
                entry["matched"] = matched_skills
                entry["missing"] = missing_skills

            # CGPA → add context
            if key == "cgpa_score" and score is not None:
                entry["note"] = "Meets requirement" if score >= 100 else "Below minimum CGPA"

            # Experience → add context
            if key == "experience_score" and score is not None:
                entry["note"] = "Meets requirement" if score >= 100 else "Below required experience"

            breakdown[label] = entry

        # Reconstruct final score from breakdown
        final_score = round(
            sum(
                (score_breakdown.get(k, 0) or 0) * (weights_used.get(k, 0) / 100)
                for k in criteria_used
                if k != "criteria_used"
            ),
            1,
        )

        prediction = predict_placement(final_score)

        # Human-readable summary sentence
        skill_sc = score_breakdown.get("skill_score", 0)
        summary = (
            f"Your skills match {round(skill_sc)}% of job requirements. "
            f"Overall match score is {final_score}/100 — placement prediction: {prediction}."
        )
        if missing_skills:
            summary += f" Key missing skills: {', '.join(missing_skills[:3])}."

        return {
            "final_score": final_score,
            "breakdown":   breakdown,
            "prediction":  prediction,
            "summary":     summary,
        }

    except Exception as e:
        return {"error": f"explain_match_score failed: {str(e)}"}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 5 — Company-wise Best Match Ranking
# ─────────────────────────────────────────────────────────────────────────────

def rank_companies(job_matches: List[dict]) -> dict:
    """
    Group job matches by company, keep only highest scoring job per company.
    Handles missing/null company names gracefully.

    Args:
        job_matches: List of job match dicts from Agent 4 output
                     (each has: company, role, match_score, placement_prediction)

    Returns:
        {
            "company_rankings": [
                {"company": "Zoho", "best_role": "Python Dev", "score": 87, "prediction": "Highly Likely"},
                ...
            ]
        }
    """
    try:
        best: dict = {}

        for match in job_matches:
            # Handle null/missing company names
            company = (match.get("company") or "").strip() or "Unknown Company"
            score   = match.get("match_score", 0) or 0

            if company not in best or score > best[company]["score"]:
                best[company] = {
                    "company":    company,
                    "best_role":  match.get("role", "Unknown Role"),
                    "score":      round(score, 1),
                    "prediction": match.get("placement_prediction", "Unknown"),
                }

        # Sort by score descending
        rankings = sorted(best.values(), key=lambda x: x["score"], reverse=True)

        return {"company_rankings": rankings}

    except Exception as e:
        return {"error": f"rank_companies failed: {str(e)}"}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 6 — Skill Trend Analyzer
# ─────────────────────────────────────────────────────────────────────────────

def analyze_skill_trends(job_matches: List[dict], candidate_skills: List[str]) -> dict:
    """
    Aggregate required skills across all matched jobs, count frequency,
    return top 10 trending skills + compare with candidate's skills.

    Args:
        job_matches:       List of job match dicts (each has score_breakdown with missing_skills,
                           or jobs list with required_skills)
        candidate_skills:  List of candidate skill name strings

    Returns:
        {
            "top_trending_skills": [{"skill": "Python", "demand_count": 8}, ...],
            "you_have":   ["Python", "SQL"],
            "you_missing": ["Docker", "Kubernetes"]
        }
    """
    try:
        all_skills: List[str] = []

        for match in job_matches:
            # Try to get required_skills directly from job data
            req = match.get("required_skills", [])
            if req:
                all_skills.extend([s.lower() for s in req])

            # Also count from missing_skills (these were in required but candidate lacks)
            missing = match.get("missing_skills", [])
            if missing:
                all_skills.extend([s.lower() for s in missing])

        if not all_skills:
            return {"error": "No skill data found in job_matches. Pass jobs with required_skills field."}

        # Count frequency
        counts = Counter(all_skills)
        top_10 = [
            {"skill": skill.title(), "demand_count": count}
            for skill, count in counts.most_common(10)
        ]

        # Compare with candidate
        cand_lower = {s.lower() for s in candidate_skills}
        top_skill_names = {entry["skill"].lower() for entry in top_10}

        you_have    = [s for s in candidate_skills if s.lower() in top_skill_names]
        you_missing = [entry["skill"] for entry in top_10 if entry["skill"].lower() not in cand_lower]

        return {
            "top_trending_skills": top_10,
            "you_have":            you_have,
            "you_missing":         you_missing,
        }

    except Exception as e:
        return {"error": f"analyze_skill_trends failed: {str(e)}"}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 7 — Adzuna Live Job Fetch with Intelligent Fallback
# ─────────────────────────────────────────────────────────────────────────────

# Static fallback jobs — used when Adzuna API is unavailable
_FALLBACK_JOBS = {
    "default": [
        {"title": "Software Engineer", "company": "Infosys", "location": "Bangalore, India",
         "description": "Build scalable backend systems using Python, Java, REST APIs, SQL, Docker, AWS.",
         "salary_min": 600000, "salary_max": 1200000, "url": "https://careers.infosys.com"},
        {"title": "Software Engineer", "company": "TCS", "location": "Chennai, India",
         "description": "Develop enterprise applications using Java, Spring Boot, SQL, OOP, Linux, Git.",
         "salary_min": 350000, "salary_max": 700000, "url": "https://ibegin.tcs.com"},
        {"title": "Associate Engineer", "company": "Wipro", "location": "Pune, India",
         "description": "Work on client projects using Python, Java, SQL, JavaScript, REST APIs, Git.",
         "salary_min": 350000, "salary_max": 650000, "url": "https://careers.wipro.com"},
        {"title": "Software Developer", "company": "Zoho", "location": "Chennai, India",
         "description": "Build Zoho products using Java, C++, Data Structures, Algorithms, SQL, JavaScript.",
         "salary_min": 500000, "salary_max": 900000, "url": "https://careers.zoho.com"},
        {"title": "Software Engineer", "company": "Freshworks", "location": "Chennai, India",
         "description": "Build SaaS products with React, Ruby on Rails, PostgreSQL, REST APIs, Docker.",
         "salary_min": 700000, "salary_max": 1400000, "url": "https://careers.freshworks.com"},
    ],
    "data scientist": [
        {"title": "Data Scientist", "company": "IBM India", "location": "Bangalore, India",
         "description": "Apply ML algorithms, Python, TensorFlow, Pandas, SQL, scikit-learn to business problems.",
         "salary_min": 800000, "salary_max": 1800000, "url": "https://careers.ibm.com"},
        {"title": "Data Analyst", "company": "Amazon India", "location": "Hyderabad, India",
         "description": "Analyze data using Python, SQL, Pandas, Excel, Power BI, Tableau, AWS.",
         "salary_min": 600000, "salary_max": 1400000, "url": "https://amazon.jobs/en/locations/hyderabad-ind"},
        {"title": "ML Engineer", "company": "Flipkart", "location": "Bangalore, India",
         "description": "Build ML pipelines using PyTorch, TensorFlow, Python, Kafka, Spark, Docker.",
         "salary_min": 1200000, "salary_max": 2500000, "url": "https://careers.flipkart.com"},
        {"title": "AI Engineer", "company": "Ola", "location": "Bangalore, India",
         "description": "Develop AI solutions with Python, NLP, Computer Vision, TensorFlow, AWS, Kubernetes.",
         "salary_min": 1000000, "salary_max": 2200000, "url": "https://careers.olacabs.com"},
        {"title": "Data Engineer", "company": "Swiggy", "location": "Bangalore, India",
         "description": "Build data infrastructure using Python, Spark, Kafka, Airflow, SQL, AWS.",
         "salary_min": 900000, "salary_max": 1800000, "url": "https://careers.swiggy.com"},
    ],
    "devops": [
        {"title": "DevOps Engineer", "company": "Razorpay", "location": "Bangalore, India",
         "description": "Manage cloud infrastructure using AWS, Kubernetes, Docker, Terraform, CI/CD, Linux.",
         "salary_min": 900000, "salary_max": 2000000, "url": "https://razorpay.com/jobs"},
        {"title": "Cloud Engineer", "company": "Deloitte India", "location": "Mumbai, India",
         "description": "Design cloud solutions on AWS, Azure, GCP with Terraform, Docker, Kubernetes, Jenkins.",
         "salary_min": 700000, "salary_max": 1600000, "url": "https://careers.deloitte.com"},
        {"title": "SRE Engineer", "company": "Google India", "location": "Hyderabad, India",
         "description": "Ensure reliability using Python, Go, Kubernetes, Prometheus, Linux, CI/CD, AWS.",
         "salary_min": 1500000, "salary_max": 3500000, "url": "https://careers.google.com"},
        {"title": "DevOps Engineer", "company": "Paytm", "location": "Noida, India",
         "description": "Build CI/CD pipelines using Jenkins, Docker, Kubernetes, AWS, Linux, Ansible, Git.",
         "salary_min": 800000, "salary_max": 1800000, "url": "https://careers.paytm.com"},
        {"title": "Infrastructure Engineer", "company": "CRED", "location": "Bangalore, India",
         "description": "Manage infra with Kubernetes, AWS, Terraform, Prometheus, Grafana, Linux, Python.",
         "salary_min": 1200000, "salary_max": 2500000, "url": "https://careers.cred.club"},
    ],
}


def _get_fallback_jobs(role: str) -> List[dict]:
    """Pick the best matching fallback job list based on role keyword."""
    role_lower = role.lower()
    for key in _FALLBACK_JOBS:
        if key != "default" and key in role_lower:
            return _FALLBACK_JOBS[key]
    return _FALLBACK_JOBS["default"]


def get_jobs(role: str, location: str = "India", db=None) -> dict:
    """
    Fetch live jobs from Adzuna API.
    Automatically falls back to static list if API fails.
    Embeds each job description and saves to MongoDB jobs collection.

    Layer 1 — Adzuna live API
    Layer 2 — Static fallback (5 realistic Indian jobs)

    Both layers return identical output format.

    Args:
        role:     Job role to search (e.g. "Python Developer")
        location: Location string (default: "India")
        db:       Motor/pymongo DB instance (optional — saves to MongoDB if provided)

    Returns:
        {
            "jobs": [
                {
                    "title": "...", "company": "...", "location": "...",
                    "description": "...", "salary_min": 0, "salary_max": 0,
                    "url": "...", "source": "live" | "fallback"
                },
                ...
            ],
            "source":    "live" | "fallback",
            "total":     20,
            "role":      "Python Developer",
            "location":  "India"
        }
    """
    source = "live"
    raw_jobs: List[dict] = []

    # ── Layer 1: Adzuna API ──────────────────────────────────────────────────
    try:
        app_id  = os.environ.get("ADZUNA_APP_ID", "")
        app_key = os.environ.get("ADZUNA_APP_KEY", "")

        if not app_id or not app_key:
            raise ValueError("ADZUNA_APP_ID or ADZUNA_APP_KEY not set in environment")

        resp = requests.get(
            "https://api.adzuna.com/v1/api/jobs/in/search/1",
            params={
                "app_id":           app_id,
                "app_key":          app_key,
                "what":             role,
                "where":            location,
                "results_per_page": 20,
                "content-type":     "application/json",
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])

        if not results:
            raise ValueError("Adzuna returned 0 results")

        for job in results:
            raw_jobs.append({
                "title":       job.get("title", ""),
                "company":     (job.get("company") or {}).get("display_name", "Unknown"),
                "location":    (job.get("location") or {}).get("display_name", location),
                "description": job.get("description", ""),
                "salary_min":  job.get("salary_min", 0) or 0,
                "salary_max":  job.get("salary_max", 0) or 0,
                "url":         job.get("redirect_url", ""),
                "source":      "live",
            })

    except Exception:
        # ── Layer 2: Static fallback ─────────────────────────────────────────
        source = "fallback"
        for job in _get_fallback_jobs(role):
            raw_jobs.append({**job, "source": "fallback"})

    # ── Embed + Save to MongoDB ──────────────────────────────────────────────
    final_jobs = []
    for job in raw_jobs:
        try:
            # Create embedding from title + description
            embed_text = f"{job['title']} {job['company']} {job['description'][:300]}"
            embedding  = _embedder.encode(embed_text).tolist()
            job["embedding"] = embedding
        except Exception:
            job["embedding"] = []

        final_jobs.append(job)

        # Save to MongoDB jobs collection
        if db is not None:
            try:
                db.jobs.update_one(
                    {"title": job["title"], "company": job["company"]},
                    {"$set": {
                        **job,
                        "is_active":  True,
                        "created_at": datetime.now(timezone.utc),
                    }},
                    upsert=True,
                )
            except Exception:
                pass  # Non-fatal — continue

    return {
        "jobs":     [
            {k: v for k, v in j.items() if k != "embedding"}  # don't return embedding in response
            for j in final_jobs
        ],
        "source":   source,
        "total":    len(final_jobs),
        "role":     role,
        "location": location,
    }
