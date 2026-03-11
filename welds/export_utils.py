"""
Shared export utilities for weld data (Excel and PDF).
"""
import io
from datetime import date

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from django.http import HttpResponse


EXPORT_COLUMNS = [
    ("section",      "Section"),
    ("weld_id4",     "Weld ID"),
    ("side",         "Side"),
    ("weld_type",    "Weld Type"),
    ("weld_size",    "Weld Size"),
    ("pass_fail",    "Pass/Fail"),
    ("report",       "Report"),
    ("date",         "Date"),
    ("inspector",    "Inspector"),
    ("repair_welder","Repair Welder"),
    ("note",         "Note"),
]


def generate_excel_response(queryset, filename):
    """Return an HttpResponse containing an .xlsx file for the given queryset."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Weld Data"

    header_font = Font(bold=True)
    header_fill = PatternFill(fill_type="solid", fgColor="1F4E79")
    header_font_white = Font(bold=True, color="FFFFFF")
    center = Alignment(horizontal="center", vertical="center")

    # Header row
    headers = [col_label for _, col_label in EXPORT_COLUMNS]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = center

    # Data rows
    for row_idx, weld in enumerate(queryset, start=2):
        for col_idx, (field, _) in enumerate(EXPORT_COLUMNS, start=1):
            value = getattr(weld, field, "")
            if value is None:
                value = ""
            ws.cell(row=row_idx, column=col_idx, value=str(value) if not isinstance(value, (int, float)) else value)

    # Auto-width columns
    for col_idx in range(1, len(EXPORT_COLUMNS) + 1):
        col_letter = get_column_letter(col_idx)
        max_len = 0
        for cell in ws[col_letter]:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

    # Write to buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def generate_pdf_response(queryset, filename, title, filters_desc=""):
    """Return an HttpResponse containing a landscape PDF for the given queryset."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=4,
    )

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Generated on {date.today().strftime('%B %d, %Y')}", subtitle_style))
    if filters_desc:
        story.append(Paragraph(f"Filters: {filters_desc}", subtitle_style))
    story.append(Spacer(1, 0.4 * cm))

    # Table data
    headers = [col_label for _, col_label in EXPORT_COLUMNS]
    table_data = [headers]

    pass_fill = colors.HexColor("#C6EFCE")
    fail_fill = colors.HexColor("#FFC7CE")

    pass_fail_rows = []  # track row indices (1-based, header is row 0)
    for row_idx, weld in enumerate(queryset, start=1):
        row = []
        for field, _ in EXPORT_COLUMNS:
            value = getattr(weld, field, "") or ""
            row.append(str(value))
        table_data.append(row)
        pf = (getattr(weld, "pass_fail", "") or "").lower()
        if pf == "pass":
            pass_fail_rows.append((row_idx, "pass"))
        elif pf == "fail":
            pass_fail_rows.append((row_idx, "fail"))

    col_widths = [2.5*cm, 2*cm, 1.5*cm, 2.5*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.8*cm, 3*cm, 3*cm, 4*cm]

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("WORDWRAP", (0, 1), (-1, -1), True),
    ]

    # Color-code Pass/Fail column (index 5)
    for row_idx, status in pass_fail_rows:
        fill = pass_fill if status == "pass" else fail_fill
        text_color = colors.HexColor("#276221") if status == "pass" else colors.HexColor("#9C0006")
        style_cmds.append(("BACKGROUND", (5, row_idx), (5, row_idx), fill))
        style_cmds.append(("TEXTCOLOR", (5, row_idx), (5, row_idx), text_color))
        style_cmds.append(("FONTNAME", (5, row_idx), (5, row_idx), "Helvetica-Bold"))

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
