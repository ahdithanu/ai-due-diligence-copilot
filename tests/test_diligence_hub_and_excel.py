import io
import zipfile
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.domain.schemas import (
    WorkstreamCategory,
    TaskPriority,
    TaskStatus,
    CreateTaskRequest,
    UpdateTaskRequest,
)
from backend.services.diligence_checklist_service import diligence_checklist_service
from backend.services.valuation_comps_service import valuation_comps_service
from backend.services.financial_model_excel_service import financial_model_excel_service

client = TestClient(app)


def test_diligence_checklist_service():
    inv_id = "test-inv-dd-001"
    checklist = diligence_checklist_service.get_checklist(inv_id)
    assert checklist.investment_id == inv_id
    assert len(checklist.workstreams) == 6
    assert len(checklist.tasks) >= 10
    assert 0.0 <= checklist.overall_progress_pct <= 100.0

    # Create new task
    req = CreateTaskRequest(
        title="Audited 409A Valuation & Tax Shield",
        workstream=WorkstreamCategory.TAX_STRUCTURE,
        priority=TaskPriority.HIGH,
        assigned_to="Senior Associate",
        findings_summary="Pending final receipt from Carta.",
    )
    created = diligence_checklist_service.create_task(inv_id, req)
    assert created.title == req.title
    assert created.status == TaskStatus.NOT_STARTED

    # Update task
    updated = diligence_checklist_service.update_task(
        inv_id,
        created.id,
        UpdateTaskRequest(
            status=TaskStatus.COMPLETED,
            findings_summary="409A fair market value set at $3.25/share.",
        ),
    )
    assert updated is not None
    assert updated.status == TaskStatus.COMPLETED
    assert "409A" in updated.findings_summary

    # Delete task
    del_res = diligence_checklist_service.delete_task(inv_id, created.id)
    assert del_res is True


def test_valuation_comps_service():
    inv_id = "test-inv-comps-001"
    comps = valuation_comps_service.calculate_valuation_comps(
        investment_id=inv_id,
        company_name="Acme SaaS AI",
        arr_usd=10_000_000.0,
        current_valuation_usd=50_000_000.0,
        growth_rate_pct=35.0,
        gross_margin_pct=80.0,
        ebitda_margin_pct=12.0,
    )
    assert comps.investment_id == inv_id
    assert comps.current_arr_usd == 10_000_000.0
    assert comps.target_rule_of_40_pct == 47.0
    assert len(comps.public_peers) >= 5
    assert len(comps.precedent_deals) >= 5
    assert len(comps.methodology_ranges) == 4

    # Ensure bounds ordering: low < median < high
    for m in comps.methodology_ranges:
        assert m.low_valuation_usd < m.median_valuation_usd < m.high_valuation_usd


def test_financial_model_excel_service():
    excel_bytes = financial_model_excel_service.generate_excel_model(
        company_name="Acme SaaS AI",
        arr_usd=10_000_000.0,
        valuation_usd=50_000_000.0,
        growth_rate_pct=35.0,
        gross_margin_pct=80.0,
    )
    assert excel_bytes.startswith(b"PK\x03\x04")

    # Read zip and verify expected worksheets
    with zipfile.ZipFile(io.BytesIO(excel_bytes), "r") as z:
        names = z.namelist()
        assert "[Content_Types].xml" in names
        assert "xl/workbook.xml" in names
        assert "xl/worksheets/sheet1.xml" in names
        assert "xl/worksheets/sheet2.xml" in names
        assert "xl/worksheets/sheet3.xml" in names
        assert "xl/worksheets/sheet4.xml" in names
        assert "xl/worksheets/sheet5.xml" in names

        # Validate that sheet 2 contains 3-statement line items
        sheet2_content = z.read("xl/worksheets/sheet2.xml").decode("utf-8")
        assert "Subscription Revenue" in sheet2_content
        assert "Gross Profit" in sheet2_content
        assert "EBITDA" in sheet2_content


def test_diligence_hub_api_endpoints():
    inv_id = "test-inv-api-001"

    # GET checklist
    resp = client.get(f"/api/v1/investments/{inv_id}/checklist")
    assert resp.status_code == 200
    data = resp.json()
    assert "workstreams" in data
    assert "tasks" in data

    # POST create task
    post_resp = client.post(
        f"/api/v1/investments/{inv_id}/checklist/tasks",
        json={
            "title": "Verify Series A Anti-Dilution Provisions",
            "workstream": "LEGAL_REGULATORY",
            "priority": "HIGH",
            "assigned_to": "Legal Partner",
            "findings_summary": "Broad-based weighted average anti-dilution.",
        },
    )
    assert post_resp.status_code == 200
    task_id = post_resp.json()["id"]

    # PATCH task
    patch_resp = client.patch(
        f"/api/v1/investments/{inv_id}/checklist/tasks/{task_id}",
        json={"status": "COMPLETED", "findings_summary": "Verified and approved by counsel."},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "COMPLETED"

    # DELETE task
    del_resp = client.delete(f"/api/v1/investments/{inv_id}/checklist/tasks/{task_id}")
    assert del_resp.status_code == 200

    # GET valuation comps
    comps_resp = client.get(
        f"/api/v1/investments/{inv_id}/valuation-comps?company_name=TestCo&arr=12000000&valuation=60000000"
    )
    assert comps_resp.status_code == 200
    comps_data = comps_resp.json()
    assert comps_data["current_arr_usd"] == 12_000_000.0
    assert len(comps_data["methodology_ranges"]) == 4

    # GET Excel model download
    excel_resp = client.get(
        f"/api/v1/investments/{inv_id}/financial-model/download-xlsx?company_name=TestCo&arr=12000000&valuation=60000000"
    )
    assert excel_resp.status_code == 200
    assert "openxmlformats" in excel_resp.headers["content-type"]
    assert excel_resp.content.startswith(b"PK\x03\x04")

    # GET Remediation Plan
    rem_resp = client.get(f"/api/v1/investments/{inv_id}/remediation-plan?company_name=TestCo&valuation=50000000")
    assert rem_resp.status_code == 200
    rem_data = rem_resp.json()
    assert rem_data["total_escrow_holdback_usd"] == 5_000_000.0
    assert len(rem_data["conditions_precedent"]) >= 5
    assert len(rem_data["covenants"]) >= 4
    assert len(rem_data["value_creation_plan"]) >= 6

    # PATCH Condition Precedent
    cp_id = rem_data["conditions_precedent"][0]["id"]
    patch_cp = client.patch(
        f"/api/v1/investments/{inv_id}/remediation-plan/conditions/{cp_id}",
        json={"status": "SATISFIED"},
    )
    assert patch_cp.status_code == 200
    assert patch_cp.json()["status"] == "SATISFIED"

    # POST Value Creation Milestone
    post_m = client.post(
        f"/api/v1/investments/{inv_id}/remediation-plan/milestones",
        json={
            "day_range": "DAYS_1_30",
            "workstream": "FINANCE_OPS",
            "milestone_title": "Implement Continuous Cash Flow Forecasting",
            "target_kpi_impact": "Weekly burn visibility; reduce working capital cycle by 14 days.",
            "owner": "FP&A Lead",
        },
    )
    assert post_m.status_code == 200
    assert post_m.json()["milestone_title"] == "Implement Continuous Cash Flow Forecasting"

    # GET External Intelligence
    intel_resp = client.get(f"/api/v1/investments/{inv_id}/external-intel?company_name=TestCo")
    assert intel_resp.status_code == 200
    intel_data = intel_resp.json()
    assert len(intel_data["funding_history"]) >= 3
    assert len(intel_data["competitors"]) >= 3
    assert len(intel_data["executive_team"]) >= 4
    assert intel_data["org_health"]["glassdoor_rating"] == 4.4

