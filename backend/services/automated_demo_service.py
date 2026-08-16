import asyncio
from typing import List, Dict, Any, Optional
from backend.domain.schemas import DemoStep, DemoStatusResponse, DemoControlRequest

STEP_METADATA: List[Dict[str, Any]] = [
    {
        "step": DemoStep.DEPLOYMENT_SELECTION,
        "name": "1. Deployment Selection & Profile Configuration",
        "active_tab": "deployments",
        "progress_pct": 12.5,
        "details": "Selected Growth Equity SaaS deployment profile (ID: growth_saas_default). Applied financial & risk thresholds.",
    },
    {
        "step": DemoStep.DOCUMENT_FINANCIAL_ENGINE,
        "name": "2. Document Ingestion & Deterministic Financial Engine",
        "active_tab": "financials",
        "progress_pct": 25.0,
        "details": "Ingested P&L & Cap Table docs. Computed 17 financial metrics (ARR, NRR 118%, Gross Margin 81%, LTV/CAC 4.2x, Rule of 40: 44%).",
    },
    {
        "step": DemoStep.SPECIALIST_CRITIC_LOOP,
        "name": "3. Specialist Domain & Critic Loop Execution",
        "active_tab": "graph",
        "progress_pct": 37.5,
        "details": "Executed 4 specialist nodes (Financial, Legal, Tech, Ops). Financial Critic node audited cross-statement reconciliation.",
    },
    {
        "step": DemoStep.CONTRADICTION_INTERRUPT,
        "name": "4. Contradiction Detection & Human-in-the-Loop Interrupt",
        "active_tab": "evidence",
        "progress_pct": 50.0,
        "details": "Triggered contradiction interrupt: $12M (Pitch Deck) vs $8M (Tax Filing) ARR conflict. State set to WAITING_FOR_HUMAN.",
    },
    {
        "step": DemoStep.CHECKPOINT_RECOVERY,
        "name": "5. Checkpoint History & State Recovery",
        "active_tab": "graph",
        "progress_pct": 62.5,
        "details": "Selected authoritative source ($8M verified ARR via Stripe/Audited Filing) and resumed execution from checkpoint.",
    },
    {
        "step": DemoStep.IC_DEBATE_AND_MEMO,
        "name": "6. Investment Committee Debate & Memo Synthesis",
        "active_tab": "ic_debate",
        "progress_pct": 75.0,
        "details": "Ran Bull/Bear/Skeptic IC debate agents and generated full 20-section Investment Committee Memo.",
    },
    {
        "step": DemoStep.FAILURE_LAB_FAILOVER,
        "name": "7. Failure Lab & Model Failover Simulation",
        "active_tab": "failure_lab",
        "progress_pct": 87.5,
        "details": "Injected 429 Rate Limit chaos into Gemini 1.5 Pro. Zero-downtime circuit breaker failover to GPT-4o executed successfully.",
    },
    {
        "step": DemoStep.ACCEPTANCE_AND_CANARY,
        "name": "8. Acceptance Gate & Production Canary Test",
        "active_tab": "fde_ops",
        "progress_pct": 100.0,
        "details": "Ran pre-flight acceptance gate checks (6/6 passed) and completed production canary deployment & audit teardown.",
    },
]


class AutomatedDemoService:
    """
    Background Async Class managing automated demo execution across the 8 FDE milestones:
      1. DEPLOYMENT_SELECTION: Growth Equity SaaS deployment profile.
      2. DOCUMENT_FINANCIAL_ENGINE: Ingests documents & computes 17 financial metrics.
      3. SPECIALIST_CRITIC_LOOP: Specialist nodes & financial critic audit loop.
      4. CONTRADICTION_INTERRUPT: Triggers $12M vs $8M ARR conflict -> WAITING_FOR_HUMAN.
      5. CHECKPOINT_RECOVERY: Authoritative source selection & checkpoint recovery.
      6. IC_DEBATE_AND_MEMO: Bull/Bear/Skeptic debate & 20-section memo generation.
      7. FAILURE_LAB_FAILOVER: 429 Rate Limit injection & Gemini -> GPT-4o failover.
      8. ACCEPTANCE_AND_CANARY: Pre-flight gate execution & canary teardown.
    """

    def __init__(self):
        self.active: bool = False
        self.paused: bool = False
        self.current_step_index: int = 0
        self.loop_count: int = 0
        self.auto_loop: bool = True
        self.speed: float = 1.0
        self.log_messages: List[str] = []
        self._bg_task: Optional[asyncio.Task] = None

    def start_demo(self, speed: float = 1.0, loop: bool = True) -> DemoStatusResponse:
        """
        Starts automated demo playback with specified speed multiplier and loop configuration.
        """
        self.active = True
        self.paused = False
        self.current_step_index = 0
        self.speed = speed
        self.auto_loop = loop
        step_info = STEP_METADATA[self.current_step_index]
        self._add_log(f"[Demo] Started demo playback at speed {self.speed}x (loop={self.auto_loop}). Step 1: {step_info['name']}")
        self._add_log(f"[Milestone 1/8] {step_info['name']}: {step_info['details']}")
        return self.get_status()

    def pause_demo(self) -> DemoStatusResponse:
        """
        Pauses ongoing automated demo playback.
        """
        self.paused = True
        self._add_log(f"[Demo] Paused playback at step {self.current_step_index + 1}.")
        return self.get_status()

    def resume_demo(self) -> DemoStatusResponse:
        """
        Resumes paused automated demo playback.
        """
        self.active = True
        self.paused = False
        step_info = STEP_METADATA[self.current_step_index]
        self._add_log(f"[Demo] Resumed playback at step {self.current_step_index + 1}: {step_info['name']}.")
        return self.get_status()

    def step_demo(self) -> DemoStatusResponse:
        """
        Manually steps to the next demo milestone step.
        """
        if not self.active and self.current_step_index == 0 and len(self.log_messages) == 0:
            self.active = True

        if self.current_step_index < len(STEP_METADATA) - 1:
            self.current_step_index += 1
            step_info = STEP_METADATA[self.current_step_index]
            self._add_log(f"[Milestone {self.current_step_index + 1}/8] Advanced to step {self.current_step_index + 1}: {step_info['name']}.")
            self._add_log(f"  └─ Details: {step_info['details']}")
        else:
            # Reached final step (index 7)
            if self.auto_loop:
                self.loop_count += 1
                self.current_step_index = 0
                step_info = STEP_METADATA[self.current_step_index]
                self._add_log(f"[Demo] Loop {self.loop_count} completed. Resetting to step 1: {step_info['name']}.")
            else:
                self.active = False
                self._add_log("[Demo] Reached final step (loop=False). Demo completed.")
        return self.get_status()

    def reset_demo(self) -> DemoStatusResponse:
        """
        Resets demo state back to step 1.
        """
        self.stop_background_task()
        self.active = False
        self.paused = False
        self.current_step_index = 0
        self.loop_count = 0
        self.log_messages = []
        self._add_log("[Demo] Demo state reset.")
        return self.get_status()

    def get_status(self) -> DemoStatusResponse:
        """
        Returns current demo playback status response.
        """
        step_info = STEP_METADATA[self.current_step_index]
        return DemoStatusResponse(
            active=self.active,
            paused=self.paused,
            current_step=step_info["step"].value,
            current_step_name=step_info["name"],
            active_tab=step_info["active_tab"],
            loop_count=self.loop_count,
            progress_pct=step_info["progress_pct"],
            auto_loop=self.auto_loop,
            speed=self.speed,
            log_messages=list(self.log_messages)
        )

    # Aliases for backwards compatibility with endpoints and tests
    def start(self, speed: float = 1.0, loop: bool = True) -> DemoStatusResponse:
        return self.start_demo(speed=speed, loop=loop)

    def pause(self) -> DemoStatusResponse:
        return self.pause_demo()

    def resume(self) -> DemoStatusResponse:
        return self.resume_demo()

    def step(self) -> DemoStatusResponse:
        return self.step_demo()

    def reset(self) -> DemoStatusResponse:
        return self.reset_demo()

    async def start_background_loop(self, speed: float = 1.0, loop: bool = True) -> None:
        """
        Launches continuous background async task execution loop.
        """
        self.start_demo(speed=speed, loop=loop)
        self._bg_task = asyncio.create_task(self._run_loop())

    async def _run_loop(self) -> None:
        try:
            while self.active:
                if not self.paused:
                    step_delay = max(0.5, 3.0 / self.speed)
                    await asyncio.sleep(step_delay)
                    self.step_demo()
                else:
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass

    def stop_background_task(self) -> None:
        """
        Stops background async task if running.
        """
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()
            self._bg_task = None

    def _add_log(self, message: str) -> None:
        self.log_messages.append(message)


automated_demo_service = AutomatedDemoService()
