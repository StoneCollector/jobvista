"""
Advanced AI Chatbot for JobVista using Hugging Face Transformers
Provides intelligent conversational AI for career guidance
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Handle optional AI imports gracefully
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
    import torch
    HAS_TRANSFORMERS = True
    print("Advanced Transformers available, using AI models.")
except ImportError:
    HAS_TRANSFORMERS = False
    print("Warning: Transformers not available. Install with: pip install transformers torch")

logger = logging.getLogger(__name__)

class AdvancedResumeChatbot:
    """Advanced AI Chatbot with proper conversational capabilities"""
    
    def __init__(self):
        self.conversation_model = None
        self.qa_model = None
        self.text_generator = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize advanced AI models for conversation"""
        if not HAS_TRANSFORMERS:
            logger.warning("Transformers not available, using fallback methods")
            return
        
        try:
            # Use a more capable conversational model
            print("Loading conversational AI model...")
            self.conversation_model = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-small",
                max_length=150,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=50256,
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Q&A model for specific questions
            print("Loading Q&A model...")
            self.qa_model = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad"
            )
            
            print("AI models loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
            self.conversation_model = None
            self.qa_model = None
    
    def create_resume_context(self, user_profile: Dict) -> str:
        """Create comprehensive context from user's resume and profile"""
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
        
        # Experience
        if user_profile.get('experience'):
            context_parts.append(f"Experience: {user_profile['experience']}")
        
        # Education
        if user_profile.get('education'):
            context_parts.append(f"Education: {user_profile['education']}")
        
        # Resume text
        if user_profile.get('resume_text'):
            context_parts.append(f"Resume Summary: {user_profile['resume_text'][:800]}...")
        
        return "\n".join(context_parts)
    
    def generate_response(self, question: str, user_profile: Dict, conversation_history: List[Dict] = None) -> Dict:
        """Generate intelligent AI response based on user's profile and question"""
        try:
            # Create resume context
            resume_context = self.create_resume_context(user_profile)
            
            # Always use intelligent fallback for now (it's more reliable)
            return self._generate_fallback_response(question, user_profile)
                
        except Exception as e:
            logger.error(f"Error generating chatbot response: {e}")
            return {
                'response': "I'm having trouble processing your question right now. Please try again later.",
                'confidence': 0.0,
                'type': 'error'
            }
    
    def _generate_ai_response(self, question: str, context: str, conversation_history: List[Dict] = None) -> Dict:
        """Generate response using Hugging Face models"""
        try:
            # First try Q&A if it's a specific question about the resume
            if self.qa_model and context and len(context) > 50:
                try:
                    qa_result = self.qa_model(question=question, context=context)
                    if qa_result['score'] > 0.3:  # Lower threshold for more responses
                        return {
                            'response': qa_result['answer'],
                            'confidence': qa_result['score'],
                            'type': 'qa_resume'
                        }
                except Exception as e:
                    logger.warning(f"Q&A model failed: {e}")
            
            # Skip AI models for now and use intelligent fallback
            # The AI models are not providing good responses, so use our intelligent fallback
            return self._generate_fallback_response(question, {'resume_text': context})
            
        except Exception as e:
            logger.error(f"Error in AI response generation: {e}")
            return self._generate_fallback_response(question, {'resume_text': context})
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the AI response"""
        # Remove any remaining prompt text
        response = response.replace("Human:", "").replace("Assistant:", "").strip()
        
        # Remove incomplete sentences at the end
        sentences = response.split('.')
        if len(sentences) > 1 and len(sentences[-1].strip()) < 10:
            response = '.'.join(sentences[:-1]) + '.'
        
        # Ensure response is not too short
        if len(response) < 20:
            response = "I understand your question. Let me help you with that. Could you provide more details about what specific aspect you'd like to know more about?"
        
        return response
    
    def _classify_response_type(self, question: str) -> str:
        """Classify the type of question"""
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in ['skill', 'skills', 'technology', 'tech']):
            return 'skills'
        elif any(keyword in question_lower for keyword in ['experience', 'work', 'job', 'career']):
            return 'experience'
        elif any(keyword in question_lower for keyword in ['education', 'degree', 'university', 'college']):
            return 'education'
        elif any(keyword in question_lower for keyword in ['salary', 'pay', 'compensation', 'money']):
            return 'salary'
        elif any(keyword in question_lower for keyword in ['resume', 'cv', 'application']):
            return 'resume'
        else:
            return 'general'
    
    def _calculate_confidence(self, response: str, question: str) -> float:
        """Calculate confidence score for the response"""
        # Base confidence
        confidence = 0.7
        
        # Adjust based on response length and quality
        if len(response) > 50:
            confidence += 0.1
        if len(response) > 100:
            confidence += 0.1
        
        # Check for relevant keywords
        question_words = set(question.lower().split())
        response_words = set(response.lower().split())
        overlap = len(question_words.intersection(response_words))
        if overlap > 0:
            confidence += min(0.2, overlap * 0.05)
        
        return min(0.95, confidence)
    
    def _generate_fallback_response(self, question: str, user_profile: Dict) -> Dict:
        """Generate intelligent fallback response when AI models are not available"""
        question_lower = question.lower()
        
        # Get user skills
        skills = user_profile.get('skills', '')
        if isinstance(skills, str):
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        else:
            skills_list = skills or []
        
        # Get experience and education
        experience = user_profile.get('experience', '')
        education = user_profile.get('education', '')
        
        # Generate highly intelligent contextual responses
        if any(keyword in question_lower for keyword in ['skill', 'skills', 'technology', 'tech', 'what can i do', 'what am i good at', 'lagging', 'missing', 'gap', 'improve', 'learn']):
            if skills_list:
                # Analyze skill categories
                tech_skills = [s for s in skills_list if any(tech in s.lower() for tech in ['python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker'])]
                soft_skills = [s for s in skills_list if any(soft in s.lower() for soft in ['leadership', 'communication', 'management', 'teamwork', 'problem solving'])]
                
                # Check if user is asking about skill gaps
                if any(keyword in question_lower for keyword in ['lagging', 'missing', 'gap', 'improve', 'learn', 'what should i learn']):
                    response = f"Based on your current skills in {', '.join(skills_list[:3])}, here are the key areas you should focus on to advance your career:\n\n"
                    
                    # Provide specific skill gap analysis
                    if any('react' in skill.lower() for skill in skills_list):
                        response += "**Frontend Development Gaps:**\n"
                        response += "• **Next.js** - For server-side rendering and better SEO\n"
                        response += "• **TypeScript** - For better code quality and maintainability\n"
                        response += "• **State Management** - Redux, Zustand, or Context API mastery\n"
                        response += "• **Testing** - Jest, React Testing Library, or Cypress\n\n"
                    
                    if any('django' in skill.lower() for skill in skills_list):
                        response += "**Backend Development Gaps:**\n"
                        response += "• **FastAPI** - For high-performance APIs\n"
                        response += "• **Docker & Kubernetes** - For containerization and deployment\n"
                        response += "• **PostgreSQL** - Advanced database optimization\n"
                        response += "• **Redis** - For caching and session management\n\n"
                    
                    response += "**General Tech Skills to Learn:**\n"
                    response += "• **Cloud Platforms** - AWS, Azure, or GCP\n"
                    response += "• **DevOps** - CI/CD pipelines, monitoring, and automation\n"
                    response += "• **System Design** - Scalable architecture patterns\n"
                    response += "• **Security** - OWASP, authentication, and data protection\n\n"
                    
                    response += "**Next Steps:**\n"
                    response += "1. Pick 2-3 skills from above to focus on\n"
                    response += "2. Build projects showcasing these skills\n"
                    response += "3. Get certifications in your chosen areas\n"
                    response += "4. Contribute to open-source projects\n"
                    response += "5. Network with professionals in these fields"
                else:
                    response = f"Based on your profile, you have excellent skills in {', '.join(skills_list[:3])}. "
                    
                    if tech_skills:
                        response += f"Your technical expertise in {', '.join(tech_skills[:2])} makes you valuable for software development roles. "
                    
                    if soft_skills:
                        response += f"Your {', '.join(soft_skills[:2])} skills are crucial for leadership positions. "
                    
                    response += "Consider highlighting these skills in your applications and continuing to develop them. What specific area would you like to focus on next?"
            else:
                response = "I don't see any skills listed in your profile yet. Adding your technical and soft skills will help me provide personalized career advice. You can include programming languages, frameworks, tools, and soft skills like leadership or communication."
            
            return {
                'response': response,
                'confidence': 0.9,
                'type': 'skills'
            }
        
        elif any(keyword in question_lower for keyword in ['career', 'advice', 'path', 'future', 'what should i do', 'job', 'career change']):
            if skills_list:
                response = f"Based on your skills in {', '.join(skills_list[:3])}, here are tailored career recommendations:\n\n"
                
                # Provide specific career paths based on skills
                if any('python' in skill.lower() for skill in skills_list):
                    response += "**Python Developer Path**: Backend Developer, Data Scientist, Machine Learning Engineer, or DevOps Engineer\n"
                if any('javascript' in skill.lower() or 'react' in skill.lower() for skill in skills_list):
                    response += "**Frontend/Full-Stack Path**: Frontend Developer, React Developer, or Full-Stack Developer\n"
                if any('sql' in skill.lower() or 'database' in skill.lower() for skill in skills_list):
                    response += "**Data Path**: Data Analyst, Database Administrator, or Business Intelligence Developer\n"
                if any('aws' in skill.lower() or 'cloud' in skill.lower() for skill in skills_list):
                    response += "**Cloud Path**: Cloud Engineer, DevOps Engineer, or Solutions Architect\n"
                
                response += f"\n**Next Steps**: 1) Build projects showcasing your {skills_list[0]} skills, 2) Network with professionals in your target field, 3) Consider relevant certifications, 4) Update your resume with quantifiable achievements."
            else:
                response = "To provide personalized career advice, I need to know more about your skills and interests. Consider these popular career paths:\n\n• **Software Development**: High demand, good pay, remote opportunities\n• **Data Science**: Growing field, analytical skills required\n• **Digital Marketing**: Creative and analytical, business-focused\n• **Project Management**: Leadership skills, organizational abilities\n\nWhat interests you most? I can provide specific guidance once I know your skills."
            
            return {
                'response': response,
                'confidence': 0.8,
                'type': 'career_advice'
            }
        
        elif any(keyword in question_lower for keyword in ['resume', 'cv', 'application', 'how to improve']):
            response = "Here's a comprehensive guide to improve your resume:\n\n**Content Tips:**\n• Use action verbs (Led, Developed, Implemented, Achieved)\n• Quantify achievements (Increased sales by 25%, Managed team of 5)\n• Include relevant keywords from job descriptions\n• Keep it 1-2 pages maximum\n\n**Formatting:**\n• Use a clean, professional template\n• Consistent formatting and fonts\n• Include contact info and LinkedIn\n• Proofread for errors\n\n**Pro Tips:**\n• Tailor each resume to the specific job\n• Include a compelling summary\n• Highlight relevant projects and achievements\n• Use industry-specific terminology\n\nWould you like specific advice on any of these areas?"
            
            return {
                'response': response,
                'confidence': 0.9,
                'type': 'resume'
            }
        
        elif any(keyword in question_lower for keyword in ['salary', 'pay', 'compensation', 'money', 'how much']):
            if skills_list:
                response = f"Based on your skills in {', '.join(skills_list[:3])}, here are salary expectations:\n\n"
                
                if any('python' in skill.lower() for skill in skills_list):
                    response += "**Python Developer**: $70k-120k (entry to senior)\n"
                if any('javascript' in skill.lower() for skill in skills_list):
                    response += "**JavaScript Developer**: $65k-110k (frontend/full-stack)\n"
                if any('react' in skill.lower() for skill in skills_list):
                    response += "**React Developer**: $70k-115k (frontend specialist)\n"
                
                response += "\n**Factors affecting salary:**\n• Location (SF/NY pay 20-30% more)\n• Experience level\n• Company size and industry\n• Additional skills and certifications\n\n**Negotiation tips:**\n• Research market rates for your role\n• Highlight unique skills and achievements\n• Consider total compensation (benefits, equity)\n• Practice your negotiation pitch"
            else:
                response = "Salary expectations depend on your skills, experience, and location. To give you accurate estimates, I'd need to know your technical skills and experience level. Generally:\n\n• **Entry-level**: $50k-70k\n• **Mid-level**: $70k-100k\n• **Senior-level**: $100k-150k+\n\n**High-paying skills include:**\n• Machine Learning/AI\n• Cloud Architecture (AWS/Azure)\n• DevOps/Infrastructure\n• Data Science\n\nWhat's your experience level and main skills?"
            
            return {
                'response': response,
                'confidence': 0.8,
                'type': 'salary'
            }
        
        elif any(keyword in question_lower for keyword in ['interview', 'interviewing', 'interview tips']):
            response = "Here are comprehensive interview preparation tips:\n\n**Before the Interview:**\n• Research the company and role thoroughly\n• Practice common questions (STAR method)\n• Prepare questions to ask them\n• Review your resume and projects\n\n**During the Interview:**\n• Arrive 10-15 minutes early\n• Dress professionally\n• Maintain eye contact and good posture\n• Listen carefully and ask clarifying questions\n\n**Common Questions:**\n• 'Tell me about yourself' (2-3 minute elevator pitch)\n• 'Why do you want this job?' (show research and enthusiasm)\n• 'What's your greatest weakness?' (show growth mindset)\n• 'Where do you see yourself in 5 years?' (show career planning)\n\n**Pro Tips:**\n• Use the STAR method for behavioral questions\n• Prepare specific examples of your achievements\n• Practice technical questions if applicable\n• Send a thank-you email within 24 hours"
            
            return {
                'response': response,
                'confidence': 0.9,
                'type': 'interview'
            }
        
        else:
            # General intelligent response - be more helpful and contextual
            if skills_list:
                response = f"I understand you're asking about '{question}'. Based on your skills in {', '.join(skills_list[:3])}, I can help you with:\n\n**Career Guidance:**\n• Skills analysis and development\n• Career path recommendations\n• Industry insights and trends\n\n**Application Support:**\n• Resume optimization\n• Cover letter writing\n• Interview preparation\n\n**Professional Development:**\n• Salary negotiation\n• Skill gap analysis\n• Networking strategies\n\n**Specific Questions I Can Answer:**\n• 'What skills should I learn next?'\n• 'How can I improve my resume?'\n• 'What career paths match my skills?'\n• 'How do I prepare for interviews?'\n• 'What am I lagging in?' (skill gap analysis)\n• 'What salary can I expect?'"
            else:
                response = f"I understand you're asking about '{question}'. As your AI career assistant, I can help with:\n\n**Career Guidance:**\n• Skills analysis and development\n• Career path recommendations\n• Industry insights and trends\n\n**Application Support:**\n• Resume optimization\n• Cover letter writing\n• Interview preparation\n\n**Professional Development:**\n• Salary negotiation\n• Skill gap analysis\n• Networking strategies\n\nCould you be more specific about what you'd like to know? For example:\n• 'What skills should I learn next?'\n• 'How can I improve my resume?'\n• 'What career paths match my skills?'\n• 'How do I prepare for interviews?'"
            
            return {
                'response': response,
                'confidence': 0.7,
                'type': 'general'
            }
    
    def get_suggested_questions(self, user_profile: Dict) -> List[str]:
        """Generate intelligent suggested questions based on user's profile"""
        suggestions = []
        
        skills = user_profile.get('skills', '')
        if isinstance(skills, str):
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        else:
            skills_list = skills or []
        
        # Generate personalized suggestions based on skills
        if skills_list:
            if any('python' in skill.lower() for skill in skills_list):
                suggestions.extend([
                    "What Python career paths should I pursue?",
                    "How can I advance my Python skills?",
                    "What Python projects should I build?"
                ])
            elif any('javascript' in skill.lower() or 'react' in skill.lower() for skill in skills_list):
                suggestions.extend([
                    "What frontend career opportunities are available?",
                    "How can I become a full-stack developer?",
                    "What JavaScript frameworks should I learn next?"
                ])
            elif any('sql' in skill.lower() or 'database' in skill.lower() for skill in skills_list):
                suggestions.extend([
                    "What data career paths match my skills?",
                    "How can I transition to data science?",
                    "What database technologies should I learn?"
                ])
            else:
                suggestions.extend([
                    "What career paths match my skills?",
                    "How can I leverage my technical skills?",
                    "What skills should I develop next?"
                ])
        else:
            suggestions.extend([
                "What skills should I learn for tech careers?",
                "How do I start a career in software development?",
                "What are the most in-demand tech skills?"
            ])
        
        # Add general career questions
        suggestions.extend([
            "How can I improve my resume?",
            "What salary can I expect with my skills?",
            "How do I prepare for technical interviews?",
            "What are the best job search strategies?"
        ])
        
        # Remove duplicates and return top 6
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:6]

# Global instance
advanced_chatbot = AdvancedResumeChatbot()
