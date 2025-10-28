import os
import logging
from typing import Dict, List
try:
    from django.conf import settings
except Exception:
    settings = None

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except Exception:
    HAS_GEMINI = False
    genai = None


class GeminiChatbot:
    """Gemini-powered chatbot wrapper. Keeps interface similar to advanced_chatbot."""

    def __init__(self):
        self.api_key = (
            (getattr(settings, 'GEMINI_API_KEY', None) if settings else None)
            or os.environ.get('GEMINI_API_KEY')
            or os.environ.get('GOOGLE_API_KEY')
            or 'AIzaSyCqEDXMMnrJ0oqkjlykYB8qPxQ4jr7oFgw'
        )
        # Prefer user's target model; allow override via env
        self.model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
        self._client_ready = False
        self._model = None
        self._ensure_client()

    def _ensure_client(self):
        if not HAS_GEMINI or not self.api_key:
            # Defer warnings until request-time; stay silent at import/startup
            self._client_ready = False
            return
        try:
            genai.configure(api_key=self.api_key)
            # Try preferred model; on 404, fallback to known supported ones
            candidates = [
                self.model_name,
                'gemini-2.0-flash-exp',
                'gemini-2.0-pro',
                'gemini-1.5-pro',
                'gemini-1.5-pro-latest',
                'gemini-1.5-flash',
            ]
            last_err = None
            for name in candidates:
                try:
                    self._model = genai.GenerativeModel(name)
                    self.model_name = name
                    self._client_ready = True
                    return
                except Exception as e:
                    last_err = e
                    continue
            raise last_err or RuntimeError('No Gemini model could be initialized')
        except Exception as e:
            logger.error(f"Failed to init Gemini: {e}")
            self._client_ready = False

    def is_available(self) -> bool:
        return bool(self._client_ready)

    def _build_system_preamble(self, user_profile: Dict) -> str:
        skills = user_profile.get('skills') or ''
        if isinstance(skills, str):
            skills_text = skills
        else:
            skills_text = ', '.join(skills)
        resume_text = (user_profile.get('resume_text') or '')[:1200]
        first_name = user_profile.get('first_name') or 'User'
        db_context = user_profile.get('db_context') or ''
        parts = [
            "You are JobVista's AI career assistant. Your goals: answer precisely, ask one targeted follow-up if needed, and provide 2-4 concrete next steps.",
            "Style: concise, friendly, professional, no emojis, no generic lists unless asked.",
            "If the user greets you, respond briefly and ask a specific helpful question tailored to their skills.",
            "If input is vague, propose 3 focused options as buttons-style lines (without UI syntax).",
            f"Profile→ Name: {first_name}. Skills: {skills_text}. Resume: {resume_text}.",
        ]
        if db_context:
            parts.append(f"Live data→ {db_context}.")
        parts.append("Ground answers in this profile whenever relevant.")
        return " \n".join(parts)

    def generate_response(self, question: str, user_profile: Dict, conversation_history: List[Dict] = None) -> Dict:
        # If not ready, try to (re)load API key and initialize now (supports env set after import)
        if not self._client_ready:
            # Re-read from settings/env in case it was set after startup
            try:
                from django.conf import settings as dj_settings
            except Exception:
                dj_settings = None
            self.api_key = (
                (getattr(dj_settings, 'GEMINI_API_KEY', None) if dj_settings else None)
                or os.environ.get('GEMINI_API_KEY')
                or os.environ.get('GOOGLE_API_KEY')
                or self.api_key
            )
            self._ensure_client()
            if not self._client_ready:
                return {
                    'response': None,
                    'confidence': 0.0,
                    'type': 'unavailable'
                }

        try:
            system = self._build_system_preamble(user_profile)
            # Simpler prompt composition to reduce SDK formatting issues, with few-shot coaching
            history_text = ""
            if conversation_history:
                turns = []
                for turn in conversation_history[-8:]:
                    q = turn.get('question', '').strip()
                    a = turn.get('response', '').strip()
                    if q:
                        turns.append(f"User: {q}")
                    if a:
                        turns.append(f"Assistant: {a}")
                history_text = "\n".join(turns)

            # Detect short greetings and steer a better response
            normalized = (question or '').strip().lower()
            is_greeting = normalized in {"hi", "hello", "hey", "yo", "hola", "hi!", "hello!", "hey!"}

            few_shot = (
                "Assistant guidelines:\n"
                "- Avoid repeating generic capabilities on greetings.\n"
                "- Ask one targeted question informed by the user's skills.\n"
                "- Prefer concrete steps, examples, or brief plans.\n"
                "Example:\n"
                "User: hi\n"
                "Assistant: Hi! Want to focus on resume tweaks, interview prep, or next skills to learn for React/Django?\n"
            )

            prompt_parts = [system]
            if few_shot:
                prompt_parts.append(few_shot)
            if history_text:
                prompt_parts.append(history_text)
            # Add an intent hint for greetings to avoid generic answers
            if is_greeting:
                prompt_parts.append("Assistant: Keep greeting to one short line, then ask one specific follow-up.")
            prompt_parts.append(f"User: {question}")
            prompt_parts.append("Assistant:")
            prompt = "\n\n".join(filter(None, prompt_parts))

            # Use structured contents format to avoid SDK type issues
            contents = [{"role": "user", "parts": [prompt]}]
            resp = self._model.generate_content(contents)
            text = (resp.text or '').strip()
            if not text:
                return {'response': None, 'confidence': 0.0, 'type': 'empty'}
            # Basic confidence heuristic
            conf = 0.7 + min(0.25, len(text) / 8000)
            return {'response': text, 'confidence': min(conf, 0.95), 'type': 'gemini'}
        except Exception as e:
            msg = f"Gemini response error: {e} (model={self.model_name})"
            logger.error(msg)
            return {'response': msg, 'confidence': 0.0, 'type': 'error'}


# Global instance
gemini_chatbot = GeminiChatbot()


