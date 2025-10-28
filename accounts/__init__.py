default_app_config = 'accounts.apps.AccountsConfig'

# Expose a feature flag for Gemini availability (env-based)
import os
HAS_GEMINI = bool(os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY'))

