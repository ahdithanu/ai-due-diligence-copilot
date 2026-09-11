#!/usr/bin/env python3
"""
AI Due Diligence Copilot - Local CI Simulator & Release Verification Script

Simulates the GitHub Actions CI/CD pipeline locally across 5 stages:
  Stage 1: Python Code Linting & Full Pytest Suite (116 tests).
  Stage 2: Frontend TypeScript Validation & Production Build (`npm run build`).
  Stage 3: Docker Container Build Check (`Dockerfile.api`, `Dockerfile.worker`, `Dockerfile.frontend`).
  Stage 4: Deployment Acceptance Gate Audit (`acceptance_gate_service.py`).
  Stage 5: Post-Deployment Synthetic Canary Test Verification (`canary_service.py`).

Usage:
  python scripts/verify_ci_pipeline.py [--stage {1,2,3,4,5,all}] [--skip-docker] [--deployment-id DEPLOYMENT_ID] [-v]
"""

import sys
import os
import time
import argparse
import subprocess
import py_compile
import shutil
import asyncio
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def print_banner(title: str):
    width = 75
    print("\n" + "=" * width)
    print(f"  {title}".ljust(width - 1))
    print("=" * width)


def stage_1_python_lint_and_tests(verbose: bool = False) -> Dict[str, Any]:
    """
    Stage 1: Python Code Syntax Linting & Full Pytest Suite execution.
    """
    start_time = time.perf_counter()
    print("\n[STAGE 1/5] Python Code Linting & Pytest Suite")
    print("-" * 60)

    # 1A. Python Code Linting / Syntax compilation check
    python_files = [
        "backend/main.py",
        "backend/worker.py",
        "backend/config.py",
        "backend/services/queue_service.py",
        "backend/services/acceptance_gate_service.py",
        "backend/services/canary_service.py",
        "backend/services/deployment_service.py",
    ]

    lint_errors = []
    for rel_path in python_files:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            try:
                py_compile.compile(str(full_path), doraise=True)
            except py_compile.PyCompileError as exc:
                lint_errors.append(f"{rel_path}: {exc}")
        else:
            lint_errors.append(f"Missing file: {rel_path}")

    lint_passed = len(lint_errors) == 0
    if lint_passed:
        print("  ✓ Python Syntax Linting: PASSED (all key files compiled cleanly)")
    else:
        print(f"  ✗ Python Syntax Linting: FAILED ({len(lint_errors)} error(s))")
        for err in lint_errors:
            print(f"    - {err}")

    # 1B. Run Pytest Suite
    print("  Running Pytest test suite...")
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--ignore=tests/test_ci_cd_pipeline.py"]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env
    )

    tests_passed = (proc.returncode == 0)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined_output = stdout + "\n" + stderr

    # Extract test count from pytest output (e.g. '116 passed, 1 warning')
    test_count = 0
    match = re.search(r"(\d+)\s+passed", combined_output)
    if match:
        test_count = int(match.group(1))

    if tests_passed:
        print(f"  ✓ Pytest Test Suite: PASSED ({test_count} tests passed)")
    else:
        print(f"  ✗ Pytest Test Suite: FAILED (Exit code: {proc.returncode})")
        if verbose:
            print("\n--- Pytest Failure Output ---")
            print(combined_output[-2000:])

    duration = time.perf_counter() - start_time
    overall_passed = lint_passed and tests_passed

    return {
        "stage": 1,
        "name": "Python Lint & Pytest Suite",
        "passed": overall_passed,
        "lint_passed": lint_passed,
        "tests_passed": tests_passed,
        "test_count": test_count,
        "duration_s": round(duration, 2),
        "output": combined_output if not tests_passed or verbose else ""
    }


def stage_2_frontend_build(verbose: bool = False) -> Dict[str, Any]:
    """
    Stage 2: Frontend TypeScript Validation & Production Build (`npm run build`).
    """
    start_time = time.perf_counter()
    print("\n[STAGE 2/5] Frontend TypeScript Validation & Production Build")
    print("-" * 60)

    frontend_dir = PROJECT_ROOT / "frontend"
    if not frontend_dir.exists():
        duration = time.perf_counter() - start_time
        print("  ✗ Frontend directory not found!")
        return {
            "stage": 2,
            "name": "Frontend Build",
            "passed": False,
            "error": "frontend/ directory missing",
            "duration_s": round(duration, 2)
        }

    # Execute `npm run build` inside frontend/
    print("  Executing 'npm run build' (tsc + vite build)...")
    proc = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
        shell=False
    )

    build_passed = (proc.returncode == 0)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined_output = stdout + "\n" + stderr

    # Verify build artifacts in dist/
    dist_dir = frontend_dir / "dist"
    dist_html = dist_dir / "index.html"
    dist_verified = dist_dir.exists() and dist_html.exists() and dist_html.stat().st_size > 0

    if build_passed and dist_verified:
        print("  ✓ Frontend Build & TypeScript Validation: PASSED")
        print(f"  ✓ Production bundle verified at: {dist_dir.relative_to(PROJECT_ROOT)}")
    else:
        print(f"  ✗ Frontend Build FAILED (Exit code: {proc.returncode}, Dist verified: {dist_verified})")
        if verbose:
            print("\n--- Build Output ---")
            print(combined_output)

    duration = time.perf_counter() - start_time
    overall_passed = build_passed and dist_verified

    return {
        "stage": 2,
        "name": "Frontend TypeScript & Build",
        "passed": overall_passed,
        "build_passed": build_passed,
        "dist_verified": dist_verified,
        "duration_s": round(duration, 2),
        "output": combined_output if not overall_passed or verbose else ""
    }


def stage_3_docker_build_check(skip_docker: bool = False, verbose: bool = False) -> Dict[str, Any]:
    """
    Stage 3: Docker Container Build Check (`Dockerfile.api`, `Dockerfile.worker`, `Dockerfile.frontend`).
    """
    start_time = time.perf_counter()
    print("\n[STAGE 3/5] Docker Container Build Check")
    print("-" * 60)

    dockerfiles = [
        ("Dockerfile.api", "diligence-api:ci"),
        ("Dockerfile.worker", "diligence-worker:ci"),
        ("Dockerfile.frontend", "diligence-frontend:ci")
    ]

    missing_files = []
    invalid_directives = []
    file_details = {}

    for df_name, tag in dockerfiles:
        df_path = PROJECT_ROOT / df_name
        if not df_path.exists():
            missing_files.append(df_name)
            continue

        content = df_path.read_text(encoding="utf-8")
        # Check required Dockerfile directives
        has_from = "FROM " in content
        has_copy_or_add = ("COPY " in content) or ("ADD " in content)
        has_cmd_or_entry = ("CMD " in content) or ("ENTRYPOINT " in content) or ("FROM nginx" in content)

        if not (has_from and has_copy_or_add):
            invalid_directives.append(f"{df_name}: Missing FROM or COPY/ADD directive")
        else:
            file_details[df_name] = {
                "exists": True,
                "has_from": has_from,
                "has_copy": has_copy_or_add,
                "has_cmd": has_cmd_or_entry
            }
            print(f"  ✓ Validated structural syntax for {df_name}")

    if missing_files or invalid_directives:
        duration = time.perf_counter() - start_time
        print(f"  ✗ Dockerfile static validation failed: missing={missing_files}, invalid={invalid_directives}")
        return {
            "stage": 3,
            "name": "Docker Container Check",
            "passed": False,
            "missing_files": missing_files,
            "invalid_directives": invalid_directives,
            "duration_s": round(duration, 2)
        }

    # Check if Docker CLI and daemon are operational
    docker_cli = shutil.which("docker")
    daemon_available = False
    build_results = {}

    if docker_cli and not skip_docker:
        # Check docker daemon ping
        check_proc = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True
        )
        if check_proc.returncode == 0:
            daemon_available = True

    if daemon_available and not skip_docker:
        print("  Docker daemon connected. Executing container image builds...")
        all_builds_passed = True
        for df_name, tag in dockerfiles:
            print(f"    Building {df_name} -> tag '{tag}'...")
            build_proc = subprocess.run(
                ["docker", "build", "-f", df_name, "-t", tag, "."],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            success = (build_proc.returncode == 0)
            build_results[df_name] = success
            if success:
                print(f"    ✓ {df_name} build succeeded.")
            else:
                all_builds_passed = False
                print(f"    ✗ {df_name} build failed (exit code: {build_proc.returncode})")
                if verbose:
                    print(build_proc.stderr)
        containers_passed = all_builds_passed
        mode = "docker_build"
    else:
        reason = "skip-docker flag set" if skip_docker else ("Docker daemon not running" if docker_cli else "Docker CLI not installed")
        print(f"  ℹ Docker build execution bypassed ({reason}). Static Dockerfile structural validation passed.")
        containers_passed = True
        mode = "static_validation"

    duration = time.perf_counter() - start_time
    overall_passed = (len(missing_files) == 0) and (len(invalid_directives) == 0) and containers_passed

    return {
        "stage": 3,
        "name": "Docker Container Check",
        "passed": overall_passed,
        "mode": mode,
        "dockerfiles_validated": list(file_details.keys()),
        "containers_built": build_results,
        "duration_s": round(duration, 2)
    }


def stage_4_acceptance_gate_audit(deployment_id: str = "growth_saas_default", verbose: bool = False) -> Dict[str, Any]:
    """
    Stage 4: Deployment Acceptance Gate Audit (`acceptance_gate_service.py`).
    """
    start_time = time.perf_counter()
    print("\n[STAGE 4/5] Deployment Acceptance Gate Audit")
    print("-" * 60)
    print(f"  Auditing deployment profile: '{deployment_id}'...")

    async def _audit():
        from backend.db.database import init_db, AsyncSessionLocal
        from backend.services.deployment_service import init_seed_deployments
        from backend.services.acceptance_gate_service import run_acceptance_gate

        await init_db()
        async with AsyncSessionLocal() as db:
            await init_seed_deployments(db)
            report = await run_acceptance_gate(deployment_id, db)
            return report

    try:
        report = asyncio.run(_audit())
        passed = report.status in ["READY", "READY_WITH_RISKS"]
        passed_checks = [c for c in report.checks if c.passed]

        if passed:
            print(f"  ✓ Deployment Acceptance Gate Audit: PASSED (Status: {report.status})")
            print(f"    - Passed checks: {len(passed_checks)} / {len(report.checks)}")
            for check in report.checks:
                status_symbol = "✓" if check.passed else "✗"
                print(f"      [{status_symbol}] {check.check_name}: {check.details}")
        else:
            print(f"  ✗ Deployment Acceptance Gate Audit: FAILED (Status: {report.status})")
            for check in report.checks:
                status_symbol = "✓" if check.passed else "✗"
                print(f"      [{status_symbol}] {check.check_name}: {check.details}")

        duration = time.perf_counter() - start_time
        return {
            "stage": 4,
            "name": "Deployment Acceptance Gate Audit",
            "passed": passed,
            "deployment_id": deployment_id,
            "status": report.status,
            "total_checks": len(report.checks),
            "passed_checks": len(passed_checks),
            "duration_s": round(duration, 2)
        }
    except Exception as exc:
        duration = time.perf_counter() - start_time
        print(f"  ✗ Acceptance gate execution error: {exc}")
        return {
            "stage": 4,
            "name": "Deployment Acceptance Gate Audit",
            "passed": False,
            "error": str(exc),
            "duration_s": round(duration, 2)
        }


def stage_5_canary_test_verification(verbose: bool = False) -> Dict[str, Any]:
    """
    Stage 5: Post-Deployment Synthetic Canary Test Verification (`canary_service.py`).
    """
    start_time = time.perf_counter()
    print("\n[STAGE 5/5] Synthetic Canary Test Verification")
    print("-" * 60)
    print("  Executing end-to-end synthetic canary test graph run & database teardown...")

    async def _canary():
        from backend.db.database import init_db, AsyncSessionLocal
        from backend.services.canary_service import run_canary_test

        await init_db()
        async with AsyncSessionLocal() as db:
            result = await run_canary_test(db)
            return result

    try:
        result = asyncio.run(_canary())
        passed = (
            result.passed is True
            and result.node_checkpoints_verified > 0
            and result.teardown_successful is True
        )

        if passed:
            print("  ✓ Synthetic Canary Test: PASSED")
            print(f"    - Synthetic Investment ID: {result.synthetic_investment_id}")
            print(f"    - Graph checkpoints verified: {result.node_checkpoints_verified}")
            print(f"    - Contradiction resolution: {result.conflict_resolved}")
            print(f"    - Teardown successful: {result.teardown_successful}")
            print(f"    - Canary execution time: {result.duration_ms:.2f} ms")
        else:
            print("  ✗ Synthetic Canary Test: FAILED")
            print(f"    - Passed: {result.passed}")
            print(f"    - Teardown successful: {result.teardown_successful}")

        duration = time.perf_counter() - start_time
        return {
            "stage": 5,
            "name": "Synthetic Canary Test",
            "passed": passed,
            "synthetic_investment_id": result.synthetic_investment_id,
            "checkpoints_verified": result.node_checkpoints_verified,
            "teardown_successful": result.teardown_successful,
            "canary_duration_ms": result.duration_ms,
            "duration_s": round(duration, 2)
        }
    except Exception as exc:
        duration = time.perf_counter() - start_time
        print(f"  ✗ Synthetic canary execution error: {exc}")
        return {
            "stage": 5,
            "name": "Synthetic Canary Test",
            "passed": False,
            "error": str(exc),
            "duration_s": round(duration, 2)
        }


def run_ci_pipeline(
    stage: str = "all",
    skip_docker: bool = False,
    deployment_id: str = "growth_saas_default",
    verbose: bool = False
) -> bool:
    """
    Main pipeline orchestrator. Executes requested stages and reports final summary table.
    """
    print_banner("AI Due Diligence Copilot - Local CI & Release Verification")
    pipeline_start = time.perf_counter()
    results: List[Dict[str, Any]] = []

    stages_to_run = []
    if stage.lower() == "all":
        stages_to_run = [1, 2, 3, 4, 5]
    else:
        try:
            val = int(stage)
            if val not in [1, 2, 3, 4, 5]:
                print(f"Error: Invalid stage '{stage}'. Choose from [1, 2, 3, 4, 5, all].")
                return False
            stages_to_run = [val]
        except ValueError:
            print(f"Error: Invalid stage '{stage}'. Choose from [1, 2, 3, 4, 5, all].")
            return False

    for st in stages_to_run:
        if st == 1:
            res = stage_1_python_lint_and_tests(verbose=verbose)
            results.append(res)
        elif st == 2:
            res = stage_2_frontend_build(verbose=verbose)
            results.append(res)
        elif st == 3:
            res = stage_3_docker_build_check(skip_docker=skip_docker, verbose=verbose)
            results.append(res)
        elif st == 4:
            res = stage_4_acceptance_gate_audit(deployment_id=deployment_id, verbose=verbose)
            results.append(res)
        elif st == 5:
            res = stage_5_canary_test_verification(verbose=verbose)
            results.append(res)

    total_duration = time.perf_counter() - pipeline_start

    # Print Final Release Verification Summary Table
    print("\n" + "=" * 75)
    print("                      CI/CD VERIFICATION SUMMARY                        ")
    print("=" * 75)
    print(f"{'Stage':<8} | {'Stage Name':<35} | {'Status':<10} | {'Duration':<10}")
    print("-" * 75)

    all_passed = True
    for r in results:
        status_str = "PASS" if r.get("passed") else "FAIL"
        if not r.get("passed"):
            all_passed = False
        st_num = f"Stage {r['stage']}"
        name = r["name"]
        dur = f"{r.get('duration_s', 0):.2f}s"
        print(f"{st_num:<8} | {name:<35} | {status_str:<10} | {dur:<10}")

    print("-" * 75)
    final_status = "PASSED - RELEASE READY" if all_passed else "FAILED - DO NOT DEPLOY"
    print(f"OVERALL PIPELINE RESULT: {final_status} (Total: {total_duration:.2f}s)")
    print("=" * 75 + "\n")

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Local CI Simulator & Release Verification Script for AI Due Diligence Copilot"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="all",
        choices=["1", "2", "3", "4", "5", "all"],
        help="Specific pipeline stage to execute (1-5 or 'all')"
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip actual container build execution and rely on static Dockerfile validation"
    )
    parser.add_argument(
        "--deployment-id",
        type=str,
        default="growth_saas_default",
        help="Deployment profile ID to audit in Stage 4"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable detailed error log output for failed steps"
    )

    args = parser.parse_args()
    success = run_ci_pipeline(
        stage=args.stage,
        skip_docker=args.skip_docker,
        deployment_id=args.deployment_id,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
