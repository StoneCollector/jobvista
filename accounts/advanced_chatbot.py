"""
Gemini-only chatbot proxy. This module preserves the old import path
`accounts.advanced_chatbot.advanced_chatbot` but delegates to Gemini.
"""

from typing import Dict, List

try:
    from .gemini_chatbot import gemini_chatbot
except Exception:
    gemini_chatbot = None


class AdvancedResumeChatbot:
    def generate_response(self, question: str, user_profile: Dict, conversation_history: List[Dict] = None) -> Dict:
        if gemini_chatbot is None:
            return {
                'response': 'AI is not configured. Please set GEMINI_API_KEY.',
                'confidence': 0.0,
                'type': 'unavailable'
            }
        resp = gemini_chatbot.generate_response(question, user_profile, conversation_history)
        if not resp or not resp.get('response'):
            return {
                'response': 'AI is not configured. Please set GEMINI_API_KEY.',
                'confidence': 0.0,
                'type': 'unavailable'
            }
        return resp

    def get_suggested_questions(self, user_profile: Dict) -> List[str]:
        skills = user_profile.get('skills') or ''
        if isinstance(skills, str):
            skills_list = [s.strip() for s in skills.split(',') if s.strip()]
        else:
            skills_list = skills or []
        base = [
            'What skills should I learn next?',
            'How can I improve my resume?',
            'What career paths match my skills?',
            'How do I prepare for interviews?',
            'What salary can I expect?',
        ]
        if skills_list:
            base.insert(0, f'How do I level up from {skills_list[0]}?')
        return base[:6]


advanced_chatbot = AdvancedResumeChatbot()
