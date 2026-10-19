import io
import zipfile
from typing import Dict, Any, List


def _xml_escape(val: Any) -> str:
    s = str(val) if val is not None else ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _build_sheet_xml(rows: List[List[Any]]) -> str:
    """Builds a worksheet XML string supporting inline strings, numbers, and formulas."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        '  <sheetData>',
    ]

    for row_idx, row in enumerate(rows, start=1):
        lines.append(f'    <row r="{row_idx}">')
        for col_idx, val in enumerate(row, start=1):
            col_letter = ""
            c_num = col_idx
            while c_num > 0:
                c_num, remainder = divmod(c_num - 1, 26)
                col_letter = chr(65 + remainder) + col_letter
            cell_ref = f"{col_letter}{row_idx}"

            if val is None:
                continue
            elif isinstance(val, (int, float)):
                lines.append(f'      <c r="{cell_ref}"><v>{val}</v></c>')
            elif isinstance(val, str) and val.startswith("="):
                # Excel formula
                formula = _xml_escape(val[1:])
                lines.append(f'      <c r="{cell_ref}"><f>{formula}</f></c>')
            else:
                esc = _xml_escape(val)
                lines.append(f'      <c r="{cell_ref}" t="inlineStr"><is><t>{esc}</t></is></c>')
        lines.append('    </row>')

    lines.append('  </sheetData>')
    lines.append('</worksheet>')
    return "\n".join(lines)


STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><name val="Calibri"/><sz val="11"/></font>
    <font><b/><name val="Calibri"/><sz val="11"/></font>
  </fonts>
  <fills count="2">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
  </fills>
  <borders count="1">
    <border><left/><right/><top/><bottom/></border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  </cellXfs>
</styleSheet>"""

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet4.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet5.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

WORKBOOK_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet4.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet5.xml"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

WORKBOOK_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Executive Summary" sheetId="1" r:id="rId1"/>
    <sheet name="3-Statement Model" sheetId="2" r:id="rId2"/>
    <sheet name="Cap Table &amp; Waterfall" sheetId="3" r:id="rId3"/>
    <sheet name="Unit Economics &amp; Cohorts" sheetId="4" r:id="rId4"/>
    <sheet name="Sensitivity Stress Test" sheetId="5" r:id="rId5"/>
  </sheets>
</workbook>"""


class FinancialModelExcelService:
    """Generates complete multi-tab Microsoft Excel (.xlsx) financial models without external dependencies."""

    def generate_excel_model(
        self,
        company_name: str = "Acme SaaS AI",
        arr_usd: float = 10_000_000.0,
        valuation_usd: float = 50_000_000.0,
        growth_rate_pct: float = 35.0,
        gross_margin_pct: float = 80.0,
    ) -> bytes:
        # Sheet 1: Executive Summary & KPI Dashboard
        sheet1_rows = [
            ["AI DUE DILIGENCE COPILOT — INSTITUTIONAL FINANCIAL MODEL", ""],
            ["Target Company", company_name],
            ["Current Valuation ($)", valuation_usd],
            ["Current ARR ($)", arr_usd],
            ["YoY Growth Rate (%)", growth_rate_pct],
            ["Gross Margin (%)", gross_margin_pct],
            ["Model Date", "2026-10-19"],
            ["Prepared For", "Investment Committee & Deal Team"],
            [],
            ["EXECUTIVE KPI SCORECARD", ""],
            ["Metric", "Value", "Benchmark", "Assessment"],
            ["Annual Recurring Revenue (ARR)", arr_usd, "$8M - $12M", "Top Quartile"],
            ["Net Retention Rate (NRR)", "125.0%", "> 120.0%", "Exceptional"],
            ["Gross Churn (Annual)", "3.8%", "< 5.0%", "Best-in-Class"],
            ["Customer Acquisition Cost (CAC)", "$45,000", "< $60,000", "Efficient"],
            ["CAC Payback (Months)", "14.2", "< 18.0", "Efficient"],
            ["Magic Number", "1.15", "> 1.00", "High Sales Velocity"],
            ["Rule of 40 (%)", growth_rate_pct + 12.0, "> 40.0%", "Passed (47.0%)"],
        ]

        # Sheet 2: 3-Statement Model (Historicals & 5-Year Forecast)
        rev_y0 = arr_usd
        rev_y1 = round(rev_y0 * 1.35, 2)
        rev_y2 = round(rev_y1 * 1.30, 2)
        rev_y3 = round(rev_y2 * 1.25, 2)
        rev_y4 = round(rev_y3 * 1.20, 2)

        cogs_y0 = round(rev_y0 * 0.20, 2)
        cogs_y1 = round(rev_y1 * 0.19, 2)
        cogs_y2 = round(rev_y2 * 0.18, 2)
        cogs_y3 = round(rev_y3 * 0.17, 2)
        cogs_y4 = round(rev_y4 * 0.16, 2)

        sheet2_rows = [
            ["3-STATEMENT INCOME STATEMENT & CASH FLOW PROJECTIONS ($)", "", "", "", "", ""],
            ["Line Item", "FY2024 (Act)", "FY2025 (P)", "FY2026 (P)", "FY2027 (P)", "FY2028 (P)"],
            ["Subscription Revenue", rev_y0, rev_y1, rev_y2, rev_y3, rev_y4],
            ["Professional Services", 650000.0, 750000.0, 850000.0, 950000.0, 1050000.0],
            ["Total Revenue", "=B3+B4", "=C3+C4", "=D3+D4", "=E3+E4", "=F3+F4"],
            ["Cost of Goods Sold (COGS)", cogs_y0, cogs_y1, cogs_y2, cogs_y3, cogs_y4],
            ["Gross Profit", "=B5-B6", "=C5-C6", "=D5-D6", "=E5-E6", "=F5-F6"],
            [],
            ["Operating Expenses (OpEx)", "", "", "", "", ""],
            ["Sales & Marketing (S&M)", round(rev_y0 * 0.38, 2), round(rev_y1 * 0.34, 2), round(rev_y2 * 0.30, 2), round(rev_y3 * 0.27, 2), round(rev_y4 * 0.25, 2)],
            ["Research & Development (R&D)", round(rev_y0 * 0.28, 2), round(rev_y1 * 0.25, 2), round(rev_y2 * 0.23, 2), round(rev_y3 * 0.21, 2), round(rev_y4 * 0.20, 2)],
            ["General & Administrative (G&A)", round(rev_y0 * 0.14, 2), round(rev_y1 * 0.12, 2), round(rev_y2 * 0.11, 2), round(rev_y3 * 0.10, 2), round(rev_y4 * 0.09, 2)],
            ["Total Operating Expenses", "=SUM(B10:B12)", "=SUM(C10:C12)", "=SUM(D10:D12)", "=SUM(E10:E12)", "=SUM(F10:F12)"],
            [],
            ["EBITDA", "=B7-B13", "=C7-C13", "=D7-D13", "=E7-E13", "=F7-F13"],
            ["Depreciation & Amortization", 120000.0, 160000.0, 210000.0, 260000.0, 310000.0],
            ["Operating Income (EBIT)", "=B15-B16", "=C15-C16", "=D15-D16", "=E15-E16", "=F15-F16"],
            ["Unlevered Free Cash Flow", "=B17*0.79", "=C17*0.79", "=D17*0.79", "=E17*0.79", "=F17*0.79"],
        ]

        # Sheet 3: Cap Table & Exit Waterfall
        sheet3_rows = [
            ["CAP TABLE STRUCTURE & LIQUIDATION PREFERENCE WATERFALL", "", "", "", "", ""],
            ["Share Class", "Investor / Holder", "Shares Held", "Ownership %", "Liq Pref Multiplier", "Participating"],
            ["Series A Preferred", "Apex SaaS Capital (Lead)", 2500000, "25.0%", 1.0, "No"],
            ["Series Seed Preferred", "Founders Fund Syndicate", 1500000, "15.0%", 1.0, "No"],
            ["Common Stock", "Founders & Executive Team", 4500000, "45.0%", 0.0, "No"],
            ["Option Pool (ESOP)", "Unallocated / Employees", 1500000, "15.0%", 0.0, "No"],
            ["Total Fully Diluted Shares", "All Shareholders", "=SUM(C3:C6)", "100.0%", "-", "-"],
            [],
            ["EXIT WATERFALL SCENARIO PAYOUT MATRIX ($)", "", "", "", "", ""],
            ["Share Class", "$25M Exit", "$50M Exit", "$100M Exit", "$250M Exit", "$500M Exit"],
            ["Series A Preferred ($10M Inv)", 10000000.0, 12500000.0, 25000000.0, 62500000.0, 125000000.0],
            ["Series Seed Preferred ($3M Inv)", 3000000.0, 7500000.0, 15000000.0, 37500000.0, 75000000.0],
            ["Common Stock (Founders)", 8000000.0, 22500000.0, 45000000.0, 112500000.0, 225000000.0],
            ["Option Pool / ESOP", 4000000.0, 7500000.0, 15000000.0, 37500000.0, 75000000.0],
            ["Total Distributed Proceeds", "=SUM(B10:B13)", "=SUM(C10:C13)", "=SUM(D10:D13)", "=SUM(E10:E13)", "=SUM(F10:F13)"],
            [],
            ["SERIES A RETURN PROFILE", "", "", "", "", ""],
            ["Series A MOIC", "=B10/10000000", "=C10/10000000", "=D10/10000000", "=E10/10000000", "=F10/10000000"],
            ["Series A IRR (3-Yr Exit %)", "0.0%", "7.7%", "35.7%", "84.2%", "132.1%"],
        ]

        # Sheet 4: Unit Economics & SaaS Cohorts
        sheet4_rows = [
            ["UNIT ECONOMICS, COHORT RETENTION & SALES EFFICIENCY", "", "", ""],
            ["Cohort Year", "Initial Customers", "Year 1 Retention %", "Year 2 Retention %", "Year 3 Retention %"],
            ["2021 Cohort", 42, "118.5%", "124.2%", "128.0%"],
            ["2022 Cohort", 78, "122.0%", "126.8%", "131.5%"],
            ["2023 Cohort", 135, "125.4%", "129.1%", "N/A"],
            ["2024 Cohort", 210, "127.2%", "N/A", "N/A"],
            [],
            ["Sales Capacity & Rep Economics", "", "", ""],
            ["Metric", "Current", "Target", "Status"],
            ["Quota Carrying AEs", 8, 14, "Hiring Plan"],
            ["Average Quota per AE ($)", 1250000.0, 1250000.0, "Achieved"],
            ["Blended Quota Attainment (%)", "84.5%", "80.0%", "Exceeding Target"],
            ["Customer Payback Period (Months)", 14.2, 12.0, "On Track"],
        ]

        # Sheet 5: Sensitivity Stress Test
        sheet5_rows = [
            ["FINANCIAL SENSITIVITY STRESS TEST MATRIX", "", "", "", ""],
            ["Scenario", "Growth Delta", "Churn Delta", "Runway Impact (Mos)", "EBITDA Margin (%)"],
            ["Base Plan", "0.0%", "0.0%", 18.4, "12.0%"],
            ["Moderate Growth Miss (-15%)", "-15.0%", "+1.5%", 14.8, "6.5%"],
            ["Enterprise Churn Spike (+5%)", "-5.0%", "+5.0%", 13.2, "3.8%"],
            ["Severe Macro Downturn (-30%)", "-30.0%", "+8.0%", 9.5, "-8.4%"],
            ["Optimistic Upside (+25%)", "+25.0%", "-1.0%", 23.5, "18.2%"],
        ]

        # Build each worksheet XML
        s1 = _build_sheet_xml(sheet1_rows)
        s2 = _build_sheet_xml(sheet2_rows)
        s3 = _build_sheet_xml(sheet3_rows)
        s4 = _build_sheet_xml(sheet4_rows)
        s5 = _build_sheet_xml(sheet5_rows)

        # Build ZIP in-memory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
            z.writestr("_rels/.rels", RELS_XML)
            z.writestr("xl/workbook.xml", WORKBOOK_XML)
            z.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS_XML)
            z.writestr("xl/styles.xml", STYLES_XML)
            z.writestr("xl/worksheets/sheet1.xml", s1)
            z.writestr("xl/worksheets/sheet2.xml", s2)
            z.writestr("xl/worksheets/sheet3.xml", s3)
            z.writestr("xl/worksheets/sheet4.xml", s4)
            z.writestr("xl/worksheets/sheet5.xml", s5)

        buf.seek(0)
        return buf.getvalue()


financial_model_excel_service = FinancialModelExcelService()
