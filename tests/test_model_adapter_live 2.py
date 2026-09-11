import pytest
import httpx
from pydantic import BaseModel
from typing import Optional

from backend.config import settings
from backend.engine.model_adapter import (
    ModelAdapter,
    MockModelAdapter,
    GeminiModelAdapter,
    OpenAIModelAdapter,
    get_model_adapter,
    _clean_json_string,
)


class DummyResponseModel(BaseModel):
    summary: str
    confidence_score: float
    is_valid: bool


def test_clean_json_string():
    raw_markdown = "```json\n{\"summary\": \"Test\", \"confidence_score\": 0.9, \"is_valid\": true}\n```"
    cleaned = _clean_json_string(raw_markdown)
    assert cleaned == "{\"summary\": \"Test\", \"confidence_score\": 0.9, \"is_valid\": true}"

    plain = "{\"foo\": \"bar\"}"
    assert _clean_json_string(plain) == plain


def test_get_model_adapter_factory():
    # 1. Test mock provider
    adapter = get_model_adapter(provider="mock")
    assert isinstance(adapter, MockModelAdapter)

    # 2. Test gemini with key
    adapter_gemini = get_model_adapter(provider="gemini", api_key="gemini-fake-key")
    assert isinstance(adapter_gemini, GeminiModelAdapter)
    assert adapter_gemini.api_key == "gemini-fake-key"
    assert adapter_gemini.model_name == "gemini-1.5-pro"

    # 3. Test gemini without key -> fallback to MockModelAdapter
    adapter_gemini_nokey = get_model_adapter(provider="gemini", api_key="")
    assert isinstance(adapter_gemini_nokey, MockModelAdapter)

    # 4. Test openai with key
    adapter_openai = get_model_adapter(provider="openai", api_key="sk-fake-key")
    assert isinstance(adapter_openai, OpenAIModelAdapter)
    assert adapter_openai.api_key == "sk-fake-key"
    assert adapter_openai.model_name == "gpt-4o"

    # 5. Test openai without key -> fallback to MockModelAdapter
    adapter_openai_nokey = get_model_adapter(provider="openai", api_key="")
    assert isinstance(adapter_openai_nokey, MockModelAdapter)

    # 6. Test default parameters (fallback to settings)
    adapter_default = get_model_adapter()
    if settings.LLM_PROVIDER == "gemini" and settings.LLM_API_KEY:
        assert isinstance(adapter_default, GeminiModelAdapter)
    elif settings.LLM_PROVIDER == "openai" and settings.LLM_API_KEY:
        assert isinstance(adapter_default, OpenAIModelAdapter)
    else:
        assert isinstance(adapter_default, MockModelAdapter)

    # 7. Unknown provider -> fallback to MockModelAdapter
    adapter_unknown = get_model_adapter(provider="unknown")
    assert isinstance(adapter_unknown, MockModelAdapter)


@pytest.mark.asyncio
async def test_gemini_model_adapter_text_generation():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "generativelanguage.googleapis.com" in str(request.url)
        assert "gemini-1.5-pro:generateContent" in str(request.url)
        assert "key=test-gemini-key" in str(request.url)
        payload = request.read().decode("utf-8")
        assert "System prompt test" in payload
        assert "User prompt test" in payload
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "Gemini generated text analysis"}]
                        }
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 25,
                    "candidatesTokenCount": 15,
                    "totalTokenCount": 40,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = GeminiModelAdapter(api_key="test-gemini-key", http_client=client)
        result = await adapter.generate(
            prompt="User prompt test", system_prompt="System prompt test"
        )
        assert result == "Gemini generated text analysis"
        assert adapter.get_last_token_usage() == {
            "prompt_tokens": 25,
            "completion_tokens": 15,
            "total_tokens": 40,
        }


@pytest.mark.asyncio
async def test_gemini_model_adapter_structured_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "```json\n{\"summary\": \"Strong growth\", \"confidence_score\": 0.92, \"is_valid\": true}\n```"
                                }
                            ]
                        }
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 50,
                    "candidatesTokenCount": 20,
                    "totalTokenCount": 70,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = GeminiModelAdapter(api_key="test-gemini-key", http_client=client)
        result = await adapter.generate(
            prompt="Analyze financials", response_model=DummyResponseModel
        )
        assert isinstance(result, DummyResponseModel)
        assert result.summary == "Strong growth"
        assert result.confidence_score == 0.92
        assert result.is_valid is True
        assert adapter.get_last_token_usage() == {
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "total_tokens": 70,
        }


@pytest.mark.asyncio
async def test_openai_model_adapter_text_generation():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.openai.com/v1/chat/completions"
        assert request.headers.get("Authorization") == "Bearer sk-test-openai-key"
        payload = request.read().decode("utf-8")
        assert "System prompt test" in payload
        assert "User prompt test" in payload
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "OpenAI generated text response"}
                    }
                ],
                "usage": {
                    "prompt_tokens": 30,
                    "completion_tokens": 10,
                    "total_tokens": 40,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = OpenAIModelAdapter(api_key="sk-test-openai-key", http_client=client)
        result = await adapter.generate(
            prompt="User prompt test", system_prompt="System prompt test"
        )
        assert result == "OpenAI generated text response"
        assert adapter.get_last_token_usage() == {
            "prompt_tokens": 30,
            "completion_tokens": 10,
            "total_tokens": 40,
        }


@pytest.mark.asyncio
async def test_openai_model_adapter_structured_response():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = request.read().decode("utf-8")
        assert '"response_format": {"type": "json_object"}' in payload or '"json_object"' in payload
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "{\"summary\": \"OpenAI Analysis\", \"confidence_score\": 0.88, \"is_valid\": true}"
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 60,
                    "completion_tokens": 25,
                    "total_tokens": 85,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = OpenAIModelAdapter(api_key="sk-test-openai-key", http_client=client)
        result = await adapter.generate(
            prompt="Analyze diligence document", response_model=DummyResponseModel
        )
        assert isinstance(result, DummyResponseModel)
        assert result.summary == "OpenAI Analysis"
        assert result.confidence_score == 0.88
        assert result.is_valid is True
        assert adapter.get_last_token_usage() == {
            "prompt_tokens": 60,
            "completion_tokens": 25,
            "total_tokens": 85,
        }
