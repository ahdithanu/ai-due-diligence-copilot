from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from backend.domain.schemas import ChaosSimulationConfig, CircuitBreakerStatus, ModelTaskType, ModelRoutingPolicy
from backend.services.failure_lab_service import (
    get_chaos_config,
    set_chaos_config,
    reset_chaos_config,
    get_circuit_breakers,
    reset_circuit_breakers,
    record_provider_failure,
    record_provider_success,
)
from backend.engine.model_adapter import DEFAULT_TASK_POLICIES

router = APIRouter(prefix="/failure-lab", tags=["Failure Lab"])

@router.get("/status")
async def get_failure_lab_status():
    """
    Returns current circuit breaker states and active chaos simulation configuration.
    """
    cbs = get_circuit_breakers()
    for provider in ["gemini", "openai", "mock"]:
        if provider not in cbs:
            cbs[provider] = CircuitBreakerStatus(provider=provider, state="CLOSED", failure_count=0)
    return {
        "circuit_breakers": cbs,
        "chaos_config": get_chaos_config(),
    }

@router.get("/config", response_model=ChaosSimulationConfig)
async def get_config():
    return get_chaos_config()

@router.post("/simulate", response_model=ChaosSimulationConfig)
async def trigger_simulation(config: ChaosSimulationConfig):
    return set_chaos_config(config)

@router.post("/reset", response_model=Dict[str, Any])
async def reset_lab():
    cfg = reset_chaos_config()
    cbs = reset_circuit_breakers()
    return {
        "status": "reset",
        "chaos_config": cfg,
        "circuit_breakers": cbs
    }

@router.get("/circuit-breakers", response_model=Dict[str, CircuitBreakerStatus])
async def list_circuit_breakers():
    cbs = get_circuit_breakers()
    for provider in ["gemini", "openai", "mock"]:
        if provider not in cbs:
            cbs[provider] = CircuitBreakerStatus(provider=provider, state="CLOSED", failure_count=0)
    return cbs

@router.post("/circuit-breakers/trip/{provider}", response_model=CircuitBreakerStatus)
async def trip_circuit_breaker(provider: str):
    cb = record_provider_failure(provider, threshold=1)
    cb.state = "OPEN"
    return cb

@router.post("/circuit-breakers/reset/{provider}", response_model=CircuitBreakerStatus)
async def reset_provider_circuit_breaker(provider: str):
    return record_provider_success(provider)

@router.get("/matrix")
async def get_routing_matrix():
    return {
        task_type.value if hasattr(task_type, "value") else str(task_type): policy.model_dump()
        for task_type, policy in DEFAULT_TASK_POLICIES.items()
    }
