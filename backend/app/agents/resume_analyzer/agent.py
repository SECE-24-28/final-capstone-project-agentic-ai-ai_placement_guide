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


_SMART_FEEDBACK_PROMPT = """You are a brutally honest resume coach. You have already analyzed this resume with an ATS scanner. Now give SPECIFIC feedback based on the ACTUAL content below.

CANDIDATE NAME: {candidate_name}
TARGET ROLE: {target_role}
ATS SCORE: {ats_score}/100

ACTUAL RESUME TEXT:
{resume_text}

ATS SCAN RESULTS:
- Keywords matched: {matched_keywords}
- Keywords MISSING from resume: {missing_keywords}
- Sections detected: {sections_found}
- Sections MISSING: {sections_missing}
- Metrics/numbers found: {metrics_found}
- Action verbs found: {action_verbs}
- Cosine relevance to {target_role}: {relevance}

PROJECTS IN RESUME: {projects}
EXPERIENCE IN RESUME: {experience}

Based on the ABOVE specific data, return ONLY valid JSON:
{{
  "strengths": [
    {{"section": "exact section name", "item": "exact project/experience name from resume", "reason": "specific reason why this is strong"}}
  ],
  "improvements": [
    {{"section": "exact section", "item": "exact bullet or project name", "issue": "specific problem", "fix": "rewrite example or exact change to make", "priority": "high/medium/low"}}
  ],
  "missing": [
    {{"what": "specific missing skill or section", "why": "why it matters for {target_role}", "example": "exact line to add to resume"}}
  ],
  "overall_verdict": "2-3 sentence honest verdict mentioning candidate name and specific strengths/gaps"
}}

RULES: Mention actual project names. Quote actual bullets. Give rewrite examples. No generic advice like 'add more skills'."""


def generate_smart_feedback(resume_text: str, target_role: str, parsed: dict, ats_breakdown: dict) -> dict:
    kw = ats_breakdown.get("keyword_match", {})
    sec = ats_breakdown.get("section_detection", {})
    ach = ats_breakdown.get("quantified_achievements", {})
    av = ats_breakdown.get("action_verbs", {})
    rel = ats_breakdown.get("relevance", {})

    projects_text = ", ".join(p.get("name", "") for p in parsed.get("projects", []))
    exp_text = ", ".join(f"{e.get('role','')} at {e.get('company','')}" for e in parsed.get("experience", []))

    prompt = _SMART_FEEDBACK_PROMPT.format(
        candidate_name=parsed.get("candidate_name", "Candidate"),
        target_role=target_role,
        ats_score=ats_breakdown.get("keyword_match", {}).get("score", "N/A"),
        resume_text=resume_text[:4000],
        matched_keywords=", ".join(kw.get("matched_keywords", [])[:15]),
        missing_keywords=", ".join(kw.get("missing_keywords", [])[:15]),
        sections_found=", ".join(sec.get("sections_found", [])),
        sections_missing=", ".join(sec.get("sections_missing", [])),
        metrics_found=", ".join(str(m) for m in ach.get("metrics_found", [])[:10]),
        action_verbs=", ".join(av.get("action_verbs_found", [])[:10]),
        relevance=rel.get("cosine_similarity", "N/A"),
        projects=projects_text or "None found",
        experience=exp_text or "None found",
    )
    try:
        return _parse_json(_groq_throttled(prompt))
    except Exception:
        return {"strengths": [], "improvements": [], "missing": [], "overall_verdict": ""}


# ─── Role Descriptions — defined ONCE, used by Signal 1 + Signal 6 ───────────

_ROLE_DESCRIPTIONS = {
    "software engineer":    "python java javascript c++ algorithms data structures system design sql git agile oop rest api microservices linux debugging testing object oriented programming react node html css mongodb",
    "full stack developer":  "react node javascript html css sql mongodb rest api git docker typescript express frontend backend json ajax",
    "data scientist":        "python machine learning pandas numpy scikit-learn sql statistics deep learning tensorflow keras data analysis visualization jupyter notebook",
    "devops engineer":       "docker kubernetes aws ci/cd linux terraform ansible jenkins git monitoring prometheus grafana bash shell scripting pipeline",
    "ml engineer":           "python tensorflow pytorch machine learning deep learning nlp model deployment mlops feature engineering neural network transformer",
    "frontend developer":    "react javascript typescript html css tailwind git responsive design ux figma component ui redux hooks",
    "backend developer":     "python java node rest api sql postgresql mongodb microservices docker redis caching authentication jwt api design",
    "android developer":     "kotlin java android sdk jetpack compose retrofit sqlite room mvvm coroutines gradle play store mobile app development",
    "ios developer":         "swift objective-c xcode uikit swiftui cocoapods mvvm core data app store mobile apple development",
    "mobile developer":      "kotlin swift java android ios react native flutter mobile app ui ux retrofit sqlite jetpack compose xcode cross platform",
    "data analyst":          "sql python pandas excel power bi tableau statistics data visualization reporting dashboard pivot charts",
    "cloud engineer":        "aws azure gcp terraform docker kubernetes iam s3 ec2 lambda serverless devops cloud infrastructure",
    "cybersecurity":         "network security penetration testing encryption firewall linux python vulnerability assessment ethical hacking siem",
    "embedded systems":      "c c++ microcontroller arduino raspberry pi rtos embedded linux uart spi i2c firmware hardware",
    "ai engineer":           "python machine learning deep learning nlp computer vision tensorflow pytorch openai llm transformers generative ai",
}


def _get_role_desc(role: str) -> str:
    """Find best matching role description for a given role string."""
    role_lower = role.lower().strip()
    role_words = set(role_lower.split())

    best_key  = ""
    best_overlap = 0
    for key in _ROLE_DESCRIPTIONS:
        key_words = set(key.split())
        overlap = len(key_words & role_words)
        # Also check substring match
        if key in role_lower:
            overlap += 2
        if overlap > best_overlap:
            best_overlap = overlap
            best_key = key

    if best_key:
        return _ROLE_DESCRIPTIONS[best_key], best_key

    # Fallback: generic tech keywords
    return f"{role} programming software development algorithms data structures git api", role_lower


# ─── ATS Signal 1: Keyword Match Rate (25 pts) ───────────────────────────────

def _extract_keywords(text: str) -> set:
    """Extract meaningful tokens from text using spaCy."""
    doc = _nlp(text.lower())
    tokens = set()
    for token in doc:
        if not token.is_stop and not token.is_punct and len(token.text) > 2:
            tokens.add(token.lemma_)
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip()
        if len(phrase) > 3:
            tokens.add(phrase)
    return tokens


def keyword_match_score(resume_text: str, jd_text: str = "") -> tuple:
    """Signal 1: Resume keywords vs job description keywords (25 pts)."""
    # Expand short role name into full description
    if len(jd_text.split()) <= 4:
        desc, _ = _get_role_desc(jd_text)
        jd_text = f"{jd_text} {desc}"

    jd_keywords     = _extract_keywords(jd_text)
    resume_keywords = _extract_keywords(resume_text)

    if not jd_keywords:
        return 100.0, {"matched_keywords": [], "matched_count": 0, "total_jd_keywords": 0}

    matched = jd_keywords & resume_keywords
    score   = round(min((len(matched) / len(jd_keywords)) * 100, 100.0), 1)
    # Filter missing to single clean words only (no long phrases)
    missing = sorted(w for w in (jd_keywords - resume_keywords) if len(w.split()) == 1 and len(w) > 2)[:12]

    return score, {
        "matched_keywords":  sorted(matched)[:20],
        "missing_keywords":  missing,
        "matched_count":     len(matched),
        "total_jd_keywords": len(jd_keywords),
    }


# ─── ATS Signal 2: Parseability Score (15 pts) ───────────────────────────────

def parseability_score(raw_text: str, file_bytes: bytes, filename: str) -> tuple:
    """Signal 2: How cleanly the resume text was extracted (15 pts)."""
    issues = []
    score  = 100.0

    if len(raw_text.strip()) < 200:
        score -= 60
        issues.append("Very little text extracted — likely image-based or heavily formatted PDF")

    non_ascii = sum(1 for c in raw_text if ord(c) > 127)
    ratio = non_ascii / max(len(raw_text), 1)
    if ratio > 0.15:
        score -= 20
        issues.append("High non-ASCII character ratio — may have encoding issues")

    garbled = len(re.findall(r"[^\w\s.,;:()\-@/+#&'\"]{3,}", raw_text))
    if garbled > 10:
        score -= 15
        issues.append("Possible garbled text from complex formatting")

    lines      = raw_text.split("\n")
    long_lines = sum(1 for l in lines if len(l) > 300)
    if long_lines > 3:
        score -= 10
        issues.append("Long unbroken lines detected — possible multi-column layout")

    return max(0.0, round(score, 1)), {"parseability_issues": issues}


# ─── ATS Signal 3: Section Detection (15 pts) ────────────────────────────────

_SECTION_PATTERNS = {
    "Summary":        r"(summary|objective|profile|about me|career objective)",
    "Skills":         r"(skills|technical skills|core competencies|expertise|technologies|skills acquired)",
    "Experience":     r"(experience|work experience|employment|internship|professional experience|internship experience)",
    "Education":      r"(education|academic|qualifications|degree|university|college)",
    "Projects":       r"(projects|personal projects|academic projects|portfolio)",
    "Certifications": r"(certifications?|certificates?|courses?|achievements?|awards?|coding profiles?)",
}

def section_detection_score(resume_text: str) -> tuple:
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

def quantified_achievements_score(resume_text: str) -> tuple:
    """Signal 4: Numbers/metrics in experience bullets (20 pts)."""
    metrics = re.findall(
        r"\b\d+[%x]?\b|\$\d+|\d+\+|\d+k\b|\d+\s*(hours?|days?|weeks?|months?|years?|users?|clients?|projects?|teams?|problems?|ranks?)",
        resume_text, re.IGNORECASE
    )
    count = len(set(metrics))

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
    "contributed","gained","selected","applied","utilized","built","conducted",
    "presented","participated","secured","awarded",
}

def action_verb_score(resume_text: str) -> tuple:
    """Signal 5: Strong action verbs in experience section (10 pts)."""
    words         = set(re.findall(r"\b[a-z]+\b", resume_text.lower()))
    matched_verbs = words & _ACTION_VERBS
    count         = len(matched_verbs)
    score         = min(100.0, round((count / 8) * 100, 1))

    return score, {
        "action_verbs_found": sorted(matched_verbs),
        "verb_count": count,
        "tip": "Use stronger action verbs like: Led, Built, Reduced, Increased, Deployed" if count < 4 else "Good action verb usage!",
    }


# ─── ATS Signal 6: Relevance Score (10 pts) ──────────────────────────────────

def relevance_score(resume_text: str, target_role: str) -> tuple:
    """Signal 6: Cosine similarity between resume and target role description (10 pts)."""
    role_desc, matched_key = _get_role_desc(target_role)

    # Use a broader slice covering skills + projects section
    resume_emb = _embedder.encode([resume_text[:3000]])
    role_emb   = _embedder.encode([role_desc])
    similarity = float(cosine_similarity(resume_emb, role_emb)[0][0])
    score      = round(min(similarity * 160, 100.0), 1)

    return score, {"cosine_similarity": round(similarity, 3), "matched_role": matched_key}


# ─── ATS Signal 7: Format Compliance (5 pts) ─────────────────────────────────

def format_compliance_score(resume_text: str, filename: str) -> tuple:
    """Signal 7: ATS-friendly formatting check (5 pts)."""
    issues = []
    score  = 100.0

    if re.search(r"(header|footer)", resume_text.lower()[:200]):
        score -= 20
        issues.append("Possible header/footer detected")

    if not filename.lower().endswith((".pdf", ".docx", ".doc")):
        score -= 30
        issues.append("Non-standard file format")

    # Only flag actual box-drawing chars, not pipe | used in resume text
    special = len(re.findall(r"[│┌┐└┘├┤┬┴┼─═]", resume_text))
    if special > 5:
        score -= 20
        issues.append("Table borders detected — ATS may misparse")

    words = len(resume_text.split())
    if words < 150:
        score -= 30
        issues.append("Resume too short (< 150 words)")
    elif words > 1500:
        score -= 10
        issues.append("Resume too long (> 1500 words) — consider trimming")

    return max(0.0, round(score, 1)), {"format_issues": issues, "word_count": words}


# ─── Composite ATS Score ──────────────────────────────────────────────────────

def calculate_ats_score(
    resume_text: str,
    file_bytes: bytes,
    filename: str,
    target_role: str = "Software Engineer",
) -> dict:
    s1, d1 = keyword_match_score(resume_text, target_role)
    s2, d2 = parseability_score(resume_text, file_bytes, filename)
    s3, d3 = section_detection_score(resume_text)
    s4, d4 = quantified_achievements_score(resume_text)
    s5, d5 = action_verb_score(resume_text)
    s6, d6 = relevance_score(resume_text, target_role)
    s7, d7 = format_compliance_score(resume_text, filename)

    resume_score = round(
        s1 * 0.25 + s2 * 0.15 + s3 * 0.15 +
        s4 * 0.20 + s5 * 0.10 + s6 * 0.10 + s7 * 0.05,
        1
    )

    feedback = []

    if s1 >= 80:
        feedback.append({"category": "Keywords", "message": f"Strong keyword match — {d1['matched_count']} industry keywords found", "severity": "info"})
    elif s1 >= 50:
        feedback.append({"category": "Keywords", "message": f"{d1['matched_count']} keywords found. Consider adding: {', '.join(list(d1.get('missing_keywords', []))[:4])}", "severity": "warning"})
    else:
        feedback.append({"category": "Keywords", "message": f"Only {d1['matched_count']} keywords detected. Add relevant technical skills", "severity": "error"})

    if d2["parseability_issues"]:
        for issue in d2["parseability_issues"]:
            feedback.append({"category": "Parseability", "message": issue, "severity": "warning"})
    else:
        feedback.append({"category": "Parseability", "message": "Resume text extracts cleanly — ATS-friendly", "severity": "info"})

    if d3["sections_missing"]:
        feedback.append({"category": "Sections", "message": f"Missing sections: {', '.join(d3['sections_missing'])}", "severity": "warning"})
    else:
        feedback.append({"category": "Sections", "message": "All standard sections detected", "severity": "info"})

    feedback.append({"category": "Achievements", "message": d4["tip"], "severity": "info" if d4["metrics_count"] >= 4 else "warning"})
    feedback.append({"category": "Action Verbs",  "message": d5["tip"], "severity": "info" if d5["verb_count"]    >= 4 else "warning"})

    rel = d6["cosine_similarity"]
    if rel >= 0.55:
        feedback.append({"category": "Relevance", "message": f"Good relevance to {target_role} ({rel:.0%} match)", "severity": "info"})
    elif rel >= 0.35:
        feedback.append({"category": "Relevance", "message": f"Moderate relevance to {target_role} — add more role-specific keywords", "severity": "warning"})
    else:
        feedback.append({"category": "Relevance", "message": f"Low relevance to {target_role} — tailor your resume for this role", "severity": "error"})

    if d7["format_issues"]:
        for issue in d7["format_issues"]:
            feedback.append({"category": "Format", "message": issue, "severity": "warning"})
    else:
        feedback.append({"category": "Format", "message": "ATS-friendly format detected", "severity": "info"})

    readiness = round(
        s1 * 0.35 + s2 * 0.20 + s4 * 0.20 + s3 * 0.15 + s7 * 0.10, 1
    )

    return {
        "resume_score":    resume_score,
        "readiness_score": readiness,
        "feedback":        feedback,
        "ats_breakdown": {
            "keyword_match":             {"score": s1, "weight": "25%", **d1},
            "parseability":              {"score": s2, "weight": "15%", **d2},
            "section_detection":         {"score": s3, "weight": "15%", **d3},
            "quantified_achievements":   {"score": s4, "weight": "20%", **d4},
            "action_verbs":              {"score": s5, "weight": "10%", **d5},
            "relevance":                 {"score": s6, "weight": "10%", **d6},
            "format_compliance":         {"score": s7, "weight": "5%",  **d7},
        },
    }


# ─── Embedding ────────────────────────────────────────────────────────────────

def get_resume_embedding(text: str) -> list:
    return _embedder.encode(text[:512]).tolist()


# ─── Main Agent Entry Point ───────────────────────────────────────────────────

async def analyze_resume(file_bytes: bytes, filename: str, target_role: str = "Software Engineer") -> dict:
    raw_text  = extract_text(file_bytes, filename)
    parsed    = extract_resume_data(raw_text)
    ats       = calculate_ats_score(raw_text, file_bytes, filename, target_role)
    smart_fb  = generate_smart_feedback(raw_text, target_role, parsed, ats["ats_breakdown"])
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
        "smart_feedback":  smart_fb,
        "embedding":       embedding,
    }
