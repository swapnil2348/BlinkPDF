import os, json, requests, time
from flask import current_app

# Securely read API key from environment variable.
# DO NOT store your key directly in this file. Set GEMINI_API_KEY in the environment or a .env file.
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def call_gemini_text(prompt, model='gemini-1.0', max_tokens=1024, temperature=0.2):
    """
    Simple wrapper to call Google Generative Models (Gemini) REST API.
    This function is a scaffolding/example. Make sure your environment has network access.
    Replace the endpoint and request body as required by the current Gemini API version.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError('GEMINI_API_KEY is not set in the environment.')

    # Example endpoint — verify with provider docs and update accordingly.
    url = f'https://generativelanguage.googleapis.com/v1beta2/models/{model}:generateText'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GEMINI_API_KEY}'
    }
    body = {
        'prompt': { 'text': prompt },
        'maxOutputTokens': max_tokens,
        'temperature': temperature
    }
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # Parse response depending on actual API structure. This tries common shapes.
    if 'candidates' in data:
        return data['candidates'][0].get('content', data)
    if 'output' in data:
        return data['output'].get('text', data)
    return data

def safe_call_gemini(prompt, **kwargs):
    """Call Gemini and return (success, result_or_error) without throwing."""
    try:
        r = call_gemini_text(prompt, **kwargs)
        return True, r
    except Exception as e:
        return False, str(e)
