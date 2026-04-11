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
    if n <= 1.5:
        return dict(label="Muito Ruim", text="#7F1D1D", bg="#FEF2F2",
                    border="#FECACA", bar="#DC2626", badge_bg="#FEE2E2", badge_text="#991B1B", icon="")
    if n <= 2.5:
        return dict(label="Ruim",      text="#9A3412", bg="#FFF7ED",
                    border="#FED7AA", bar="#EA580C", badge_bg="#FFEDD5", badge_text="#9A3412", icon="")
    if n <= 3.5:
        return dict(label="Regular",   text="#78350F", bg="#FFFBEB",
                    border="#FDE68A", bar="#D97706", badge_bg="#FEF3C7", badge_text="#92400E", icon="")
    if n <= 4.5:
        return dict(label="Bom",       text="#14532D", bg="#F0FDF4",
                    border="#BBF7D0", bar="#16A34A", badge_bg="#DCFCE7", badge_text="#15803D", icon="")
    return         dict(label="Excelente",text="#052E16", bg="#ECFDF5",
                    border="#6EE7B7", bar="#059669", badge_bg="#D1FAE5", badge_text="#065F46", icon="")

def _quarter_sort_key(name: str):
    if not name: return (9999, 9, "")
    s = str(name).strip().upper()
    m = re.search(r"(\d)\s*T\s*(\d{2,4})", s)
    if not m: return (9999, 9, s)
    q = int(m.group(1))
    y = int(m.group(2))
    if y < 100: y += 2000
    return (y, q, s)

def _extract_charts(text: str) -> list:
    try:
        for m in re.finditer(r"```json\s*([\s\S]*?)\s*```", text or ""):
            raw = json.loads(m.group(1))
            if isinstance(raw, list):
                cleaned = []
                for item in raw:
                    if not isinstance(item, dict): continue
                    cleaned.append({
                        "name": item.get("name") or item.get("periodo") or item.get("label") or "",
                        "receita": _f(item.get("receita")),
                        "lucro": _f(item.get("lucro")),
                        "divida": _f(item.get("divida")),
                        "ebitda": _f(item.get("ebitda")),
                        "margemBruta": _f(item.get("margemBruta")),
                        "margemLiquida": _f(item.get("margemLiquida")),
                        "segmentos": item.get("segmentos") if isinstance(item.get("segmentos"), list) else [],
                        "despesas_var": item.get("despesas_var") if isinstance(item.get("despesas_var"), list) else [],
                    })
                cleaned.sort(key=lambda d: _quarter_sort_key(d.get("name")))
                return cleaned
    except Exception:
        pass
    return []

def _extract_composicao(text: str) -> dict:
    """Extrai o JSON específico de Composição de Receita"""
    try:
        for m in re.finditer(r"```json\s*([\s\S]*?)\s*```", text or ""):
            raw = json.loads(m.group(1))
            if isinstance(raw, dict):
                if "Composição da Receita" in raw:
                    return raw["Composição da Receita"]
                elif any(isinstance(v, (int, float, dict)) for v in raw.values()):
                    return raw
    except Exception:
        pass
    return {}

def _clean_md(text: str) -> str:
    if not text: return ""
    lines = text.split("\n")
    out, in_table, in_ul = [], False, False
    for line in lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            if not in_table:
                if in_ul: out.append("</ul>"); in_ul = False
                out.append('<div class="tbl-wrap"><table class="tbl"><tbody>')
                in_table = True
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.match(r"^[-:]+$", c) for c in cells): continue
            is_hdr = not any("<td>" in r for r in out[-6:])
            tag = "th" if is_hdr else "td"
            row = "".join(f"<{tag}>{_h.escape(c)}</{tag}>" for c in cells)
            out.append(f"<tr>{row}</tr>")
            continue
        if in_table:
            out.append("</tbody></table></div>"); in_table = False
        if re.match(r"^[-•*]\s", s):
            if not in_ul: out.append('<ul class="md-ul">'); in_ul = True
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s[2:])
            # Transforma os timestamps (ex: [12:34]) numa badge bonita
            body = re.sub(r"(\[\d{1,2}:\d{2}\])", r"<span style='color:#7C3AED; font-weight:700; background:#F5F3FF; padding:2px 6px; border-radius:4px; font-family:monospace; font-size:12px;'>\1</span>", body)
            out.append(f"<li>{body}</li>")
            continue
        if in_ul:
            out.append("</ul>"); in_ul = False
        if s:
            s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
            # Transforma os timestamps (ex: [12:34]) numa badge bonita
            s = re.sub(r"(\[\d{1,2}:\d{2}\])", r"<span style='color:#7C3AED; font-weight:700; background:#F5F3FF; padding:2px 6px; border-radius:4px; font-family:monospace; font-size:12px;'>\1</span>", s)
            out.append(s)
    if in_table: out.append("</tbody></table></div>")
    if in_ul: out.append("</ul>")
    combined = "\n".join(out)
    paras = re.split(r"\n{2,}", combined)
    result = []
    for p in paras:
        p = p.strip()
        if not p: continue
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
        if b: secs.append({"num": 0, "title": "Visão Geral do Trimestre", "body": b, "nota": None})
    
    for n in range(1, 5):
        pat = rf"\*?\*?Se[cç][aã]o\s*{n}[:\s\–\-].*?\n([\s\S]*?)(?=\*?\*?Se[cç][aã]o\s*{n+1}|\Z)"
        m = re.search(pat, text or "", re.IGNORECASE)
        if not m: continue
        body = m.group(1).strip()
        nm = re.search(rf"Nota\s+Se[cç][aã]o\s+{n}[:\s]+(\d[.,]?\d?)\s*/\s*5", body, re.IGNORECASE)
        nota = _f(nm.group(1)) if nm else None
        body = re.sub(rf"\*?\*?Nota\s+Se[cç][aã]o\s+{n}[:\s]+\d[.,]?\d?\s*/\s*5\*?\*?", "", body).strip()
        body = re.sub(r"```json[\s\S]*?```", "", body).strip()
        secs.append({"num": n, "title": titles.get(n, f"Seção {n}"), "body": body, "nota": nota})
    return secs


# ═══════════════════════════════════════════════════════════════
# CHART CONFIG PER SECTION
# ═══════════════════════════════════════════════════════════════

SECTION_CHARTS = {
    0: [
        {
            "id": "cS0A", "title": "Receita & Lucro — Visão Geral", "sub": "Evolução nos últimos trimestres",
            "evo_var": "rec", 
            "js": """new Chart(document.getElementById('cS0A'),{type:'bar',data:{labels,datasets:[
  {label:'Receita',data:rec,backgroundColor:'rgba(30,64,175,.18)',borderColor:'#1E40AF',borderWidth:2,borderRadius:5,maxBarThickness:32},
  {label:'Lucro',  data:luc,backgroundColor:'rgba(5,150,105,.75)',borderRadius:5,maxBarThickness:32},
]},options:{...BASE,scales:{x:XA,y:YA}}});"""
        },
    ],
    1: [
        {
            "id": "cS1A", "title": "Evolução da Receita", "sub": "Crescimento trimestral absoluto",
            "evo_var": "rec",
            "js": """new Chart(document.getElementById('cS1A'),{type:'bar',data:{labels,datasets:[
  {label:'Receita',data:rec,backgroundColor:'rgba(30,64,175,.18)',borderColor:'#1E40AF',borderWidth:2,borderRadius:5,maxBarThickness:32},
]},options:{...BASE,scales:{x:XA,y:YA}}});"""
        },
{
            "id": "cS1B", "title": "Composição da Receita", "sub": "Share de Categorias (Último Trimestre)",
            "js": """
            try {
                const wrap = document.getElementById('cS1B')?.parentElement;
                if(wrap && typeof CD !== 'undefined' && CD.length > 0) {
                    let compData = {};
                    for(let i=CD.length-1; i>=0; i--){
                        if(CD[i].composicao_receita && Object.keys(CD[i].composicao_receita || {}).length > 0) { 
                            compData = CD[i].composicao_receita; 
                            break; 
                        } else if(CD[i].segmentos && CD[i].segmentos.length > 0) {
                            CD[i].segmentos.forEach(s => compData[s.nome] = parseFloat(s.valor));
                            break;
                        }
                    }
                    
                    let cats = {};
                    if(Object.keys(compData).length > 0) {
                        const isNested = Object.values(compData).some(v => typeof v === 'object' && !Array.isArray(v) && v !== null);
                        cats = isNested ? compData : { "Composição Geral": compData };
                    }
                    
                    const keys = Object.keys(cats);
                    if(keys.length === 0) {
                        wrap.innerHTML = '<div style="padding:30px;text-align:center;color:#9CA3AF;font-size:12px;">Dados não disponíveis.</div>';
                    } else {
                        wrap.innerHTML = ''; 
                        wrap.style.display = 'flex';
                        wrap.style.flexDirection = 'column'; 
                        wrap.style.gap = '40px'; 
                        wrap.style.alignItems = 'center';
                        wrap.style.padding = '20px 0';
                        wrap.style.height = 'auto'; 
                        
                        keys.forEach((catName, idx) => {
                            const dataObj = cats[catName];
                            const labels = Object.keys(dataObj);
                            const data = Object.values(dataObj).map(v => parseFloat(v));
                            
                            const col = document.createElement('div');
                            col.style.width = '100%';
                            col.style.display = 'flex';
                            col.style.flexDirection = 'column';
                            
                            if(keys.length > 1) {
                                const title = document.createElement('div');
                                title.innerText = catName.toUpperCase();
                                title.style.textAlign = 'center';
                                title.style.fontSize = '12px';
                                title.style.fontWeight = 'bold';
                                title.style.color = '#475569';
                                title.style.marginBottom = '15px';
                                title.style.letterSpacing = '0.05em';
                                col.appendChild(title);
                            }
                            
                            const canWrap = document.createElement('div');
                            canWrap.style.position = 'relative';
                            canWrap.style.height = '240px'; 
                            canWrap.style.width = '100%';
                            
                            const can = document.createElement('canvas');
                            can.id = 'donut_dinamico_' + idx;
                            can.style.cursor = 'zoom-in';
                            can.onclick = () => openModal(can.id);
                            
                            canWrap.appendChild(can);
                            col.appendChild(canWrap);
                            wrap.appendChild(col);
                            
                            new Chart(can, {
                                type: 'doughnut',
                                data: {
                                    labels: labels,
                                    datasets: [{
                                        data: data,
                                        backgroundColor: ['#1E3A8A','#059669','#D97706','#7C3AED', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6'],
                                        borderWidth: 2, hoverOffset: 4
                                    }]
                                },
                                options: {
                                    ...BASE, cutout: '50%',
                                    maintainAspectRatio: false, 
                                    layout: { padding: 10 },
                                    plugins: {
                                        ...BASE.plugins,
                                        legend: { display: true, position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
                                        datalabels: { 
                                            ...BASE.plugins.datalabels, 
                                            display: true,
                                            color: '#111827',
                                            anchor: 'end',
                                            align: 'end',
                                            offset: 2,
                                            font: { weight: 'bold', size: 11 },
                                            formatter: (v, ctx) => {
                                                const total = ctx.dataset.data.reduce((a,b)=>a+b,0);
                                                return total ? (v/total*100).toFixed(1)+'%' : '';
                                            } 
                                        }
                                    }
                                }
                            });
                        });
                    }
                }
            } catch(e) { 
                console.error("Erro ao desenhar os gráficos.", e); 
            }
            """
        },
    ],
    2: [
        {
            "id": "cS2A", "title": "Margens Bruta e Líquida (%)", "sub": "Comparativo trimestral de margens",
            "evo_var": "mL",
            "js": """new Chart(document.getElementById('cS2A'),{type:'line',data:{labels,datasets:[
  {label:'Margem Bruta',  data:mB,borderColor:'#7C3AED',backgroundColor:'rgba(124,58,237,.07)',
   fill:true,borderWidth:2.5,pointBackgroundColor:'#7C3AED',pointRadius:4,tension:.35},
  {label:'Margem Líquida',data:mL,borderColor:'#D97706',backgroundColor:'transparent',
   borderWidth:2,borderDash:[5,3],pointBackgroundColor:'#D97706',pointRadius:4,tension:.35},
]},options:{...BASE,scales:{x:XA,y:{...YA,ticks:{...YA.ticks,callback:v=>v+'%'}}}}});"""
        },
        {
            "id": "cS2B", "title": "Variação de Despesas YoY", "sub": "Crescimento/Queda de Gastos (% ou p.p.)",
            "js": """
            let desp = [];
            for(let i=CD.length-1; i>=0; i--){
                if(CD[i].despesas_var && CD[i].despesas_var.length > 0) { desp = CD[i].despesas_var; break; }
            }
            
            const varLabels = desp.length ? desp.map(d => d.nome) : ['P&D', 'Vendas/Mkt', 'G&A'];
            const varData   = desp.length ? desp.map(d => parseFloat(d.var_pct)) : [7.1, 0.1, -9.1];

            const bgColors = varData.map((v, i) => {
                const nameL = varLabels[i].toLowerCase();
                const isRev = nameL.includes('receita') || nameL.includes('rec.');
                if (isRev) return v >= 0 ? 'rgba(16, 185, 129, 0.85)' : 'rgba(239, 68, 68, 0.85)';
                return v <= 0 ? 'rgba(16, 185, 129, 0.85)' : 'rgba(239, 68, 68, 0.85)';
            });
            
            new Chart(document.getElementById('cS2B'),{
                type: 'bar',
                data:{
                    labels: varLabels,
                    datasets:[{
                        label: 'Variação',
                        data: varData,
                        backgroundColor: bgColors,
                        borderRadius: 4,
                        barPercentage: 0.6
                    }]
                },
                options:{
                    ...BASE, indexAxis: 'y',
                    plugins: {
                       ...BASE.plugins,
                       datalabels: { ...BASE.plugins.datalabels, align: 'right', anchor: 'end', formatter: v => (v > 0 ? '+' : '') + v.toFixed(1) + '%' }
                    },
                    scales:{
                        x: { grid:{color:'#F1F5F9'}, border:{display:false}, ticks:{color:'#9CA3AF', font:{size:10}, callback:v=>v+'%'} },
                        y: { grid:{display:false}, border:{display:false}, ticks:{color:'#475569', font:{size:11, weight:'500'}} }
                    }
                }
            });"""
        },
    ],
    3: [
        {
            "id": "cS3A", "title": "Dívida vs EBITDA", "sub": "Evolução do Endividamento e Geração de Caixa",
            "evo_var": "divida",
            "evo_invert": True,
            "js": """new Chart(document.getElementById('cS3A'),{type:'bar',data:{labels,datasets:[
  {label:'Dívida',data:divida,type:'line',borderColor:'#DC2626',backgroundColor:'rgba(220,38,38,0.05)',
   fill:true,borderWidth:2.5,pointBackgroundColor:'#DC2626',pointRadius:4,tension:.35, datalabels: { align: 'top', anchor: 'end' } },
  {label:'EBITDA/L.Oper',data:ebitda,backgroundColor:'rgba(5,150,105,.8)',borderRadius:4,maxBarThickness:30, datalabels: { align: 'bottom', anchor: 'end' } }
]},options:{...BASE,scales:{x:XA,y:YA}}});"""
        },
    ],
    4: [
        {
            "id": "cS4A", "title": "Lucro Líquido por Trimestre", "sub": "Evolução do bottom-line",
            "evo_var": "luc",
            "js": """new Chart(document.getElementById('cS4A'),{type:'bar',data:{labels,datasets:[
  {label:'Lucro',data:luc,
   backgroundColor:luc.map((_,i)=>i===luc.length-1?'rgba(5,150,105,.9)':'rgba(5,150,105,.35)'),
   borderColor:'#059669',borderWidth:1.5,borderRadius:6,maxBarThickness:36},
]},options:{...BASE,scales:{x:XA,y:YA}}});"""
        },
        {
            "id": "cS4B", "title": "Margem Líquida (%)", "sub": "Rentabilidade sobre a receita",
            "evo_var": "mL",
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
    is_call = meta.get("tipo") == "Earnings Call"

    rn  = _f(data.get("receita_nota", 0))
    ln  = _f(data.get("lucro_nota", 0))
    dn  = _f(data.get("divida_nota", 0))
    ren = _f(data.get("rentabilidade_nota", 0))
    g   = _f(data.get("nota_geral", 0))
    tese = data.get("tese_investimento", "")

    tg   = _score_theme(g)
    secs = _parse_sections(analise) if not is_call else []
    raw_cd = data.get("chart_data") or _extract_charts(analise)
    comp_data = _extract_composicao(analise)
    
    cd = [d for d in raw_cd if str(d.get("name","")) in analise]
    if not cd: cd = raw_cd
    
    cd = [d for d in cd if _f(d.get("receita", 0)) > 0]
    cd = sorted(cd, key=lambda d: _quarter_sort_key(d.get("name")))
    
    # Se for call, não passamos gráficos
    cj   = json.dumps(cd) if not is_call else "[]"
    cj_comp = json.dumps(comp_data) if not is_call else "{}"

    tese_c    = re.sub(r"\*\*|\*", "", tese).strip()
    tese_html = "".join(f"<p>{_h.escape(p.strip())}</p>" for p in tese_c.split("\n\n") if p.strip()) or f"<p>{_h.escape(tese_c)}</p>"

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

    # Lógica Condicional: O que mostrar no canto direito do Hero
    if is_call:
        hero_right_html = f"""
        <div class="hero-right" style="background:#F5F3FF; border-color:#DDD6FE;">
          <span class="hero-score-lbl" style="color:#7C3AED;">Tipo de Documento</span>
          <div style="font-size:38px; margin: 10px 0;">🎙️</div>
          <div class="hero-score-verdict" style="color:#6D28D9;">Earnings Call</div>
        </div>
        """
        hero_desc = "Resumo analítico gerado por IA com base na transcrição da teleconferência de resultados. Focado em insights da diretoria, guidance, expansão e perguntas do mercado."
    else:
        hero_right_html = f"""
        <div class="hero-right">
          <span class="hero-score-lbl">Score IA — Média Ponderada</span>
          {_hero_ring(g, 110)}
          <div class="hero-score-verdict">{tg['label']}</div>
        </div>
        """
        hero_desc = "Relatório completo gerado por IA com base no release de resultados oficial. Avaliação de receita, margens, endividamento e rentabilidade com visão estratégica."

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

    # Oculta pilares se for Call
    pillars_html = "".join(_pillar(p) for p in pillars) if not is_call else ""
    sumbar_display = "none" if is_call else "block"

    all_chart_js = []

    def _section_block(s):
        t  = _score_theme(s["nota"]) if s["nota"] is not None else None
        charts_cfg = SECTION_CHARTS.get(s["num"], [])

        nota_box = ""
        if t:
            nota_box = f"""
<div class="nota-box" style="background:{t['bg']};border:1px solid {t['border']};">
  <div class="nota-box-label">Nota desta seção</div>
  <div class="nota-box-val" style="color:{t['bar']}">{s['nota']:.0f}<span class="nota-box-denom">/5</span></div>
  <div class="nota-box-tag" style="background:{t['badge_bg']};color:{t['badge_text']}">{t['icon']} {t['label']}</div>
</div>"""

        chart_panels_html = ""
        for cfg in charts_cfg[:2]:
            has_evo = "evo_var" in cfg
            evo_html = f'<div id="evo-{cfg["id"]}" class="cp-evo"></div>' if has_evo else ""
            
            js_snippet = f"if(document.getElementById('{cfg['id']}')&&CD.length){{{cfg['js']}}}"
            if has_evo:
                invert_flag = str(cfg.get('evo_invert', 'false')).lower()
                js_snippet += f" setTimeout(()=>renderEvo('{cfg['id']}', {cfg['evo_var']}, {invert_flag}), 100);"
            
            all_chart_js.append(js_snippet)

            chart_panels_html += f"""
<div class="chart-panel">
  <div class="cp-top">
      <div>
          <div class="cp-title">{cfg['title']}</div>
          <div class="cp-sub">{cfg['sub']}</div>
      </div>
      {evo_html}
  </div>
  <div class="cp-wrap" title="Clique para expandir">
    <canvas id="{cfg['id']}" onclick="openModal('{cfg['id']}')"></canvas>
  </div>
</div>"""

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

    # Condicional: Renderização das Seções e Gráficos
    if is_call:
        secs_html = f"""
<section class="sec-block fade-in" style="--acc:#8B5CF6; border-color:#DDD6FE;">
  <div class="sec-accent-bar"></div>
  <div class="sec-inner">
    <div class="sec-head">
      <div>
        <h2 class="sec-title">Principais Insights e Timestamps</h2>
      </div>
    </div>
    <div class="sec-layout--full">
      <div class="sec-text abody">{_clean_md(analise)}</div>
    </div>
  </div>
</section>"""
        charts_js = ""
    else:
        secs_html = "".join(_section_block(s) for s in secs)
        charts_js = "\n".join(all_chart_js)

    verdict_labels = {
        "Muito Ruim": ("vtag-sell",  "Resultado Muito Fraco"),
        "Ruim":       ("vtag-sell",  "Resultado Fraco"),
        "Regular":    ("vtag-watch", "Resultado Regular"),
        "Bom":        ("vtag-buy",   "Resultado Bom"),
        "Excelente":  ("vtag-buy",   "Resultado Excelente"),
    }
    vcls, vtitle = verdict_labels.get(tg["label"], ("vtag-watch", "—"))

    # Lógica Condicional: Grid de Conclusão Final
    if is_call:
        conclusion_grid_html = f"""
      <div class="c-grid" style="grid-template-columns:1fr 1fr;">
        <div>
          <div class="c-cell-lbl">Empresa · Período</div>
          <div class="c-cell-val">{_h.escape(empresa.title())}</div>
          <div style="font-size:12px;color:#64748B;margin-top:3px">{_h.escape(periodo)}</div>
        </div>
        <div>
          <div class="c-cell-lbl">Aviso Legal</div>
          <div class="c-cell-val" style="font-size:12px;line-height:1.5;color:#94A3B8">
            Resumo gerado por Inteligência Artificial a partir da transcrição. Não constitui recomendação de investimento.
          </div>
        </div>
      </div>"""
        conclusion_title = "Fim da Transcrição"
        conclusion_body  = ""
    else:
        conclusion_grid_html = f"""
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
      </div>"""
        conclusion_title = "Conclusão Estratégica e Outlook"
        conclusion_body  = f'<div class="c-body">{tese_html}</div>'

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{_h.escape(empresa.title())} · {_h.escape(periodo)} · FinAnalyzer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-datalabels/2.2.0/chartjs-plugin-datalabels.min.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{font-size:16px;scroll-behavior:smooth}}
body{{font-family:'DM Sans',system-ui,sans-serif;background:#F1F5F9;color:#111827;line-height:1.65;-webkit-font-smoothing:antialiased}}

@media print{{
  body{{background:#fff}}
  .no-print{{display:none!important}}
  .page-break{{break-before:page}}
  .sec-block{{break-inside:avoid}}
  .chart-panel {{ break-inside: avoid; }}
  .cp-wrap {{ height: 280px !important; }}
}}

@keyframes fadeUp{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
.fade-in{{animation:fadeUp .6s ease-out forwards;}} 

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
.tb-score{{font-family:'DM Mono',monospace;font-size:14px;font-weight:500;color:{tg['bar'] if not is_call else '#7C3AED'}}}
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
.sumbar{{background:#0F172A;padding:0; display:{sumbar_display};}}
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

.sec-layout{{display:grid;grid-template-columns:1fr 300px;gap:28px;align-items:start}}
.sec-layout--full{{display:block}}

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

.sec-aside{{display:flex;flex-direction:column;gap:14px}}

.nota-box{{border-radius:10px;padding:16px;text-align:center}}
.nota-box-label{{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:#6B7280;display:block;margin-bottom:6px}}
.nota-box-val{{font-family:'DM Mono',monospace;font-size:38px;font-weight:500;
  line-height:1;display:block;margin-bottom:6px}}
.nota-box-denom{{font-size:15px;color:#9CA3AF;font-weight:400}}
.nota-box-tag{{font-size:11px;font-weight:700;padding:4px 10px;
  border-radius:4px;display:inline-block}}

.chart-panel{{border:1px solid #E5E7EB;border-radius:10px;padding:16px;background:#FAFAFA}}
.cp-top {{display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;}}
.cp-title{{font-size:12px;font-weight:600;color:#111827;margin-bottom:2px}}
.cp-sub{{font-size:11px;color:#9CA3AF;}}
.cp-wrap{{position:relative;width:100%;height:260px; margin-top: 10px;}}

/* ─── MODAL (LIGHTBOX) ─── */
.modal {{
  display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%;
  background-color: rgba(15, 23, 42, 0.85); backdrop-filter: blur(4px);
  align-items: center; justify-content: center;
}}
.modal-content {{
  background: #fff; border-radius: 12px; padding: 24px;
  width: 90%; max-width: 900px; height: 80vh;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  position: relative;
}}
.modal-close {{
  position: absolute; top: -15px; right: -15px; background: #EF4444; color: #fff;
  border: none; border-radius: 50%; width: 32px; height: 32px; cursor: pointer;
  font-size: 16px; font-weight: bold; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}}
.modal-canvas-wrap {{ position: relative; width: 100%; height: 100%; }}

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

<div id="chartModal" class="modal no-print" onclick="closeModal(event)">
  <div class="modal-content" onclick="event.stopPropagation()">
    <button class="modal-close" onclick="closeModal()">×</button>
    <div class="modal-canvas-wrap">
      <canvas id="modalCanvas"></canvas>
    </div>
  </div>
</div>

<nav class="topbar no-print">
  <div class="tb-brand">
    <div class="tb-cube">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="white"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22" fill="none" stroke="rgba(255,255,255,.5)" stroke-width="1.5"/></svg>
    </div>
    <span class="tb-name">FinAnalyzer</span>
  </div>
  <nav class="tb-nav">
    <a href="#analise" class="tb-link">Análise</a>
    <a href="#conclusao" class="tb-link">Resumo</a>
  </nav>
  <div class="tb-right">
    <span><span class="tb-score-lbl">{"Status" if is_call else "Score IA"}</span><span class="tb-score">{"Call Analisado" if is_call else f"{g:.1f}/5"}</span></span>
    <button class="print-btn" onclick="window.print()">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg> Salvar PDF
    </button>
  </div>
</nav>

<div class="hero">
  <div class="hero-inner">
    <div class="hero-row">
      <div class="hero-left">
        <div class="hero-period"><div class="hero-dot"></div>{_h.escape(periodo)} · {"Earnings Call" if is_call else "Resultados Trimestrais"}</div>
        <h1 class="hero-empresa">{_h.escape(empresa.title())}</h1>
        <p class="hero-desc">{hero_desc}</p>
      </div>
      {hero_right_html}
    </div>
    <div id="indicadores" class="pillars">{pillars_html}</div>
  </div>
</div>

<div class="sumbar"><div class="sumbar-inner" id="sumbarInner"></div></div>

<div class="main">
  <div id="analise">
    <div class="sec-label">{"Extração Textual" if is_call else "Análise Completa por IA"}</div>
    <div class="sec-heading">{"Leitura da Transcrição" if is_call else "Leitura dos Resultados"}</div>
    {secs_html}
  </div>

  <div class="divider page-break"></div>

  <div id="conclusao">
    <div class="conclusion" style="{'background:linear-gradient(135deg, #1E1B4B 0%, #4C1D95 100%);' if is_call else ''}">
      <div class="c-eyebrow">{"Síntese" if is_call else "Tese de Investimento"}</div>
      <h2 class="c-title">{conclusion_title}</h2>
      {conclusion_body}
      {conclusion_grid_html}
    </div>
  </div>
</div>

<div class="footer no-print">
  <span>Gerado pelo <strong style="color:#6B7280">FinAnalyzer</strong> · Documento Oficial · Não é recomendação de investimento</span>
  <span>{_h.escape(empresa.title())} · {_h.escape(periodo)}</span>
</div>

<script>
try {{ Chart.register(ChartDataLabels); }} catch(e) {{ console.error("DataLabels error", e); }}

const CD = __CHART_JSON__;
const COMP_DATA = __COMPOSICAO_JSON__;
const NOTAS = {{ receita:__RN__, lucro:__LN__, divida:__DN__, roe:__REN__, geral:__G__ }};

const formatBRL = (v) => {{
  let n = Number(String(v ?? '').replace(',', '.'));
  if (!Number.isFinite(n) || n === 0) return '0';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e9) return sign + (abs / 1e9).toFixed(2) + ' Bi';
  if (abs >= 1e6) return sign + (abs / 1e6).toFixed(2) + ' M';
  if (abs >= 1e3) return sign + (abs / 1e3).toFixed(2) + ' K';
  return sign + abs.toFixed(2);
}};

const formatPct = (v) => {{
  let n = Number(String(v ?? '').replace(',', '.'));
  return Number.isFinite(n) ? n.toFixed(2) + '%' : '0%';
}};

const renderEvo = (chartId, dataArr, invertColor = false) => {{
  if (!dataArr) return;
  const validData = dataArr.filter(v => v !== 0 && v !== null && v !== undefined);
  if (validData.length < 2) return;
  const first = validData[0], last = validData[validData.length - 1];
  if (!first || first === 0) return;
  const pct = ((last - first) / Math.abs(first)) * 100;
  
  const el = document.getElementById('evo-' + chartId);
  if (el) {{
      const isPositive = pct >= 0;
      let isGood = isPositive;
      if (invertColor) isGood = !isPositive; 

      const color = isGood ? '#10B981' : '#EF4444';
      const bg    = isGood ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';
      const icon  = isPositive ? '↗' : '↘';
      
      el.innerHTML = `<span style="display:inline-flex; align-items:center; gap:3px; color:${{color}}; font-weight:700; font-size:11px; background:${{bg}}; padding:3px 8px; border-radius:6px; letter-spacing:0.03em;">${{icon}} ${{Math.abs(pct).toFixed(1)}}%</span>`;
  }}
}};

try {{
    const el  = document.querySelector('.hero-right svg text');
    if (el) {{
        const tgt = NOTAS.geral; let st = null;
        const run = ts => {{
            if (!st) st = ts;
            const p = Math.min((ts - st) / 800, 1);
            el.textContent = (tgt * (1 - Math.pow(1-p,3))).toFixed(1);
            if (p < 1) requestAnimationFrame(run);
            else el.textContent = tgt.toFixed(1);
        }};
        setTimeout(() => requestAnimationFrame(run), 400);
    }}
}} catch(e) {{ console.error("Ring error", e); }}

try {{
  const bar = document.getElementById('sumbarInner');
  if (bar && CD.length) {{
      const toNum = v => {{
        const n = Number(String(v ?? '').replace(',', '.'));
        return Number.isFinite(n) ? n : 0;
      }};
      
      const sorted = [...CD].sort((a, b) => {{
        const A = a?.name || ''; const B = b?.name || '';
        const ma = String(A).toUpperCase().match(/(\d)\s*T\s*(\d{{2,4}})/);
        const mb = String(B).toUpperCase().match(/(\d)\s*T\s*(\d{{2,4}})/);
        const key = (m) => m ? [Number(m[2]) < 100 ? 2000 + Number(m[2]) : Number(m[2]), Number(m[1])] : [9999, 9];
        const ka = key(ma), kb = key(mb);
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
        {{v: formatBRL(last.receita),   l: 'Receita',    d: delta(last.receita, prev?.receita)}},
        {{v: formatBRL(last.lucro),     l: 'Lucro',      d: delta(last.lucro, prev?.lucro)}},
        {{v: formatPct(last.margemBruta),    l: 'Mg. Bruta',  d: delta(last.margemBruta, prev?.margemBruta)}},
        {{v: formatPct(last.margemLiquida),  l: 'Mg. Líquida',d: delta(last.margemLiquida, prev?.margemLiquida)}},
        {{v: NOTAS.geral.toFixed(1)+'/5', l: 'Score IA', d: ''}},
      ].forEach(it => {{
        const c = document.createElement('div');
        c.className = 'sum-cell';
        c.innerHTML = `<div class="sum-val">${{it.v}}</div><div class="sum-lbl">${{it.l}}</div>${{it.d}}`;
        bar.appendChild(c);
      }});
  }} else if(bar) {{ document.querySelector('.sumbar').style.display='none'; }}
}} catch(e) {{ console.error("Summary bar error", e); }}

const TT = {{ backgroundColor:'#0F172A', titleColor:'#fff', bodyColor:'#CBD5E1', borderColor:'#1E293B', borderWidth:1, cornerRadius:8, padding:10 }};

const XA = {{ 
    grid:{{display:false}}, 
    ticks:{{color:'#9CA3AF', font:{{size:10}}}}, 
    border:{{display:false}} 
}};

const YA = {{ 
    grid:{{color:'#F1F5F9'}}, 
    border:{{display:false}}, 
    ticks:{{
        color:'#9CA3AF', font:{{size:10}}, 
        callback: function(value) {{ return formatBRL(value); }}
    }} 
}};

const BASE = {{
  responsive: true, maintainAspectRatio: false,
  animation: {{duration: 800, easing: 'easeOutQuart'}},
  layout: {{ padding: {{ top: 35, right: 35, bottom: 10, left: 10 }} }}, 
  plugins: {{
    legend: {{display: false}}, 
    tooltip: TT,
    datalabels: {{
      color: '#475569',
      font: {{ weight: '600', size: 10 }},
      anchor: 'end',
      align: function(context) {{
          return context.chart.config.options.indexAxis === 'y' ? 'right' : 'top';
      }},
      offset: 4,
      formatter: function(value, context) {{
          const lbl = context.dataset.label || '';
          if (lbl.includes('Margem') || lbl.includes('Spread')) return value.toFixed(1) + '%';
          return formatBRL(value);
      }}
    }}
  }}
}};

/* ─── LÓGICA DO MODAL (LIGHTBOX) ─── */
let activeModalChart = null;

function openModal(chartId) {{
    const originalChart = Chart.getChart(chartId);
    if(!originalChart) return;
    
    document.getElementById('chartModal').style.display = 'flex';
    const ctx = document.getElementById('modalCanvas').getContext('2d');
    
    if(activeModalChart) activeModalChart.destroy();
    
    activeModalChart = new Chart(ctx, {{
        type: originalChart.config.type,
        data: originalChart.config.data,
        options: {{
            ...originalChart.config.options,
            maintainAspectRatio: false,
            responsive: true
        }}
    }});
}}

function closeModal(e) {{
    document.getElementById('chartModal').style.display = 'none';
    if(activeModalChart) {{
        activeModalChart.destroy();
        activeModalChart = null;
    }}
}}

try {{
  if (CD.length > 0) {{
      const labels = CD.map(d => d.name || '');
      const rec    = CD.map(d => d.receita || 0);
      const luc    = CD.map(d => d.lucro || 0);
      const divida = CD.map(d => d.divida || 0);
      const ebitda = CD.map(d => d.ebitda || 0);
      const mB     = CD.map(d => d.margemBruta || 0);
      const mL     = CD.map(d => d.margemLiquida || 0);
      {charts_js}
  }}
}} catch(e) {{ console.error("Chart generation error:", e); }}

</script>
</body>
</html>
""".replace("__CHART_JSON__", cj)\
   .replace("__COMPOSICAO_JSON__", cj_comp)\
   .replace("__RN__",  str(rn))\
   .replace("__LN__",  str(ln))\
   .replace("__DN__",  str(dn))\
   .replace("__REN__", str(ren))\
   .replace("__G__",   str(g))\
   .replace("{charts_js}", charts_js)

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