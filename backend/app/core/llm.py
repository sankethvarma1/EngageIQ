import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    usage: Optional[Dict[str, int]] = None


class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class NemotronProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(content="LLM not configured. Please set NEMOTRON_API_KEY.")

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")

            return LLMResponse(content=content, usage=usage)

        except Exception as e:
            return LLMResponse(content=f"LLM error: {str(e)}")


class MockProvider(LLMProvider):
    def is_available(self) -> bool:
        return True

    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        last_msg = messages[-1].content if messages else ""
        return LLMResponse(
            content=f"[Mock Response] I received your query: {last_msg[:100]}... "
            f"This is a simulated response. Configure NEMOTRON_API_KEY for real AI responses."
        )


def get_llm_provider() -> LLMProvider:
    api_key = os.getenv("NEMOTRON_API_KEY", "")
    base_url = os.getenv("NEMOTRON_BASE_URL", "https://integrate.api.nvidia.com/v1")
    model = os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")

    if api_key:
        return NemotronProvider(api_key, base_url, model)
    return MockProvider()