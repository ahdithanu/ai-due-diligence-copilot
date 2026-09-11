#!/usr/bin/env python3
"""
Standalone CLI Demo Runner Script
Executes continuous automated demo loops of the AI Investment Due Diligence Copilot in terminal.
Demonstrates the 8 FDE milestones:
  1. DEPLOYMENT_SELECTION: Selects Growth Equity SaaS deployment.
  2. DOCUMENT_FINANCIAL_ENGINE: Ingests documents & computes 17 financial metrics.
  3. SPECIALIST_CRITIC_LOOP: Executes specialist nodes & financial critic audit.
  4. CONTRADICTION_INTERRUPT: Triggers $12M vs $8M ARR conflict -> WAITING_FOR_HUMAN.
  5. CHECKPOINT_RECOVERY: Selects authoritative source & resumes from point-in-time checkpoint.
  6. IC_DEBATE_AND_MEMO: Runs Bull/Bear/Skeptic debate & generates 20-section memo.
  7. FAILURE_LAB_FAILOVER: Injects 429 Rate Limit & demonstrates Gemini -> GPT-4o failover.
  8. ACCEPTANCE_AND_CANARY: Executes pre-flight gate & canary teardown.
"""

import sys
import os
import asyncio
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.automated_demo_service import automated_demo_service


def render_progress_bar(pct: float, width: int = 25) -> str:
    filled = int(round(width * pct / 100.0))
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct:5.1f}%"


async def run_loop(speed: float = 1.0, count: int = 0):
    print("=" * 78)
    print(" 🚀 STARTING AUTOMATED DEMO CLI RUNNER")
    print("    AI Investment Due Diligence Copilot — FDE Engine")
    print("=" * 78)
    mode_str = "Infinite" if count == 0 else str(count)
    print(f" Playback Speed: {speed}x | Mode: Continuous Loop | Target Loops: {mode_str}")
    print("-" * 78)

    status = automated_demo_service.start_demo(speed=speed, loop=True)
    step_delay = max(0.1, 1.5 / speed)

    loop_iteration = 1
    step_count = 0

    try:
        while True:
            status = automated_demo_service.get_status()
            step_count += 1
            progress_bar = render_progress_bar(status.progress_pct)

            print()
            print(f"📍 [LOOP #{status.loop_count}] Milestone: {status.current_step_name}")
            print(f"   ├─ Step Identifier: {status.current_step}")
            print(f"   ├─ Active UI Tab   : {status.active_tab}")
            print(f"   ├─ Progress        : {progress_bar}")

            if status.log_messages:
                latest_log = status.log_messages[-1]
                print(f"   └─ Latest Event    : {latest_log}")

            await asyncio.sleep(step_delay)

            # Advance to next milestone step
            next_status = automated_demo_service.step_demo()

            if next_status.loop_count > loop_iteration:
                print()
                print("🔄 " * 26)
                print(f"  🎉 COMPLETED DEMO LOOP #{loop_iteration}! AUTO-RESETTING FOR LOOP #{next_status.loop_count}...")
                print("🔄 " * 26)
                loop_iteration = next_status.loop_count
                await asyncio.sleep(0.5)

            if count > 0 and loop_iteration > count:
                print()
                print(f"✅ Target loop count ({count}) reached. Stopping demo runner.")
                break
    except asyncio.CancelledError:
        print("\nDemo playback task cancelled.")


def main():
    parser = argparse.ArgumentParser(description="Run Standalone CLI Automated Demo for AI Investment Diligence Copilot")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier (e.g. 1.0, 2.0, 5.0)")
    parser.add_argument("--count", type=int, default=0, help="Number of demo loops to run (0 = infinite)")
    args = parser.parse_args()

    try:
        asyncio.run(run_loop(speed=args.speed, count=args.count))
    except KeyboardInterrupt:
        print("\n\n🛑 Demo playback stopped by user (KeyboardInterrupt). Exiting cleanly.")


if __name__ == "__main__":
    main()
