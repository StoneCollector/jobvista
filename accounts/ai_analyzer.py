import re
from typing import Dict, List, Optional
from collections import Counter
import math

try:
    import textstat
except ImportError:
    textstat = None

# Import enhanced AI analyzer
try:
    from .ai_enhanced import ai_analyzer
    HAS_ENHANCED_AI = True
except ImportError:
    HAS_ENHANCED_AI = False
    ai_analyzer = None


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
    """Extract a sorted list of unique explicit skills from text using AI."""
    if HAS_ENHANCED_AI and ai_analyzer:
        try:
            # Use enhanced AI skill extraction
            ai_skills = ai_analyzer.extract_skills_from_text(text)
            if ai_skills:
                return ai_skills
        except Exception as e:
            print(f"AI skill extraction failed, using fallback: {e}")
    
    # Fallback to pattern-based extraction
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
    with context for each issue using AI.
    """
    if HAS_ENHANCED_AI and ai_analyzer:
        try:
            # Use enhanced AI analysis
            ai_analysis = ai_analyzer.analyze_resume_quality(resume_text)
            return {
                "score": ai_analysis.get('score', 0),
                "suggestions": ai_analysis.get('suggestions', []),
                "strengths": ai_analysis.get('strengths', []),
                "areas_for_improvement": ai_analysis.get('areas_for_improvement', []),
                "readability": {"score": ai_analysis.get('score', 0)}
            }
        except Exception as e:
            print(f"AI resume analysis failed, using fallback: {e}")
    
    # Fallback to pattern-based analysis
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
    Performs comprehensive checks for ATS compatibility.
    """
    report = {
        "has_contact_info": False,
        "uses_standard_sections": False,
        "warnings": [],
        "score": 0,
        "recommendations": []
    }

    # Check for email and phone
    email_match = re.search(r"[\w.-]+@[\w.-]+", text)
    phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    
    if email_match and phone_match:
        report["has_contact_info"] = True
        report["score"] += 20
    elif email_match or phone_match:
        report["warnings"].append("Include both email and phone number for better contact.")
        report["score"] += 10
    else:
        report["warnings"].append("Missing contact information. Add email and phone number.")

    # Check for standard section headers
    standard_sections = ["education", "experience", "skills", "projects", "summary", "objective"]
    found_sections = [s for s in standard_sections if s in text.lower()]
    if len(found_sections) >= 3:
        report["uses_standard_sections"] = True
        report["score"] += 25
    elif len(found_sections) >= 2:
        report["score"] += 15
        report["warnings"].append("Add more standard sections like 'Summary' or 'Projects'.")
    else:
        report["warnings"].append("Missing standard sections like 'Experience' or 'Skills'. Use simple text headers.")

    # Check for keywords density
    word_count = len(text.split())
    if word_count < 200:
        report["warnings"].append("Resume is too short. Aim for 200-400 words.")
    elif word_count > 600:
        report["warnings"].append("Resume is too long. Keep it concise (400-600 words).")
    else:
        report["score"] += 15

    # Check for action verbs
    action_verbs = ["achieved", "developed", "implemented", "managed", "created", "improved", "increased", "reduced"]
    verb_count = sum(1 for verb in action_verbs if verb in text.lower())
    if verb_count >= 3:
        report["score"] += 15
    else:
        report["recommendations"].append("Use more action verbs to describe your achievements.")

    # Check for quantifiable results
    if re.search(r'\d+%|\$\d+|\d+\+', text):
        report["score"] += 10
    else:
        report["recommendations"].append("Include quantifiable results and metrics in your experience.")

    # Check for complex layouts (heuristic)
    if "\t" in text or "  " in text.replace("\n", ""):
        report["warnings"].append(
            "Resume may contain complex formatting (tables or columns) that can confuse ATS. Use a single-column layout.")
        report["score"] -= 10

    # Check for file format compatibility
    if "pdf" in text.lower() or "doc" in text.lower():
        report["recommendations"].append("Save your resume as a PDF for better ATS compatibility.")

    # Calculate final score
    report["score"] = max(0, min(100, report["score"]))
    
    if report["score"] >= 80:
        report["recommendations"].append("Great! Your resume is ATS-friendly.")
    elif report["score"] >= 60:
        report["recommendations"].append("Good ATS compatibility. Consider the suggestions above.")
    else:
        report["recommendations"].append("Your resume needs improvement for ATS compatibility.")

    return report


def calculate_skill_match_score(user_skills: List[str], job_requirements: str) -> float:
    """
    Calculate a match score between user skills and job requirements.
    """
    if not user_skills or not job_requirements:
        return 0.0
    
    job_text = job_requirements.lower()
    matched_skills = []
    
    for skill in user_skills:
        skill_lower = skill.lower().strip()
        if skill_lower in job_text:
            matched_skills.append(skill)
    
    if not matched_skills:
        return 0.0
    
    # Calculate score based on matched skills ratio and total skills
    match_ratio = len(matched_skills) / len(user_skills)
    skill_density = len(matched_skills) / len(job_text.split()) * 100
    
    # Weighted score: 70% match ratio, 30% skill density
    score = (match_ratio * 0.7 + min(skill_density, 1.0) * 0.3) * 100
    
    return min(100.0, max(0.0, score))


def extract_key_phrases(text: str, max_phrases: int = 10) -> List[str]:
    """
    Extract key phrases from text using simple frequency analysis.
    """
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
    
    # Extract words and phrases
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    words = [w for w in words if w not in stop_words]
    
    # Count frequency
    word_counts = Counter(words)
    
    # Get most common phrases
    phrases = []
    for word, count in word_counts.most_common(max_phrases):
        if count > 1:  # Only include words that appear more than once
            phrases.append(word)
    
    return phrases
