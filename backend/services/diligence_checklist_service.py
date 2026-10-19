import uuid
from typing import Dict, List, Optional
from backend.domain.schemas import (
    WorkstreamCategory,
    TaskPriority,
    TaskStatus,
    ChecklistTask,
    WorkstreamSummary,
    DiligenceChecklistResponse,
    CreateTaskRequest,
    UpdateTaskRequest,
)

WORKSTREAM_META = {
    WorkstreamCategory.FINANCIAL_QOE: "Financial & Quality of Earnings (QoE)",
    WorkstreamCategory.COMMERCIAL_GTM: "Commercial & Go-To-Market (GTM)",
    WorkstreamCategory.TECHNICAL_PRODUCT: "Technical Architecture & Product",
    WorkstreamCategory.LEGAL_REGULATORY: "Legal, IP & Regulatory Compliance",
    WorkstreamCategory.MANAGEMENT_HR: "Management, Org & HR Due Diligence",
    WorkstreamCategory.TAX_STRUCTURE: "Tax Structure & Entity Formation",
}

DEFAULT_TASKS = [
    # Financial QoE
    {
        "title": "Quality of Earnings (QoE) Revenue Recognition & EBITDA Adjustments",
        "workstream": WorkstreamCategory.FINANCIAL_QOE,
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.COMPLETED,
        "assigned_to": "Finance Lead",
        "findings_summary": "ARR verified at $10.0M. Non-recurring implementation fees ($650k) excluded from recurring base.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-101", "rag-chunk-104"],
    },
    {
        "title": "Net Retention Rate (NRR) Cohort Bridge & Gross Churn Analysis",
        "workstream": WorkstreamCategory.FINANCIAL_QOE,
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.COMPLETED,
        "assigned_to": "Finance Lead",
        "findings_summary": "NRR holds at 125%. Enterprise tier gross logo retention at 96.2%.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-108"],
    },
    {
        "title": "Working Capital, Cash Runway & Debt Obligations Audit",
        "workstream": WorkstreamCategory.FINANCIAL_QOE,
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.IN_PROGRESS,
        "assigned_to": "Analyst",
        "findings_summary": "18.4 months runway remaining at $315k/mo net burn. No subordinated venture debt.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-112"],
    },
    # Commercial GTM
    {
        "title": "Customer Concentration Audit (Top 10 Accounts & Churn Sensitivity)",
        "workstream": WorkstreamCategory.COMMERCIAL_GTM,
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.BLOCKED,
        "assigned_to": "Deal Lead",
        "findings_summary": "Top client represents 35% of total ARR. Waiting for customer interview NDA clearance.",
        "flags_count": 1,
        "evidence_chunk_ids": ["rag-chunk-201"],
    },
    {
        "title": "Sales Velocity, CAC Payback & Magic Number Benchmarking",
        "workstream": WorkstreamCategory.COMMERCIAL_GTM,
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.COMPLETED,
        "assigned_to": "GTM Analyst",
        "findings_summary": "Magic Number at 1.15x (top-quartile). Blended CAC payback at 14 months.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-205"],
    },
    {
        "title": "Competitive Win/Loss & Pricing Power Verification",
        "workstream": WorkstreamCategory.COMMERCIAL_GTM,
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.IN_PROGRESS,
        "assigned_to": "GTM Analyst",
        "findings_summary": "Direct win rate vs incumbent legacy vendors is 68%. Strong pricing elasticity.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-209"],
    },
    # Technical & Product
    {
        "title": "Cloud Infrastructure, Single Point of Failure (SPOF) & Multi-Region Audit",
        "workstream": WorkstreamCategory.TECHNICAL_PRODUCT,
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.COMPLETED,
        "assigned_to": "Technical Director",
        "findings_summary": "AWS multi-AZ architecture validated. RTO < 15 mins, RPO < 1 min.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-301"],
    },
    {
        "title": "Open Source Licensing & Software Supply Chain (GPL / AGPL scan)",
        "workstream": WorkstreamCategory.TECHNICAL_PRODUCT,
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.COMPLETED,
        "assigned_to": "Technical Director",
        "findings_summary": "Automated SBOM audit clean. Zero viral copyleft licenses detected in production code.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-304"],
    },
    {
        "title": "Key Person Dependency on Founding CTO & Technical Bus Factor",
        "workstream": WorkstreamCategory.TECHNICAL_PRODUCT,
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.IN_PROGRESS,
        "assigned_to": "Deal Lead",
        "findings_summary": "Founding CTO holds critical cryptographic credentials. Recommending VP Eng hire prior to Series B.",
        "flags_count": 1,
        "evidence_chunk_ids": ["rag-chunk-309"],
    },
    # Legal & Regulatory
    {
        "title": "Cap Table, Option Pool Unallocated Reserve & Liquidation Preference Audit",
        "workstream": WorkstreamCategory.LEGAL_REGULATORY,
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.COMPLETED,
        "assigned_to": "Legal Counsel",
        "findings_summary": "Series A Preferred 1x non-participating confirmed. Unallocated ESOP at 12.5%.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-401"],
    },
    {
        "title": "Customer MSA Review, SLA Liabilities & Intellectual Property Assignment",
        "workstream": WorkstreamCategory.LEGAL_REGULATORY,
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.IN_PROGRESS,
        "assigned_to": "Legal Counsel",
        "findings_summary": "Proprietary IP assignment signed by 100% of full-time employees and contractors.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-405"],
    },
    # Management & HR
    {
        "title": "Founder Vesting Schedule & 4-Year Reverse Dilution Covenants",
        "workstream": WorkstreamCategory.MANAGEMENT_HR,
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.COMPLETED,
        "assigned_to": "Deal Lead",
        "findings_summary": "Founders agreed to fresh 4-year vesting schedule with 1-year cliff on 25% of holdings.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-501"],
    },
    {
        "title": "Engineering & Go-To-Market Key Hire Plan (Post-Close Budget)",
        "workstream": WorkstreamCategory.MANAGEMENT_HR,
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.IN_PROGRESS,
        "assigned_to": "Talent Partner",
        "findings_summary": "Headcount plan allocates $1.8M for Head of Sales and 4 quota-carrying AEs.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-504"],
    },
    # Tax Structure
    {
        "title": "Delaware C-Corp Standing & QSBS Section 1202 Eligibility Review",
        "workstream": WorkstreamCategory.TAX_STRUCTURE,
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.COMPLETED,
        "assigned_to": "Tax Counsel",
        "findings_summary": "Delaware certificate in good standing. Shares qualify for federal QSBS capital gains exclusion.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-601"],
    },
    {
        "title": "State Sales Tax Nexus Exposure & International VAT Compliance",
        "workstream": WorkstreamCategory.TAX_STRUCTURE,
        "priority": TaskPriority.LOW,
        "status": TaskStatus.IN_PROGRESS,
        "assigned_to": "Tax Counsel",
        "findings_summary": "Automated tax engine handles 48 US states. Minor UK VAT audit underway.",
        "flags_count": 0,
        "evidence_chunk_ids": ["rag-chunk-603"],
    },
]


class DiligenceChecklistService:
    """Manages multi-workstream private equity diligence checklists and task trackers."""

    def __init__(self):
        self._stores: Dict[str, List[ChecklistTask]] = {}

    def _get_or_init_store(self, investment_id: str) -> List[ChecklistTask]:
        if investment_id not in self._stores:
            tasks = []
            for t in DEFAULT_TASKS:
                task = ChecklistTask(
                    id=str(uuid.uuid4()),
                    title=t["title"],
                    workstream=t["workstream"],
                    priority=t["priority"],
                    status=t["status"],
                    assigned_to=t["assigned_to"],
                    findings_summary=t["findings_summary"],
                    flags_count=t["flags_count"],
                    due_date="2026-11-15",
                    evidence_chunk_ids=t["evidence_chunk_ids"],
                )
                tasks.append(task)
            self._stores[investment_id] = tasks
        return self._stores[investment_id]

    def get_checklist(self, investment_id: str) -> DiligenceChecklistResponse:
        tasks = self._get_or_init_store(investment_id)

        # Aggregate by workstream
        workstream_summaries: List[WorkstreamSummary] = []
        total_tasks_count = len(tasks)
        completed_tasks_count = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

        for ws, display_name in WORKSTREAM_META.items():
            ws_tasks = [t for t in tasks if t.workstream == ws]
            total_ws = len(ws_tasks)
            completed_ws = sum(1 for t in ws_tasks if t.status == TaskStatus.COMPLETED)
            blocked_ws = sum(1 for t in ws_tasks if t.status == TaskStatus.BLOCKED)
            pct = round((completed_ws / total_ws * 100.0), 1) if total_ws > 0 else 0.0

            if blocked_ws > 0:
                status = "ATTENTION_REQUIRED"
            elif completed_ws == total_ws:
                status = "COMPLETED"
            elif completed_ws > 0:
                status = "IN_PROGRESS"
            else:
                status = "NOT_STARTED"

            workstream_summaries.append(
                WorkstreamSummary(
                    workstream=ws,
                    display_name=display_name,
                    total_tasks=total_ws,
                    completed_tasks=completed_ws,
                    completion_pct=pct,
                    blocked_tasks=blocked_ws,
                    status=status,
                )
            )

        overall_pct = (
            round((completed_tasks_count / total_tasks_count * 100.0), 1)
            if total_tasks_count > 0
            else 0.0
        )

        return DiligenceChecklistResponse(
            investment_id=investment_id,
            overall_progress_pct=overall_pct,
            workstreams=workstream_summaries,
            tasks=tasks,
        )

    def create_task(self, investment_id: str, request: CreateTaskRequest) -> ChecklistTask:
        tasks = self._get_or_init_store(investment_id)
        new_task = ChecklistTask(
            id=str(uuid.uuid4()),
            title=request.title,
            workstream=request.workstream,
            priority=request.priority,
            status=TaskStatus.NOT_STARTED,
            assigned_to=request.assigned_to,
            findings_summary=request.findings_summary,
            flags_count=0,
            due_date="2026-11-30",
            evidence_chunk_ids=[],
        )
        tasks.append(new_task)
        return new_task

    def update_task(
        self, investment_id: str, task_id: str, request: UpdateTaskRequest
    ) -> Optional[ChecklistTask]:
        tasks = self._get_or_init_store(investment_id)
        for task in tasks:
            if task.id == task_id:
                if request.status is not None:
                    task.status = request.status
                if request.findings_summary is not None:
                    task.findings_summary = request.findings_summary
                if request.flags_count is not None:
                    task.flags_count = request.flags_count
                if request.assigned_to is not None:
                    task.assigned_to = request.assigned_to
                return task
        return None

    def delete_task(self, investment_id: str, task_id: str) -> bool:
        tasks = self._get_or_init_store(investment_id)
        for i, t in enumerate(tasks):
            if t.id == task_id:
                tasks.pop(i)
                return True
        return False


diligence_checklist_service = DiligenceChecklistService()
