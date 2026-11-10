import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_executive_report(results_list: list) -> str:
    report_path = "/tmp/GFI_Executive_Screening_Report.pdf"
    doc = SimpleDocTemplate(report_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#10b981'),
        spaceAfter=4
    )
    
    story.append(Paragraph("Growth For Impact (GFI) — Applicant Screening Report", title_style))
    story.append(Paragraph(f"Total Applicants Evaluated: <b>{len(results_list)}</b> | Role Alignment Vector Engine", styles['Normal']))
    story.append(Spacer(1, 12))
    
    table_data = [["Candidate File", "Recommended Role", "LCA Score", "UI/UX Score"]]
    for r in results_list:
        table_data.append([
            str(r.get("filename", "Unknown"))[:35],
            str(r.get("recommended_role", "N/A")),
            f"{r.get('lca_match_score', 0)}%",
            f"{r.get('uiux_match_score', 0)}%"
        ])
        
    t = Table(table_data, colWidths=[240, 160, 70, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#111827')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f9fafb')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(t)
    doc.build(story)
    return report_path
