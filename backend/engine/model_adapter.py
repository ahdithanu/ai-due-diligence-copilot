from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar, Union, Dict, Any, List
import json
import httpx
import asyncio
import logging
from pydantic import BaseModel

from backend.config import settings
from backend.domain.schemas import (
    ModelTaskType,
    ModelRoutingPolicy,
    ChaosSimulationConfig,
    CircuitBreakerStatus,
)

T = TypeVar("T", bound=BaseModel)


def _clean_json_string(text: str) -> str:
    """
    Remove markdown code block backticks if present around JSON response text.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


class ModelAdapter(ABC):
    """
    Abstract LLM Provider Abstraction interface.
    Supports text generation and structured response output using Pydantic models.
    """

    def __init__(self, model_name: str = "mock-llm", provider_name: str = "generic"):
        self.model_name = model_name
        self.provider_name = provider_name
        self.last_token_usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_model: Optional[Type[T]] = None,
        **kwargs: Any
    ) -> Union[str, T]:
        """
        Generate a text response or structured response model from prompt.
        """
        pass

    def get_last_token_usage(self) -> Dict[str, int]:
        return self.last_token_usage


class GeminiModelAdapter(ModelAdapter):
    """
    Live LLM Provider Adapter for Google Gemini API via httpx.AsyncClient.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-1.5-pro",
        timeout: float = 60.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        super().__init__(model_name=model_name, provider_name="gemini")
        self.api_key = api_key
        self.timeout = timeout
        self.http_client = http_client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_model: Optional[Type[T]] = None,
        **kwargs: Any
    ) -> Union[str, T]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        payload: Dict[str, Any] = {"contents": contents}

        if system_prompt:
            payload["system_instruction"] = {"parts": [{"text": system_prompt}]}

        generation_config: Dict[str, Any] = {}
        if response_model is not None:
            generation_config["response_mime_type"] = "application/json"
            try:
                generation_config["response_schema"] = response_model.model_json_schema()
            except Exception:
                pass

            schema_str = json.dumps(response_model.model_json_schema())
            prompt_with_schema = f"{prompt}\n\nRespond with a valid JSON object adhering strictly to this JSON schema:\n{schema_str}"
            contents[0]["parts"][0]["text"] = prompt_with_schema

        if generation_config:
            payload["generationConfig"] = generation_config

        client = kwargs.get("http_client") or self.http_client
        if client is not None:
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
        else:
            async with httpx.AsyncClient(timeout=self.timeout) as async_client:
                response = await async_client.post(url, json=payload, headers={"Content-Type": "application/json"})

        response.raise_for_status()
        data = response.json()

        usage = data.get("usageMetadata", {})
        self.last_token_usage = {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens": usage.get("totalTokenCount", 0),
        }

        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates returned from Gemini API")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise ValueError("No text parts returned from Gemini API")

        raw_text = parts[0].get("text", "")

        if response_model is not None:
            cleaned_json = _clean_json_string(raw_text)
            return response_model.model_validate_json(cleaned_json)

        return raw_text


class OpenAIModelAdapter(ModelAdapter):
    """
    Live LLM Provider Adapter for OpenAI API via httpx.AsyncClient.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o",
        timeout: float = 60.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        super().__init__(model_name=model_name, provider_name="openai")
        self.api_key = api_key
        self.timeout = timeout
        self.http_client = http_client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_model: Optional[Type[T]] = None,
        **kwargs: Any
    ) -> Union[str, T]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        user_content = prompt
        if response_model is not None:
            schema_str = json.dumps(response_model.model_json_schema())
            user_content = f"{prompt}\n\nRespond with a valid JSON object adhering strictly to this JSON schema:\n{schema_str}"

        messages.append({"role": "user", "content": user_content})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
        }

        if response_model is not None:
            payload["response_format"] = {"type": "json_object"}

        client = kwargs.get("http_client") or self.http_client
        if client is not None:
            response = await client.post(url, json=payload, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=self.timeout) as async_client:
                response = await async_client.post(url, json=payload, headers=headers)

        response.raise_for_status()
        data = response.json()

        usage = data.get("usage", {})
        self.last_token_usage = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("No choices returned from OpenAI API")

        raw_text = choices[0].get("message", {}).get("content", "")

        if response_model is not None:
            cleaned_json = _clean_json_string(raw_text)
            return response_model.model_validate_json(cleaned_json)

        return raw_text


class MockModelAdapter(ModelAdapter):
    """
    Mock LLM Adapter for deterministic graph execution and offline testing.
    Can return registered canned Pydantic objects or text responses.
    """

    def __init__(self, model_name: str = "mock-gpt-4o"):
        super().__init__(model_name=model_name, provider_name="mock")
        self.custom_responses: Dict[Any, Any] = {}
        self.call_history: List[Dict[str, Any]] = []
        self.default_evaluation_pass: bool = True
        self.default_evaluation_scores: Dict[str, float] = {
            "evidence_coverage_score": 0.85,
            "citation_correctness_score": 0.90,
            "logical_consistency_score": 0.88,
            "financial_correctness_score": 0.92,
            "completeness_score": 0.85,
        }

    def register_response(self, key: Any, response: Any):
        """
        Register a specific response for a key (can be a response_model class or string key).
        """
        self.custom_responses[key] = response

    def set_evaluation_behavior(self, overall_pass: bool, scores: Optional[Dict[str, float]] = None):
        """
        Configure mock evaluation results for AgentEvaluationResult generation.
        """
        self.default_evaluation_pass = overall_pass
        if scores:
            self.default_evaluation_scores.update(scores)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_model: Optional[Type[T]] = None,
        **kwargs: Any
    ) -> Union[str, T]:
        prompt_tokens = len(prompt.split()) + (len(system_prompt.split()) if system_prompt else 0)

        self.call_history.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "response_model": response_model.__name__ if response_model else None,
            "kwargs": kwargs
        })

        if response_model is not None:
            origin = getattr(response_model, "__origin__", None)
            if origin is list or response_model is list:
                self.last_token_usage = {"prompt_tokens": prompt_tokens, "completion_tokens": 50, "total_tokens": prompt_tokens + 50}
                return []
            if origin is dict or response_model is dict:
                self.last_token_usage = {"prompt_tokens": prompt_tokens, "completion_tokens": 50, "total_tokens": prompt_tokens + 50}
                return {}

            if response_model in self.custom_responses:
                resp = self.custom_responses[response_model]
                if callable(resp):
                    result = resp(prompt)
                else:
                    result = resp
            elif getattr(response_model, "__name__", "") == "AgentEvaluationResult":
                from backend.domain.schemas import AgentEvaluationResult
                result = AgentEvaluationResult(
                    evaluator_name="MockCriticEvaluator",
                    target_node="AnalystGenerator",
                    overall_pass=self.default_evaluation_pass,
                    critique_feedback=[] if self.default_evaluation_pass else ["Insufficient evidence citation for market size claim.", "Financial revenue growth calculation lacks supporting chunk reference."],
                    **self.default_evaluation_scores
                )
            elif getattr(response_model, "__name__", "") == "SpecialistAnalysis":
                from backend.domain.schemas import SpecialistAnalysis, ClaimNode, ClaimType, MaterialityLevel
                result = SpecialistAnalysis(
                    domain="Financial",
                    summary="Company shows strong ARR growth of 120% YoY, reaching $5.2M ARR in Q4 2024.",
                    claims=[
                        ClaimNode(
                            text="ARR grew 120% YoY to $5.2M",
                            claim_type=ClaimType.FACT,
                            materiality=MaterialityLevel.HIGH,
                            supporting_reasoning="Verified against financial statement doc."
                        )
                    ],
                    strengths=["High ARR growth rate", "Expanding gross margins (78%)"],
                    concerns=["High net burn rate ($400k/mo)"],
                    confidence_score=0.88,
                    iteration_count=1,
                    passed_evaluation=False
                )
            else:
                try:
                    result = response_model()
                except Exception:
                    fields = {}
                    model_fields = getattr(response_model, "model_fields", {})
                    for name, field in model_fields.items():
                        if field.annotation is str:
                            fields[name] = f"Mock {name}"
                        elif field.annotation is float or field.annotation is Optional[float]:
                            fields[name] = 0.9
                        elif field.annotation is int or field.annotation is Optional[int]:
                            fields[name] = 1
                        elif field.annotation is bool:
                            fields[name] = True
                    result = response_model(**fields)

            completion_tokens = 150
            self.last_token_usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
            return result

        if prompt in self.custom_responses:
            res_text = str(self.custom_responses[prompt])
        else:
            res_text = f"Mock LLM response for: {prompt[:50]}..."

        completion_tokens = len(res_text.split())
        self.last_token_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
        return res_text


DEFAULT_TASK_POLICIES: Dict[ModelTaskType, ModelRoutingPolicy] = {
    ModelTaskType.FAST_EXTRACTION: ModelRoutingPolicy(
        primary_provider="gemini",
        primary_model="gemini-1.5-flash",
        fallback_provider="openai",
        fallback_model="gpt-4o-mini",
        timeout_seconds=15.0,
        max_retries=2,
        circuit_breaker_threshold=3,
    ),
    ModelTaskType.DETERMINISTIC_MATH: ModelRoutingPolicy(
        primary_provider="gemini",
        primary_model="gemini-1.5-pro",
        fallback_provider="openai",
        fallback_model="gpt-4o",
        timeout_seconds=30.0,
        max_retries=3,
        circuit_breaker_threshold=3,
    ),
    ModelTaskType.REASONING_SYNTHESIS: ModelRoutingPolicy(
        primary_provider="gemini",
        primary_model="gemini-1.5-pro",
        fallback_provider="openai",
        fallback_model="gpt-4o",
        timeout_seconds=45.0,
        max_retries=3,
        circuit_breaker_threshold=3,
    ),
    ModelTaskType.CRITIC_AUDIT: ModelRoutingPolicy(
        primary_provider="openai",
        primary_model="gpt-4o",
        fallback_provider="gemini",
        fallback_model="gemini-1.5-pro",
        timeout_seconds=45.0,
        max_retries=3,
        circuit_breaker_threshold=3,
    ),
}


class RoutedModelAdapter(ModelAdapter):
    """
    Model Routing & Circuit Breaker Adapter.
    Wraps primary adapter (GeminiModelAdapter, OpenAIModelAdapter, or MockModelAdapter) and fallback adapter.
    Inspects task type or chaos simulation configuration (backend/services/failure_lab_service.py).
    On exception or chaos trigger (Rate Limit 429, Timeout, Schema corruption), records failure, updates circuit breaker,
    logs failover event, and executes fallback adapter seamlessly.
    """

    def __init__(
        self,
        primary_adapter: Optional[ModelAdapter] = None,
        fallback_adapter: Optional[ModelAdapter] = None,
        routing_policy: Optional[ModelRoutingPolicy] = None,
        task_type: Optional[ModelTaskType] = None,
        primary_provider: Optional[str] = None,
        fallback_provider: Optional[str] = None,
        model_name: str = "routed-llm",
    ):
        super().__init__(model_name=model_name, provider_name="routed")
        self.task_type = task_type

        if routing_policy is not None:
            self.policy = routing_policy
        elif task_type is not None and task_type in DEFAULT_TASK_POLICIES:
            self.policy = DEFAULT_TASK_POLICIES[task_type]
        else:
            self.policy = ModelRoutingPolicy(
                primary_provider="gemini",
                primary_model="gemini-1.5-pro",
                fallback_provider="mock",
                fallback_model="mock-llm",
                timeout_seconds=30.0,
                max_retries=3,
                circuit_breaker_threshold=3,
            )

        if primary_adapter is not None:
            self.primary_adapter = primary_adapter
            self.primary_provider = primary_provider or getattr(primary_adapter, "provider_name", self.policy.primary_provider)
        else:
            self.primary_provider = primary_provider or self.policy.primary_provider
            self.primary_adapter = get_model_adapter(
                provider=self.primary_provider,
                model_name=self.policy.primary_model,
            )

        if fallback_adapter is not None:
            self.fallback_adapter = fallback_adapter
            self.fallback_provider = fallback_provider or getattr(fallback_adapter, "provider_name", self.policy.fallback_provider)
        else:
            self.fallback_provider = fallback_provider or self.policy.fallback_provider
            self.fallback_adapter = get_model_adapter(
                provider=self.fallback_provider,
                model_name=self.policy.fallback_model,
            )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_model: Optional[Type[T]] = None,
        **kwargs: Any
    ) -> Union[str, T]:
        from backend.services.failure_lab_service import (
            get_chaos_config,
            get_circuit_breakers,
            record_provider_failure,
            record_provider_success,
        )

        logger = logging.getLogger("RoutedModelAdapter")
        chaos_config = get_chaos_config()
        target_node = kwargs.get("node_name") or kwargs.get("target_node")

        node_matches = (
            chaos_config.target_node is None
            or (target_node is not None and str(target_node).lower() == chaos_config.target_node.lower())
        )

        # 1. Chaos Latency Injection
        if node_matches and chaos_config.inject_latency_ms > 0:
            logger.info(f"Injecting chaos latency: {chaos_config.inject_latency_ms}ms")
            await asyncio.sleep(chaos_config.inject_latency_ms / 1000.0)

        # 2. Check Circuit Breaker Status for Primary Provider
        circuit_breakers = get_circuit_breakers()
        primary_cb = circuit_breakers.get(self.primary_provider.lower())
        primary_circuit_open = primary_cb is not None and primary_cb.state == "OPEN"

        primary_failed = False
        failure_reason = ""

        if primary_circuit_open:
            logger.warning(
                f"Circuit breaker for primary provider '{self.primary_provider}' is OPEN. "
                f"Bypassing primary and failing over to fallback '{self.fallback_provider}'."
            )
            primary_failed = True
            failure_reason = f"Circuit breaker OPEN for provider '{self.primary_provider}'"
        else:
            # 3. Chaos Rate Limit Injection BEFORE primary execution
            if node_matches and chaos_config.inject_rate_limit:
                primary_failed = True
                failure_reason = "Rate Limit 429 (Chaos Injected)"
                logger.warning(f"Primary provider '{self.primary_provider}' chaos rate limit triggered.")
            else:
                try:
                    timeout_val = self.policy.timeout_seconds
                    if timeout_val > 0:
                        res = await asyncio.wait_for(
                            self.primary_adapter.generate(
                                prompt, system_prompt=system_prompt, response_model=response_model, **kwargs
                            ),
                            timeout=timeout_val,
                        )
                    else:
                        res = await self.primary_adapter.generate(
                            prompt, system_prompt=system_prompt, response_model=response_model, **kwargs
                        )

                    # 4. Chaos Schema Corruption Injection AFTER call
                    if node_matches and chaos_config.inject_schema_corruption:
                        primary_failed = True
                        failure_reason = "Schema Corruption (Chaos Injected)"
                        logger.warning(f"Primary provider '{self.primary_provider}' chaos schema corruption triggered.")
                    else:
                        # Primary succeeded cleanly
                        record_provider_success(self.primary_provider)
                        self.last_token_usage = self.primary_adapter.get_last_token_usage()
                        return res

                except asyncio.TimeoutError:
                    primary_failed = True
                    failure_reason = f"Timeout after {self.policy.timeout_seconds}s"
                    logger.warning(f"Primary provider '{self.primary_provider}' timed out.")
                except Exception as e:
                    primary_failed = True
                    failure_reason = str(e)
                    logger.warning(f"Primary provider '{self.primary_provider}' failed with error: {e}")

        # Primary failed or circuit was open -> failover to fallback
        if primary_failed:
            record_provider_failure(self.primary_provider, threshold=self.policy.circuit_breaker_threshold)
            logger.info(
                f"[FAILOVER EVENT] Primary provider '{self.primary_provider}' failed ({failure_reason}). "
                f"Executing fallback provider '{self.fallback_provider}'."
            )

            try:
                res = await self.fallback_adapter.generate(
                    prompt, system_prompt=system_prompt, response_model=response_model, **kwargs
                )
                record_provider_success(self.fallback_provider)
                self.last_token_usage = self.fallback_adapter.get_last_token_usage()
                return res
            except Exception as fallback_err:
                record_provider_failure(self.fallback_provider, threshold=self.policy.circuit_breaker_threshold)
                logger.error(
                    f"Fallback provider '{self.fallback_provider}' failed with error: {fallback_err}"
                )
                raise RuntimeError(
                    f"Both primary ('{self.primary_provider}') and fallback ('{self.fallback_provider}') adapters failed. "
                    f"Primary error: {failure_reason}. Fallback error: {fallback_err}"
                ) from fallback_err


def get_model_adapter(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    task_type: Optional[ModelTaskType] = None,
    routing_policy: Optional[ModelRoutingPolicy] = None,
    routed: bool = False,
    **kwargs: Any,
) -> ModelAdapter:
    """
    Model Factory function for returning configured ModelAdapter.
    If task_type or routing_policy is provided or routed=True, returns RoutedModelAdapter.
    Defaults to settings.LLM_PROVIDER and settings.LLM_API_KEY.
    Returns GeminiModelAdapter for "gemini", OpenAIModelAdapter for "openai",
    and MockModelAdapter for "mock" or when no API key is set.
    """
    if routed or task_type is not None or routing_policy is not None:
        return RoutedModelAdapter(
            task_type=task_type,
            routing_policy=routing_policy,
            **kwargs
        )

    eff_provider = provider if provider is not None else settings.LLM_PROVIDER
    eff_api_key = api_key if api_key is not None else settings.LLM_API_KEY

    p_norm = (eff_provider or "").lower().strip()
    key_norm = (eff_api_key or "").strip()

    if p_norm == "gemini":
        if not key_norm:
            return MockModelAdapter(**kwargs)
        return GeminiModelAdapter(api_key=key_norm, **kwargs)
    elif p_norm == "openai":
        if not key_norm:
            return MockModelAdapter(**kwargs)
        return OpenAIModelAdapter(api_key=key_norm, **kwargs)
    else:
        return MockModelAdapter(**kwargs)
