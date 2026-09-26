"""Habilidades divertidas do JARVIS — piadas, fatos, citações e motivação.

Dados do projeto JARVIS-on-Messenger (MIT), em server/skills/data/.
Endpoint: GET /api/skills (lista) e GET /api/skills/{kind} (um item aleatório).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/skills", tags=["skills"])

_DATA = Path(__file__).resolve().parent / "data"

_KINDS = {
    "joke": ("jokes.json", "jokes", "piada"),
    "fact": ("facts.json", "facts", "fato"),
    "quote": ("quotes.json", "quotes", "citação"),
    "motivation": ("motivations.json", "motivations", "motivação"),
}


def _load(kind: str) -> str:
    file_name, key, _label = _KINDS[kind]
    with open(_DATA / file_name, encoding="utf-8") as handle:
        items = json.load(handle)[key]
    return random.choice(items)  # noqa: S311


@router.get("")
async def list_skills() -> dict:
    return {
        "skills": [
            {"id": kind, "endpoint": f"/api/skills/{kind}", "label": meta[2]}
            for kind, meta in _KINDS.items()
        ]
    }


@router.get("/{kind}")
async def get_skill(kind: str) -> dict:
    if kind not in _KINDS:
        raise HTTPException(status_code=404, detail="habilidade desconhecida")
    return {"skill": kind, "text": _load(kind)}
