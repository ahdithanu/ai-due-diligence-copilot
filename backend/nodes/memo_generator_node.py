import logging
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.domain.schemas import DiligenceState, DiligenceStatus
from backend.engine.node import BaseNode
from backend.engine.model_adapter import ModelAdapter
from backend.services.memo_generator import generate_investment_memo
from backend.db.models import InvestmentMemoModel

logger = logging.getLogger(__name__)


class MemoGeneratorNode(BaseNode):
    """
    Memo Generator Node: Calls memo_generator.py to render an institutional investment memo
    with evidence citations, updates DiligenceState, and saves the memo markdown to InvestmentMemoModel in DB.
    """

    def __init__(
        self,
        name: str = "MemoGenerator",
        db_session: Optional[AsyncSession] = None,
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(
            name=name,
            description="Generates institutional markdown investment memo and persists to database",
            model_adapter=model_adapter
        )
        self.db_session = db_session

    async def process(self, state: DiligenceState) -> DiligenceState:
        # Generate memo markdown
        memo_markdown = generate_investment_memo(state)
        state.memo_markdown = memo_markdown
        state.status = DiligenceStatus.MEMO_GENERATED

        # Persist to InvestmentMemoModel in database if session is available
        if self.db_session:
            await self._save_memo_to_db(state, memo_markdown, self.db_session)

        return state

    async def _save_memo_to_db(self, state: DiligenceState, memo_markdown: str, db: AsyncSession):
        stmt = select(InvestmentMemoModel).where(InvestmentMemoModel.investment_id == state.investment_id)
        result = await db.execute(stmt)
        memo_model = result.scalar_one_or_none()

        rec = state.recommendation or "PASS"
        conf = state.confidence_score if state.confidence_score is not None else 0.0

        if memo_model:
            memo_model.memo_markdown = memo_markdown
            memo_model.recommendation = rec
            memo_model.confidence_score = conf
        else:
            memo_model = InvestmentMemoModel(
                id=str(uuid.uuid4()),
                investment_id=state.investment_id,
                memo_markdown=memo_markdown,
                recommendation=rec,
                confidence_score=conf
            )
            db.add(memo_model)

        await db.commit()
