from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid

from backend.domain.schemas import DiligenceState, ExecutionLogEntry
from backend.engine.model_adapter import ModelAdapter

class BaseNode(ABC):
    """
    Abstract Base Class for graph processing nodes with automatic execution tracking.
    """

    def __init__(self, name: str, description: str = "", model_adapter: Optional[ModelAdapter] = None):
        self.name = name
        self.description = description
        self.model_adapter = model_adapter

    @abstractmethod
    async def process(self, state: DiligenceState) -> DiligenceState:
        """
        Subclasses implement node business logic here.
        Modifies state in-place or returns updated state.
        """
        pass

    async def execute(self, state: DiligenceState, iteration: int = 0) -> DiligenceState:
        """
        Execution wrapper handling logging, token usage tracking, and error handling.
        """
        start_time = datetime.now(timezone.utc)
        exec_id = str(uuid.uuid4())

        input_summary = {
            "status": state.status,
            "company_name": state.company_name,
            "evidence_count": len(state.evidence_records),
            "specialist_analyses_count": len(state.specialist_analyses),
        }

        log_entry = ExecutionLogEntry(
            execution_id=exec_id,
            node_name=self.name,
            start_time=start_time,
            status="RUNNING",
            input_summary=input_summary,
            iteration=iteration,
            model_name=self.model_adapter.model_name if self.model_adapter else None
        )

        try:
            state = await self.process(state)
            
            log_entry.status = "COMPLETED"
            log_entry.end_time = datetime.now(timezone.utc)
            log_entry.output_summary = {
                "status": state.status,
                "specialist_analyses_count": len(state.specialist_analyses),
                "evaluations_count": len(state.evaluations),
                "recommendation": state.recommendation
            }

            if self.model_adapter:
                log_entry.token_usage = self.model_adapter.get_last_token_usage()

            # Attach latest evaluation result if available and created in this node
            if state.evaluations:
                latest_eval = state.evaluations[-1]
                if latest_eval.target_node == self.name:
                    log_entry.evaluation_result = latest_eval

            state.execution_history.append(log_entry)
            return state

        except Exception as e:
            log_entry.status = "FAILED"
            log_entry.end_time = datetime.now(timezone.utc)
            log_entry.error_message = str(e)
            state.execution_history.append(log_entry)
            raise e
