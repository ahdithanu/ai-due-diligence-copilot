"""
Tests for verify_ci_pipeline.py local CI/CD pipeline simulator and Docker/Compose container configuration files.
"""

import sys
import os
import subprocess
import pytest
from pathlib import Path

# Project root path resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.verify_ci_pipeline import (
    stage_1_python_lint_and_tests,
    stage_2_frontend_build,
    stage_3_docker_build_check,
    stage_4_acceptance_gate_audit,
    stage_5_canary_test_verification,
    run_ci_pipeline
)


def test_stage_1_python_lint_and_tests():
    """Verify Stage 1 (Python linting & Pytest suite execution)."""
    result = stage_1_python_lint_and_tests(verbose=False)
    assert result["stage"] == 1
    assert result["passed"] is True
    assert result["lint_passed"] is True
    assert result["tests_passed"] is True
    assert result["test_count"] >= 116


def test_stage_2_frontend_build():
    """Verify Stage 2 (Frontend TypeScript validation & build)."""
    result = stage_2_frontend_build(verbose=False)
    assert result["stage"] == 2
    assert result["passed"] is True
    assert result["build_passed"] is True
    assert result["dist_verified"] is True
    assert (PROJECT_ROOT / "frontend" / "dist" / "index.html").exists()


def test_stage_3_docker_build_check():
    """Verify Stage 3 (Docker container configuration & build check)."""
    # Test default mode (skip_docker=True to test static structural check)
    result = stage_3_docker_build_check(skip_docker=True, verbose=False)
    assert result["stage"] == 3
    assert result["passed"] is True
    assert len(result["dockerfiles_validated"]) == 3
    assert "Dockerfile.api" in result["dockerfiles_validated"]
    assert "Dockerfile.worker" in result["dockerfiles_validated"]
    assert "Dockerfile.frontend" in result["dockerfiles_validated"]


def test_stage_4_acceptance_gate_audit():
    """Verify Stage 4 (Deployment Acceptance Gate Audit)."""
    # Test valid deployment profile
    result = stage_4_acceptance_gate_audit(deployment_id="growth_saas_default", verbose=False)
    assert result["stage"] == 4
    assert result["passed"] is True
    assert result["status"] in ["READY", "READY_WITH_RISKS"]
    assert result["passed_checks"] >= 5

    # Test non-existent deployment profile audit handling
    bad_result = stage_4_acceptance_gate_audit(deployment_id="non_existent_profile_xyz", verbose=False)
    assert bad_result["stage"] == 4
    assert bad_result["passed"] is False
    assert bad_result["status"] == "NOT_READY"


def test_stage_5_canary_test_verification():
    """Verify Stage 5 (Synthetic Canary Test run & teardown)."""
    result = stage_5_canary_test_verification(verbose=False)
    assert result["stage"] == 5
    assert result["passed"] is True
    assert result["checkpoints_verified"] > 0
    assert result["teardown_successful"] is True
    assert result["canary_duration_ms"] > 0


def test_full_ci_pipeline_runner():
    """Verify run_ci_pipeline orchestrator for all stages and single stage."""
    # Test single stage execution
    stage1_success = run_ci_pipeline(stage="1", skip_docker=True, verbose=False)
    assert stage1_success is True

    # Test full pipeline execution
    all_success = run_ci_pipeline(stage="all", skip_docker=True, verbose=False)
    assert all_success is True

    # Test invalid stage error handling
    invalid_success = run_ci_pipeline(stage="99", skip_docker=True, verbose=False)
    assert invalid_success is False


def test_cli_execution():
    """Verify verify_ci_pipeline.py CLI script execution via subprocess."""
    cmd = [sys.executable, "scripts/verify_ci_pipeline.py", "--stage", "4", "--skip-docker"]
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Deployment Acceptance Gate Audit" in proc.stdout
    assert "OVERALL PIPELINE RESULT: PASSED" in proc.stdout


def test_dockerfile_api_configuration():
    """Validate structure and configuration of Dockerfile.api."""
    df_path = PROJECT_ROOT / "Dockerfile.api"
    assert df_path.exists()
    content = df_path.read_text()

    assert "FROM python:3.10-slim" in content
    assert "WORKDIR /app" in content
    assert "COPY requirements.txt pyproject.toml /app/" in content
    assert "EXPOSE 8000" in content
    assert "HEALTHCHECK" in content
    assert "uvicorn" in content


def test_dockerfile_worker_configuration():
    """Validate structure and configuration of Dockerfile.worker."""
    df_path = PROJECT_ROOT / "Dockerfile.worker"
    assert df_path.exists()
    content = df_path.read_text()

    assert "FROM python:3.10-slim" in content
    assert "WORKDIR /app" in content
    assert "COPY requirements.txt pyproject.toml /app/" in content
    assert 'CMD ["python", "backend/worker.py"]' in content


def test_dockerfile_frontend_configuration():
    """Validate structure and configuration of Dockerfile.frontend."""
    df_path = PROJECT_ROOT / "Dockerfile.frontend"
    assert df_path.exists()
    content = df_path.read_text()

    assert "FROM node:20-alpine AS builder" in content
    assert "FROM nginx:alpine" in content
    assert "COPY --from=builder /app/dist /usr/share/nginx/html" in content
    assert "EXPOSE 80" in content


def test_docker_compose_configuration():
    """Validate structure and configuration of docker-compose.yml."""
    compose_path = PROJECT_ROOT / "docker-compose.yml"
    assert compose_path.exists()
    content = compose_path.read_text()

    assert "services:" in content
    assert "db:" in content
    assert "api:" in content
    assert "worker:" in content
    assert "frontend:" in content
    assert "Dockerfile.api" in content
    assert "Dockerfile.worker" in content
    assert "Dockerfile.frontend" in content
    assert "8000:8000" in content
    assert "3000:80" in content
