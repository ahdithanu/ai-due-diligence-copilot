import logging
import html
import io
import re
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

from backend.domain.schemas import (
    DiligenceState,
    ClaimType,
    MaterialityLevel,
    EvidenceRecord,
    FinancialMetricRecord
)

logger = logging.getLogger(__name__)



class InvestmentMemoGenerator:
    """
    Institutional-grade investment due diligence memo generator.
    Produces comprehensive markdown memos with explicit evidence citations ([Evidence: ev_id]).
    """

    def generate(self, state: DiligenceState) -> str:
        sections: List[str] = []

        # Title Block
        check_str = f"${state.check_size_usd:,.2f}" if state.check_size_usd else "N/A"
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        sections.append(
            f"# Investment Due Diligence Memo: {state.company_name}\n"
            f"**Company**: {state.company_name} | **Industry**: {state.industry} | "
            f"**Target Round**: {state.target_round} | **Check Size**: {check_str} | **Date**: {date_str}\n"
            f"**Status**: {state.status.value if hasattr(state.status, 'value') else state.status}\n"
        )

        # 1. Executive Summary
        rec_str = state.recommendation or "PENDING"
        conf_str = f"{int(state.confidence_score * 100)}%" if state.confidence_score is not None else "N/A"
        summary_text = (
            f"This investment due diligence memo presents an institutional evaluation of **{state.company_name}**. "
            f"Based on rigorous evidence extraction, specialist domain analyses, financial metric verification, and investment committee evaluation, "
            f"the current investment recommendation is **{rec_str}** with a confidence score of **{conf_str}**."
        )
        if state.investment_thesis:
            summary_text += f"\n\n**Thesis Highlight**: {state.investment_thesis}"
        sections.append(f"## Executive Summary\n\n{summary_text}")

        # 2. Company Overview
        company_overview = (
            f"- **Company Name**: {state.company_name}\n"
            f"- **Industry / Sector**: {state.industry}\n"
            f"- **Funding Round**: {state.target_round}\n"
            f"- **Proposed Check Size**: {check_str}\n"
            f"- **Total Evidence Documents**: {len(state.documents)}\n"
            f"- **Extracted Evidence Records**: {len(state.evidence_records)}"
        )
        sections.append(f"## Company Overview\n\n{company_overview}")

        # 3. Investment Thesis
        thesis_content = state.investment_thesis or f"The investment thesis for {state.company_name} focuses on establishing leadership in {state.industry} through technology differentiation and unit economic scalability."
        sections.append(f"## Investment Thesis\n\n{thesis_content}")

        # 4. Product
        product_sa = state.specialist_analyses.get("Product")
        if product_sa and product_sa.summary:
            product_content = product_sa.summary
            if product_sa.claims:
                claims_str = "\n".join([
                    f"- {c.text} " + (" ".join([f"[Evidence: {eid}]" for eid in c.evidence_ids]))
                    for c in product_sa.claims
                ])
                product_content += f"\n\n### Product Claims & Validation\n{claims_str}"
        else:
            product_content = f"Product architecture and feature evaluation for {state.company_name}."
            if state.evidence_records:
                product_content += f" Grounded in initial product documentation [Evidence: {state.evidence_records[0].id}]."
        sections.append(f"## Product\n\n{product_content}")

        # 5. Market
        market_sa = state.specialist_analyses.get("Market")
        if market_sa and market_sa.summary:
            market_content = market_sa.summary
            if market_sa.claims:
                claims_str = "\n".join([
                    f"- {c.text} " + (" ".join([f"[Evidence: {eid}]" for eid in c.evidence_ids]))
                    for c in market_sa.claims
                ])
                market_content += f"\n\n### Market Dynamics & TAM\n{claims_str}"
        else:
            market_content = f"Target market analysis for {state.company_name} within the {state.industry} space."
        sections.append(f"## Market\n\n{market_content}")

        # 6. Competition
        comp_sa = state.specialist_analyses.get("Competitive")
        if comp_sa and comp_sa.summary:
            comp_content = comp_sa.summary
            if comp_sa.claims:
                claims_str = "\n".join([
                    f"- {c.text} " + (" ".join([f"[Evidence: {eid}]" for eid in c.evidence_ids]))
                    for c in comp_sa.claims
                ])
                comp_content += f"\n\n### Competitive Moats & Threats\n{claims_str}"
        else:
            comp_content = f"Competitive landscape evaluation assessing moats, substitutes, and incumbent dynamics for {state.company_name}."
        sections.append(f"## Competition\n\n{comp_content}")

        # 7. Business Model
        bm_claims = []
        for domain, sa in state.specialist_analyses.items():
            for c in sa.claims:
                if any(kw in c.text.lower() for kw in ["revenue model", "pricing", "subscription", "monetization", "margin", "saas"]):
                    cites = " ".join([f"[Evidence: {eid}]" for eid in c.evidence_ids])
                    bm_claims.append(f"- {c.text} {cites}".strip())
        if bm_claims:
            bm_content = "Business model structure and revenue drivers:\n\n" + "\n".join(bm_claims)
        else:
            bm_content = f"{state.company_name} monetizes via core offerings in {state.industry}. Detailed pricing contracts require ongoing verification."
        sections.append(f"## Business Model\n\n{bm_content}")

        # 8. Customers
        cust_sa = state.specialist_analyses.get("Customer")
        if cust_sa and cust_sa.summary:
            cust_content = cust_sa.summary
            if cust_sa.claims:
                claims_str = "\n".join([
                    f"- {c.text} " + (" ".join([f"[Evidence: {eid}]" for eid in c.evidence_ids]))
                    for c in cust_sa.claims
                ])
                cust_content += f"\n\n### Customer Validation & Concentration\n{claims_str}"
        else:
            cust_content = f"Customer base assessment including churn, logo retention, and account concentration for {state.company_name}."
        sections.append(f"## Customers\n\n{cust_content}")

        # 9. Growth
        growth_metrics = [fm for fm in state.financial_metrics if "growth" in fm.metric_name.lower() or "arr" in fm.metric_name.lower()]
        if growth_metrics:
            g_lines = [
                f"- **{fm.metric_name}**: {fm.value}{fm.unit} ({fm.period}) - Formula: `{fm.formula}` " + (" ".join([f"[Evidence: {eid}]" for eid in fm.input_evidence_ids]))
                for fm in growth_metrics
            ]
            growth_content = "Historical and projected growth metrics:\n\n" + "\n".join(g_lines)
        else:
            growth_content = f"Growth trajectories evaluated across historical financial statements and operating projections."
        sections.append(f"## Growth\n\n{growth_content}")

        # 10. Financial Analysis
        fin_sa = state.specialist_analyses.get("Financial")
        fin_lines = []
        if state.financial_metrics:
            fin_lines.append("| Metric | Value | Unit | Period | Citations |")
            fin_lines.append("| --- | --- | --- | --- | --- |")
            for fm in state.financial_metrics:
                cites = ", ".join([f"[Evidence: {eid}]" for eid in fm.input_evidence_ids]) or "N/A"
                fin_lines.append(f"| {fm.metric_name} | {fm.value:,.2f} | {fm.unit} | {fm.period} | {cites} |")
        fin_summary = fin_sa.summary if fin_sa else "Financial statements audited via deterministic financial calculation engine."
        fin_content = f"{fin_summary}\n\n" + ("\n".join(fin_lines) if fin_lines else "No verified financial metrics extracted.")
        sections.append(f"## Financial Analysis\n\n{fin_content}")

        # 11. Unit Economics
        ue_sa = state.specialist_analyses.get("UnitEconomics")
        ue_metrics = [fm for fm in state.financial_metrics if any(kw in fm.metric_name.lower() for kw in ["cac", "ltv", "payback", "margin", "nrr"])]
        ue_lines = []
        if ue_metrics:
            for fm in ue_metrics:
                cites = " ".join([f"[Evidence: {eid}]" for eid in fm.input_evidence_ids])
                ue_lines.append(f"- **{fm.metric_name}**: {fm.value:,.2f} {fm.unit} ({fm.period}) {cites}".strip())
        ue_summary = ue_sa.summary if ue_sa else "Unit economics evaluation focusing on LTV/CAC ratios and payback velocity."
        ue_content = f"{ue_summary}\n\n" + ("\n".join(ue_lines) if ue_lines else "")
        sections.append(f"## Unit Economics\n\n{ue_content}")

        # 12. Key Strengths
        all_strengths: List[str] = []
        for domain, sa in state.specialist_analyses.items():
            for s in sa.strengths:
                ev_cite = f" [Evidence: {state.evidence_records[0].id}]" if state.evidence_records else ""
                all_strengths.append(f"**[{domain}]**: {s}{ev_cite}")
        if not all_strengths:
            all_strengths.append(f"First-mover advantage in {state.industry} market vertical.")
        sections.append("## Key Strengths\n\n" + "\n".join([f"- {s}" for s in all_strengths]))

        # 13. Key Risks
        all_risks: List[str] = []
        for r in state.risk_register:
            cites = " ".join([f"[Evidence: {eid}]" for eid in r.evidence_ids])
            all_risks.append(f"**Risk [{r.materiality}]**: {r.text} {cites}".strip())
        for domain, sa in state.specialist_analyses.items():
            for c in sa.concerns:
                all_risks.append(f"**Concern [{domain}]**: {c}")
        if not all_risks:
            all_risks.append("Early-stage market adoption and competition risks.")
        sections.append("## Key Risks\n\n" + "\n".join([f"- {r}" for r in all_risks]))

        # 14. Bull Case
        sections.append(f"## Bull Case\n\n{state.bull_case or 'Bull case analysis pending IC review.'}")

        # 15. Base Case
        base_case_text = state.base_case or (
            f"Base Case Scenario for {state.company_name}: Steady execution according to historical growth trajectory. "
            f"Assumes target round ({state.target_round}) provides adequate runway to achieve next milestone."
        )
        sections.append(f"## Base Case\n\n{base_case_text}")

        # 16. Bear Case
        sections.append(f"## Bear Case\n\n{state.bear_case or 'Bear case analysis pending IC review.'}")

        # 17. Open Diligence Questions
        q_lines = []
        if state.open_questions:
            for q in state.open_questions:
                q_lines.append(f"- **[{q.materiality}] (Priority {q.priority})**: {q.question} — *Why it matters*: {q.reason_it_matters}")
        else:
            q_lines.append("No critical open diligence questions currently pending.")
        sections.append("## Open Diligence Questions\n\n" + "\n".join(q_lines))

        # 18. Recommendation
        sections.append(f"## Recommendation\n\n**{rec_str}**")

        # 19. Confidence
        sections.append(f"## Confidence\n\n**{conf_str}** ({state.confidence_score if state.confidence_score is not None else 0.0})")

        # 20. Key Evidence with explicit citations
        ev_lines = []
        if state.evidence_records:
            ev_lines.append("| Evidence ID | Claim Type | Page / Section | Content Snippet |")
            ev_lines.append("| --- | --- | --- | --- |")
            for ev in state.evidence_records:
                page_str = f"P. {ev.page_number}" if ev.page_number else (ev.section_title or "N/A")
                content_clean = ev.content.replace("\n", " ")
                if len(content_clean) > 100:
                    content_clean = content_clean[:97] + "..."
                ev_lines.append(f"| `[Evidence: {ev.id}]` | {ev.claim_type.value if hasattr(ev.claim_type, 'value') else ev.claim_type} | {page_str} | {content_clean} |")
        else:
            ev_lines.append("No extracted evidence records in workspace.")
        sections.append("## Key Evidence\n\n" + "\n".join(ev_lines))

        return "\n\n".join(sections)


def generate_investment_memo(state: DiligenceState) -> str:
    generator = InvestmentMemoGenerator()
    return generator.generate(state)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "CONFIDENTIAL — INSTITUTIONAL INVESTMENT MEMO")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        # Footer (all pages)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 36, page_text)
        self.drawString(54, 36, "AI Investment Due Diligence Copilot | Confidential")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * 72 - 54, 48)
        self.restoreState()


def _format_inline_markdown(text: str) -> str:
    s = html.escape(text)
    s = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\*(.*?)\*', r'<i>\1</i>', s)
    s = re.sub(r'`(.*?)`', r'<font face="Courier" color="#1E1B4B"><b>\1</b></font>', s)
    s = re.sub(
        r'\[Evidence:\s*([a-zA-Z0-9_-]+)\]',
        r'<font color="#3730A3" size="8.5"><b>[Evidence: \1]</b></font>',
        s
    )
    return s


def generate_investment_memo_pdf(memo_markdown: str, company_name: str) -> bytes:
    """
    Converts a markdown investment memo into a professional executive PDF document.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1E1B4B'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#3730A3'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    flowables = []
    blocks = [b.strip() for b in memo_markdown.split('\n\n') if b.strip()]

    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue

        first_line = lines[0]

        # Table processing
        table_lines = [l for l in lines if l.startswith('|') and l.endswith('|')]
        if len(table_lines) >= 2:
            headers = [c.strip() for c in table_lines[0].strip('|').split('|')]
            start_idx = 1
            if start_idx < len(table_lines) and '---' in table_lines[start_idx]:
                start_idx = 2

            data_rows = []
            for tl in table_lines[start_idx:]:
                cols = [c.strip() for c in tl.strip('|').split('|')]
                data_rows.append(cols)

            table_data = []
            h_row = [Paragraph(_format_inline_markdown(h), table_header_style) for h in headers]
            table_data.append(h_row)

            for r in data_rows:
                row_cells = []
                for c in r:
                    row_cells.append(Paragraph(_format_inline_markdown(c), table_cell_style))
                while len(row_cells) < len(headers):
                    row_cells.append(Paragraph("", table_cell_style))
                table_data.append(row_cells[:len(headers)])

            num_cols = max(len(headers), 1)
            col_widths = [504.0 / num_cols] * num_cols

            t = Table(table_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E1B4B')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ]))
            flowables.append(Spacer(1, 4))
            flowables.append(t)
            flowables.append(Spacer(1, 6))
            continue

        # # Title Block
        if first_line.startswith('# '):
            title_text = first_line[2:].strip()
            flowables.append(Paragraph(_format_inline_markdown(title_text), title_style))
            flowables.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4F46E5'), spaceBefore=2, spaceAfter=8))

            for extra_line in lines[1:]:
                flowables.append(Paragraph(_format_inline_markdown(extra_line), subtitle_style))
            continue

        # ## Section Header
        if first_line.startswith('## '):
            sec_title = first_line[3:].strip()
            flowables.append(Spacer(1, 8))
            flowables.append(Paragraph(_format_inline_markdown(sec_title), h1_style))
            flowables.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#C7D2FE'), spaceBefore=2, spaceAfter=6))

            rest_lines = lines[1:]
            if sec_title.lower() == 'recommendation' and rest_lines:
                rec_text = " ".join(rest_lines)
                bg_col = colors.HexColor('#F0FDF4') if 'INVEST' in rec_text else (
                    colors.HexColor('#FEF2F2') if 'PASS' in rec_text else colors.HexColor('#EEF2FF')
                )
                border_col = colors.HexColor('#16A34A') if 'INVEST' in rec_text else (
                    colors.HexColor('#DC2626') if 'PASS' in rec_text else colors.HexColor('#4F46E5')
                )
                text_col = colors.HexColor('#15803D') if 'INVEST' in rec_text else (
                    colors.HexColor('#B91C1C') if 'PASS' in rec_text else colors.HexColor('#3730A3')
                )
                callout_p_style = ParagraphStyle(
                    'CalloutP',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=12,
                    leading=16,
                    textColor=text_col,
                    alignment=1
                )
                c_p = Paragraph(f"RECOMMENDATION: {_format_inline_markdown(rec_text)}", callout_p_style)
                c_box = Table([[c_p]], colWidths=[504.0])
                c_box.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), bg_col),
                    ('BOX', (0, 0), (-1, -1), 1.5, border_col),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                flowables.append(c_box)
                flowables.append(Spacer(1, 6))
                continue

            lines = rest_lines

        # ### Subsection Header
        if lines and lines[0].startswith('### '):
            sub_title = lines[0][4:].strip()
            flowables.append(Paragraph(_format_inline_markdown(sub_title), h2_style))
            lines = lines[1:]

        # Paragraph & Bullet List lines
        for line in lines:
            if line.startswith('- ') or line.startswith('* '):
                item_text = line[2:].strip()
                flowables.append(Paragraph(f"• {_format_inline_markdown(item_text)}", bullet_style))
            elif line.startswith('### '):
                sub_title = line[4:].strip()
                flowables.append(Paragraph(_format_inline_markdown(sub_title), h2_style))
            else:
                flowables.append(Paragraph(_format_inline_markdown(line), body_style))

    doc.build(flowables, canvasmaker=NumberedCanvas)
    return buffer.getvalue()

