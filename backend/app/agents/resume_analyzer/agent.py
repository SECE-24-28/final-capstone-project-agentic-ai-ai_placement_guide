"""
Agent 1: Resume Analyzer
Responsibilities: Parse PDF/DOCX → Extract structured data → ATS Score → Feedback
"""
import re
import json
import io
from pathlib import Path

import fitz  # PyMuPDF
import spacy
from groq import Groq
from docx import Document
from sentence_transformers import SentenceTransformer

from app.core.config import settings

_client = Groq(api_key=settings.GROQ_API_KEY)
_embedder = SentenceTransformer("all-MiniLM-L6-v2")

try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    _nlp = spacy.load("en_core_web_sm")


def _groq(prompt: str, max_tokens: int = 4096) -> str:
    for attempt in range(3):
        try:
            response = _client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON only."}, {"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content.strip()
            if content:
                return content
        except Exception as e:
            if attempt == 2:
                raise
    return "{}"


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    # Extract first JSON object if extra text exists
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


# ─── Text Extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    raise ValueError(f"Unsupported file format: {ext}")


# ─── Groq Extraction ─────────────────────────────────────────────────────────

_EXTRACTION_PROMPT = """You are an expert resume parser. Extract ALL information from the resume text below.
Return ONLY valid JSON, no markdown, no explanation.

Resume Text:
{resume_text}

Return this exact JSON structure:
{{
  "candidate_name": "full name or null",
  "email": "email or null",
  "phone": "phone number or null",
  "cgpa": numeric value or null,
  "graduation_year": integer year or null,
  "skills": [
    {{"name": "skill name", "category": "Programming/Framework/Tool/Soft Skill/Database/Cloud", "proficiency": "Beginner/Intermediate/Advanced or null"}}
  ],
  "education": [
    {{"degree": "B.Tech/B.E./M.Tech etc", "institution": "college name", "field_of_study": "CS/ECE etc", "start_year": int or null, "end_year": int or null, "cgpa": float or null}}
  ],
  "experience": [
    {{"company": "company name", "role": "job title", "start_date": "Month Year", "end_date": "Month Year or Present", "description": "brief summary", "duration_months": int or null}}
  ],
  "projects": [
    {{"name": "project name", "description": "what it does", "tech_stack": ["tech1","tech2"], "url": "github url or null"}}
  ],
  "certifications": [
    {{"name": "cert name", "issuer": "Google/AWS/Coursera etc", "year": int or null}}
  ]
}}"""

def parse_resume_with_groq(resume_text: str) -> dict:
    prompt = _EXTRACTION_PROMPT.format(resume_text=resume_text[:6000])
    return _parse_json(_groq(prompt))


# ─── ATS Scoring ─────────────────────────────────────────────────────────────

_ATS_PROMPT = """You are an ATS (Applicant Tracking System) expert. Analyze this resume and return ONLY valid JSON.

Resume Text:
{resume_text}

Score the resume from 0-100 based on:
1. Contact Information completeness (name, email, phone) - 10 points
2. Skills section (quantity, relevance, technical depth) - 25 points
3. Education section (degree, institution, CGPA) - 15 points
4. Work Experience / Internships - 20 points
5. Projects (quality, tech stack, impact) - 15 points
6. Certifications - 10 points
7. Formatting / Keywords / ATS Compatibility - 5 points

Return:
{{
  "resume_score": integer 0-100,
  "feedback": [
    {{"category": "Contact Info", "message": "specific feedback", "severity": "info|warning|error"}},
    {{"category": "Skills", "message": "specific feedback", "severity": "info|warning|error"}},
    {{"category": "Experience", "message": "specific feedback", "severity": "info|warning|error"}},
    {{"category": "Projects", "message": "specific feedback", "severity": "info|warning|error"}},
    {{"category": "Education", "message": "specific feedback", "severity": "info|warning|error"}},
    {{"category": "Certifications", "message": "specific feedback", "severity": "info|warning|error"}},
    {{"category": "Overall", "message": "overall improvement suggestion", "severity": "info"}}
  ]
}}"""

def calculate_ats_score(resume_text: str) -> dict:
    prompt = _ATS_PROMPT.format(resume_text=resume_text[:5000])
    return _parse_json(_groq(prompt))


# ─── Embedding ────────────────────────────────────────────────────────────────

def get_resume_embedding(text: str) -> list:
    return _embedder.encode(text[:512]).tolist()


# ─── Main Agent Entry Point ───────────────────────────────────────────────────

async def analyze_resume(file_bytes: bytes, filename: str) -> dict:
    raw_text = extract_text(file_bytes, filename)
    parsed = parse_resume_with_groq(raw_text)
    ats = calculate_ats_score(raw_text)
    embedding = get_resume_embedding(raw_text)

    return {
        "raw_text": raw_text,
        "candidate_name": parsed.get("candidate_name"),
        "email": parsed.get("email"),
        "phone": parsed.get("phone"),
        "cgpa": parsed.get("cgpa"),
        "graduation_year": parsed.get("graduation_year"),
        "skills": parsed.get("skills", []),
        "education": parsed.get("education", []),
        "experience": parsed.get("experience", []),
        "projects": parsed.get("projects", []),
        "certifications": parsed.get("certifications", []),
        "resume_score": ats.get("resume_score", 0),
        "feedback": ats.get("feedback", []),
        "embedding": embedding,
    }
