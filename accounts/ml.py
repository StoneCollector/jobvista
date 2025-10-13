import re
from collections import Counter
from difflib import get_close_matches
from typing import List, Tuple, Dict

# Handle optional imports gracefully
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


CANONICAL_SKILLS = [
    # Programming
    'python','java','javascript','typescript','c++','c#','go','ruby','php','swift','kotlin',
    # Web / Backend
    'django','flask','fastapi','spring','spring boot','node','express','graphql','rest',
    # Frontend
    'react','next.js','vue','angular','svelte','html','css','tailwind','bootstrap',
    # Data / Cloud
    'sql','mysql','postgresql','mongodb','redis','elasticsearch','aws','gcp','azure',
    'kubernetes','docker','terraform','spark','hadoop','pandas','numpy','scikit-learn',
    # Mobile
    'android','ios','react native','flutter',
]


TOKEN_RE = re.compile(r"[a-zA-Z0-9+#.]+")


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t.lower() for t in TOKEN_RE.findall(text)]


def bag_of_words(tokens: List[str]) -> Counter:
    return Counter(tokens)


def cosine_similarity(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    # dot product
    common = set(a.keys()) & set(b.keys())
    dot = sum(a[t] * b[t] for t in common)
    # norms
    na = sum(v*v for v in a.values()) ** 0.5
    nb = sum(v*v for v in b.values()) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def extract_skills_from_text(text: str, threshold: float = 0.84) -> List[str]:
    """Match tokens to a canonical skills list using fuzzy matching."""
    tokens = set(tokenize(text))
    found = set()
    for skill in CANONICAL_SKILLS:
        base = skill.lower()
        if base in tokens:
            found.add(skill)
        else:
            # fuzzy match single-token skills only
            if ' ' not in base:
                match = get_close_matches(base, tokens, n=1, cutoff=threshold)
                if match:
                    found.add(skill)
    return sorted(found)


def compute_resume_keywords(skills_csv: str, extra_text: str = '') -> Tuple[List[str], Counter]:
    """Return (skills, vector) for a resume/profile."""
    skills = [s.strip() for s in (skills_csv or '').split(',') if s.strip()]
    if extra_text:
        inferred = extract_skills_from_text(extra_text)
        for s in inferred:
            if s not in skills:
                skills.append(s)
    tokens = tokenize(' '.join(skills) + ' ' + extra_text)
    return skills, bag_of_words(tokens)


def score_job_match(resume_vec: Counter, job_text: str) -> int:
    job_vec = bag_of_words(tokenize(job_text))
    sim = cosine_similarity(resume_vec, job_vec)
    # Map similarity to 0-100 with a gentle curve
    score = int(max(0, min(100, round(sim * 140))))
    return score


