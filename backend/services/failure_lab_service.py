from datetime import datetime, timezone
from typing import Dict, Optional, Any, Union
from backend.domain.schemas import ChaosSimulationConfig, CircuitBreakerStatus


class FailureLabService:
    """
    Failure Lab Service managing global/deployment chaos simulation rules
    and provider circuit breaker state dictionary.
    """

    _chaos_config: ChaosSimulationConfig = ChaosSimulationConfig()
    _circuit_breakers: Dict[str, CircuitBreakerStatus] = {}

    @classmethod
    def get_chaos_config(cls) -> ChaosSimulationConfig:
        """
        Get current chaos simulation configuration.
        """
        return cls._chaos_config

    @classmethod
    def set_chaos_config(
        cls, config: Union[ChaosSimulationConfig, Dict[str, Any]]
    ) -> ChaosSimulationConfig:
        """
        Set or update chaos simulation configuration.
        """
        if isinstance(config, dict):
            cls._chaos_config = ChaosSimulationConfig(**config)
        elif isinstance(config, ChaosSimulationConfig):
            cls._chaos_config = config
        else:
            raise ValueError("Config must be a ChaosSimulationConfig instance or dict")
        return cls._chaos_config

    @classmethod
    def reset_chaos_config(cls) -> ChaosSimulationConfig:
        """
        Reset chaos simulation configuration to default (all disabled).
        """
        cls._chaos_config = ChaosSimulationConfig()
        return cls._chaos_config

    @classmethod
    def get_circuit_breakers(cls) -> Dict[str, CircuitBreakerStatus]:
        """
        Get all provider circuit breaker statuses.
        """
        return cls._circuit_breakers

    @classmethod
    def record_provider_failure(
        cls, provider: str, threshold: int = 3
    ) -> CircuitBreakerStatus:
        """
        Record a failure for a given provider.
        If failure count reaches or exceeds threshold, transition state to OPEN.
        """
        key = provider.lower().strip()
        if key not in cls._circuit_breakers:
            cls._circuit_breakers[key] = CircuitBreakerStatus(
                provider=key,
                state="CLOSED",
                failure_count=0,
                last_failure_timestamp=None,
            )

        cb = cls._circuit_breakers[key]
        cb.failure_count += 1
        cb.last_failure_timestamp = datetime.now(timezone.utc)

        if cb.failure_count >= threshold:
            cb.state = "OPEN"

        return cb

    @classmethod
    def record_provider_success(cls, provider: str) -> CircuitBreakerStatus:
        """
        Record a success for a given provider.
        Resets failure count to 0 and state to CLOSED.
        """
        key = provider.lower().strip()
        if key not in cls._circuit_breakers:
            cls._circuit_breakers[key] = CircuitBreakerStatus(
                provider=key,
                state="CLOSED",
                failure_count=0,
                last_failure_timestamp=None,
            )

        cb = cls._circuit_breakers[key]
        cb.failure_count = 0
        cb.state = "CLOSED"
        return cb

    @classmethod
    def reset_circuit_breakers(cls) -> Dict[str, CircuitBreakerStatus]:
        """
        Reset all circuit breakers to empty state.
        """
        cls._circuit_breakers.clear()
        return cls._circuit_breakers


# Module-level convenience function aliases
def get_chaos_config() -> ChaosSimulationConfig:
    return FailureLabService.get_chaos_config()


def set_chaos_config(
    config: Union[ChaosSimulationConfig, Dict[str, Any]]
) -> ChaosSimulationConfig:
    return FailureLabService.set_chaos_config(config)


def reset_chaos_config() -> ChaosSimulationConfig:
    return FailureLabService.reset_chaos_config()


def get_circuit_breakers() -> Dict[str, CircuitBreakerStatus]:
    return FailureLabService.get_circuit_breakers()


def record_provider_failure(
    provider: str, threshold: int = 3
) -> CircuitBreakerStatus:
    return FailureLabService.record_provider_failure(provider, threshold)


def record_provider_success(provider: str) -> CircuitBreakerStatus:
    return FailureLabService.record_provider_success(provider)


def reset_circuit_breakers() -> Dict[str, CircuitBreakerStatus]:
    return FailureLabService.reset_circuit_breakers()
