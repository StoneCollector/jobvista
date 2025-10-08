import re
from typing import Dict, List, Optional

try:
    import textstat
except ImportError:
    textstat = None


# --- Text Processing Utilities ---

def normalize(s: str) -> str:
    """Lowercase, remove special chars, and normalize whitespace."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9+.#/\- ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# --- Skill Extraction & Inference ---

DEFAULT_SKILLS = {
    "python", "java", "c", "c++", "c#", ".net", "javascript", "typescript",
    "node", "node.js", "react", "angular", "vue", "django", "flask",
    "spring", "fastapi", "sql", "mysql", "postgres", "mongodb", "redis",
    "elasticsearch", "aws", "azure", "gcp", "docker", "kubernetes",
    "terraform", "linux", "pandas", "numpy", "scikit-learn", "sklearn",
    "tensorflow", "pytorch", "nlp", "llm", "machine learning",
    "deep learning", "data science", "etl", "airflow",
}

SKILL_SYNONYMS = {
    "js": "javascript", "ts": "typescript", "tf": "tensorflow",
    "scikit learn": "scikit-learn", "ml": "machine learning",
    "dl": "deep learning", "postgresql": "postgres",
}

SKILL_TRIGGERS = {
    "management": ["manage", "led a team", "spearheaded", "oversaw", "directed the"],
    "leadership": ["led", "lead", "mentored", "guided", "directed", "coached"],
    "communication": ["presented", "authored", "negotiated", "liaised", "wrote"],
    "problem-solving": ["optimized", "resolved", "troubleshoot", "debugged", "fixed"],
    "software development": ["developed", "engineered", "built", "coded", "programmed"],
    "data analysis": ["analyzed", "interpreted", "visualized data", "data model"],
    "design": ["designed", "prototyped", "wireframed", "ux", "ui"],
}


def canonicalize_skill(tok: str) -> str:
    """Map skill synonyms to a canonical form."""
    t = tok.strip().lower()
    return SKILL_SYNONYMS.get(t, t)


def extract_skills(
        text: str, custom_list: Optional[List[str]] = None
) -> List[str]:
    """Extract a sorted list of unique explicit skills from text."""
    normalized_text = normalize(text)
    toks = normalized_text.split()
    found_skills = set()

    for t in toks:
        c = canonicalize_skill(t)
        if c in DEFAULT_SKILLS:
            found_skills.add(c)

    bigrams = zip(toks, toks[1:])
    for a, b in bigrams:
        bigram = canonicalize_skill(f"{a} {b}")
        if bigram in DEFAULT_SKILLS:
            found_skills.add(bigram)

    if custom_list:
        for s in custom_list:
            s_norm = canonicalize_skill(s)
            if s_norm in normalized_text:
                found_skills.add(s_norm)

    return sorted(list(found_skills))


def infer_skills_from_text(resume_text: str) -> List[str]:
    """Infers skills from descriptive text using trigger phrases."""
    inferred_skills = set()
    text = resume_text.lower()
    for skill, triggers in SKILL_TRIGGERS.items():
        for trigger in triggers:
            if trigger in text:
                inferred_skills.add(skill)
                break
    return sorted(list(inferred_skills))


# --- Resume Quality Analysis ---

ACTION_VERBS = ["built", "developed", "designed", "led", "optimized", "implemented"]
GENERIC_PHRASES = ["responsible for", "worked on", "team player", "duties included"]
PASSIVE_HINT_PATTERN = re.compile(r"\b(?:was|were|is|are|been)\b\s+\w+ed\b", re.I)


def resume_quality(resume_text: str) -> Dict[str, object]:
    """
    Analyzes resume text for quality and provides actionable feedback
    with context for each issue.
    """
    suggestions = []

    for phrase in GENERIC_PHRASES:
        if phrase in resume_text.lower():
            suggestions.append({
                "message": "Avoid generic phrases. Use specific action verbs to describe your impact.",
                "context": phrase
            })

    for match in PASSIVE_HINT_PATTERN.finditer(resume_text):
        suggestions.append({
            "message": "Prefer active voice ('I built X') over passive voice ('X was built').",
            "context": match.group(0)
        })

    if not any(verb in resume_text.lower() for verb in ACTION_VERBS):
        suggestions.append({
            "message": "Start bullet points with strong action verbs like 'developed', 'optimized', or 'led'.",
            "context": None
        })

    readability = {}
    if textstat:
        try:
            readability['flesch_reading_ease'] = textstat.flesch_reading_ease(resume_text)
        except Exception:
            pass

    return {
        "readability": readability,
        "suggestions": suggestions,
    }


def check_ats_friendliness(text: str) -> Dict[str, object]:
    """
    Performs basic checks for ATS compatibility.
    """
    report = {
        "has_contact_info": False,
        "uses_standard_sections": False,
        "warnings": [],
    }

    # Check for email and phone
    if re.search(r"[\w.-]+@[\w.-]+", text) and re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text):
        report["has_contact_info"] = True

    # Check for standard section headers
    standard_sections = ["education", "experience", "skills", "projects"]
    found_sections = [s for s in standard_sections if s in text.lower()]
    if len(found_sections) >= 2:
        report["uses_standard_sections"] = True
    else:
        report["warnings"].append("Missing standard sections like 'Experience' or 'Skills'. Use simple text headers.")

    # Check for complex layouts (heuristic)
    if "\t" in text or "  " in text.replace("\n", ""):
        report["warnings"].append(
            "Resume may contain complex formatting (tables or columns) that can confuse ATS. Use a single-column layout.")

    return report
