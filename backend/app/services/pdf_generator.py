import io
from datetime import datetime, timezone
from fpdf import FPDF
from app.schemas.card import CardData

class CompliancePDF(FPDF):
    def header(self):
        # Header banner
        self.set_fill_color(31, 31, 31)  # Sidebar color (#1F1F1F)
        self.rect(0, 0, self.w, 24, "F")
        
        self.set_text_color(250, 250, 250)  # Primary text (#FAFAFA)
        self.set_font("Helvetica", "B", 12)
        self.set_xy(10, 7)
        self.cell(0, 10, "AGENT COMPLIANCE CARD GENERATOR", ln=False)
        
        self.set_font("Helvetica", "I", 9)
        self.set_xy(150, 7)
        self.cell(50, 10, "Enterprise AI Governance", align="R")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(113, 113, 122)  # Muted color (#71717A)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Confidential - Internal Compliance Audit File", align="C")


def generate_compliance_pdf(card_name: str, card_data: CardData, completeness_score: float, mappings: dict) -> bytes:
    pdf = CompliancePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(True, margin=15)
    pdf.set_margins(15, 25, 15)
    pdf.add_page()

    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    gutter = 5

    def section_title(title: str, number: str) -> None:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(198, 124, 46)
        pdf.cell(0, 9, f"{number}. {title}", ln=True)
        pdf.ln(1)

    def render_field_label(value: str) -> None:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(21, 21, 21)
        pdf.cell(0, 6, value, ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 51, 51)

    def safe_text(text: str) -> str:
        return text or "-"

    def render_key_value_list(rows: list[tuple[str, str]]) -> None:
        for label, text in rows:
            render_field_label(label)
            pdf.multi_cell(0, 5, safe_text(text))
            pdf.ln(2)

    def current_y() -> float:
        return pdf.get_y()

    def ensure_space(height: float) -> None:
        if pdf.get_y() + height > pdf.h - 15:
            pdf.add_page()

    def render_table_header(columns: list[tuple[str, float]]) -> None:
        pdf.set_fill_color(31, 31, 31)
        pdf.set_text_color(250, 250, 250)
        pdf.set_font("Helvetica", "B", 9)
        for title, width in columns:
            pdf.cell(width, 8, title, border=1, fill=True)
        pdf.ln(8)
        pdf.set_text_color(21, 21, 21)
        pdf.set_font("Helvetica", "", 9)

    def get_multicell_height(text: str, width: float, line_height: float = 5.0) -> float:
        if not text:
            return line_height
        words = text.replace("\n", " ").split(" ")
        line = ""
        num_lines = 1
        for word in words:
            test_line = f"{line} {word}".strip()
            if pdf.get_string_width(test_line) > width - 2:
                line = word
                num_lines += 1
            else:
                line = test_line
        return num_lines * line_height

    def render_row(columns: list[tuple[str, float]]) -> None:
        start_x = pdf.get_x()
        start_y = pdf.get_y()
        heights = [get_multicell_height(text, width) for text, width in columns]
        row_height = max(heights)
        ensure_space(row_height + 4)

        for (text, width), height in zip(columns, heights):
            pdf.set_xy(start_x, start_y)
            pdf.multi_cell(width, 5, text, border=1)
            start_x += width
        pdf.set_xy(15, start_y + row_height)

    # Header content
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(21, 21, 21)
    pdf.cell(0, 10, f"Agent Compliance Card: {card_name}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(113, 113, 122)
    pdf.cell(0, 5, f"Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Version: {card_data.version}", ln=True)
    pdf.ln(4)

    pdf.set_draw_color(198, 124, 46)
    pdf.set_line_width(0.8)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    # Summary metrics panel
    pdf.set_fill_color(43, 43, 43)
    pdf.rect(15, pdf.get_y(), page_width, 28, "F")
    pdf.set_xy(18, pdf.get_y() + 5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(250, 250, 250)
    pdf.cell(55, 6, "Comprehensiveness", ln=0)
    pdf.cell(55, 6, "Risk Classification", ln=0)
    pdf.cell(55, 6, "Confidence", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(250, 250, 250)
    pdf.set_x(18)
    pdf.cell(55, 6, f"{completeness_score}%", ln=0)
    pdf.cell(55, 6, card_data.risk_classification.title(), ln=0)
    pdf.cell(55, 6, f"{int(card_data.confidence_score * 100)}%", ln=1)
    pdf.set_x(18)
    pdf.cell(55, 6, "", ln=0)
    pdf.cell(55, 6, "", ln=0)
    pdf.cell(55, 6, f"{card_data.llm_info.provider} {card_data.llm_info.model_name}", ln=1)
    pdf.ln(10)

    section_title("Executive Summary & Boundaries", "1")
    render_key_value_list([
        ("Purpose", card_data.purpose),
        ("Boundary & Scope", card_data.scope),
    ])

    section_title("LLM, Prompts & Operations", "2")
    render_key_value_list([
        ("Prompt Strategy / System Instructions", card_data.prompt_info),
        ("Operational Bounds", card_data.operations),
    ])

    section_title("Tool Inventory & Access Capabilities", "3")
    ensure_space(40)
    if not card_data.tool_inventory:
        pdf.multi_cell(0, 5, "No tool inventory entries were provided.")
    else:
        columns = [
            ("Tool Name", page_width * 0.2),
            ("Description", page_width * 0.45),
            ("Permissions", page_width * 0.2),
            ("Impact Level", page_width * 0.15)
        ]
        render_table_header(columns)
        for tool in card_data.tool_inventory:
            row_values = [
                (safe_text(tool.name), columns[0][1]),
                (safe_text(tool.description), columns[1][1]),
                (safe_text(", ".join(tool.permissions)), columns[2][1]),
                (safe_text(tool.impact_level.title()), columns[3][1])
            ]
            render_row(row_values)
        pdf.ln(4)

    section_title("Data Governance, Autonomy & Escalation", "4")
    render_key_value_list([
        ("Data Access Permissions", card_data.data_access),
        ("Primary Data Sources", ", ".join(card_data.data_sources)),
        ("Decision Authority", card_data.decision_authority),
        ("Human Oversight", card_data.human_oversight),
        ("Incident Contact", card_data.incident_contact),
        ("Known Limitations", ", ".join(card_data.known_limitations)),
    ])

    section_title("Compliance & Regulation Framework Mapping", "5")
    for fw_name, fw_info in mappings.items():
        ensure_space(35)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(21, 21, 21)
        pdf.cell(0, 6, fw_name, ln=True)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(113, 113, 122)
        pdf.multi_cell(0, 5, safe_text(fw_info.get("description", "")))
        pdf.ln(2)
        mapping_columns = [
            ("ID", page_width * 0.12),
            ("Checkpoint", page_width * 0.42),
            ("Status", page_width * 0.18),
            ("Remediation", page_width * 0.28),
        ]
        render_table_header(mapping_columns)
        for check in fw_info.get("checks", []):
            status = check.get("status", "unknown").title()
            remediation = safe_text(check.get("remediation", "-"))
            render_row([
                (safe_text(str(check.get("id", ""))), mapping_columns[0][1]),
                (safe_text(check.get("title", "")), mapping_columns[1][1]),
                (status, mapping_columns[2][1]),
                (remediation, mapping_columns[3][1]),
            ])
        pdf.ln(4)

    return bytes(pdf.output())
