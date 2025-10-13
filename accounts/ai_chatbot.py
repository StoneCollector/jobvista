"""
AI Chatbot for JobVista - Resume-based Q&A System
Uses Hugging Face transformers to create a personalized chatbot
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Handle optional AI imports gracefully
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("Warning: Transformers not available. Install with: pip install transformers torch")

logger = logging.getLogger(__name__)

class ResumeChatbot:
    """AI Chatbot trained on user's resume and profile data"""
    
    def __init__(self):
        self.conversation_model = None
        self.qa_model = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize AI models for conversation and Q&A"""
        if not HAS_TRANSFORMERS:
            logger.warning("Transformers not available, using fallback methods")
            return
        
        try:
            # Use a smaller, faster model for real-time chat
            self.conversation_model = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-small",
                max_length=150,
                do_sample=True,
                temperature=0.7
            )
            
            # Q&A model for resume-specific questions
            self.qa_model = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad"
            )
            
            logger.info("AI Chatbot models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing chatbot models: {e}")
            self.conversation_model = None
            self.qa_model = None
    
    def create_resume_context(self, user_profile: Dict) -> str:
        """Create a comprehensive context from user's resume and profile"""
        context_parts = []
        
        # Basic information
        if user_profile.get('first_name') and user_profile.get('last_name'):
            context_parts.append(f"Name: {user_profile['first_name']} {user_profile['last_name']}")
        
        if user_profile.get('email'):
            context_parts.append(f"Email: {user_profile['email']}")
        
        if user_profile.get('phone'):
            context_parts.append(f"Phone: {user_profile['phone']}")
        
        # Skills
        if user_profile.get('skills'):
            skills = user_profile['skills']
            if isinstance(skills, str):
                skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
            else:
                skills_list = skills
            context_parts.append(f"Skills: {', '.join(skills_list)}")
        
        # Experience (if available)
        if user_profile.get('experience'):
            context_parts.append(f"Experience: {user_profile['experience']}")
        
        # Education (if available)
        if user_profile.get('education'):
            context_parts.append(f"Education: {user_profile['education']}")
        
        # Resume text (if available)
        if user_profile.get('resume_text'):
            context_parts.append(f"Resume Summary: {user_profile['resume_text'][:500]}...")
        
        return "\n".join(context_parts)
    
    def generate_response(self, question: str, user_profile: Dict, conversation_history: List[Dict] = None) -> Dict:
        """Generate AI response based on user's resume and question"""
        try:
            # Create resume context
            resume_context = self.create_resume_context(user_profile)
            
            # Determine question type and generate appropriate response
            question_lower = question.lower()
            
            if any(keyword in question_lower for keyword in ['skill', 'skills', 'technology', 'tech']):
                return self._handle_skills_question(question, user_profile)
            
            elif any(keyword in question_lower for keyword in ['experience', 'work', 'job', 'career']):
                return self._handle_experience_question(question, user_profile)
            
            elif any(keyword in question_lower for keyword in ['education', 'degree', 'university', 'college']):
                return self._handle_education_question(question, user_profile)
            
            elif any(keyword in question_lower for keyword in ['salary', 'pay', 'compensation', 'money']):
                return self._handle_salary_question(question, user_profile)
            
            elif any(keyword in question_lower for keyword in ['job', 'position', 'role', 'career advice']):
                return self._handle_career_advice_question(question, user_profile)
            
            else:
                return self._handle_general_question(question, user_profile, conversation_history)
                
        except Exception as e:
            logger.error(f"Error generating chatbot response: {e}")
            return {
                'response': "I'm having trouble processing your question right now. Please try again later.",
                'confidence': 0.0,
                'type': 'error'
            }
    
    def _handle_skills_question(self, question: str, user_profile: Dict) -> Dict:
        """Handle questions about skills and technologies"""
        skills = user_profile.get('skills', '')
        if isinstance(skills, str):
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        else:
            skills_list = skills
        
        if not skills_list:
            return {
                'response': "I don't see any skills listed in your profile yet. You can add your skills in the profile section to get personalized advice.",
                'confidence': 0.8,
                'type': 'skills'
            }
        
        # Analyze question for specific skill mentions
        question_lower = question.lower()
        mentioned_skills = [skill for skill in skills_list if skill.lower() in question_lower]
        
        if mentioned_skills:
            response = f"Based on your profile, you have experience with {', '.join(mentioned_skills)}. "
            if len(mentioned_skills) == 1:
                response += f"{mentioned_skills[0]} is a valuable skill in today's job market. "
            response += f"Your other skills include {', '.join([s for s in skills_list if s not in mentioned_skills][:3])}."
        else:
            response = f"Your current skills include {', '.join(skills_list[:5])}. "
            if len(skills_list) > 5:
                response += f"You have {len(skills_list)} total skills listed in your profile."
        
        return {
            'response': response,
            'confidence': 0.9,
            'type': 'skills',
            'mentioned_skills': mentioned_skills
        }
    
    def _handle_experience_question(self, question: str, user_profile: Dict) -> Dict:
        """Handle questions about work experience"""
        experience = user_profile.get('experience', '')
        resume_text = user_profile.get('resume_text', '')
        
        if not experience and not resume_text:
            return {
                'response': "I don't see any work experience details in your profile. You can add your experience in the profile section to get better career advice.",
                'confidence': 0.8,
                'type': 'experience'
            }
        
        # Extract experience-related information
        experience_info = experience or resume_text[:300] + "..." if resume_text else "No experience details available"
        
        response = f"Based on your profile, here's what I can tell you about your experience: {experience_info}"
        
        return {
            'response': response,
            'confidence': 0.8,
            'type': 'experience'
        }
    
    def _handle_education_question(self, question: str, user_profile: Dict) -> Dict:
        """Handle questions about education"""
        education = user_profile.get('education', '')
        
        if not education:
            return {
                'response': "I don't see any education details in your profile. You can add your educational background in the profile section.",
                'confidence': 0.8,
                'type': 'education'
            }
        
        response = f"Based on your profile, your educational background includes: {education}"
        
        return {
            'response': response,
            'confidence': 0.9,
            'type': 'education'
        }
    
    def _handle_salary_question(self, question: str, user_profile: Dict) -> Dict:
        """Handle questions about salary expectations"""
        skills = user_profile.get('skills', '')
        if isinstance(skills, str):
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        else:
            skills_list = skills
        
        # Simple salary estimation based on skills
        high_demand_skills = ['python', 'javascript', 'react', 'aws', 'docker', 'kubernetes', 'machine learning', 'ai']
        user_high_demand_skills = [skill for skill in skills_list if any(hd_skill in skill.lower() for hd_skill in high_demand_skills)]
        
        if user_high_demand_skills:
            response = f"Based on your skills in {', '.join(user_high_demand_skills[:3])}, you're likely in a high-demand field. "
            response += "Salary expectations can vary based on location, experience, and company size. "
            response += "I'd recommend researching current market rates for your specific skills and experience level."
        else:
            response = "Salary expectations depend on many factors including your skills, experience, location, and the specific role. "
            response += "I'd recommend researching current market rates for your field and experience level."
        
        return {
            'response': response,
            'confidence': 0.7,
            'type': 'salary'
        }
    
    def _handle_career_advice_question(self, question: str, user_profile: Dict) -> Dict:
        """Handle career advice questions"""
        skills = user_profile.get('skills', '')
        if isinstance(skills, str):
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        else:
            skills_list = skills
        
        # Generate career advice based on skills
        if not skills_list:
            response = "To provide better career advice, I'd need to know more about your skills and experience. "
            response += "Please complete your profile with your skills and work experience."
        else:
            response = f"Based on your skills in {', '.join(skills_list[:3])}, here are some career suggestions: "
            
            # Skill-based career advice
            if any('python' in skill.lower() for skill in skills_list):
                response += "Consider roles in Data Science, Backend Development, or AI/ML. "
            if any('javascript' in skill.lower() or 'react' in skill.lower() for skill in skills_list):
                response += "Frontend Development or Full-Stack roles would be great fits. "
            if any('aws' in skill.lower() or 'cloud' in skill.lower() for skill in skills_list):
                response += "Cloud Engineering or DevOps roles are excellent options. "
            
            response += "Keep building your skills and consider getting certifications in your areas of interest."
        
        return {
            'response': response,
            'confidence': 0.8,
            'type': 'career_advice'
        }
    
    def _handle_general_question(self, question: str, user_profile: Dict, conversation_history: List[Dict] = None) -> Dict:
        """Handle general questions using AI model"""
        if not self.conversation_model:
            return {
                'response': "I'm here to help with questions about your profile, skills, and career. What would you like to know?",
                'confidence': 0.5,
                'type': 'general'
            }
        
        try:
            # Create context for the conversation
            context = self.create_resume_context(user_profile)
            
            # Simple response generation (fallback)
            if 'hello' in question.lower() or 'hi' in question.lower():
                response = f"Hello! I'm your AI career assistant. I can help you with questions about your profile, skills, and career advice. What would you like to know?"
            elif 'help' in question.lower():
                response = "I can help you with questions about your skills, experience, education, salary expectations, and career advice. Just ask me anything about your profile!"
            else:
                response = "I'm here to help with questions about your profile and career. You can ask me about your skills, experience, or career advice. What would you like to know?"
            
            return {
                'response': response,
                'confidence': 0.6,
                'type': 'general'
            }
            
        except Exception as e:
            logger.error(f"Error in general question handling: {e}")
            return {
                'response': "I'm here to help with questions about your profile and career. What would you like to know?",
                'confidence': 0.5,
                'type': 'general'
            }
    
    def get_suggested_questions(self, user_profile: Dict) -> List[str]:
        """Generate suggested questions based on user's profile"""
        suggestions = []
        
        skills = user_profile.get('skills', '')
        if skills:
            suggestions.append("What are my strongest skills?")
            suggestions.append("What career paths match my skills?")
        
        if user_profile.get('experience'):
            suggestions.append("How can I improve my experience section?")
        
        if user_profile.get('education'):
            suggestions.append("How does my education help my career?")
        
        # Always include these general suggestions
        suggestions.extend([
            "What salary can I expect?",
            "What skills should I learn next?",
            "How can I improve my resume?",
            "What are the best job search strategies?"
        ])
        
        return suggestions[:6]  # Return top 6 suggestions

# Global instance
resume_chatbot = ResumeChatbot()
