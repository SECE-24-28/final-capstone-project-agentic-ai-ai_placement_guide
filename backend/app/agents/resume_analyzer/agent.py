"""
Agent 1: Resume Analyzer
ATS Scoring — 7 measurable signals (NO LLM opinion scoring):

  1. Keyword Match Rate     (25 pts) — resume keywords vs common tech JD keywords
  2. Parseability Score     (15 pts) — clean text extraction check
  3. Section Detection      (15 pts) — standard sections found
  4. Quantified Achievements(20 pts) — numbers/metrics in experience bullets
  5. Action Verb Density    (10 pts) — strong verbs in experience
  6. Relevance Score        (10 pts) — cosine similarity resume vs target role
  7. Format Compliance      ( 5 pts) — ATS-friendly format checks

Output stays compatible with Agents 2, 3, 4.
Groq used ONLY for structured data extraction (not scoring).
"""
import re
import json
import io
import time
from pathlib import Path
from typing import List

import fitz
import spacy
import numpy as np
from groq import Groq
from docx import Document
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.core.embedder import embedder as _embedder

_client = Groq(api_key=settings.GROQ_API_KEY)

try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    _nlp = spacy.load("en_core_web_sm")

_last_call_time = 0.0
_MIN_INTERVAL   = 2.0


def _groq_throttled(prompt: str) -> str:
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_call_time = time.time()

    for attempt in range(3):
        try:
            response = _client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON only."},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "AuthenticationError" in type(e).__name__ or "invalid_api_key" in str(e):
                raise
            if "RateLimitError" in type(e).__name__:
                raise
            if attempt == 2:
                raise
    return "{}"


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*",     "", raw)
    raw = re.sub(r"\s*```$",     "", raw)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        raw = m.group(0)
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


# ─── Groq: Structured Extraction ONLY ────────────────────────────────────────

_EXTRACTION_PROMPT = """Extract ALL structured data from this resume. Return ONLY valid JSON. Do NOT skip any projects, experiences, or certifications — extract every single one.

Resume:
{resume_text}

Return this exact JSON structure (include ALL items found, not just one example):
{{"candidate_name":"full name or null","email":"email or null","phone":"phone or null","cgpa":null,"graduation_year":null,
"skills":[{{"name":"skill name","category":"Programming/Framework/Tool/Database/Cloud/Other","proficiency":"Beginner/Intermediate/Advanced"}}],
"education":[{{"degree":"degree","institution":"institution name","field_of_study":"field","start_year":null,"end_year":null,"cgpa":null}}],
"experience":[{{"company":"company name","role":"job title","start_date":"date","end_date":"date or Present","description":"full description of responsibilities and achievements","duration_months":null}}],
"projects":[{{"name":"project name","description":"full project description including what it does and your contribution","tech_stack":["tech1","tech2"],"url":null}}],
"certifications":[{{"name":"certification name","issuer":"issuing organization","year":null}}]}}"""


def extract_resume_data(resume_text: str) -> dict:
    prompt = _EXTRACTION_PROMPT.format(resume_text=resume_text[:6000])
    return _parse_json(_groq_throttled(prompt))


# ─── ATS Signal 1: Keyword Match Rate (25 pts) ───────────────────────────────
# Dynamic: extract keywords from job description / target role text

def _extract_keywords(text: str) -> set:
    """Extract meaningful tokens (nouns, proper nouns, technical terms) from text."""
    doc = _nlp(text.lower())
    tokens = set()
    for token in doc:
        if not token.is_stop and not token.is_punct and len(token.text) > 2:
            tokens.add(token.lemma_)
    # Also capture multi-word phrases like "machine learning", "data structures"
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip()
        if len(phrase) > 3:
            tokens.add(phrase)
    return tokens


def keyword_match_score(resume_text: str, jd_text: str = "") -> tuple[float, dict]:
    """Signal 1: Resume keywords vs job description keywords (25 pts)."""
    if not jd_text.strip():
        # Fallback: treat target_role string as minimal JD
        jd_text = jd_text or resume_text  # no-op: gives 100 — caller should pass role
    jd_keywords = _extract_keywords(jd_text)
    resume_keywords = _extract_keywords(resume_text)
    if not jd_keywords:
        return 100.0, {"matched_keywords": [], "matched_count": 0, "total_jd_keywords": 0}
    matched = jd_keywords & resume_keywords
    score = round(min((len(matched) / len(jd_keywords)) * 100, 100.0), 1)
    missing = sorted(jd_keywords - resume_keywords)[:15]
    return score, {
        "matched_keywords": sorted(matched)[:20],
        "missing_keywords": missing,
        "matched_count": len(matched),
        "total_jd_keywords": len(jd_keywords),
    }


# ─── ATS Signal 2: Parseability Score (15 pts) ───────────────────────────────

def parseability_score(raw_text: str, file_bytes: bytes, filename: str) -> tuple[float, dict]:
    """Signal 2: How cleanly the resume text was extracted (15 pts)."""
    issues = []
    score  = 100.0

    # Too short → likely parsing failure
    if len(raw_text.strip()) < 200:
        score -= 60
        issues.append("Very little text extracted — likely image-based or heavily formatted PDF")

    # High ratio of non-ASCII → encoding/table issues
    non_ascii = sum(1 for c in raw_text if ord(c) > 127)
    ratio = non_ascii / max(len(raw_text), 1)
    if ratio > 0.15:
        score -= 20
        issues.append("High non-ASCII character ratio — may have encoding issues")

    # Check for garbled text patterns
    garbled = len(re.findall(r"[^\w\s.,;:()\-@/+#&'\"]{3,}", raw_text))
    if garbled > 10:
        score -= 15
        issues.append("Possible garbled text from complex formatting")

    # Very long single line → no line breaks (columns/tables)
    lines = raw_text.split("\n")
    long_lines = sum(1 for l in lines if len(l) > 300)
    if long_lines > 3:
        score -= 10
        issues.append("Long unbroken lines detected — possible multi-column layout")

    score = max(0.0, round(score, 1))
    return score, {"parseability_issues": issues}


# ─── ATS Signal 3: Section Detection (15 pts) ────────────────────────────────

_SECTION_PATTERNS = {
    "Summary":        r"\b(summary|objective|profile|about me|career objective)\b",
    "Skills":         r"\b(skills|technical skills|core competencies|expertise|technologies)\b",
    "Experience":     r"\b(experience|work experience|employment|internship|professional experience)\b",
    "Education":      r"\b(education|academic|qualifications|degree|university|college)\b",
    "Projects":       r"\b(projects|personal projects|academic projects|portfolio)\b",
    "Certifications": r"\b(certifications?|certificates?|courses?|achievements?|awards?)\b",
}

def section_detection_score(resume_text: str) -> tuple[float, dict]:
    """Signal 3: Standard resume sections present (15 pts)."""
    text_lower = resume_text.lower()
    found, missing = [], []
    for section, pattern in _SECTION_PATTERNS.items():
        if re.search(pattern, text_lower):
            found.append(section)
        else:
            missing.append(section)

    score = round((len(found) / len(_SECTION_PATTERNS)) * 100, 1)
    return score, {"sections_found": found, "sections_missing": missing}


# ─── ATS Signal 4: Quantified Achievements (20 pts) ─────────────────────────

def quantified_achievements_score(resume_text: str) -> tuple[float, dict]:
    """Signal 4: Numbers/metrics in experience bullets (20 pts)."""
    # Find numbers, percentages, dollar amounts, multipliers
    metrics = re.findall(
        r"\b\d+[%x]?\b|\$\d+|\d+\+|\d+k\b|\d+\s*(hours?|days?|weeks?|months?|years?|users?|clients?|projects?|teams?)",
        resume_text, re.IGNORECASE
    )
    count = len(set(metrics))

    # Score: 0=0pts, 3=50pts, 6+=100pts
    if count == 0:
        score = 0.0
    elif count >= 6:
        score = 100.0
    else:
        score = round((count / 6) * 100, 1)

    return score, {
        "metrics_found": list(set(metrics))[:10],
        "metrics_count": count,
        "tip": "Add more numbers (%, $, counts) to quantify your achievements" if count < 4 else "Good use of metrics!",
    }


# ─── ATS Signal 5: Action Verb Density (10 pts) ──────────────────────────────

_ACTION_VERBS = {
    "led","built","developed","designed","implemented","created","managed","reduced",
    "increased","improved","optimized","deployed","launched","delivered","achieved",
    "automated","analyzed","collaborated","coordinated","engineered","established",
    "executed","generated","integrated","maintained","mentored","migrated","monitored",
    "produced","resolved","streamlined","architected","configured","debugged","tested",
}

def action_verb_score(resume_text: str) -> tuple[float, dict]:
    """Signal 5: Strong action verbs in experience section (10 pts)."""
    words = set(re.findall(r"\b[a-z]+\b", resume_text.lower()))
    matched_verbs = words & _ACTION_VERBS
    count = len(matched_verbs)

    # Score: 0=0, 4=50, 8+=100
    score = min(100.0, round((count / 8) * 100, 1))
    return score, {
        "action_verbs_found": sorted(matched_verbs),
        "verb_count": count,
        "tip": "Use stronger action verbs like: Led, Built, Reduced, Increased, Deployed" if count < 4 else "Good action verb usage!",
    }


# ─── ATS Signal 6: Relevance Score (10 pts) ──────────────────────────────────

_ROLE_DESCRIPTIONS = {
    "software engineer": "python java algorithms data structures system design sql git agile oop rest api microservices",
    "full stack developer": "react node javascript html css sql mongodb rest api git docker typescript",
    "data scientist": "python machine learning pandas numpy scikit-learn sql statistics deep learning tensorflow",
    "devops engineer": "docker kubernetes aws ci/cd linux terraform ansible jenkins git monitoring",
    "ml engineer": "python tensorflow pytorch machine learning deep learning nlp model deployment mlops",
    "frontend developer": "react javascript typescript html css tailwind git responsive design ux",
    "backend developer": "python java node rest api sql postgresql mongodb microservices docker",
    "android developer": "kotlin java android sdk jetpack compose retrofit sqlite",
    "data analyst": "sql python pandas excel power bi tableau statistics data visualization",
}

def relevance_score(resume_text: str, target_role: str) -> tuple[float, dict]:
    """Signal 6: Cosine similarity between resume and target role description (10 pts)."""
    role_lower = target_role.lower()

    # Find best matching role description
    role_desc = None
    for key, desc in _ROLE_DESCRIPTIONS.items():
        if key in role_lower or any(w in role_lower for w in key.split()):
            role_desc = desc
            break

    if not role_desc:
        role_desc = target_role  # fallback: use role name itself

    resume_emb = _embedder.encode([resume_text[:1000]])
    role_emb   = _embedder.encode([role_desc])
    similarity = float(cosine_similarity(resume_emb, role_emb)[0][0])
    score      = round(min(similarity * 150, 100.0), 1)  # scale up cosine (0.5~0.7 typical)

    return score, {"cosine_similarity": round(similarity, 3), "matched_role": role_lower}


# ─── ATS Signal 7: Format Compliance (5 pts) ─────────────────────────────────

def format_compliance_score(resume_text: str, filename: str) -> tuple[float, dict]:
    """Signal 7: ATS-friendly formatting check (5 pts)."""
    issues = []
    score  = 100.0

    # Check for common non-ATS-friendly patterns
    if re.search(r"(header|footer)", resume_text.lower()[:200]):
        score -= 20
        issues.append("Possible header/footer detected")

    # Check file format
    if filename.lower().endswith(".pdf"):
        pass  # PDF is fine
    elif filename.lower().endswith((".docx", ".doc")):
        pass  # DOCX is fine
    else:
        score -= 30
        issues.append("Non-standard file format")

    # Check for excessive special characters (tables, borders)
    special = len(re.findall(r"[|│┌┐└┘├┤┬┴┼─═]", resume_text))
    if special > 5:
        score -= 20
        issues.append("Table borders detected — ATS may misparse")

    # Check length (too short = incomplete, too long = poor formatting)
    words = len(resume_text.split())
    if words < 150:
        score -= 30
        issues.append("Resume too short (< 150 words)")
    elif words > 1500:
        score -= 10
        issues.append("Resume too long (> 1500 words) — consider trimming")

    score = max(0.0, round(score, 1))
    return score, {"format_issues": issues, "word_count": words if "words" in dir() else 0}


# ─── Composite ATS Score (weighted sum) ──────────────────────────────────────

def calculate_ats_score(
    resume_text: str,
    file_bytes: bytes,
    filename: str,
    target_role: str = "Software Engineer",
) -> dict:
    """
    Compute all 7 ATS signals and combine into final score.
    Returns score + per-signal breakdown + feedback list.
    """
    # Use target_role as the JD proxy for keyword extraction
    s1, d1 = keyword_match_score(resume_text, target_role)
    s2, d2 = parseability_score(resume_text, file_bytes, filename)
    s3, d3 = section_detection_score(resume_text)
    s4, d4 = quantified_achievements_score(resume_text)
    s5, d5 = action_verb_score(resume_text)
    s6, d6 = relevance_score(resume_text, target_role)
    s7, d7 = format_compliance_score(resume_text, filename)

    # Weighted sum → final ATS score
    resume_score = round(
        s1 * 0.25 +
        s2 * 0.15 +
        s3 * 0.15 +
        s4 * 0.20 +
        s5 * 0.10 +
        s6 * 0.10 +
        s7 * 0.05,
        1
    )

    # Build feedback from signals
    feedback = []

    # Signal 1
    if s1 >= 80:
        feedback.append({"category": "Keywords", "message": f"Strong keyword match — {d1['matched_count']} industry keywords found", "severity": "info"})
    elif s1 >= 50:
        feedback.append({"category": "Keywords", "message": f"{d1['matched_count']} keywords found. Add more: Docker, AWS, REST API, Git", "severity": "warning"})
    else:
        feedback.append({"category": "Keywords", "message": f"Only {d1['matched_count']} keywords detected. Add relevant technical skills", "severity": "error"})

    # Signal 2
    if d2["parseability_issues"]:
        for issue in d2["parseability_issues"]:
            feedback.append({"category": "Parseability", "message": issue, "severity": "warning"})
    else:
        feedback.append({"category": "Parseability", "message": "Resume text extracts cleanly — ATS-friendly", "severity": "info"})

    # Signal 3
    if d3["sections_missing"]:
        feedback.append({"category": "Sections", "message": f"Missing sections: {', '.join(d3['sections_missing'])}", "severity": "warning"})
    else:
        feedback.append({"category": "Sections", "message": "All standard sections detected", "severity": "info"})

    # Signal 4
    feedback.append({"category": "Achievements", "message": d4["tip"], "severity": "info" if d4["metrics_count"] >= 4 else "warning"})

    # Signal 5
    feedback.append({"category": "Action Verbs", "message": d5["tip"], "severity": "info" if d5["verb_count"] >= 4 else "warning"})

    # Signal 6
    rel = d6["cosine_similarity"]
    if rel >= 0.6:
        feedback.append({"category": "Relevance", "message": f"High relevance to {target_role} role ({rel:.0%} match)", "severity": "info"})
    elif rel >= 0.4:
        feedback.append({"category": "Relevance", "message": f"Moderate relevance to {target_role} — add more role-specific keywords", "severity": "warning"})
    else:
        feedback.append({"category": "Relevance", "message": f"Low relevance to {target_role} — tailor your resume for this role", "severity": "error"})

    # Signal 7
    if d7["format_issues"]:
        for issue in d7["format_issues"]:
            feedback.append({"category": "Format", "message": issue, "severity": "warning"})
    else:
        feedback.append({"category": "Format", "message": "ATS-friendly format detected", "severity": "info"})

    readiness = round(
        s1 * 0.35 +
        s2 * 0.20 +
        s4 * 0.20 +
        s3 * 0.15 +
        s7 * 0.10,
        1
    )

    return {
        "resume_score": resume_score,
        "readiness_score": readiness,
        "feedback": feedback,
        "ats_breakdown": {
            "keyword_match":    {"score": s1, "weight": "25%", **d1},
            "parseability":     {"score": s2, "weight": "15%", **d2},
            "section_detection":{"score": s3, "weight": "15%", **d3},
            "quantified_achievements": {"score": s4, "weight": "20%", **d4},
            "action_verbs":     {"score": s5, "weight": "10%", **d5},
            "relevance":        {"score": s6, "weight": "10%", **d6},
            "format_compliance":{"score": s7, "weight": "5%",  **d7},
        },
    }


# ─── Embedding ────────────────────────────────────────────────────────────────

def get_resume_embedding(text: str) -> list:
    return _embedder.encode(text[:512]).tolist()


# ─── Main Agent Entry Point ───────────────────────────────────────────────────

async def analyze_resume(file_bytes: bytes, filename: str, target_role: str = "Software Engineer") -> dict:
    raw_text  = extract_text(file_bytes, filename)
    parsed    = extract_resume_data(raw_text)          # Groq: structured extraction only
    ats       = calculate_ats_score(raw_text, file_bytes, filename, target_role)  # Python: measurable signals
    embedding = get_resume_embedding(raw_text)

    return {
        "raw_text":        raw_text,
        "candidate_name":  parsed.get("candidate_name"),
        "email":           parsed.get("email"),
        "phone":           parsed.get("phone"),
        "cgpa":            parsed.get("cgpa"),
        "graduation_year": parsed.get("graduation_year"),
        "skills":          parsed.get("skills", []),
        "education":       parsed.get("education", []),
        "experience":      parsed.get("experience", []),
        "projects":        parsed.get("projects", []),
        "certifications":  parsed.get("certifications", []),
        "resume_score":    ats["resume_score"],
        "readiness_score": ats["readiness_score"],
        "feedback":        ats["feedback"],
        "ats_breakdown":   ats["ats_breakdown"],
        "embedding":       embedding,
    }
