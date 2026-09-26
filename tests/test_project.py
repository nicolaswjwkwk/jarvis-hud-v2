from pathlib import Path

def test_mobile_html_exists():
    assert Path("mobile.html").is_file()

def test_server_file_exists():
    assert Path("server/app.py").is_file()

def test_backend_has_health():
    assert Path("server/app.py").read_text().count("/health") > 0

def test_requirements_file_exists():
    assert Path("requirements.txt").is_file()


# ── Testes de API (JARVIS Backend) ──────────────────────────────
from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_health_api():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["service"] == "jarvis-backend"


def test_auth_status_api():
    response = client.get("/auth/status")
    assert response.status_code == 200


def test_chat_degraded_fallback():
    """Sem Ollama ativo, o backend deve responder em modo degradado."""
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "olá"}]})
    assert response.status_code == 200
    body = response.json()
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body.get("degraded") is True


def test_chat_rejects_empty():
    response = client.post("/api/chat", json={"messages": []})
    assert response.status_code == 422
