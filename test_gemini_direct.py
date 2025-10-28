#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JobSite.settings')
django.setup()

from accounts.gemini_chatbot import gemini_chatbot

print('Testing Gemini Chatbot directly...')

try:
    # Test simple response
    test_context = {
        'first_name': 'Test',
        'skills': 'Python, Django',
        'resume_text': '',
        'db_context': ''
    }
    
    response = gemini_chatbot.generate_response("Hello, can you help me?", test_context)
    print('Gemini response:', response)
    
    if response and response.get('response'):
        print('SUCCESS: Gemini is working!')
        print('Response type:', response.get('type', 'unknown'))
        print('Response preview:', response['response'][:100] + '...')
    else:
        print('FAILED: No response from Gemini')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
