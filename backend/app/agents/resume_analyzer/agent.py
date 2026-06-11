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
from app.core.config import settings
from app.core.embedder import embedder as _embedder

_client = Groq(api_key=settings.GROQ_API_KEY)

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
            if "AuthenticationError" in type(e).__name__ or "invalid_api_key" in str(e):
                raise
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


# ─── Combined Extraction + ATS in ONE Groq call (saves ~3000 tokens) ─────────

_COMBINED_PROMPT = """Parse this resume and score it. Return ONLY valid JSON.

Resume:
{resume_text}

Return:
{{"candidate_name":"name or null","email":"email or null","phone":"phone or null","cgpa":null,"graduation_year":null,
"skills":[{{"name":"skill","category":"Programming/Framework/Tool/Database/Cloud","proficiency":"Beginner/Intermediate/Advanced"}}],
"education":[{{"degree":"degree","institution":"college","field_of_study":"field","start_year":null,"end_year":null,"cgpa":null}}],
"experience":[{{"company":"company","role":"role","start_date":"date","end_date":"date","description":"summary","duration_months":null}}],
"projects":[{{"name":"name","description":"desc","tech_stack":["tech"],"url":null}}],
"certifications":[{{"name":"name","issuer":"issuer","year":null}}],
"resume_score":0,
"feedback":[{{"category":"Contact Info","message":"feedback","severity":"info"}},{{"category":"Skills","message":"feedback","severity":"info"}},{{"category":"Experience","message":"feedback","severity":"warning"}},{{"category":"Projects","message":"feedback","severity":"info"}},{{"category":"Overall","message":"suggestion","severity":"info"}}]}}

resume_score 0-100: contact(10)+skills(25)+education(15)+experience(20)+projects(15)+certs(10)+format(5)"""


def parse_and_score_resume(resume_text: str) -> dict:
    """Single Groq call for both extraction + ATS scoring — saves ~3000 tokens."""
    prompt = _COMBINED_PROMPT.format(resume_text=resume_text[:3000])
    return _parse_json(_groq(prompt, max_tokens=2048))


# ─── Embedding ────────────────────────────────────────────────────────────────

def get_resume_embedding(text: str) -> list:
    return _embedder.encode(text[:512]).tolist()


# ─── Main Agent Entry Point ───────────────────────────────────────────────────

async def analyze_resume(file_bytes: bytes, filename: str) -> dict:
    raw_text = extract_text(file_bytes, filename)
    result   = parse_and_score_resume(raw_text)   # 1 call instead of 2
    embedding = get_resume_embedding(raw_text)

    return {
        "raw_text":        raw_text,
        "candidate_name":  result.get("candidate_name"),
        "email":           result.get("email"),
        "phone":           result.get("phone"),
        "cgpa":            result.get("cgpa"),
        "graduation_year": result.get("graduation_year"),
        "skills":          result.get("skills", []),
        "education":       result.get("education", []),
        "experience":      result.get("experience", []),
        "projects":        result.get("projects", []),
        "certifications":  result.get("certifications", []),
        "resume_score":    result.get("resume_score", 0),
        "feedback":        result.get("feedback", []),
        "embedding":       embedding,
    }
