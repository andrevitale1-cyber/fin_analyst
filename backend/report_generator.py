# Prompt enviado para o Gemini:
# [
# 	{
# 		"resource": "/c:/Users/André Vitale/Documents/projeto_analise1/backend/report_generator.py",
# 		"owner": "Pylance",
# 		"severity": 8,
# 		"message": "Unterminated expression in f-string; expecting \"}\"",
# 		"source": "Pylance",
# 		"startLineNumber": 800,
# 		"startColumn": 26,
# 		"endLineNumber": 800,
# 		"endColumn": 27,
# 		"modelVersionId": 22,
# 		"origin": "extHost1"
# 	},{
# 		"resource": "/c:/Users/André Vitale/Documents/projeto_analise1/backend/report_generator.py",
# 		"owner": "Pylance",
# 		"code": {
# 			"value": "reportUndefinedVariable",
# 			"target": {
# 				"$mid": 1,
# 				"path": "/microsoft/pylance-release/blob/main/docs/diagnostics/reportUndefinedVariable.md",
# 				"scheme": "https",
# 				"authority": "github.com"
# 			}
# 		},
# 		"severity": 4,
# 		"message": "\"let\" is not defined",
# 		"source": "Pylance",
# 		"startLineNumber": 800,
# 		"startColumn": 22,
# 		"endLineNumber": 800,
# 		"endColumn": 25,
# 		"modelVersionId": 22,
# 		"origin": "extHost1"
# 	}
# ]
# esses sao os ultimos erros

"""
report_generator.py  —  FinAnalyzer v4
════════════════════════════════════════════════════════════════
Adicione ao main.py (2 linhas):

    from report_generator import router as report_router
    app.include_router(report_router)   # logo após app = FastAPI(...)

Endpoint:   GET /api/report/{item_id}
Frontend:   window.open(`${API_BASE}/api/report/${item.id}`, '_blank')
════════════════════════════════════════════════════════════════
"""

import json, re, html as _h
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _f(v) -> float:
    try:
        return float(str(v).replace(",", ".").strip())
    except Exception:
        return 0.0


def _score_theme(n: float) -> dict:
    """
    1 → vermelho forte   2 → vermelho suave
    3 → âmbar/amarelo    4 → verde suave    5 → verde forte
    """
    if n <= 1.5:
        return dict(label="Muito Ruim", text="#7F1D1D", bg="#FEF2F2",
                    border="#FECACA", bar="#DC2626", badge_bg="#FEE2E2",
                    badge_text="#991B1B", icon="")
    if n <= 2.5:
        return dict(label="Ruim",      text="#9A3412", bg="#FFF7ED",
                    border="#FED7AA", bar="#EA580C", badge_bg="#FFEDD5",
                    badge_text="#9A3412", icon="")
    if n <= 3.5:
        return dict(label="Regular",   text="#78350F", bg="#FFFBEB",
                    border="#FDE68A", bar="#D97706", badge_bg="#FEF3C7",
                    badge_text="#92400E", icon="")
    if n <= 4.5:
        return dict(label="Bom",       text="#14532D", bg="#F0FDF4",
                    border="#BBF7D0", bar="#16A34A", badge_bg="#DCFCE7",
                    badge_text="#15803D", icon="")
    return         dict(label="Excelente",text="#052E16", bg="#ECFDF5",
                    border="#6EE7B7", bar="#059669", badge_bg="#D1FAE5",
                    badge_text="#065F46", icon="")


def _quarter_sort_key(name: str):
    """Sort helper for labels like 3T24, 4T2024, 1T25."""
    if not name:
        return (9999, 9, "")
    s = str(name).strip().upper()
    m = re.search(r"(\d)\s*T\s*(\d{2,4})", s)
    if not m:
        return (9999, 9, s)
    q = int(m.group(1))
    y = int(m.group(2))
    if y < 100:
        y += 2000
    return (y, q, s)


def _extract_charts(text: str) -> list:
    try:
        m = re.search(r"```json\s*([\s\S]*?)\s*```", text or "")
        if m:
            raw = json.loads(m.group(1))
            if isinstance(raw, list):
                cleaned = []
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    cleaned.append({
                        "name": item.get("name") or item.get("periodo") or item.get("label") or "",
                        "receita": _f(item.get("receita")),
                        "lucro": _f(item.get("lucro")),
                        "margemBruta": _f(item.get("margemBruta")),
                        "margemLiquida": _f(item.get("margemLiquida")),
                        "opex_ga": _f(item.get("opex_ga", 35)),
                        "opex_mk": _f(item.get("opex_mk", 25)),
                        "opex_da": _f(item.get("opex_da", 15)),
                        "opex_outras": _f(item.get("opex_outras", 25)),
                    })
                cleaned.sort(key=lambda d: _quarter_sort_key(d.get("name")))
                return cleaned
    except Exception:
        pass
    return []


def _clean_md(text: str) -> str:
    """Markdown → HTML limpo: tabelas, bold, bullets, parágrafos."""
    if not text:
        return ""
    lines = text.split("\n")
    out, in_table, in_ul = [], False, False
    for line in lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            if not in_table:
                if in_ul:
                    out.append("</ul>")
                    in_ul = False
                out.append('<div class="tbl-wrap"><table class="tbl"><tbody>')
                in_table = True
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.match(r"^[-:]+$", c) for c in cells):
                continue
            is_hdr = not any("<td>" in r for r in out[-6:])
            tag = "th" if is_hdr else "td"
            row = "".join(f"<{tag}>{_h.escape(c)}</{tag}>" for c in cells)
            out.append(f"<tr>{row}</tr>")
            continue
        if in_table:
            out.append("</tbody></table></div>")
            in_table = False
        if re.match(r"^[-•*]\s", s):
            if not in_ul:
                out.append('<ul class="md-ul">')
                in_ul = True
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s[2:])
            out.append(f"<li>{body}</li>")
            continue
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if s:
            s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
            out.append(s)
    if in_table:
        out.append("</tbody></table></div>")
    if in_ul:
        out.append("</ul>")
    combined = "\n".join(out)
    paras = re.split(r"\n{2,}", combined)
    result = []
    for p in paras:
        p = p.strip()
        if not p:
            continue
        result.append(p if p.startswith("<") else f"<p>{p}</p>")
    return "\n".join(result)


def _parse_sections(text: str) -> list:
    titles = {
        1: "Evolução Operacional e Top Line",
        2: "Rentabilidade e Margens",
        3: "Estrutura de Capital e Gestão de Risco",
        4: "Sumário Executivo do Lucro Líquido",
    }
    secs = []
    intro = re.search(r"^([\s\S]*?)(?=\*?\*?Se[cç][aã]o\s*1)", text or "", re.IGNORECASE)
    if intro:
        b = intro.group(1).strip().replace("**", "")
        if b:
            secs.append({"num": 0, "title": "Visão Geral do Trimestre", "body": b, "nota": None})
    for n in range(1, 6):
        pat = rf"\*?\*?Se[cç][aã]o\s*{n}[:\s\–\-].*?\n([\s\S]*?)(?=\*?\*?Se[cç][aã]o\s*{n+1}|\Z)"
        m = re.search(pat, text or "", re.IGNORECASE)
        if not m:
            continue
        body = m.group(1).strip()
        nm = re.search(
            rf"Nota\s+Se[cç][aã]o\s+{n}[:\s]+(\d[.,]?\d?)\s*/\s*5",
            body, re.IGNORECASE,
        )
        nota = _f(nm.group(1)) if nm else None
        body = re.sub(
            rf"\*?\*?Nota\s+Se[cç][aã]o\s+{n}[:\s]+\d[.,]?\d?\s*/\s*5\*?\*?", "", body
        ).strip()
        body = re.sub(r"```json[\s\S]*?```", "", body).strip()
        secs.append({"num": n, "title": titles.get(n, f"Seção {n}"), "body": body, "nota": nota})
    return secs


# ═══════════════════════════════════════════════════════════════
# CHART CONFIG PER SECTION
# ═══════════════════════════════════════════════════════════════

SECTION_CHARTS = {
    # Seção 0 (intro) — overview: receita + lucro barras
    0: [
        {
            "id": "cS0A",
            "title": "Receita & Lucro — Visão Geral",
            "sub": "Evolução nos últimos trimestres",
            "legend": [("Receita","#1E40AF"), ("Lucro","#059669")],
            "js": """new Chart(document.getElementById('cS0A'),{type:'bar',data:{labels,datasets:[
  {label:'Receita',data:rec,backgroundColor:'rgba(30,64,175,.18)',borderColor:'#1E40AF',borderWidth:2,borderRadius:5,maxBarThickness:32},
  {label:'Lucro',  data:luc,backgroundColor:'rgba(5,150,105,.75)',borderRadius:5,maxBarThickness:32},
]},options:{...BASE,scales:{x:XA,y:YA}}});"""
        },
    ],

    # Seção 1 (Top Line) — receita barras + margem bruta linha
    1: [
        {
            "id": "cS1A",
            "title": "Evolução da Receita",
            "sub": "Crescimento trimestral",
            "legend": [("Receita","#1E40AF"), ("Lucro","#059669")],
            "js": """new Chart(document.getElementById('cS1A'),{type:'bar',data:{labels,datasets:[
  {label:'Receita',data:rec,backgroundColor:'rgba(30,64,175,.18)',borderColor:'#1E40AF',borderWidth:2,borderRadius:5,maxBarThickness:32},
  {label:'Lucro',  data:luc,backgroundColor:'rgba(5,150,105,.75)',borderRadius:5,maxBarThickness:32},
]},options:{...BASE,scales:{x:XA,y:YA}}});"""
        },
        {
            "id": "cS1B",
            "title": "Margem Bruta (%)",
            "sub": "Tendência da margem bruta ao longo do tempo",
            "legend": [("Margem Bruta","#7C3AED")],
            "js": """new Chart(document.getElementById('cS1B'),{type:'line',data:{labels,datasets:[
  {label:'Margem Bruta',data:mB,borderColor:'#7C3AED',backgroundColor:'rgba(124,58,237,.08)',
   fill:true,borderWidth:2.5,pointBackgroundColor:'#7C3AED',pointRadius:4,tension:.35},
]},options:{...BASE,scales:{x:XA,y:{...YA,ticks:{...YA.ticks,callback:v=>v+'%'}}}}});"""
        },
    ],

    # Seção 2 (Margens) — margem bruta vs líquida linha
    2: [
        {
            "id": "cS2A",
            "title": "Margens Bruta e Líquida (%)",
            "sub": "Comparativo trimestral de margens",
            "legend": [("Bruta","#7C3AED"), ("Líquida","#D97706")],
            "js": """new Chart(document.getElementById('cS2A'),{type:'line',data:{labels,datasets:[
  {label:'Margem Bruta',  data:mB,borderColor:'#7C3AED',backgroundColor:'rgba(124,58,237,.07)',
   fill:true,borderWidth:2.5,pointBackgroundColor:'#7C3AED',pointRadius:4,tension:.35},
  {label:'Margem Líquida',data:mL,borderColor:'#D97706',backgroundColor:'transparent',
   borderWidth:2,borderDash:[5,3],pointBackgroundColor:'#D97706',pointRadius:4,tension:.35},
]},options:{...BASE,scales:{x:XA,y:{...YA,ticks:{...YA.ticks,callback:v=>v+'%'}}}}});"""
        },
       {
            "id": "cS2B",
            "title": "Composição das Despesas (OPEX)",
            "sub": "Share de cada despesa no OPEX total - Último Trimestre",
            "legend": [("G&A","#1E3A8A"), ("Marketing","#9CA3AF"), ("D&A","#059669"), ("Outras","#D97706")],
            "js": """
            // Extrai os dados do último trimestre (o último item no array CD)
            const lastData = CD[CD.length - 1];
            const opexLabels = ['Gerais e Administrativas', 'Marketing e Vendas', 'Depreciação e Amortização', 'Outras Despesas'];
            
            // Usa os dados extraídos ou os fallbacks
            const opexData = [
                lastData.opex_ga || 35, 
                lastData.opex_mk || 25, 
                lastData.opex_da || 15, 
                lastData.opex_outras || 25
            ]; 
            
            new Chart(document.getElementById('cS2B'),{
                type:'doughnut',
                data:{
                    labels: opexLabels,
                    datasets:[{
                        data: opexData,
                        backgroundColor: ['#1E3A8A','#9CA3AF','#059669','#D97706'],
                        borderWidth: 2,
                        hoverOffset: 4
                    }]
                },
                options:{
                    ...BASE,
                    cutout:'65%'
                }
            });"""
        },
    ],

    # Seção 3 (Capital/Dívida) — lucro linha + lucro barras 
    3: [
        {
            "id": "cS3A",
            "title": "Geração de Resultado",
            "sub": "Lucro acumulado — proxy de fluxo de caixa",
            "legend": [("Lucro","#059669")],
            "js": """new Chart(document.getElementById('cS3A'),{type:'line',data:{labels,datasets:[
  {label:'Lucro',data:luc,borderColor:'#059669',backgroundColor:'rgba(5,150,105,.08)',
   fill:true,borderWidth:2.5,pointBackgroundColor:'#059669',pointRadius:4,tension:.35},
  {label:'Lucro',data:luc,backgroundColor:'rgba(5,150,105,.8)',borderRadius:4,maxBarThickness:30}
]},options:{...BASE,scales:{x:XA,y:YA}}});"""
        },
    ],

    # Seção 4 (Lucro) — lucro barras + margem líquida linha
    4: [
        {
            "id": "cS4A",
            "title": "Lucro Líquido por Trimestre",
            "sub": "Evolução do bottom-line",
            "legend": [("Lucro","#059669")],
            "js": """new Chart(document.getElementById('cS4A'),{type:'bar',data:{labels,datasets:[
  {label:'Lucro',data:luc,
   backgroundColor:luc.map((_,i)=>i===luc.length-1?'rgba(5,150,105,.9)':'rgba(5,150,105,.35)'),
   borderColor:'#059669',borderWidth:1.5,borderRadius:6,maxBarThickness:36},
]},options:{...BASE,scales:{x:XA,y:YA}}});"""
        },
        {
            "id": "cS4B",
            "title": "Margem Líquida (%)",
            "sub": "Rentabilidade sobre a receita",
            "legend": [("Margem Líquida","#D97706")],
            "js": """new Chart(document.getElementById('cS4B'),{type:'line',data:{labels,datasets:[
  {label:'Margem Líquida',data:mL,borderColor:'#D97706',backgroundColor:'rgba(217,119,6,.08)',
   fill:true,borderWidth:2.5,pointBackgroundColor:'#D97706',pointRadius:4,tension:.35},
]},options:{...BASE,scales:{x:XA,y:{...YA,ticks:{...YA.ticks,callback:v=>v+'%'}}}}});"""
        },
    ],
}


# ═══════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_report_html(resultado: dict) -> str:
    meta    = resultado.get("metadata", {})
    data    = resultado.get("data", {})
    analise = resultado.get("analise_completa", "")

    empresa = (meta.get("empresa") or "Empresa").upper()
    periodo = meta.get("periodo") or ""

    rn  = _f(data.get("receita_nota", 0))
    ln  = _f(data.get("lucro_nota", 0))
    dn  = _f(data.get("divida_nota", 0))
    ren = _f(data.get("rentabilidade_nota", 0))
    g   = _f(data.get("nota_geral", 0))
    tese = data.get("tese_investimento", "")

    tg   = _score_theme(g)
    secs = _parse_sections(analise)
    raw_cd = data.get("chart_data") or _extract_charts(analise)
    # keep only quarters mentioned in analysis text to avoid hallucinations
    cd = [d for d in raw_cd if str(d.get("name","")) in analise]
    if not cd:
        cd = raw_cd
    cd = sorted(cd, key=lambda d: _quarter_sort_key(d.get("name")))
    cj   = json.dumps(cd)

    tese_c    = re.sub(r"\*\*|\*", "", tese).strip()
    tese_html = "".join(
        f"<p>{_h.escape(p.strip())}</p>" for p in tese_c.split("\n\n") if p.strip()
    ) or f"<p>{_h.escape(tese_c)}</p>"

    # ── HERO SCORE RING ─────────────────────────────────────
    def _hero_ring(nota, size=110):
        t  = _score_theme(nota)
        R  = size // 2 - 10
        cx = cy = size // 2
        C  = 2 * 3.14159 * R
        dash = C * (nota / 5)
        gap  = C - dash
        off  = C * 0.25
        return (
            f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#E5E7EB" stroke-width="10"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{t["bar"]}" stroke-width="10"'
            f' stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-dashoffset="{off:.1f}" stroke-linecap="round"/>'
            f'<text x="{cx}" y="{cy-6}" text-anchor="middle" dominant-baseline="middle"'
            f' style="font-family:\'DM Sans\',sans-serif;font-size:{size//4}px;font-weight:700;fill:{t["bar"]}">{nota:.1f}</text>'
            f'<text x="{cx}" y="{cy+14}" text-anchor="middle"'
            f' style="font-family:\'DM Sans\',sans-serif;font-size:11px;fill:#9CA3AF;">/5</text>'
            f'</svg>'
        )

    # ── PILLAR CARDS ────────────────────────────────────────
    pillars = [
        {"label": "Receita",           "nota": rn,  "icon": "REV"},
        {"label": "Margem & Lucro",    "nota": ln,  "icon": "M&L"},
        {"label": "Dívida & Risco",    "nota": dn,  "icon": "RISC"},
        {"label": "Rentabilidade ROE", "nota": ren, "icon": "ROE"},
    ]

    def _pillar(p):
        t   = _score_theme(p["nota"])
        pct = int(p["nota"] / 5 * 100)
        return f"""<div class="pillar" style="border-top:3px solid {t['bar']}">
  <div class="pillar-top">
    <span class="pillar-icon">{p['icon']}</span>
    <span class="pillar-badge" style="background:{t['badge_bg']};color:{t['badge_text']};">{t['icon']} {t['label']}</span>
  </div>
  <div class="pillar-nota" style="color:{t['bar']}">{p['nota']:.1f}<span class="pillar-denom">/5</span></div>
  <div class="pillar-label">{p['label']}</div>
  <div class="pillar-track"><div class="pillar-fill" style="width:{pct}%;background:{t['bar']}"></div></div>
</div>"""

    pillars_html = "".join(_pillar(p) for p in pillars)

    # ── BUILD SECTION BLOCKS ────────────────────────────────
    all_chart_js = []   # collect all chart JS snippets

    def _section_block(s):
        t  = _score_theme(s["nota"]) if s["nota"] is not None else None
        charts_cfg = SECTION_CHARTS.get(s["num"], [])
        has_charts = bool(charts_cfg and cd)

        # nota box
        nota_box = ""
        if t:
            nota_box = f"""
<div class="nota-box" style="background:{t['bg']};border:1px solid {t['border']};">
  <div class="nota-box-label">Nota desta seção</div>
  <div class="nota-box-val" style="color:{t['bar']}">{s['nota']:.0f}<span class="nota-box-denom">/5</span></div>
  <div class="nota-box-tag" style="background:{t['badge_bg']};color:{t['badge_text']}">{t['icon']} {t['label']}</div>
</div>"""

        # chart panels HTML (max 2 charts per section)
        chart_panels_html = ""
        for cfg in charts_cfg[:2]:
            legend_html = "".join(
                f'<span class="leg-i"><span class="leg-dot" style="background:{c}"></span>{lbl}</span>'
                for lbl, c in cfg["legend"]
            )
            chart_panels_html += f"""
<div class="chart-panel">
  <div class="cp-title">{cfg['title']}</div>
  <div class="cp-sub">{cfg['sub']}</div>
  <div class="cp-legend">{legend_html}</div>
  <div class="cp-wrap"><canvas id="{cfg['id']}"></canvas></div>
</div>"""
            all_chart_js.append(
                f"if(document.getElementById('{cfg['id']}')&&CD.length){{{cfg['js']}}}"
            )

        # aside: nota box on top, then charts
        aside_html = ""
        if nota_box or chart_panels_html:
            aside_html = f'<div class="sec-aside">{nota_box}{chart_panels_html}</div>'

        num_label = f'<span class="sec-num">Seção {s["num"]}</span>' if s["num"] > 0 else ""
        acc = t["bar"] if t else "#E5E7EB"

        return f"""
<section class="sec-block fade-in" style="--acc:{acc}">
  <div class="sec-accent-bar"></div>
  <div class="sec-inner">
    <div class="sec-head">
      <div>
        {num_label}
        <h2 class="sec-title">{_h.escape(s['title'])}</h2>
      </div>
    </div>
    <div class="sec-layout{'--full' if not aside_html else ''}">
      <div class="sec-text abody">{_clean_md(s['body'])}</div>
      {aside_html}
    </div>
  </div>
</section>"""

    secs_html    = "".join(_section_block(s) for s in secs)
    charts_js    = "\n".join(all_chart_js)

    # ── VERDICT ─────────────────────────────────────────────
    verdict_labels = {
        "Muito Ruim": ("vtag-sell",  "Resultado Muito Fraco"),
        "Ruim":       ("vtag-sell",  "Resultado Fraco"),
        "Regular":    ("vtag-watch", "Resultado Regular"),
        "Bom":        ("vtag-buy",   "Resultado Bom"),
        "Excelente":  ("vtag-buy",   "Resultado Excelente"),
    }
    vcls, vtitle = verdict_labels.get(tg["label"], ("vtag-watch", "—"))

    # ── FINAL HTML ──────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{_h.escape(empresa.title())} · {_h.escape(periodo)} · FinAnalyzer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{font-size:16px;scroll-behavior:smooth}}
body{{font-family:'DM Sans',system-ui,sans-serif;background:#F1F5F9;color:#111827;line-height:1.65;-webkit-font-smoothing:antialiased}}

@media print{{
  body{{background:#fff}}
  .no-print{{display:none!important}}
  .page-break{{break-before:page}}
  .sec-block{{break-inside:avoid}}
  .fade-in{{opacity:1!important;transform:none!important;animation:none!important}}
}}

@keyframes fadeUp{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
.fade-in{{opacity:0;animation:fadeUp .5s ease forwards;animation-play-state:paused}}

::-webkit-scrollbar{{width:5px;height:5px}}
::-webkit-scrollbar-thumb{{background:#CBD5E1;border-radius:3px}}

/* ─── TOPBAR ─── */
.topbar{{
  position:sticky;top:0;z-index:200;height:50px;
  background:rgba(255,255,255,.96);backdrop-filter:blur(8px);
  border-bottom:1px solid #E5E7EB;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 36px;
}}
.tb-brand{{display:flex;align-items:center;gap:10px}}
.tb-cube{{width:28px;height:28px;background:#1E3A8A;border-radius:6px;display:flex;align-items:center;justify-content:center}}
.tb-name{{font-weight:600;font-size:14px;color:#1E3A8A;letter-spacing:-.01em}}
.tb-nav{{display:flex;gap:4px}}
.tb-link{{font-size:11px;font-weight:500;color:#6B7280;padding:5px 11px;border-radius:6px;text-decoration:none;transition:all .15s;border:1px solid transparent}}
.tb-link:hover{{background:#F8FAFC;color:#111827;border-color:#E5E7EB}}
.tb-right{{display:flex;align-items:center;gap:12px}}
.tb-score{{font-family:'DM Mono',monospace;font-size:14px;font-weight:500;color:{tg['bar']}}}
.tb-score-lbl{{font-size:11px;color:#9CA3AF;margin-right:4px}}
.print-btn{{background:#1E3A8A;color:#fff;border:none;border-radius:6px;padding:7px 14px;
  font-family:'DM Sans',sans-serif;font-size:12px;font-weight:600;cursor:pointer;
  display:flex;align-items:center;gap:5px;transition:opacity .15s}}
.print-btn:hover{{opacity:.85}}

/* ─── HERO ─── */
.hero{{background:#fff;border-bottom:1px solid #E5E7EB;padding:44px 36px 36px}}
.hero-inner{{max-width:1100px;margin:0 auto}}
.hero-row{{display:flex;gap:40px;align-items:flex-start;margin-bottom:36px}}
.hero-left{{flex:1;min-width:0}}
.hero-period{{
  display:inline-flex;align-items:center;gap:6px;
  background:#EFF6FF;border:1px solid #BFDBFE;
  border-radius:999px;padding:4px 12px;
  font-size:11px;font-weight:600;color:#1D4ED8;
  letter-spacing:.05em;text-transform:uppercase;margin-bottom:14px;
}}
.hero-dot{{width:5px;height:5px;background:#3B82F6;border-radius:50%}}
.hero-empresa{{font-family:'Playfair Display',serif;font-size:clamp(32px,5vw,56px);font-weight:900;
  line-height:.95;letter-spacing:-.03em;color:#0F172A;margin-bottom:12px}}
.hero-desc{{font-size:15px;color:#6B7280;font-weight:300;max-width:460px;line-height:1.6}}
.hero-right{{flex-shrink:0;display:flex;flex-direction:column;align-items:center;
  padding:24px 32px;background:{tg['bg']};border:1.5px solid {tg['border']};
  border-radius:16px;text-align:center;min-width:180px}}
.hero-score-lbl{{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:{tg['text']};margin-bottom:10px;opacity:.7}}
.hero-score-verdict{{font-size:14px;font-weight:700;color:{tg['text']};margin-top:8px}}

/* ─── PILLARS ─── */
.pillars{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.pillar{{background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:18px 20px;
  transition:transform .18s,box-shadow .18s}}
.pillar:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.07)}}
.pillar-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}
.pillar-icon{{font-size:18px}}
.pillar-badge{{font-size:10px;font-weight:700;padding:3px 7px;border-radius:4px}}
.pillar-nota{{font-family:'DM Mono',monospace;font-size:30px;font-weight:500;line-height:1}}
.pillar-denom{{font-size:13px;color:#9CA3AF;font-weight:400}}
.pillar-label{{font-size:12px;color:#6B7280;margin-top:2px;margin-bottom:10px}}
.pillar-track{{height:4px;background:#F1F5F9;border-radius:99px;overflow:hidden}}
.pillar-fill{{height:100%;border-radius:99px}}

/* ─── SUMMARY BAR ─── */
.sumbar{{background:#0F172A;padding:0}}
.sumbar-inner{{max-width:1100px;margin:0 auto;display:flex}}
.sum-cell{{flex:1;padding:16px 24px;border-right:1px solid rgba(255,255,255,.07);transition:background .15s}}
.sum-cell:last-child{{border-right:none}}
.sum-cell:hover{{background:rgba(255,255,255,.04)}}
.sum-val{{font-family:'DM Mono',monospace;font-size:17px;font-weight:500;color:#fff;line-height:1;margin-bottom:3px}}
.sum-lbl{{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:rgba(255,255,255,.4)}}
.sum-d{{font-size:11px;font-weight:600;margin-top:3px;display:inline-block}}
.d-up{{color:#34D399}}.d-dn{{color:#F87171}}.d-ne{{color:rgba(255,255,255,.3)}}

/* ─── MAIN LAYOUT ─── */
.main{{max-width:1100px;margin:0 auto;padding:36px 36px 80px}}
.sec-label{{font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  color:#6B7280;margin-bottom:6px}}
.sec-heading{{font-family:'Playfair Display',serif;font-size:26px;font-weight:700;
  color:#0F172A;margin-bottom:28px;letter-spacing:-.02em}}

/* ─── SECTION BLOCK ─── */
.sec-block{{
  background:#fff;border-radius:14px;border:1px solid #E5E7EB;
  overflow:hidden;margin-bottom:18px;
  transition:box-shadow .2s;
}}
.sec-block:hover{{box-shadow:0 4px 18px rgba(0,0,0,.06)}}
.sec-accent-bar{{height:4px;background:var(--acc)}}
.sec-inner{{padding:28px 32px}}
.sec-head{{margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #F1F5F9}}
.sec-num{{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:#9CA3AF;display:block;margin-bottom:3px}}
.sec-title{{font-family:'Playfair Display',serif;font-size:21px;font-weight:700;
  color:#0F172A;letter-spacing:-.01em}}

/* text | aside two-column */
.sec-layout{{display:grid;grid-template-columns:1fr 300px;gap:28px;align-items:start}}
.sec-layout--full{{display:block}}

/* ─── ANALYSIS TEXT ─── */
.abody{{font-size:14px;line-height:1.85;color:#374151}}
.abody p{{margin-bottom:12px}}
.abody p:last-child{{margin-bottom:0}}
.abody strong{{color:#111827;font-weight:600}}
.abody ul.md-ul{{margin:8px 0 12px 18px}}
.abody ul.md-ul li{{margin-bottom:5px}}
.tbl-wrap{{overflow-x:auto;margin:12px 0}}
.tbl{{width:100%;border-collapse:collapse;font-size:13px}}
.tbl th{{background:#F8FAFC;color:#374151;font-weight:600;font-size:11px;
  letter-spacing:.05em;text-transform:uppercase;padding:8px 12px;
  border-bottom:2px solid #E5E7EB;text-align:left}}
.tbl td{{padding:8px 12px;border-bottom:1px solid #F1F5F9;color:#374151}}
.tbl tbody tr:last-child td{{border-bottom:none}}
.tbl tbody tr:hover td{{background:#F8FAFC}}

/* ─── ASIDE (nota + charts) ─── */
.sec-aside{{display:flex;flex-direction:column;gap:14px}}

/* nota box */
.nota-box{{border-radius:10px;padding:16px;text-align:center}}
.nota-box-label{{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:#6B7280;display:block;margin-bottom:6px}}
.nota-box-val{{font-family:'DM Mono',monospace;font-size:38px;font-weight:500;
  line-height:1;display:block;margin-bottom:6px}}
.nota-box-denom{{font-size:15px;color:#9CA3AF;font-weight:400}}
.nota-box-tag{{font-size:11px;font-weight:700;padding:4px 10px;
  border-radius:4px;display:inline-block}}

/* chart panel */
.chart-panel{{border:1px solid #E5E7EB;border-radius:10px;padding:16px;background:#FAFAFA}}
.cp-title{{font-size:12px;font-weight:600;color:#111827;margin-bottom:2px}}
.cp-sub{{font-size:11px;color:#9CA3AF;margin-bottom:10px}}
.cp-legend{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:10px}}
.leg-i{{display:flex;align-items:center;gap:5px;font-size:11px;color:#6B7280}}
.leg-dot{{width:8px;height:8px;border-radius:2px;flex-shrink:0}}
.cp-wrap{{position:relative;width:100%;height:160px}}

/* ─── DIVIDER ─── */
.divider{{height:1px;background:#E5E7EB;margin:36px 0}}

/* ─── CONCLUSION ─── */
.conclusion{{
  background:linear-gradient(135deg,#0F172A 0%,#1E3A8A 100%);
  border-radius:16px;padding:44px 52px;
  position:relative;overflow:hidden;
}}
.conclusion::after{{content:'';position:absolute;right:-60px;top:-60px;
  width:240px;height:240px;border-radius:50%;background:rgba(255,255,255,.03)}}
.c-eyebrow{{font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  color:#93C5FD;margin-bottom:14px;display:flex;align-items:center;gap:8px}}
.c-eyebrow::before{{content:'';display:block;width:20px;height:1px;background:#93C5FD}}
.c-title{{font-family:'Playfair Display',serif;font-size:26px;font-weight:700;
  color:#fff;line-height:1.2;margin-bottom:18px;letter-spacing:-.02em}}
.c-body{{font-size:14px;color:#CBD5E1;line-height:1.85;margin-bottom:28px}}
.c-body p{{margin-bottom:12px}}
.c-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;
  border-top:1px solid rgba(255,255,255,.1);padding-top:24px}}
.c-cell-lbl{{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:#64748B;margin-bottom:5px}}
.c-cell-val{{font-size:14px;font-weight:600;color:#fff}}
.vtag{{display:inline-block;padding:4px 10px;border-radius:4px;font-size:11px;
  font-weight:700;margin-top:6px;letter-spacing:.04em;text-transform:uppercase}}
.vtag-buy{{background:rgba(16,185,129,.2);color:#34D399;border:1px solid rgba(16,185,129,.3)}}
.vtag-watch{{background:rgba(251,191,36,.15);color:#FBBF24;border:1px solid rgba(251,191,36,.25)}}
.vtag-sell{{background:rgba(239,68,68,.2);color:#F87171;border:1px solid rgba(239,68,68,.3)}}

/* ─── FOOTER ─── */
.footer{{border-top:1px solid #E5E7EB;padding:22px 36px;
  max-width:1100px;margin:0 auto;
  display:flex;justify-content:space-between;align-items:center;
  font-size:11px;color:#9CA3AF}}

/* ─── RESPONSIVE ─── */
@media(max-width:860px){{
  .pillars{{grid-template-columns:1fr 1fr}}
  .hero-row{{flex-direction:column}}
  .hero-right{{width:100%;flex-direction:row;align-items:center;justify-content:space-between}}
  .sec-layout{{grid-template-columns:1fr}}
  .main{{padding:24px 16px 60px}}
  .topbar,.hero,.footer{{padding-left:16px;padding-right:16px}}
  .conclusion{{padding:32px 24px}}
  .c-grid{{grid-template-columns:1fr 1fr}}
  .sumbar-inner{{flex-wrap:wrap}}
  .sum-cell{{min-width:50%;border-right:none;border-bottom:1px solid rgba(255,255,255,.07)}}
}}
</style>
</head>
<body>

<nav class="topbar no-print">
  <div class="tb-brand">
    <div class="tb-cube">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="white">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22" fill="none" stroke="rgba(255,255,255,.5)" stroke-width="1.5"/>
      </svg>
    </div>
    <span class="tb-name">FinAnalyzer</span>
  </div>
  <nav class="tb-nav">
    <a href="#indicadores" class="tb-link">Indicadores</a>
    <a href="#analise"     class="tb-link">Análise</a>
    <a href="#conclusao"   class="tb-link">Conclusão</a>
  </nav>
  <div class="tb-right">
    <span><span class="tb-score-lbl">Score IA</span><span class="tb-score">{g:.1f}/5</span></span>
    <button class="print-btn" onclick="window.print()">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 6 2 18 2 18 9"/>
        <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
        <rect x="6" y="14" width="12" height="8"/>
      </svg>
      Salvar PDF
    </button>
  </div>
</nav>

<div class="hero">
  <div class="hero-inner">
    <div class="hero-row">
      <div class="hero-left">
        <div class="hero-period">
          <div class="hero-dot"></div>
          {_h.escape(periodo)} · Resultados Trimestrais
        </div>
        <h1 class="hero-empresa">{_h.escape(empresa.title())}</h1>
        <p class="hero-desc">
          Relatório completo gerado por IA com base no release de resultados oficial.
          Avaliação de receita, margens, endividamento e rentabilidade com visão estratégica.
        </p>
      </div>
      <div class="hero-right">
        <span class="hero-score-lbl">Score IA — Média Ponderada</span>
        {_hero_ring(g, 110)}
        <div class="hero-score-verdict">{tg['label']}</div>
      </div>
    </div>

    <div id="indicadores" class="pillars">
      {pillars_html}
    </div>
  </div>
</div>

<div class="sumbar"><div class="sumbar-inner" id="sumbarInner"></div></div>

<div class="main">

  <div id="analise">
    <div class="sec-label">Análise Completa por IA</div>
    <div class="sec-heading">Leitura dos Resultados</div>
    {secs_html}
  </div>

  <div class="divider page-break"></div>

  <div id="conclusao">
    <div class="conclusion">
      <div class="c-eyebrow">Tese de Investimento</div>
      <h2 class="c-title">Conclusão Estratégica e Outlook</h2>
      <div class="c-body">{tese_html}</div>
      <div class="c-grid">
        <div>
          <div class="c-cell-lbl">Score Final</div>
          <div class="c-cell-val">{g:.1f} / 5</div>
          <span class="vtag {vcls}">{vtitle}</span>
        </div>
        <div>
          <div class="c-cell-lbl">Empresa · Período</div>
          <div class="c-cell-val">{_h.escape(empresa.title())}</div>
          <div style="font-size:12px;color:#64748B;margin-top:3px">{_h.escape(periodo)}</div>
        </div>
        <div>
          <div class="c-cell-lbl">Aviso Legal</div>
          <div class="c-cell-val" style="font-size:12px;line-height:1.5;color:#94A3B8">
            Gerado por IA. Não constitui recomendação de investimento.
          </div>
        </div>
      </div>
    </div>
  </div>

</div>

<div class="footer no-print">
  <span>Gerado pelo <strong style="color:#6B7280">FinAnalyzer</strong> · Dados do release oficial · Não é recomendação de investimento</span>
  <span>{_h.escape(empresa.title())} · {_h.escape(periodo)}</span>
</div>

<script>
const CD    = __CHART_JSON__;
const NOTAS = {{ receita:__RN__, lucro:__LN__, divida:__DN__, roe:__REN__, geral:__G__ }};

/* score ring counter */
(()=>{{
  const el  = document.querySelector('.hero-right svg text');
  if (!el) return;
  const tgt = NOTAS.geral; let st = null;
  const run = ts => {{
    if (!st) st = ts;
    const p = Math.min((ts - st) / 800, 1);
    el.textContent = (tgt * (1 - Math.pow(1-p,3))).toFixed(1);
    if (p < 1) requestAnimationFrame(run);
    else el.textContent = tgt.toFixed(1);
  }};
  setTimeout(() => requestAnimationFrame(run), 400);
}})();

/* summary bar */
(()=>{{
  const bar = document.getElementById('sumbarInner');
  if (!bar || !CD.length) {{ document.querySelector('.sumbar').style.display='none'; return; }}

  const toNum = v => {{
    const n = Number(String(v ?? '').replace(',', '.'));
    return Number.isFinite(n) ? n : 0;
  }};
  
  // FIX: Chaves duplicadas adicionadas abaixo
  const fmt = v => {{ let n=toNum(v); if(n<10) n=n*1000; return (Math.round(n*100)/100).toString(); }}
  
  const sorted = [...CD].sort((a, b) => {{
    const A = a?.name || '';
    const B = b?.name || '';
    const ma = String(A).toUpperCase().match(/(\d)\s*T\s*(\d{{2,4}})/);
    const mb = String(B).toUpperCase().match(/(\d)\s*T\s*(\d{{2,4}})/);
    const key = (m, s) => m ? [Number(m[2]) < 100 ? 2000 + Number(m[2]) : Number(m[2]), Number(m[1])] : [9999, 9];
    const ka = key(ma, A), kb = key(mb, B);
    if (ka[0] !== kb[0]) return ka[0] - kb[0];
    if (ka[1] !== kb[1]) return ka[1] - kb[1];
    return String(A).localeCompare(String(B));
  }});
  const last = sorted[sorted.length - 1];
  const prev = sorted.length > 1 ? sorted[sorted.length - 2] : null;
  const delta = (a, b) => {{
    const aa = toNum(a), bb = toNum(b);
    if (!bb) return '<span class="sum-d d-ne">—</span>';
    const d = ((aa - bb) / Math.abs(bb) * 100).toFixed(1);
    return `<span class="sum-d ${{d>=0?'d-up':'d-dn'}}">${{d>=0?'▲':'▼'}} ${{Math.abs(d)}}%</span>`;
  }};
  [
    {{v: fmt(last.receita), l: 'Receita',      d: delta(last.receita, prev?.receita)}},
    {{v: fmt(last.lucro),   l: 'Lucro',        d: delta(last.lucro, prev?.lucro)}},
    {{v: `${{fmt(last.margemBruta)}}%`,  l: 'Mg. Bruta',  d: delta(last.margemBruta, prev?.margemBruta)}},
    {{v: `${{fmt(last.margemLiquida)}}%`,l: 'Mg. Líquida',d: delta(last.margemLiquida, prev?.margemLiquida)}},
    {{v: NOTAS.geral.toFixed(1)+'/5', l: 'Score IA', d: ''}},
  ].forEach(it => {{
    const c = document.createElement('div');
    c.className = 'sum-cell';
    c.innerHTML = `<div class="sum-val">${{it.v}}</div><div class="sum-lbl">${{it.l}}</div>${{it.d}}`;
    bar.appendChild(c);
  }});
}})();

/* shared chart.js config */
const TT = {{ backgroundColor:'#0F172A', titleColor:'#fff', bodyColor:'#CBD5E1',
              borderColor:'#1E293B', borderWidth:1, cornerRadius:8, padding:10 }};
const XA = {{ grid:{{display:false}}, ticks:{{color:'#9CA3AF',font:{{size:10}}}}, border:{{display:false}} }};
const YA = {{ grid:{{color:'#F1F5F9'}}, border:{{display:false}}, ticks:{{color:'#9CA3AF',font:{{size:10}}}} }};
const BASE = {{
  responsive:true, maintainAspectRatio:false,
  animation:{{duration:800, easing:'easeOutQuart'}},
  plugins:{{legend:{{display:false}}, tooltip:TT}},
}};

/* section charts (only if data exists) */
(()=>{{
  if (!CD.length) return;
  const labels = CD.map(d => d.name || '');
  const rec    = CD.map(d => d.receita || 0);
  const luc    = CD.map(d => d.lucro || 0);
  const mB     = CD.map(d => d.margemBruta || 0);
  const mL     = CD.map(d => d.margemLiquida || 0);
  {charts_js}
}})();

/* intersection observer for fade-in */
const io = new IntersectionObserver(entries => entries.forEach(e => {{
  if (e.isIntersecting) e.target.style.animationPlayState = 'running';
}}), {{ threshold: 0.06 }});
document.querySelectorAll('.fade-in').forEach(el => {{
  el.style.animationPlayState = 'paused';
  io.observe(el);
}});
</script>
</body>
</html>
""".replace("__CHART_JSON__", cj)\
   .replace("__RN__",  str(rn))\
   .replace("__LN__",  str(ln))\
   .replace("__DN__",  str(dn))\
   .replace("__REN__", str(ren))\
   .replace("__G__",   str(g))\
   .replace("{charts_js}", charts_js)


# ═══════════════════════════════════════════════════════════════
# FASTAPI ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/report/{item_id}", response_class=HTMLResponse)
def get_report(item_id: int):
    from main import get_db_connection
    conn = get_db_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT resultado_json FROM historico WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Análise não encontrada.")
        resultado = json.loads(row[0])
        return HTMLResponse(content=generate_report_html(resultado), status_code=200)
    finally:
        cur.close()
        conn.close()