"""
report_generator.py
────────────────────────────────────────────────────────────
Módulo de geração de relatório HTML para o FinAnalyzer.

COMO USAR:
1. Coloque este arquivo na mesma pasta que main.py
2. No main.py, adicione no topo:
      from report_generator import generate_report_html, router as report_router
   E logo depois do app = FastAPI(...):
      app.include_router(report_router)

Isso cria dois endpoints:
  GET  /api/report/{item_id}          → HTML completo para abrir no browser / imprimir
  GET  /api/report/{item_id}/preview  → mesmo HTML em iframe (para o frontend)
────────────────────────────────────────────────────────────
"""

import json
import re
import html as html_lib
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter()


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _score_color(n: float) -> dict:
    """Retorna as cores CSS para cada faixa de nota."""
    if n >= 4.0:
        return {"text": "#0A6640", "bg": "#D1FAE5", "border": "#6EE7B7", "label": "Excelente"}
    if n >= 3.0:
        return {"text": "#1D4ED8", "bg": "#DBEAFE", "border": "#93C5FD", "label": "Bom"}
    if n >= 2.0:
        return {"text": "#92400E", "bg": "#FEF3C7", "border": "#FDE68A", "label": "Regular"}
    return {"text": "#991B1B", "bg": "#FEE2E2", "border": "#FCA5A5", "label": "Fraco"}


def _bar_pct(n: float) -> int:
    return min(100, int((n / 5.0) * 100))


def _pillar_color_class(key: str) -> str:
    return {"receita": "blue", "lucro": "green", "divida": "red", "rentabilidade": "amber"}.get(key, "blue")


def _safe_float(val) -> float:
    try:
        return float(str(val).replace(",", ".").strip())
    except Exception:
        return 0.0


def _extract_chart_data(analise_text: str) -> list:
    """Extrai o array JSON da Seção 7 da análise do Gemini."""
    if not analise_text:
        return []
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", analise_text)
        if match:
            return json.loads(match.group(1))
    except Exception:
        pass
    return []


def _clean_markdown(text: str) -> str:
    """Converte markdown simples em HTML."""
    if not text:
        return ""
    # Tabelas markdown → HTML básico
    lines = text.split("\n")
    result = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_table:
                result.append('<div class="md-table-wrap"><table class="md-table">')
                in_table = True
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(re.match(r"^[-:]+$", c) for c in cells):
                continue  # linha separadora
            tag = "th" if not any(isinstance(r, str) and "<th>" in r for r in result[-3:]) else "td"
            row = "".join(f"<{tag}>{html_lib.escape(c)}</{tag}>" for c in cells)
            result.append(f"<tr>{row}</tr>")
        else:
            if in_table:
                result.append("</table></div>")
                in_table = False
            # bold
            stripped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
            # bullet
            if stripped.startswith("- ") or stripped.startswith("• "):
                stripped = f"<li>{stripped[2:]}</li>"
            elif stripped.startswith("* "):
                stripped = f"<li>{stripped[2:]}</li>"
            result.append(stripped)
    if in_table:
        result.append("</table></div>")

    # Wrap <li> em <ul>
    output = "\n".join(result)
    output = re.sub(r"(<li>.*?</li>\n?)+", lambda m: f"<ul>{m.group(0)}</ul>", output, flags=re.DOTALL)

    # Parágrafos
    paras = re.split(r"\n{2,}", output)
    html_parts = []
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if p.startswith("<"):
            html_parts.append(p)
        else:
            html_parts.append(f"<p>{p}</p>")
    return "\n".join(html_parts)


def _parse_sections(analise_text: str) -> list:
    """
    Quebra a análise completa em seções limpas.
    Retorna lista de dicts: {title, body, nota}
    """
    if not analise_text:
        return []

    section_titles = {
        1: "Evolução Operacional e Top Line",
        2: "Rentabilidade e Margens",
        3: "Estrutura de Capital e Gestão de Risco",
        4: "Sumário Executivo do Lucro Líquido",
        5: "Conclusão Estratégica e Outlook",
    }

    sections = []

    # Parágrafo introdutório (antes da Seção 1)
    intro_match = re.search(r"^([\s\S]*?)(?=\*?\*?Seção\s*1)", analise_text, re.IGNORECASE)
    if intro_match:
        intro_body = intro_match.group(1).strip().replace("**", "")
        if intro_body:
            sections.append({"title": "Visão Geral do Trimestre", "body": intro_body, "nota": None, "num": 0})

    for num in range(1, 6):
        pattern = rf"\*?\*?Seção\s*{num}[:\s\–\-].*?\n([\s\S]*?)(?=\*?\*?Seção\s*{num+1}|\Z)"
        match = re.search(pattern, analise_text, re.IGNORECASE)
        if match:
            body = match.group(1).strip()
            # Extrai nota
            nota_match = re.search(rf"Nota\s+Seção\s+{num}[:\s]+(\d(?:[.,]\d)?)\s*/\s*5", body, re.IGNORECASE)
            nota = _safe_float(nota_match.group(1)) if nota_match else None
            # Remove a linha de nota do body
            body = re.sub(rf"\*?\*?Nota\s+Seção\s+{num}[:\s]+\d[.,]?\d?\s*/\s*5\*?\*?", "", body).strip()
            # Remove bloco JSON
            body = re.sub(r"```json[\s\S]*?```", "", body).strip()
            sections.append({
                "title": section_titles.get(num, f"Seção {num}"),
                "body": body,
                "nota": nota,
                "num": num,
            })

    return sections


# ──────────────────────────────────────────────
# TEMPLATE HTML PRINCIPAL
# ──────────────────────────────────────────────

def generate_report_html(resultado: dict) -> str:
    meta = resultado.get("metadata", {})
    data = resultado.get("data", {})
    analise = resultado.get("analise_completa", "")

    empresa = (meta.get("empresa") or "Empresa").upper()
    periodo = meta.get("periodo") or ""

    receita_nota    = _safe_float(data.get("receita_nota", 0))
    lucro_nota      = _safe_float(data.get("lucro_nota", 0))
    divida_nota     = _safe_float(data.get("divida_nota", 0))
    rentab_nota     = _safe_float(data.get("rentabilidade_nota", 0))
    nota_geral      = _safe_float(data.get("nota_geral", 0))
    tese            = data.get("tese_investimento", "")

    score_colors = _score_color(nota_geral)

    # KPI cards
    pillars = [
        {"label": "Receita",           "nota": receita_nota, "key": "blue",  "icon": "dollar"},
        {"label": "Margem / Lucro",    "nota": lucro_nota,   "key": "green", "icon": "percent"},
        {"label": "Dívida / Risco",    "nota": divida_nota,  "key": "red",   "icon": "alert"},
        {"label": "Rentabilidade ROE", "nota": rentab_nota,  "key": "amber", "icon": "trend"},
    ]

    def pillar_card(p):
        c = _score_color(p["nota"])
        icons = {
            "dollar":  '<path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
            "percent": '<line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
            "alert":   '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
            "trend":   '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
        }
        color_map = {
            "blue":  ("var(--itau)",    "var(--itau-bg)"),
            "green": ("var(--emerald)", "var(--emerald-light)"),
            "red":   ("#DC2626",        "var(--red-light)"),
            "amber": ("#D97706",        "var(--amber-light)"),
        }
        top_color, icon_bg = color_map[p["key"]]
        nota_fmt = f"{p['nota']:.1f}"
        bar_pct  = _bar_pct(p["nota"])
        return f"""
        <div class="kpi-card">
          <div style="width:36px;height:36px;border-radius:6px;background:{icon_bg};display:flex;align-items:center;justify-content:center;margin-bottom:16px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{top_color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              {icons[p['icon']]}
            </svg>
          </div>
          <div style="font-size:12px;color:var(--ink-40);font-weight:500;margin-bottom:8px;">{p['label']}</div>
          <div style="font-family:'Playfair Display',serif;font-size:36px;font-weight:700;line-height:1;color:var(--ink);margin-bottom:4px;">
            {nota_fmt}<span style="font-size:15px;color:var(--ink-40);font-family:'DM Sans',sans-serif;font-weight:300;">/5</span>
          </div>
          <div style="height:4px;background:var(--ink-20);border-radius:99px;margin-top:14px;overflow:hidden;">
            <div style="height:100%;width:{bar_pct}%;background:{top_color};border-radius:99px;"></div>
          </div>
          <span style="display:inline-block;margin-top:10px;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;background:{c['bg']};color:{c['text']};">{c['label']}</span>
        </div>"""

    kpi_html = "".join(pillar_card(p) for p in pillars)

    # Seções da análise
    sections = _parse_sections(analise)
    chart_data_raw = _extract_chart_data(analise)

    def render_section(s):
        nota_badge = ""
        if s["nota"] is not None:
            c = _score_color(s["nota"])
            nota_badge = f"""
            <span style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;
              border-radius:6px;font-size:12px;font-weight:700;
              background:{c['bg']};color:{c['text']};border:1px solid {c['border']};margin-left:auto;">
              {s['nota']:.1f}/5 — {c['label']}
            </span>"""
        body_html = _clean_markdown(s["body"])
        num_label = f"Seção {s['num']} — " if s["num"] > 0 else ""
        return f"""
        <div class="section-block avoid-break">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--ink-20);">
            <h2 style="font-family:'Playfair Display',serif;font-size:22px;font-weight:700;color:var(--ink);letter-spacing:-0.01em;flex:1;">
              <span style="font-size:13px;font-weight:400;color:var(--ink-40);display:block;margin-bottom:4px;font-family:'DM Sans',sans-serif;">{num_label}</span>
              {html_lib.escape(s['title'])}
            </h2>
            {nota_badge}
          </div>
          <div class="analysis-body">
            {body_html}
          </div>
        </div>"""

    sections_html = "".join(render_section(s) for s in sections)

    # Chart data JSON para JS
    chart_json = json.dumps(chart_data_raw) if chart_data_raw else "[]"

    # Tese de investimento limpa
    tese_clean = re.sub(r"\*\*|\*", "", tese).strip()
    tese_paras = "".join(f"<p>{html_lib.escape(p.strip())}</p>" for p in tese_clean.split("\n\n") if p.strip())
    if not tese_paras:
        tese_paras = f"<p>{html_lib.escape(tese_clean)}</p>"

    # Score cover color
    sc = _score_color(nota_geral)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{empresa} — Análise {periodo} · FinAnalyzer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --itau:#003087;--itau-light:#1a4db3;--itau-bg:#EEF3FF;
  --emerald:#0A6640;--emerald-light:#D1FAE5;
  --red:#991B1B;--red-light:#FEE2E2;
  --amber:#92400E;--amber-light:#FEF3C7;
  --ink:#0F172A;--ink-60:#475569;--ink-40:#94A3B8;--ink-20:#E2E8F0;
  --page:#FAFAF9;--white:#FFFFFF;--radius:12px;
}}
html{{font-size:16px}}
body{{font-family:'DM Sans',system-ui,sans-serif;background:var(--page);color:var(--ink);line-height:1.65;-webkit-font-smoothing:antialiased}}
@media print{{
  body{{background:white}}
  .no-print{{display:none!important}}
  .page-break{{break-before:page}}
  .avoid-break{{break-inside:avoid}}
}}

/* COVER */
.cover{{min-height:100vh;display:flex;flex-direction:column;justify-content:space-between;padding:64px 72px;background:var(--white);border-bottom:1px solid var(--ink-20);position:relative;overflow:hidden}}
.cover::before{{content:'';position:absolute;top:0;right:0;width:480px;height:480px;background:radial-gradient(circle at 100% 0%,var(--itau-bg) 0%,transparent 70%);pointer-events:none}}
.cover-header{{display:flex;justify-content:space-between;align-items:flex-start}}
.brand-mark{{display:flex;align-items:center;gap:12px}}
.brand-cube{{width:36px;height:36px;background:var(--itau);border-radius:8px;display:flex;align-items:center;justify-content:center}}
.brand-name{{font-weight:600;font-size:15px;color:var(--itau);letter-spacing:-0.02em}}
.brand-sub{{font-size:11px;color:var(--ink-40);display:block;margin-top:-2px}}
.period-pill{{background:var(--itau-bg);border:1px solid #C7D7F5;border-radius:999px;padding:6px 16px;font-size:12px;font-weight:500;color:var(--itau);letter-spacing:.04em;text-transform:uppercase}}
.cover-body{{flex:1;display:flex;flex-direction:column;justify-content:center;padding:80px 0 60px}}
.cover-eyebrow{{font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-40);margin-bottom:24px}}
.cover-title{{font-family:'Playfair Display',Georgia,serif;font-size:clamp(52px,7vw,84px);font-weight:900;line-height:.95;letter-spacing:-.03em;color:var(--ink);margin-bottom:32px}}
.cover-title span{{color:var(--itau)}}
.cover-desc{{font-size:17px;color:var(--ink-60);font-weight:300;max-width:560px;line-height:1.6}}
.score-block{{display:flex;align-items:center;gap:40px;margin-top:64px;padding-top:48px;border-top:1px solid var(--ink-20)}}
.score-number{{font-family:'Playfair Display',serif;font-size:88px;font-weight:900;line-height:1;letter-spacing:-.04em}}
.score-denom{{font-size:28px;color:var(--ink-40);font-weight:300}}
.score-label{{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-40)}}
.score-desc{{font-size:20px;font-weight:600;margin-top:4px}}
.cover-footer{{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--ink-40)}}
.badge-warning{{display:flex;align-items:center;gap:6px;background:#FEF3C7;border:1px solid #FDE68A;border-radius:4px;padding:4px 10px;font-size:11px;font-weight:600;color:var(--amber);letter-spacing:.06em;text-transform:uppercase}}

/* CONTENT */
.content{{max-width:1100px;margin:0 auto;padding:80px 48px}}
.section-label{{font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--itau);margin-bottom:10px}}
.section-title{{font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:var(--ink);margin-bottom:40px;letter-spacing:-.02em}}
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:64px}}
.kpi-card{{background:var(--white);border:1px solid var(--ink-20);border-radius:var(--radius);padding:24px}}
.charts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:64px}}
.chart-card{{background:var(--white);border:1px solid var(--ink-20);border-radius:var(--radius);padding:32px}}
.chart-wrap{{position:relative;width:100%;height:220px}}
.chart-full{{background:var(--white);border:1px solid var(--ink-20);border-radius:var(--radius);padding:40px;margin-bottom:64px}}
.chart-full-wrap{{position:relative;width:100%;height:280px}}
.section-divider{{height:1px;background:var(--ink-20);margin:64px 0}}
.section-block{{background:var(--white);border:1px solid var(--ink-20);border-radius:var(--radius);padding:40px;margin-bottom:24px}}
.analysis-body{{font-size:15px;line-height:1.8;color:var(--ink-60)}}
.analysis-body p{{margin-bottom:16px}}
.analysis-body strong{{color:var(--ink);font-weight:600}}
.analysis-body ul{{margin:12px 0 16px 20px;}}
.analysis-body li{{margin-bottom:6px}}
.md-table-wrap{{overflow-x:auto;margin:16px 0}}
.md-table{{width:100%;border-collapse:collapse;font-size:13px}}
.md-table th,.md-table td{{padding:10px 14px;text-align:left;border-bottom:1px solid var(--ink-20)}}
.md-table th{{background:var(--itau-bg);color:var(--itau);font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase}}
.md-table tr:last-child td{{border-bottom:none}}
.md-table tr:hover td{{background:#F8FAFC}}
.conclusion{{background:var(--ink);border-radius:var(--radius);padding:56px 64px;margin-bottom:64px;position:relative;overflow:hidden}}
.conclusion::before{{content:'"';position:absolute;top:-24px;left:48px;font-family:'Playfair Display',serif;font-size:240px;color:rgba(255,255,255,.04);line-height:1;pointer-events:none}}
.conclusion-label{{font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#60A5FA;margin-bottom:24px;display:flex;align-items:center;gap:8px}}
.conclusion-label::before{{content:'';display:block;width:24px;height:1px;background:#60A5FA}}
.conclusion-title{{font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:white;line-height:1.2;margin-bottom:28px;letter-spacing:-.02em}}
.conclusion-body{{font-size:15px;color:#CBD5E1;line-height:1.8;max-width:720px}}
.conclusion-body p{{margin-bottom:16px}}
.verdict-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;border-top:1px solid rgba(255,255,255,.1);padding-top:40px;margin-top:40px}}
.verdict-label{{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:8px}}
.verdict-value{{font-size:16px;font-weight:600;color:white}}
.tag{{display:inline-block;padding:4px 12px;border-radius:4px;font-size:12px;font-weight:700;margin-top:6px;letter-spacing:.04em;text-transform:uppercase}}
.tag-buy{{background:rgba(16,185,129,.2);color:#34D399;border:1px solid rgba(16,185,129,.3)}}
.tag-watch{{background:rgba(251,191,36,.15);color:#FBBF24;border:1px solid rgba(251,191,36,.25)}}
.tag-neutral{{background:rgba(148,163,184,.15);color:#94A3B8;border:1px solid rgba(148,163,184,.2)}}
.report-footer{{border-top:1px solid var(--ink-20);padding:32px 48px;max-width:1100px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--ink-40)}}
.print-btn{{position:fixed;top:24px;right:24px;background:var(--itau);color:white;border:none;border-radius:6px;padding:10px 20px;font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:8px;z-index:100;box-shadow:0 4px 16px rgba(0,48,135,.3);transition:opacity .2s}}
.print-btn:hover{{opacity:.88}}
@media(max-width:900px){{
  .kpi-grid{{grid-template-columns:repeat(2,1fr)}}
  .charts-grid{{grid-template-columns:1fr}}
  .cover{{padding:40px 24px}}
  .content{{padding:40px 20px}}
  .cover-title{{font-size:42px}}
  .score-number{{font-size:56px}}
  .conclusion{{padding:36px 28px}}
  .verdict-grid{{grid-template-columns:1fr 1fr}}
  .section-block{{padding:24px}}
}}
</style>
</head>
<body>

<button class="print-btn no-print" onclick="window.print()">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
  Salvar PDF
</button>

<!-- ══ CAPA ══ -->
<div class="cover">
  <div class="cover-header">
    <div class="brand-mark">
      <div class="brand-cube">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22" stroke="rgba(255,255,255,.5)" stroke-width="1.5" fill="none"/></svg>
      </div>
      <div>
        <span class="brand-name">FinAnalyzer</span>
        <span class="brand-sub">Análise Fundamentalista por IA</span>
      </div>
    </div>
    <div class="period-pill">{html_lib.escape(periodo)} · Resultados Trimestrais</div>
  </div>

  <div class="cover-body">
    <div class="cover-eyebrow">Relatório de Análise Fundamentalista</div>
    <h1 class="cover-title">{html_lib.escape(empresa.title())}<br><span>{html_lib.escape(periodo)}</span></h1>
    <p class="cover-desc">
      Relatório completo gerado por IA com base no release de resultados oficial.
      Avaliação de receita, margens, endividamento e rentabilidade com visão estratégica.
    </p>

    <div class="score-block">
      <div style="display:flex;align-items:baseline;gap:6px;">
        <span class="score-number" style="color:{sc['text']};">{nota_geral:.1f}</span>
        <span class="score-denom">/5</span>
      </div>
      <div>
        <div class="score-label">Score IA — Média Ponderada</div>
        <div class="score-desc" style="color:{sc['text']};">{sc['label']}</div>
      </div>
    </div>
  </div>

  <div class="cover-footer">
    <span>Gerado automaticamente · Dados do release oficial</span>
    <div class="badge-warning">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      Não é recomendação de investimento
    </div>
  </div>
</div>

<!-- ══ CONTEÚDO ══ -->
<div class="content">

  <!-- KPIs -->
  <div style="margin-bottom:48px;">
    <div class="section-label">Avaliação Fundamentalista</div>
    <div class="section-title">Notas por Pilar</div>
  </div>
  <div class="kpi-grid avoid-break">
    {kpi_html}
  </div>

  <!-- Gráficos (só aparecem se houver dados da Seção 7) -->
  <div id="charts-section" style="display:none;">
    <div class="charts-grid avoid-break">
      <div class="chart-card">
        <div style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:4px;">Receita vs Lucro</div>
        <div style="font-size:12px;color:var(--ink-40);margin-bottom:16px;">Evolução trimestral extraída do release</div>
        <div style="display:flex;gap:16px;margin-bottom:16px;flex-wrap:wrap;">
          <span style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink-60);">
            <span style="width:10px;height:10px;border-radius:2px;background:#003087;display:inline-block;"></span>Receita
          </span>
          <span style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink-60);">
            <span style="width:10px;height:10px;border-radius:2px;background:#0A6640;display:inline-block;"></span>Lucro
          </span>
        </div>
        <div class="chart-wrap"><canvas id="chartReceitaLucro"></canvas></div>
      </div>
      <div class="chart-card">
        <div style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:4px;">Margens Financeiras</div>
        <div style="font-size:12px;color:var(--ink-40);margin-bottom:16px;">Margem bruta e líquida (%)</div>
        <div style="display:flex;gap:16px;margin-bottom:16px;flex-wrap:wrap;">
          <span style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink-60);">
            <span style="width:10px;height:10px;border-radius:2px;background:#7C3AED;display:inline-block;"></span>Margem Bruta
          </span>
          <span style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink-60);">
            <span style="width:10px;height:10px;border-radius:2px;background:#D97706;display:inline-block;"></span>Margem Líquida
          </span>
        </div>
        <div class="chart-wrap"><canvas id="chartMargens"></canvas></div>
      </div>
    </div>
  </div>

  <div class="section-divider"></div>

  <!-- Análise Completa -->
  <div style="margin-bottom:48px;">
    <div class="section-label">Análise Completa por IA</div>
    <div class="section-title">Leitura dos Resultados</div>
  </div>

  {sections_html}

  <div class="section-divider page-break"></div>

  <!-- Conclusão / Tese -->
  <div class="conclusion avoid-break">
    <div class="conclusion-label">Tese de Investimento</div>
    <h2 class="conclusion-title">Conclusão Estratégica e Outlook</h2>
    <div class="conclusion-body">
      {tese_paras}
    </div>
    <div class="verdict-grid">
      <div>
        <div class="verdict-label">Score Final</div>
        <div class="verdict-value">{nota_geral:.1f} / 5</div>
        <span class="tag {'tag-buy' if nota_geral >= 4 else 'tag-watch' if nota_geral >= 3 else 'tag-neutral'}"
          style="margin-top:8px;display:inline-block;">
          {'Resultado Sólido' if nota_geral >= 4 else 'Resultado Moderado' if nota_geral >= 3 else 'Resultado Fraco'}
        </span>
      </div>
      <div>
        <div class="verdict-label">Empresa</div>
        <div class="verdict-value">{html_lib.escape(empresa.title())}</div>
        <div style="font-size:13px;color:#64748B;margin-top:6px;">{html_lib.escape(periodo)}</div>
      </div>
      <div>
        <div class="verdict-label">Aviso</div>
        <div class="verdict-value" style="font-size:13px;line-height:1.5;color:#94A3B8;">
          Este relatório é gerado por IA. Não constitui recomendação de investimento.
        </div>
      </div>
    </div>
  </div>

</div>

<!-- FOOTER -->
<div class="report-footer no-print">
  <div style="max-width:480px;line-height:1.6;">
    Gerado automaticamente pelo FinAnalyzer com base nos dados do release oficial.
    Não constitui recomendação de investimento. Consulte um assessor qualificado.
  </div>
  <div style="text-align:right;">
    <div style="font-weight:600;color:var(--ink-60);margin-bottom:4px;">FinAnalyzer</div>
    <div>{html_lib.escape(empresa.title())} · {html_lib.escape(periodo)}</div>
  </div>
</div>

<script>
const CHART_DATA = {chart_json};

if (CHART_DATA && CHART_DATA.length > 0) {{
  document.getElementById('charts-section').style.display = 'block';

  const labels = CHART_DATA.map(d => d.name || '');

  // Chart 1: Receita vs Lucro
  new Chart(document.getElementById('chartReceitaLucro'), {{
    type: 'bar',
    data: {{
      labels,
      datasets: [
        {{
          label: 'Receita',
          data: CHART_DATA.map(d => d.receita || 0),
          backgroundColor: '#C7D7F5',
          borderRadius: 6,
          maxBarThickness: 40
        }},
        {{
          label: 'Lucro',
          data: CHART_DATA.map(d => d.lucro || 0),
          backgroundColor: '#003087',
          borderRadius: 6,
          maxBarThickness: 40
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ grid: {{ display: false }}, ticks: {{ color: '#94A3B8', font: {{ size: 12 }} }}, border: {{ display: false }} }},
        y: {{ grid: {{ color: '#F1F5F9' }}, border: {{ display: false }}, ticks: {{ color: '#94A3B8', font: {{ size: 12 }} }} }}
      }}
    }}
  }});

  // Chart 2: Margens
  new Chart(document.getElementById('chartMargens'), {{
    type: 'line',
    data: {{
      labels,
      datasets: [
        {{
          label: 'Margem Bruta',
          data: CHART_DATA.map(d => d.margemBruta || 0),
          borderColor: '#7C3AED',
          backgroundColor: 'rgba(124,58,237,0.08)',
          fill: true,
          borderWidth: 2.5,
          pointBackgroundColor: '#7C3AED',
          pointRadius: 4,
          tension: 0.3
        }},
        {{
          label: 'Margem Líquida',
          data: CHART_DATA.map(d => d.margemLiquida || 0),
          borderColor: '#D97706',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [5, 3],
          pointBackgroundColor: '#D97706',
          pointRadius: 4,
          tension: 0.3
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ grid: {{ display: false }}, ticks: {{ color: '#94A3B8', font: {{ size: 12 }} }}, border: {{ display: false }} }},
        y: {{ grid: {{ color: '#F1F5F9' }}, border: {{ display: false }}, ticks: {{ color: '#94A3B8', font: {{ size: 12 }} }}, callback: v => v + '%' }} }}
      }}
    }}
  }});
}}
</script>
</body>
</html>"""


# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.get("/api/report/{item_id}", response_class=HTMLResponse)
def get_report(item_id: int):
    """
    Retorna o relatório HTML completo de uma análise.
    Abrir diretamente no browser → Ctrl+P para salvar como PDF.
    """
    from main import get_db_connection   # import local para evitar circular
    import json

    conn = get_db_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT resultado_json FROM historico WHERE id = %s",
            (item_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Análise não encontrada.")
        resultado = json.loads(row[0])
        html = generate_report_html(resultado)
        return HTMLResponse(content=html, status_code=200)
    finally:
        cur.close()
        conn.close()