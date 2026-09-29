"""Optional Local Reasoning Provider interface (Ollama/llama.cpp/local LLM)."""

from typing import Any
from qf_app.generation.generator import GeneratedQuestion


class LocalReasoningProvider:
    """Optional abstraction for local offline LLMs (e.g. Ollama).

    Disabled by default. System is 100% functional with deterministic templates.
    """

    def __init__(self, endpoint_url: str = "http://localhost:11434", model_name: str = "llama3") -> None:
        self.endpoint_url = endpoint_url
        self.model_name = model_name
        self.enabled = False

    async def generate_question(self, topic: str, context: str) -> GeneratedQuestion | None:
        """Optional local LLM question generation."""
        if not self.enabled:
            return None
        # Placeholder for optional local reasoning call
        return None
