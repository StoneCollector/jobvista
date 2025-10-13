"""
Enhanced AI Analysis System using Hugging Face Transformers
Provides comprehensive resume analysis, skill extraction, and career recommendations
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, date
import numpy as np

# Handle optional AI imports gracefully
try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("Warning: Transformers not available. Install with: pip install transformers torch")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: Scikit-learn not available. Install with: pip install scikit-learn")

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """Enhanced AI analyzer using Hugging Face transformers"""
    
    def __init__(self):
        self.skill_extractor = None
        self.sentiment_analyzer = None
        self.text_classifier = None
        self.vectorizer = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize AI models"""
        if not HAS_TRANSFORMERS:
            logger.warning("Transformers not available, using fallback methods")
            return
        
        try:
            # Skill extraction using NER
            self.skill_extractor = pipeline(
                "ner",
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                aggregation_strategy="simple"
            )
            
            # Sentiment analysis for career advice
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
            
            # Text classification for job categories
            self.text_classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium"
            )
            
            logger.info("AI models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
            self.skill_extractor = None
            self.sentiment_analyzer = None
            self.text_classifier = None
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from resume text using AI"""
        if not text or not text.strip():
            return []
        
        skills = []
        
        # Use AI model if available
        if self.skill_extractor and HAS_TRANSFORMERS:
            try:
                # Extract entities from text
                entities = self.skill_extractor(text[:512])  # Limit text length
                
                # Filter for skill-related entities
                skill_keywords = [
                    'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node',
                    'django', 'flask', 'spring', 'express', 'mongodb', 'mysql', 'postgresql',
                    'aws', 'azure', 'docker', 'kubernetes', 'git', 'jenkins', 'ci/cd',
                    'machine learning', 'ai', 'data science', 'analytics', 'sql', 'nosql',
                    'html', 'css', 'bootstrap', 'tailwind', 'sass', 'less', 'webpack',
                    'agile', 'scrum', 'kanban', 'project management', 'leadership',
                    'communication', 'teamwork', 'problem solving', 'analytical thinking'
                ]
                
                for entity in entities:
                    if entity['score'] > 0.7:  # High confidence
                        entity_text = entity['word'].lower()
                        if any(keyword in entity_text for keyword in skill_keywords):
                            skills.append(entity['word'])
                            
            except Exception as e:
                logger.error(f"Error in AI skill extraction: {e}")
        
        # Fallback: Pattern-based skill extraction
        skills.extend(self._extract_skills_patterns(text))
        
        # Remove duplicates and clean
        skills = list(set([skill.strip().title() for skill in skills if skill.strip()]))
        
        return skills[:20]  # Limit to top 20 skills
    
    def _extract_skills_patterns(self, text: str) -> List[str]:
        """Fallback pattern-based skill extraction"""
        skills = []
        
        # Common technical skills patterns
        skill_patterns = [
            r'\b(?:Python|Java|JavaScript|Java|C\+\+|C#|PHP|Ruby|Go|Swift|Kotlin)\b',
            r'\b(?:React|Angular|Vue|Node\.?js|Express|Django|Flask|Spring|Laravel)\b',
            r'\b(?:HTML|CSS|JavaScript|TypeScript|Bootstrap|Tailwind|Sass|Less)\b',
            r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|SQLite|Oracle|SQL Server)\b',
            r'\b(?:AWS|Azure|Google Cloud|Docker|Kubernetes|Jenkins|Git|GitHub)\b',
            r'\b(?:Machine Learning|AI|Data Science|Analytics|Statistics|R|Pandas|NumPy)\b',
            r'\b(?:Agile|Scrum|Kanban|Project Management|Leadership|Communication)\b'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.extend(matches)
        
        return skills
    
    def analyze_resume_quality(self, text: str) -> Dict:
        """Analyze resume quality and provide suggestions"""
        analysis = {
            'score': 0,
            'suggestions': [],
            'strengths': [],
            'areas_for_improvement': []
        }
        
        if not text:
            analysis['suggestions'].append("Resume is empty. Please add content.")
            return analysis
        
        # Calculate quality score
        score = 0
        max_score = 100
        
        # Length check (10-20% of score)
        word_count = len(text.split())
        if 200 <= word_count <= 800:
            score += 15
            analysis['strengths'].append("Good resume length")
        elif word_count < 200:
            score += 5
            analysis['areas_for_improvement'].append("Resume is too short. Add more details about your experience.")
        else:
            score += 10
            analysis['areas_for_improvement'].append("Resume might be too long. Consider condensing.")
        
        # Contact information check (10% of score)
        contact_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
            r'\b(?:linkedin\.com|github\.com)\b'  # Social profiles
        ]
        
        contact_score = sum(1 for pattern in contact_patterns if re.search(pattern, text, re.IGNORECASE))
        score += contact_score * 3
        if contact_score == 3:
            analysis['strengths'].append("Complete contact information")
        else:
            analysis['areas_for_improvement'].append("Add missing contact information")
        
        # Skills section check (20% of score)
        skills_section = re.search(r'(?:skills|technical skills|core competencies)', text, re.IGNORECASE)
        if skills_section:
            score += 20
            analysis['strengths'].append("Skills section present")
        else:
            analysis['areas_for_improvement'].append("Add a dedicated skills section")
        
        # Experience section check (25% of score)
        experience_keywords = ['experience', 'worked', 'developed', 'managed', 'led', 'created', 'implemented']
        experience_count = sum(1 for keyword in experience_keywords if keyword.lower() in text.lower())
        if experience_count >= 3:
            score += 25
            analysis['strengths'].append("Strong experience descriptions")
        elif experience_count >= 1:
            score += 15
            analysis['areas_for_improvement'].append("Expand on your experience descriptions")
        else:
            analysis['areas_for_improvement'].append("Add more detailed experience descriptions")
        
        # Education section check (10% of score)
        education_keywords = ['education', 'degree', 'university', 'college', 'bachelor', 'master', 'phd']
        if any(keyword in text.lower() for keyword in education_keywords):
            score += 10
            analysis['strengths'].append("Education section present")
        else:
            analysis['areas_for_improvement'].append("Add education information")
        
        # ATS-friendly check (20% of score)
        ats_keywords = ['achieved', 'increased', 'improved', 'developed', 'managed', 'led', 'created']
        ats_count = sum(1 for keyword in ats_keywords if keyword.lower() in text.lower())
        if ats_count >= 5:
            score += 20
            analysis['strengths'].append("ATS-friendly language used")
        elif ats_count >= 2:
            score += 10
            analysis['areas_for_improvement'].append("Use more action verbs and quantifiable achievements")
        else:
            analysis['areas_for_improvement'].append("Use more action verbs and quantifiable achievements")
        
        analysis['score'] = min(score, max_score)
        
        # Generate overall suggestions
        if analysis['score'] >= 80:
            analysis['suggestions'].append("Excellent resume! Consider adding more specific achievements.")
        elif analysis['score'] >= 60:
            analysis['suggestions'].append("Good resume. Focus on the areas for improvement listed above.")
        else:
            analysis['suggestions'].append("Resume needs significant improvement. Address all areas listed above.")
        
        return analysis
    
    def generate_career_advice(self, skills: List[str], experience_years: int = 0) -> Dict:
        """Generate personalized career advice based on skills and experience"""
        advice = {
            'recommendations': [],
            'skill_gaps': [],
            'next_steps': [],
            'market_insights': []
        }
        
        # Analyze skill gaps
        high_demand_skills = [
            'Python', 'JavaScript', 'React', 'AWS', 'Docker', 'Kubernetes',
            'Machine Learning', 'Data Science', 'SQL', 'Git', 'Agile'
        ]
        
        user_skills_lower = [skill.lower() for skill in skills]
        missing_skills = [skill for skill in high_demand_skills 
                         if not any(skill.lower() in user_skill for user_skill in user_skills_lower)]
        
        if missing_skills:
            advice['skill_gaps'] = missing_skills[:5]  # Top 5 missing skills
            advice['recommendations'].append(f"Consider learning: {', '.join(missing_skills[:3])}")
        
        # Experience-based advice
        if experience_years < 2:
            advice['next_steps'].append("Focus on building a strong portfolio with personal projects")
            advice['next_steps'].append("Consider contributing to open source projects")
            advice['recommendations'].append("Apply for internships or entry-level positions")
        elif experience_years < 5:
            advice['next_steps'].append("Consider specializing in a specific technology stack")
            advice['next_steps'].append("Start mentoring junior developers")
            advice['recommendations'].append("Look for mid-level positions with growth opportunities")
        else:
            advice['next_steps'].append("Consider leadership or senior technical roles")
            advice['next_steps'].append("Share your expertise through speaking or writing")
            advice['recommendations'].append("Look for senior or lead positions")
        
        # Market insights
        if 'python' in user_skills_lower:
            advice['market_insights'].append("Python developers are in high demand, especially in data science and AI")
        if 'react' in user_skills_lower:
            advice['market_insights'].append("React skills are highly valued in frontend development")
        if 'aws' in user_skills_lower:
            advice['market_insights'].append("Cloud skills (AWS) are increasingly important")
        
        return advice
    
    def recommend_jobs(self, user_skills: List[str], job_listings: List[Dict], user_preferences: Dict = None) -> List[Dict]:
        """Recommend jobs based on user skills and preferences"""
        if not job_listings:
            return []
        
        recommendations = []
        
        for job in job_listings:
            # Calculate skill match score
            job_skills = self._extract_job_skills(job.get('description', '') + ' ' + job.get('requirements', ''))
            match_score = self._calculate_skill_match(user_skills, job_skills)
            
            # Calculate location preference (if provided)
            location_score = 1.0
            if user_preferences and 'location' in user_preferences:
                if user_preferences['location'].lower() in job.get('location', '').lower():
                    location_score = 1.2
            
            # Calculate salary preference (if provided)
            salary_score = 1.0
            if user_preferences and 'min_salary' in user_preferences:
                job_salary = job.get('salary_min', 0)
                if job_salary >= user_preferences['min_salary']:
                    salary_score = 1.1
            
            # Calculate overall recommendation score
            overall_score = match_score * location_score * salary_score
            
            recommendations.append({
                'job': job,
                'match_score': min(overall_score, 1.0),
                'skill_match': match_score,
                'matched_skills': [skill for skill in user_skills if skill.lower() in ' '.join(job_skills).lower()]
            })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _extract_job_skills(self, job_text: str) -> List[str]:
        """Extract skills from job description"""
        return self.extract_skills_from_text(job_text)
    
    def _calculate_skill_match(self, user_skills: List[str], job_skills: List[str]) -> float:
        """Calculate skill match percentage"""
        if not job_skills:
            return 0.0
        
        user_skills_lower = [skill.lower() for skill in user_skills]
        job_skills_lower = [skill.lower() for skill in job_skills]
        
        matches = sum(1 for skill in job_skills_lower 
                     if any(user_skill in skill or skill in user_skill 
                           for user_skill in user_skills_lower))
        
        return matches / len(job_skills) if job_skills else 0.0
    
    def generate_profile_insights(self, profile_data: Dict) -> Dict:
        """Generate AI-powered profile insights"""
        insights = {
            'profile_completeness': 0,
            'strengths': [],
            'recommendations': [],
            'market_position': 'entry',
            'growth_potential': 'medium'
        }
        
        # Calculate profile completeness
        completeness_score = 0
        max_score = 100
        
        if profile_data.get('skills'):
            completeness_score += 25
        if profile_data.get('resume'):
            completeness_score += 25
        if profile_data.get('profile_picture'):
            completeness_score += 10
        if profile_data.get('phone'):
            completeness_score += 10
        if profile_data.get('email'):
            completeness_score += 10
        if profile_data.get('first_name') and profile_data.get('last_name'):
            completeness_score += 20
        
        insights['profile_completeness'] = completeness_score
        
        # Generate insights based on completeness
        if completeness_score >= 80:
            insights['strengths'].append("Complete and professional profile")
            insights['market_position'] = 'senior'
        elif completeness_score >= 60:
            insights['strengths'].append("Good profile foundation")
            insights['market_position'] = 'mid'
        else:
            insights['recommendations'].append("Complete your profile to improve visibility")
            insights['market_position'] = 'entry'
        
        # Skills-based insights
        skills = profile_data.get('skills', [])
        if isinstance(skills, str):
            skills = [skill.strip() for skill in skills.split(',') if skill.strip()]
        
        if len(skills) >= 10:
            insights['strengths'].append("Diverse skill set")
            insights['growth_potential'] = 'high'
        elif len(skills) >= 5:
            insights['strengths'].append("Good skill foundation")
            insights['growth_potential'] = 'medium'
        else:
            insights['recommendations'].append("Add more skills to your profile")
            insights['growth_potential'] = 'low'
        
        return insights

# Global instance
ai_analyzer = AIAnalyzer()
