"""PDF de entrega de credenciales iniciales de CMs y admins (especificación,
sección 2: la contraseña se muestra una sola vez, para entregar por un canal
seguro). Este documento es la versión imprimible/archivable de ese momento
único; el backend nunca vuelve a tener la contraseña en claro después.
"""
import datetime as dt
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.platypus import Image, SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.reports.branding import BORDER, INK, INK_LIGHT, LOGO_PATH, ORANGE, PURPLE, PURPLE_DARK, SURFACE_ALT

ROL_LABEL = {'cm': 'Community Manager', 'admin': 'Administrador'}


def generar_pdf_credenciales(usuarios: list[dict], output_path: str | Path) -> None:
    """usuarios: [{"nombre", "username", "password", "rol"}, ...]"""
    doc = SimpleDocTemplate(
        str(output_path), pagesize=letter,
        topMargin=22 * mm, bottomMargin=18 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleInn', parent=styles['Title'], textColor=PURPLE_DARK, fontSize=20, spaceAfter=2)
    subtitle_style = ParagraphStyle('SubtitleInn', parent=styles['Normal'], textColor=INK_LIGHT, fontSize=10, spaceAfter=16)
    note_style = ParagraphStyle('NoteInn', parent=styles['Normal'], textColor=INK, fontSize=9, leading=13)

    logo = Image(str(LOGO_PATH), width=15 * mm, height=15 * mm) if LOGO_PATH.exists() else Spacer(1, 1)
    encabezado = Table(
        [[logo, Paragraph('INNquietus', title_style)]],
        colWidths=[20 * mm, None],
    )
    encabezado.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    story = [
        encabezado,
        Paragraph(f"Credenciales de acceso inicial — generadas el {dt.date.today().strftime('%d/%m/%Y')}", subtitle_style),
    ]

    header = ['Nombre', 'Usuario', 'Contraseña', 'Rol']
    rows = [header] + [
        [u['nombre'], u['username'], u['password'], ROL_LABEL.get(u['rol'], u['rol'])]
        for u in usuarios
    ]
    table = Table(rows, colWidths=[45 * mm, 40 * mm, 45 * mm, 38 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('FONTNAME', (2, 1), (2, -1), 'Courier'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, SURFACE_ALT]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), INK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(table)
    story.append(Spacer(1, 18))

    story.append(Paragraph(
        '<b>Importante:</b> estas contraseñas se generaron una sola vez y el sistema no vuelve a mostrarlas. '
        'Entrégalas por un canal seguro (por ejemplo WhatsApp directo a cada persona) y pide que las guarden '
        'en un gestor de contraseñas. Si alguien la pierde, un admin puede generar una nueva desde '
        '"Reseteo de contraseñas" — eso invalida la anterior de inmediato.',
        note_style,
    ))

    def _footer(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(ORANGE)
        canvas.rect(0, 0, doc.pagesize[0], 4, fill=1, stroke=0)
        canvas.setFillColor(INK_LIGHT)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(20 * mm, 10 * mm, 'INNquietus · Documento confidencial de uso interno')
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


def generar_txt_credenciales(usuarios: list[dict], output_path: str | Path) -> None:
    lines = [
        'INNquietus — Credenciales de acceso inicial',
        f"Generado el {dt.date.today().strftime('%d/%m/%Y')}",
        '',
    ]
    for u in usuarios:
        lines.append(f"{u['nombre']}")
        lines.append(f"  Usuario:    {u['username']}")
        lines.append(f"  Contraseña: {u['password']}")
        lines.append(f"  Rol:        {ROL_LABEL.get(u['rol'], u['rol'])}")
        lines.append('')
    lines.append('Documento confidencial de uso interno — no reenviar por canales no seguros.')
    Path(output_path).write_text('\n'.join(lines), encoding='utf-8')
