"""Downloadable, watermarked PDFs of saved quarterly and call analyses."""
from html import escape
from io import BytesIO
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from call_analysis import without_key_moments


def inline(text):
    text = str(text).translate(str.maketrans({'\u2011': '-', '\u2013': '-', '\u2014': '-',
                                             '\u2212': '-', '\u2264': '<=', '\u2265': '>=', '\u2192': '->'}))
    text = escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Documents are untrusted: only http(s) links become PDF annotations.
    return re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)', r'<link href="\2" color="#0369a1">\1</link>', text)


def generate_analysis_pdf(result: dict, locale='pt') -> bytes:
    en = locale == 'en'
    meta, data = result.get('metadata') or {}, result.get('data') or {}
    company = str(meta.get('empresa') or meta.get('company') or 'FinAnalyser')
    is_call = meta.get('tipo') == 'Earnings Call'
    title = ('Call analysis' if en else 'Análise do call') if is_call else ('Quarterly analysis' if en else 'Análise trimestral')
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=22*mm, bottomMargin=22*mm, title=f'{company} - {title}', author='FinAnalyser')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('BodyCopy', fontName='Helvetica', fontSize=10, leading=16,
                              textColor=colors.HexColor('#334155'), spaceAfter=9, splitLongWords=True))
    styles.add(ParagraphStyle('Company', parent=styles['Title'], alignment=0, fontSize=25, leading=30,
                              textColor=colors.HexColor('#0f172a'), spaceAfter=10))
    styles.add(ParagraphStyle('Section', parent=styles['Heading2'], textColor=colors.HexColor('#0369a1'),
                              fontSize=12, leading=17, spaceBefore=14, spaceAfter=9))
    styles.add(ParagraphStyle('Score', parent=styles['BodyCopy'], alignment=TA_CENTER, fontSize=9, leading=14))
    story = [Paragraph(inline(company), styles['Company']),
             Paragraph(inline(f'{title} | {meta.get("periodo") or ""}'), styles['BodyCopy']), Spacer(1, 8*mm)]
    if not is_call:
        labels = ['Overall', 'Revenue', 'Net income', 'Net debt', 'Profitability'] if en else ['Geral', 'Receita', 'Lucro líquido', 'Dívida líquida', 'Rentabilidade']
        keys = ['nota_geral', 'receita_nota', 'lucro_nota', 'divida_nota', 'rentabilidade_nota']
        scores = Table([[Paragraph(inline(f'{label}\n{data.get(key, "-")}/5').replace('\n', '<br/>'), styles['Score'])
                         for label, key in zip(labels, keys)]], colWidths=[doc.width/5]*5)
        scores.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f1f5f9')),
                                    ('TOPPADDING',(0,0),(-1,-1),12), ('BOTTOMPADDING',(0,0),(-1,-1),12),
                                    ('VALIGN',(0,0),(-1,-1),'TOP')]))
        story.extend([scores, Spacer(1, 6*mm)])

    # Export the complete saved analysis, including the thesis fallback for older records.
    text = str(result.get('analise_completa') or data.get('tese_investimento') or '')
    if is_call:
        text = without_key_moments(text)
    text = re.sub(r'```json[\s\S]*?```', '', text, flags=re.I)
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('|') and line.endswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                cells = lines[i].strip().strip('|').split('|')
                if not all(re.fullmatch(r'\s*:?-+:?\s*', cell) for cell in cells):
                    rows.append(cells)
                i += 1
            columns = max(map(len, rows), default=0)
            if columns:
                table = Table([[Paragraph(inline(cell.strip()), styles['BodyCopy']) for cell in row] + ['']*(columns-len(row))
                               for row in rows], colWidths=[doc.width/columns]*columns, repeatRows=1, splitInRow=1)
                table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e0f2fe')),
                                           ('GRID',(0,0),(-1,-1),.3,colors.HexColor('#cbd5e1')),
                                           ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),
                                           ('TOPPADDING',(0,0),(-1,-1),6)]))
                story.extend([table, Spacer(1, 4*mm)])
            continue
        heading = bool(re.match(r'^(?:#{1,6}\s|(?:\*\*)?(?:Section|Seção|Se[cç][aã]o)\s*\d+|\d+\.\s)', line, re.I))
        line = re.sub(r'^#{1,6}\s+', '', line)
        bullet = bool(re.match(r'^[-*]\s+', line))
        line = re.sub(r'^[-*]\s+', '', line)
        story.append(Paragraph(inline(line), styles['Section'] if heading else styles['BodyCopy'],
                               bulletText='-' if bullet else None))
        i += 1
    sources = [result.get('source'), *(result.get('financial_sources') or [])]
    sources = [source for source in sources if isinstance(source, dict) and re.match(r'^https?://', str(source.get('url', '')))]
    if sources:
        story.append(Paragraph('Sources' if en else 'Fontes', styles['Section']))
        for source in sources:
            story.append(Paragraph(inline(f'{source.get("name") or "Source"}: {source["url"]}'), styles['BodyCopy']))

    def decorate(canvas, document):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#edf1f6'))
        canvas.translate(A4[0]/2, A4[1]/2)
        canvas.rotate(38)
        canvas.setFont('Helvetica-Bold', 64)
        canvas.drawCentredString(0, 0, 'FinAnalyser')
        canvas.restoreState()
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.setFont('Helvetica', 8)
        canvas.drawString(20*mm, A4[1]-14*mm, 'FinAnalyser | finanalyser.com.br')
        canvas.drawString(20*mm, 12*mm, 'Research - FinAnalyser' if en else 'Pesquisa - FinAnalyser')
        canvas.drawRightString(A4[0]-20*mm, 12*mm, f'{"Page" if en else "Página"} {document.page}')
        canvas.restoreState()

    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return stream.getvalue()
