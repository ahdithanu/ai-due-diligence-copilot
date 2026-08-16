import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Float, Integer, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.database import Base
from backend.domain.schemas import DiligenceStatus, DocumentType, ClaimType

class InvestmentModel(Base):
    __tablename__ = "investments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    target_round: Mapped[str] = mapped_column(String(100), nullable=False)
    check_size_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=DiligenceStatus.CREATED.value)
    state_snapshot_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    documents: Mapped[List["DocumentModel"]] = relationship("DocumentModel", back_populates="investment", cascade="all, delete-orphan")
    evidence_records: Mapped[List["EvidenceRecordModel"]] = relationship("EvidenceRecordModel", back_populates="investment", cascade="all, delete-orphan")

class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investment_id: Mapped[str] = mapped_column(String(36), ForeignKey("investments.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), default=DocumentType.OTHER.value)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    investment: Mapped["InvestmentModel"] = relationship("InvestmentModel", back_populates="documents")
    chunks: Mapped[List["DocumentChunkModel"]] = relationship("DocumentChunkModel", back_populates="document", cascade="all, delete-orphan")

class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="chunks")

class EvidenceRecordModel(Base):
    __tablename__ = "evidence_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investment_id: Mapped[str] = mapped_column(String(36), ForeignKey("investments.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(36), ForeignKey("document_chunks.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    claim_type: Mapped[str] = mapped_column(String(50), default=ClaimType.FACT.value)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    investment: Mapped["InvestmentModel"] = relationship("InvestmentModel", back_populates="evidence_records")

class FinancialMetricModel(Base):
    __tablename__ = "financial_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investment_id: Mapped[str] = mapped_column(String(36), ForeignKey("investments.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(50), nullable=False)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    input_evidence_ids_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_deterministic: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

class ExecutionLogModel(Base):
    __tablename__ = "execution_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investment_id: Mapped[str] = mapped_column(String(36), ForeignKey("investments.id"), nullable=False)
    execution_id: Mapped[str] = mapped_column(String(36), nullable=False)
    node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    input_summary_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_summary_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token_usage_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    evaluation_result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    next_edge_selected: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class InvestmentMemoModel(Base):
    __tablename__ = "investment_memos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investment_id: Mapped[str] = mapped_column(String(36), ForeignKey("investments.id"), nullable=False)
    memo_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class DeploymentModel(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    deployment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    investment_strategy: Mapped[str] = mapped_column(String(100), nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class GraphCheckpointModel(Base):
    __tablename__ = "graph_checkpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), nullable=False)
    deployment_id: Mapped[str] = mapped_column(String(36), nullable=False)
    investment_id: Mapped[str] = mapped_column(String(36), ForeignKey("investments.id"), nullable=False)
    node_id: Mapped[str] = mapped_column(String(100), nullable=False)
    graph_state_version: Mapped[int] = mapped_column(Integer, default=1)
    iteration_count: Mapped[int] = mapped_column(Integer, default=0)
    state_snapshot_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    evaluation_results_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    routing_decision: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="RUNNING")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ExecutionFailureModel(Base):
    __tablename__ = "execution_failures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), nullable=False)
    investment_id: Mapped[str] = mapped_column(String(36), ForeignKey("investments.id"), nullable=False)
    failed_node: Mapped[str] = mapped_column(String(100), nullable=False)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    retryable: Mapped[bool] = mapped_column(Boolean, default=True)
    checkpoint_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    suggested_recovery_action: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("investments.id", ondelete="SET NULL"), nullable=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)



