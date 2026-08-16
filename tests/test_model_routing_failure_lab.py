import pytest
import asyncio
from fastapi.testclient import TestClient

from backend.main import app
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
    DEFAULT_TASK_POLICIES,
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


# ---------------------------------------------------------------------------
# 1. Test RoutedModelAdapter Task-based Model Selection
# ---------------------------------------------------------------------------
def test_task_based_model_selection():
    """Test task-based model selection for each ModelTaskType."""
    # FAST_EXTRACTION -> Gemini 1.5 Flash primary, OpenAI GPT-4o mini fallback
    fast_adapter = get_model_adapter(task_type=ModelTaskType.FAST_EXTRACTION)
    assert isinstance(fast_adapter, RoutedModelAdapter)
    assert fast_adapter.policy.primary_provider == "gemini"
    assert fast_adapter.policy.primary_model == "gemini-1.5-flash"
    assert fast_adapter.policy.fallback_provider == "openai"
    assert fast_adapter.policy.fallback_model == "gpt-4o-mini"

    # DETERMINISTIC_MATH -> Gemini 1.5 Pro primary, OpenAI GPT-4o fallback
    math_adapter = get_model_adapter(task_type=ModelTaskType.DETERMINISTIC_MATH)
    assert isinstance(math_adapter, RoutedModelAdapter)
    assert math_adapter.policy.primary_provider == "gemini"
    assert math_adapter.policy.primary_model == "gemini-1.5-pro"
    assert math_adapter.policy.fallback_provider == "openai"
    assert math_adapter.policy.fallback_model == "gpt-4o"

    # REASONING_SYNTHESIS -> Gemini 1.5 Pro primary, OpenAI GPT-4o fallback
    reasoning_adapter = get_model_adapter(task_type=ModelTaskType.REASONING_SYNTHESIS)
    assert isinstance(reasoning_adapter, RoutedModelAdapter)
    assert reasoning_adapter.policy.primary_provider == "gemini"
    assert reasoning_adapter.policy.primary_model == "gemini-1.5-pro"

    # CRITIC_AUDIT -> OpenAI GPT-4o primary, Gemini 1.5 Pro fallback
    critic_adapter = get_model_adapter(task_type=ModelTaskType.CRITIC_AUDIT)
    assert isinstance(critic_adapter, RoutedModelAdapter)
    assert critic_adapter.policy.primary_provider == "openai"
    assert critic_adapter.policy.primary_model == "gpt-4o"
    assert critic_adapter.policy.fallback_provider == "gemini"
    assert critic_adapter.policy.fallback_model == "gemini-1.5-pro"


# ---------------------------------------------------------------------------
# 2. Test Automatic Failover when Primary Provider Returns Error / Chaos Injection
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_automatic_failover_on_primary_error():
    """Test automatic failover to fallback adapter when primary raises an exception."""
    primary = FailingModelAdapter(provider_name="primary_error_provider")
    fallback = MockModelAdapter(model_name="fallback-mock")
    fallback.provider_name = "fallback_ok_provider"

    adapter = RoutedModelAdapter(
        primary_adapter=primary,
        fallback_adapter=fallback,
        primary_provider="primary_error_provider",
        fallback_provider="fallback_ok_provider",
    )

    response = await adapter.generate("Test prompt for failover")
    assert "Mock LLM response" in response
    assert len(fallback.call_history) == 1

    cbs = get_circuit_breakers()
    assert "primary_error_provider" in cbs
    assert cbs["primary_error_provider"].failure_count == 1


@pytest.mark.asyncio
async def test_automatic_failover_on_chaos_rate_limit():
    """Test automatic failover when chaos rate limit is enabled."""
    primary = MockModelAdapter(model_name="primary-mock")
    primary.provider_name = "primary_rate_limited"
    fallback = MockModelAdapter(model_name="fallback-mock")
    fallback.provider_name = "fallback_ok"

    adapter = RoutedModelAdapter(
        primary_adapter=primary,
        fallback_adapter=fallback,
        primary_provider="primary_rate_limited",
        fallback_provider="fallback_ok",
    )

    set_chaos_config(ChaosSimulationConfig(inject_rate_limit=True))

    response = await adapter.generate("Test prompt under rate limit chaos")
    assert "Mock LLM response" in response
    assert len(primary.call_history) == 0  # Primary was skipped
    assert len(fallback.call_history) == 1

    cbs = get_circuit_breakers()
    assert "primary_rate_limited" in cbs
    assert cbs["primary_rate_limited"].failure_count == 1


@pytest.mark.asyncio
async def test_automatic_failover_on_chaos_schema_corruption():
    """Test automatic failover when chaos schema corruption is enabled."""
    primary = MockModelAdapter(model_name="primary-mock")
    primary.provider_name = "primary_corrupt"
    fallback = MockModelAdapter(model_name="fallback-mock")
    fallback.provider_name = "fallback_ok"

    adapter = RoutedModelAdapter(
        primary_adapter=primary,
        fallback_adapter=fallback,
        primary_provider="primary_corrupt",
        fallback_provider="fallback_ok",
    )

    set_chaos_config(ChaosSimulationConfig(inject_schema_corruption=True))

    response = await adapter.generate("Test prompt under schema corruption chaos")
    assert "Mock LLM response" in response
    assert len(primary.call_history) == 1  # Primary ran but failed post-check
    assert len(fallback.call_history) == 1

    cbs = get_circuit_breakers()
    assert "primary_corrupt" in cbs
    assert cbs["primary_corrupt"].failure_count == 1


# ---------------------------------------------------------------------------
# 3. Test Circuit Breaker State Transitions (CLOSED -> OPEN)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_circuit_breaker_state_transitions():
    """Test circuit breaker transitions from CLOSED to OPEN after consecutive failures."""
    primary = FailingModelAdapter(provider_name="unstable_node")
    fallback = MockModelAdapter(model_name="fallback-mock")
    fallback.provider_name = "reliable_node"

    policy = ModelRoutingPolicy(
        primary_provider="unstable_node",
        primary_model="model1",
        fallback_provider="reliable_node",
        fallback_model="model2",
        circuit_breaker_threshold=3,
    )

    adapter = RoutedModelAdapter(
        primary_adapter=primary,
        fallback_adapter=fallback,
        routing_policy=policy,
    )

    # Initially CLOSED
    cbs = get_circuit_breakers()
    assert "unstable_node" not in cbs or cbs["unstable_node"].state == "CLOSED"

    # Call 1 -> failure 1 (CLOSED)
    await adapter.generate("Invocation 1")
    cbs = get_circuit_breakers()
    assert cbs["unstable_node"].failure_count == 1
    assert cbs["unstable_node"].state == "CLOSED"

    # Call 2 -> failure 2 (CLOSED)
    await adapter.generate("Invocation 2")
    cbs = get_circuit_breakers()
    assert cbs["unstable_node"].failure_count == 2
    assert cbs["unstable_node"].state == "CLOSED"

    # Call 3 -> failure 3 -> Trips to OPEN
    await adapter.generate("Invocation 3")
    cbs = get_circuit_breakers()
    assert cbs["unstable_node"].failure_count == 3
    assert cbs["unstable_node"].state == "OPEN"

    # Call 4 -> Since circuit is OPEN, primary is bypassed completely
    fallback_calls_before = len(fallback.call_history)
    response = await adapter.generate("Invocation 4")
    assert "Mock LLM response" in response
    assert len(fallback.call_history) == fallback_calls_before + 1

    # Reset circuit breakers restores CLOSED state
    reset_circuit_breakers()
    cbs = get_circuit_breakers()
    assert "unstable_node" not in cbs or cbs["unstable_node"].state == "CLOSED"


# ---------------------------------------------------------------------------
# 4. Test Chaos Simulation API Endpoints (GET /status, POST /simulate, POST /reset)
# ---------------------------------------------------------------------------
def test_chaos_simulation_api_endpoints():
    """Test API endpoints GET /status, POST /simulate, POST /reset."""
    client = TestClient(app)

    # 1. GET /api/v1/failure-lab/status
    res_status = client.get("/api/v1/failure-lab/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "circuit_breakers" in data_status
    assert "chaos_config" in data_status
    assert data_status["chaos_config"]["inject_rate_limit"] is False

    # 2. POST /api/v1/failure-lab/simulate
    simulate_payload = {
        "inject_rate_limit": True,
        "inject_latency_ms": 250,
        "inject_schema_corruption": True,
        "target_node": "AnalystGenerator",
    }
    res_simulate = client.post("/api/v1/failure-lab/simulate", json=simulate_payload)
    assert res_simulate.status_code == 200
    data_simulate = res_simulate.json()
    assert data_simulate["inject_rate_limit"] is True
    assert data_simulate["inject_latency_ms"] == 250
    assert data_simulate["inject_schema_corruption"] is True
    assert data_simulate["target_node"] == "AnalystGenerator"

    # Verify active chaos config in service and GET /status
    active_config = get_chaos_config()
    assert active_config.inject_rate_limit is True
    assert active_config.inject_latency_ms == 250

    res_status_updated = client.get("/api/v1/failure-lab/status")
    assert res_status_updated.status_code == 200
    assert res_status_updated.json()["chaos_config"]["inject_rate_limit"] is True

    # 3. POST /api/v1/failure-lab/reset
    res_reset = client.post("/api/v1/failure-lab/reset")
    assert res_reset.status_code == 200
    data_reset = res_reset.json()
    assert data_reset["status"] == "reset"
    assert data_reset["chaos_config"]["inject_rate_limit"] is False

    # Verify service state reset
    reset_config = get_chaos_config()
    assert reset_config.inject_rate_limit is False
    assert reset_config.inject_latency_ms == 0
    assert reset_config.inject_schema_corruption is False
