from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Dict

from server.config import CONFIG


def build_google_auth_url() -> str:
    if not CONFIG.google_client_id:
        raise RuntimeError('GOOGLE_CLIENT_ID is not configured')
    params = {
        'client_id': CONFIG.google_client_id,
        'redirect_uri': CONFIG.google_redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent',
    }
    return 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)


def exchange_google_code(code: str) -> Dict[str, Any]:
    if not CONFIG.google_client_id or not CONFIG.google_client_secret:
        raise RuntimeError('Google OAuth is not configured')
    payload = {
        'code': code,
        'client_id': CONFIG.google_client_id,
        'client_secret': CONFIG.google_client_secret,
        'redirect_uri': CONFIG.google_redirect_uri,
        'grant_type': 'authorization_code',
    }
    data = urllib.parse.urlencode(payload).encode('utf-8')
    request = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=data,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode('utf-8')
        return json.loads(body)


def fetch_google_userinfo(access_token: str) -> Dict[str, Any]:
    request = urllib.request.Request(
        'https://openidconnect.googleapis.com/v1/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
        method='GET',
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode('utf-8')
        return json.loads(body)
