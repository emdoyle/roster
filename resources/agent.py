from typing import List

from .base import YamlResource


class AgentBackend(YamlResource):
    model: str


class AgentPrompt(YamlResource):
    strategy: str
    tools: List[str] = []


class AgentMemory(YamlResource):
    strategy: str


class Agent(YamlResource):
    backend: AgentBackend
    prompt: AgentPrompt
    memory: AgentMemory
