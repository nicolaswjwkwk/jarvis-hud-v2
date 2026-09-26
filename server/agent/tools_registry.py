from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ToolMeta:
    name: str
    description: str
    handler: Any


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolMeta] = {}

    def register(self, name: str, description: str, handler: Any) -> None:
        self._tools[name] = ToolMeta(name=name, description=description, handler=handler)

    def get(self, name: str) -> ToolMeta | None:
        return self._tools.get(name)

    def list(self) -> List[Dict[str, str]]:
        return [{'name': item.name, 'description': item.description} for item in self._tools.values()]


TOOL_REGISTRY = ToolRegistry()


def register_builtin_tools() -> None:
    TOOL_REGISTRY.register('web_search', 'Search externally for current facts', lambda q: {'ok': True, 'query': q})
    TOOL_REGISTRY.register('memory_read', 'Read persisted memory', lambda q: {'ok': True, 'query': q})
    TOOL_REGISTRY.register('memory_write', 'Write a note to memory', lambda q: {'ok': True, 'query': q})
    TOOL_REGISTRY.register('send_whatsapp', 'Send a WhatsApp outbound message', lambda q: {'ok': True, 'query': q})


register_builtin_tools()
