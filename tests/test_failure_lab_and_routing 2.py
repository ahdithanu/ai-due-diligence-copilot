import pytest
import asyncio
from datetime import datetime
from backend.domain.schemas import (
    ModelTaskType,
    ModelRoutingPolicy,
    ChaosSimulationConfig,
    CircuitBreakerStatus,
)
from backend.services.failure_lab_service import (
    FailureLabService,
    get_chaos_config,
    set_chaos_config,
    reset_chaos_config,
    get_circuit_breakers,
    record_provider_failure,
    record_provider_success,
    reset_circuit_breakers,
)
from backend.engine.model_adapter import (
    MockModelAdapter,
    RoutedModelAdapter,
    get_model_adapter,
)


class FailingModelAdapter(MockModelAdapter):
    """A mock adapter that always raises an exception on generate."""

    def __init__(self, error_msg: str = "Primary Provider 500 Internal Error", provider_name: str = "failing_primary"):
        super().__init__(model_name="failing-model")
        self.provider_name = provider_name
        self.error_msg = error_msg

    async def generate(self, prompt: str, system_prompt=None, response_model=None, **kwargs):
        raise RuntimeError(self.error_msg)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset failure lab service state before each test."""
    reset_chaos_config()
    reset_circuit_breakers()
    yield
    reset_chaos_config()
    reset_circuit_breakers()


def test_schemas_instantiation():
    """Verify new domain schemas instantiate correctly."""
    assert ModelTaskType.FAST_EXTRACTION == "FAST_EXTRACTION"
    assert ModelTaskType.DETERMINISTIC_MATH == "DETERMINISTIC_MATH"
    assert ModelTaskType.REASONING_SYNTHESIS == "REASONING_SYNTHESIS"
    assert ModelTaskType.CRITIC_AUDIT == "CRITIC_AUDIT"

    policy = ModelRoutingPolicy(
        primary_provider="gemini",
        primary_model="gemini-1.5-pro",
        fallback_provider="openai",
        fallback_model="gpt-4o",
        timeout_seconds=20.0,
        max_retries=2,
        circuit_breaker_threshold=4,
    )
    assert policy.primary_provider == "gemini"
    assert policy.circuit_breaker_threshold == 4

    chaos = ChaosSimulationConfig(
        inject_rate_limit=True,
        inject_latency_ms=100,
        inject_schema_corruption=False,
        target_node="AnalystGenerator",
    )
    assert chaos.inject_rate_limit is True
    assert chaos.target_node == "AnalystGenerator"

    cb = CircuitBreakerStatus(
        provider="gemini",
        state="CLOSED",
        failure_count=0,
    )
    assert cb.provider == "gemini"
    assert cb.state == "CLOSED"


def test_failure_lab_service():
    """Test FailureLabService operations."""
    # Default chaos config
    config = get_chaos_config()
    assert config.inject_rate_limit is False

    # Set chaos config
    new_config = set_chaos_config({"inject_rate_limit": True, "inject_latency_ms": 50})
    assert get_chaos_config().inject_rate_limit is True
    assert get_chaos_config().inject_latency_ms == 50

    # Reset chaos config
    reset_chaos_config()
    assert get_chaos_config().inject_rate_limit is False

    # Record failures
    cb1 = record_provider_failure("gemini", threshold=3)
    assert cb1.failure_count == 1
    assert cb1.state == "CLOSED"

    record_provider_failure("gemini", threshold=3)
    cb3 = record_provider_failure("gemini", threshold=3)
    assert cb3.failure_count == 3
    assert cb3.state == "OPEN"

    # Circuit breakers dictionary
    cbs = get_circuit_breakers()
    assert "gemini" in cbs
    assert cbs["gemini"].state == "OPEN"

    # Record success resets circuit breaker
    cb_succ = record_provider_success("gemini")
    assert cb_succ.failure_count == 0
    assert cb_succ.state == "CLOSED"


@pytest.mark.asyncio
async def test_routed_model_adapter_success():
    """Test RoutedModelAdapter normal primary execution path."""
    primary = MockModelAdapter(model_name="primary-mock")
    primary.provider_name = "primary_prov"
    fallback = MockModelAdapter(model_name="fallback-mock")
    fallback.provider_name = "fallback_prov"

    adapter = RoutedModelAdapter(
        primary_adapter=primary,
        fallback_adapter=fallback,
        primary_provider="primary_prov",
        fallback_provider="fallback_prov",
    )

    res = await adapter.generate("Test prompt")
    assert "Mock LLM response" in res
    assert len(primary.call_history) == 1
    assert len(fallback.call_history) == 0


@pytest.mark.asyncio
async def test_routed_model_adapter_failover():
    """Test RoutedModelAdapter failover when primary fails."""
    primary = FailingModelAdapter(provider_name="primary_failing")
    fallback = MockModelAdapter(model_name="fallback-mock")
    fallback.provider_name = "fallback_ok"

    adapter = RoutedModelAdapter(
        primary_adapter=primary,
        fallback_adapter=fallback,
        primary_provider="primary_failing",
        fallback_provider="fallback_ok",
    )

    res = await adapter.generate("Test failover prompt")
    assert "Mock LLM response" in res
    assert len(fallback.call_history) == 1

    cbs = get_circuit_breakers()
    assert "primary_failing" in cbs
    assert cbs["primary_failing"].failure_count == 1


@pytest.mark.asyncio
async def test_routed_model_adapter_circuit_breaker_open():
    """Test circuit breaker tripping to OPEN and bypassing primary directly."""
    primary = FailingModelAdapter(provider_name="unstable_primary")
    fallback = MockModelAdapter(model_name="fallback-mock")
    fallback.provider_name = "reliable_fallback"

    policy = ModelRoutingPolicy(
        primary_provider="unstable_primary",
        primary_model="model1",
        fallback_provider="reliable_fallback",
        fallback_model="model2",
        circuit_breaker_threshold=2,
    )

    adapter = RoutedModelAdapter(
        primary_adapter=primary,
        fallback_adapter=fallback,
        routing_policy=policy,
    )

    # 1st failure
    await adapter.generate("Call 1")
    # 2nd failure -> trips circuit breaker to OPEN
    await adapter.generate("Call 2")

    cbs = get_circuit_breakers()
    assert cbs["unstable_primary"].state == "OPEN"

    # 3rd call should bypass primary completely without calling primary.generate
    call_count_before = len(fallback.call_history)
    res = await adapter.generate("Call 3")
    assert "Mock LLM response" in res
    assert len(fallback.call_history) == call_count_before + 1


@pytest.mark.asyncio
async def test_routed_model_adapter_chaos_rate_limit():
    """Test chaos rate limit injection triggers failover."""
    primary = MockModelAdapter(model_name="primary-mock")
    primary.provider_name = "primary_prov"
    fallback = MockModelAdapter(model_name="fallback-mock")
    fallback.provider_name = "fallback_prov"

    adapter = RoutedModelAdapter(
        primary_adapter=primary,
        fallback_adapter=fallback,
        primary_provider="primary_prov",
        fallback_provider="fallback_prov",
    )

    set_chaos_config({"inject_rate_limit": True})

    res = await adapter.generate("Chaos test")
    assert "Mock LLM response" in res
    assert len(primary.call_history) == 0  # Primary skipped due to rate limit chaos
    assert len(fallback.call_history) == 1
