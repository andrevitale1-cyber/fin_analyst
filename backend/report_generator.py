"""
report_generator.py  —  FinAnalyzer v2
════════════════════════════════════════════════════════════════
Coloque na mesma pasta do main.py e adicione 2 linhas:

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

# ─────────── helpers ───────────

def _f(v) -> float:
    try: return float(str(v).replace(",",".").strip())
    except: return 0.0

def _score(n):
    if n>=4: return {"text":"#0A6640","bg":"#D1FAE5","border":"#6EE7B7","label":"Excelente","hex":"#0A6640"}
    if n>=3: return {"text":"#1D4ED8","bg":"#DBEAFE","border":"#93C5FD","label":"Bom",      "hex":"#1D4ED8"}
    if n>=2: return {"text":"#92400E","bg":"#FEF3C7","border":"#FDE68A","label":"Regular",  "hex":"#D97706"}
    return         {"text":"#991B1B","bg":"#FEE2E2","border":"#FCA5A5","label":"Fraco",     "hex":"#DC2626"}

def _extract_charts(text):
    try:
        m = re.search(r"```json\s*([\s\S]*?)\s*```", text or "")
        if m: return json.loads(m.group(1))
    except: pass
    return []

def _clean_md(text):
    if not text: return ""
    lines = text.split("\n")
    out, in_table, in_ul = [], False, False
    for line in lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            if not in_table:
                if in_ul: out.append("</ul>"); in_ul=False
                out.append('<div class="tbl-wrap"><table class="tbl">')
                in_table=True
            cells=[c.strip() for c in s.strip("|").split("|")]
            if all(re.match(r"^[-:]+$",c) for c in cells): continue
            is_hdr = not any("<td>" in r for r in out[-5:])
            tag="th" if is_hdr else "td"
            row="".join(f"<{tag}>{_h.escape(c)}</{tag}>" for c in cells)
            out.append(f"<tr>{row}</tr>"); continue
        if in_table: out.append("</table></div>"); in_table=False
        if re.match(r"^[-•*]\s",s):
            if not in_ul: out.append("<ul>"); in_ul=True
            body=re.sub(r"\*\*(.+?)\*\*",r"<strong>\1</strong>",s[2:])
            out.append(f"<li>{body}</li>"); continue
        if in_ul: out.append("</ul>"); in_ul=False
        if s:
            s=re.sub(r"\*\*(.+?)\*\*",r"<strong>\1</strong>",s)
            out.append(s)
    if in_table: out.append("</table></div>")
    if in_ul: out.append("</ul>")
    combined="\n".join(out)
    paras=re.split(r"\n{2,}",combined)
    res=[]
    for p in paras:
        p=p.strip()
        if not p: continue
        res.append(p if p.startswith("<") else f"<p>{p}</p>")
    return "\n".join(res)

def _parse_sections(text):
    titles={1:"Evolução Operacional e Top Line",2:"Rentabilidade e Margens",
            3:"Estrutura de Capital e Gestão de Risco",4:"Sumário Executivo do Lucro Líquido",
            5:"Conclusão Estratégica e Outlook"}
    secs=[]
    intro=re.search(r"^([\s\S]*?)(?=\*?\*?Seção\s*1)",text or "",re.IGNORECASE)
    if intro:
        b=intro.group(1).strip().replace("**","")
        if b: secs.append({"num":0,"title":"Visão Geral do Trimestre","body":b,"nota":None})
    for n in range(1,6):
        pat=rf"\*?\*?Seção\s*{n}[:\s\–\-].*?\n([\s\S]*?)(?=\*?\*?Seção\s*{n+1}|\Z)"
        m=re.search(pat,text or "",re.IGNORECASE)
        if not m: continue
        body=m.group(1).strip()
        nm=re.search(rf"Nota\s+Seção\s+{n}[:\s]+(\d[.,]?\d?)\s*/\s*5",body,re.IGNORECASE)
        nota=_f(nm.group(1)) if nm else None
        body=re.sub(rf"\*?\*?Nota\s+Seção\s+{n}[:\s]+\d[.,]?\d?\s*/\s*5\*?\*?","",body).strip()
        body=re.sub(r"```json[\s\S]*?```","",body).strip()
        secs.append({"num":n,"title":titles.get(n,f"Seção {n}"),"body":body,"nota":nota})
    return secs

# ─────────── main generator ───────────

def generate_report_html(resultado: dict) -> str:
    meta    = resultado.get("metadata",{})
    data    = resultado.get("data",{})
    analise = resultado.get("analise_completa","")

    empresa = (meta.get("empresa") or "Empresa").upper()
    periodo = meta.get("periodo") or ""

    rn  = _f(data.get("receita_nota",0))
    ln  = _f(data.get("lucro_nota",0))
    dn  = _f(data.get("divida_nota",0))
    ren = _f(data.get("rentabilidade_nota",0))
    g   = _f(data.get("nota_geral",0))
    tese= data.get("tese_investimento","")
    sc  = _score(g)

    secs   = _parse_sections(analise)
    charts = _extract_charts(analise)
    cj     = json.dumps(charts)

    tese_clean = re.sub(r"\*\*|\*","",tese).strip()
    tese_html  = "".join(
        f"<p>{_h.escape(p.strip())}</p>" for p in tese_clean.split("\n\n") if p.strip()
    ) or f"<p>{_h.escape(tese_clean)}</p>"

    # pillar cards
    pillars=[
        {"label":"Receita",          "nota":rn,  "accent":"#003087","icon_bg":"#EEF3FF",
         "icon":'<path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>'},
        {"label":"Margem / Lucro",   "nota":ln,  "accent":"#0A6640","icon_bg":"#D1FAE5",
         "icon":'<line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>'},
        {"label":"Dívida / Risco",   "nota":dn,  "accent":"#DC2626","icon_bg":"#FEE2E2",
         "icon":'<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'},
        {"label":"Rentabilidade ROE","nota":ren, "accent":"#D97706","icon_bg":"#FEF3C7",
         "icon":'<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>'},
    ]
    def pkard(p):
        c=_score(p["nota"]); pct=min(100,int(p["nota"]/5*100))
        return f"""<div class="kpi-card" style="--acc:{p['accent']};">
          <div class="kpi-icon" style="background:{p['icon_bg']};">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{p['accent']}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{p['icon']}</svg>
          </div>
          <div class="kpi-label">{p['label']}</div>
          <div class="kpi-value">{p['nota']:.1f}<span class="kpi-denom">/5</span></div>
          <div class="kpi-track"><div class="kpi-fill" style="width:{pct}%;background:{p['accent']};"></div></div>
          <span class="kpi-badge" style="background:{c['bg']};color:{c['text']};">{c['label']}</span>
        </div>"""
    kpis = "".join(pkard(p) for p in pillars)

    # section blocks
    icons={0:"🔍",1:"📊",2:"📈",3:"🏦",4:"💰",5:"🎯"}
    def sblock(s):
        nb=""
        if s["nota"] is not None:
            c=_score(s["nota"])
            nb=f'<span class="sec-badge" style="background:{c["bg"]};color:{c["text"]};border-color:{c["border"]};">{s["nota"]:.1f}/5 — {c["label"]}</span>'
        nl=f'<span class="sec-num">Seção {s["num"]}</span>' if s["num"]>0 else ""
        return f"""<div class="sec-block fade-in">
          <div class="sec-hdr">
            <div class="sec-hdr-l">
              <div class="sec-ico">{icons.get(s['num'],'📋')}</div>
              <div>{nl}<h2 class="sec-title">{_h.escape(s['title'])}</h2></div>
            </div>{nb}
          </div>
          <div class="abody">{_clean_md(s['body'])}</div>
        </div>"""
    secs_html="".join(sblock(s) for s in secs)

    if g>=4:   vt,vc="Resultado Sólido","tag-buy"
    elif g>=3: vt,vc="Resultado Moderado","tag-watch"
    else:      vt,vc="Resultado Fraco","tag-neutral"

    CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --blue:#003087;--blue-bg:#EEF3FF;
  --green:#0A6640;--green-bg:#D1FAE5;
  --red:#DC2626;--red-bg:#FEE2E2;
  --amber:#D97706;--amber-bg:#FEF3C7;
  --ink:#0F172A;--ink60:#475569;--ink40:#94A3B8;--ink20:#E2E8F0;--ink10:#F8FAFC;
  --page:#F7F8FA;--white:#fff;--r:12px;--rsm:6px;
}
html{font-size:16px;scroll-behavior:smooth}
body{font-family:'DM Sans',system-ui,sans-serif;background:var(--page);color:var(--ink);line-height:1.65;-webkit-font-smoothing:antialiased}
@media print{
  body{background:#fff}
  .no-print{display:none!important}
  .page-break{break-before:page}
  .avoid-break{break-inside:avoid}
  .fade-in{opacity:1!important;transform:none!important;animation:none!important}
}
@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@keyframes barGrow{from{width:0!important}to{}}
@keyframes scoreCount{from{opacity:0;transform:scale(.85)}to{opacity:1;transform:scale(1)}}
.fade-in{opacity:0;animation:fadeUp .55s ease forwards;animation-play-state:paused}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-thumb{background:var(--ink20);border-radius:3px}

/* PRINT BTN */
.print-btn{
  position:fixed;top:20px;right:20px;background:var(--blue);color:#fff;
  border:none;border-radius:var(--rsm);padding:10px 18px;
  font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;
  cursor:pointer;display:flex;align-items:center;gap:8px;
  z-index:999;box-shadow:0 4px 20px rgba(0,48,135,.35);
  transition:transform .15s,box-shadow .15s;
}
.print-btn:hover{transform:translateY(-1px);box-shadow:0 6px 28px rgba(0,48,135,.4)}

/* COVER */
.cover{min-height:100vh;display:flex;flex-direction:column;justify-content:space-between;padding:60px 72px;background:var(--white);border-bottom:1px solid var(--ink20);position:relative;overflow:hidden}
.cgrad{position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse 55% 55% at 95% 5%,#EEF3FF 0%,transparent 60%),radial-gradient(ellipse 25% 35% at 2% 98%,rgba(10,102,64,.06) 0%,transparent 50%)}
.chdr{display:flex;justify-content:space-between;align-items:flex-start;position:relative}
.brand{display:flex;align-items:center;gap:12px}
.bcube{width:36px;height:36px;background:var(--blue);border-radius:8px;display:flex;align-items:center;justify-content:center}
.bname{font-weight:600;font-size:15px;color:var(--blue);letter-spacing:-.02em}
.bsub{font-size:11px;color:var(--ink40);display:block;margin-top:-2px}
.ppill{background:var(--blue-bg);border:1px solid #C7D7F5;border-radius:999px;padding:6px 16px;font-size:12px;font-weight:500;color:var(--blue);letter-spacing:.04em;text-transform:uppercase}
.cbody{flex:1;display:flex;flex-direction:column;justify-content:center;padding:80px 0 56px;position:relative}
.ceyebrow{font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--ink40);margin-bottom:20px}
.ctitle{font-family:'Playfair Display',serif;font-size:clamp(48px,7vw,86px);font-weight:900;line-height:.95;letter-spacing:-.03em;color:var(--ink);margin-bottom:28px}
.ctitle span{color:var(--blue)}
.cdesc{font-size:17px;color:var(--ink60);font-weight:300;max-width:540px;line-height:1.6;margin-bottom:52px}
.srow{display:flex;align-items:center;gap:40px;padding-top:36px;border-top:1px solid var(--ink20)}
.snum{font-family:'Playfair Display',serif;font-size:88px;font-weight:900;line-height:1;letter-spacing:-.04em;animation:scoreCount .8s ease .4s both}
.sdenom{font-size:28px;color:var(--ink40);font-weight:300}
.slbl{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--ink40)}
.sdesc{font-size:20px;font-weight:600;margin-top:4px}
.cfooter{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--ink40);position:relative}
.bwarn{display:flex;align-items:center;gap:6px;background:#FEF3C7;border:1px solid #FDE68A;border-radius:4px;padding:4px 10px;font-size:11px;font-weight:600;color:var(--amber);letter-spacing:.06em;text-transform:uppercase}

/* CONTENT */
.content{max-width:1120px;margin:0 auto;padding:80px 48px}
.slabel{font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--blue);margin-bottom:8px}
.stitle{font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:var(--ink);margin-bottom:40px;letter-spacing:-.02em}
.divider{height:1px;background:var(--ink20);margin:72px 0}

/* KPIs */
.kgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:64px}
.kpi-card{background:var(--white);border:1px solid var(--ink20);border-radius:var(--r);padding:24px;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s;cursor:default}
.kpi-card:hover{transform:translateY(-3px);box-shadow:0 8px 28px rgba(0,0,0,.08)}
.kpi-card::after{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--acc);border-radius:var(--r) var(--r) 0 0}
.kpi-icon{width:38px;height:38px;border-radius:var(--rsm);display:flex;align-items:center;justify-content:center;margin-bottom:16px}
.kpi-label{font-size:12px;color:var(--ink40);font-weight:500;margin-bottom:8px}
.kpi-value{font-family:'Playfair Display',serif;font-size:38px;font-weight:700;line-height:1;color:var(--ink)}
.kpi-denom{font-size:16px;color:var(--ink40);font-family:'DM Sans',sans-serif;font-weight:300}
.kpi-track{height:4px;background:var(--ink20);border-radius:99px;margin-top:14px;overflow:hidden}
.kpi-fill{height:100%;border-radius:99px;animation:barGrow 1s ease .6s both}
.kpi-badge{display:inline-block;margin-top:10px;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600}

/* GAUGE ROW */
.grow{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:64px}
.gcard{background:var(--white);border:1px solid var(--ink20);border-radius:var(--r);padding:24px;text-align:center;transition:transform .2s,box-shadow .2s}
.gcard:hover{transform:translateY(-2px);box-shadow:0 6px 22px rgba(0,0,0,.07)}
.gval{font-family:'Playfair Display',serif;font-size:26px;font-weight:700;line-height:1;margin-bottom:4px}
.glbl{font-size:12px;color:var(--ink40)}

/* STATS STRIP */
.sstrip{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1px;background:var(--ink20);border:1px solid var(--ink20);border-radius:var(--r);overflow:hidden;margin-bottom:64px}
.scell{background:var(--white);padding:20px 24px;transition:background .15s}
.scell:hover{background:var(--ink10)}
.sval{font-family:'DM Mono',monospace;font-size:20px;font-weight:500;color:var(--blue);line-height:1;margin-bottom:4px}
.slab{font-size:11px;color:var(--ink40)}
.sdelta{font-size:11px;font-weight:600;margin-top:6px;display:inline-block;padding:2px 6px;border-radius:4px}
.dup{background:var(--green-bg);color:var(--green)}
.ddn{background:var(--red-bg);color:var(--red)}

/* CHARTS */
.c2{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px}
.c3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:24px;margin-bottom:24px}
.ccard{background:var(--white);border:1px solid var(--ink20);border-radius:var(--r);padding:28px}
.ccard-full{background:var(--white);border:1px solid var(--ink20);border-radius:var(--r);padding:32px;margin-bottom:24px}
.ctit{font-size:14px;font-weight:600;color:var(--ink);margin-bottom:3px}
.csub{font-size:12px;color:var(--ink40);margin-bottom:18px}
.cleg{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:14px}
.cleg-i{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink60)}
.cdot{width:10px;height:10px;border-radius:2px;flex-shrink:0}
.cwrap{position:relative;width:100%}
.h180{height:180px}.h220{height:220px}.h260{height:260px}.h300{height:300px}

/* SECTIONS */
.sec-block{background:var(--white);border:1px solid var(--ink20);border-radius:var(--r);padding:40px;margin-bottom:20px;transition:box-shadow .2s}
.sec-block:hover{box-shadow:0 4px 22px rgba(0,0,0,.06)}
.sec-hdr{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:22px;padding-bottom:18px;border-bottom:1px solid var(--ink20)}
.sec-hdr-l{display:flex;align-items:flex-start;gap:14px;flex:1}
.sec-ico{font-size:22px;margin-top:2px;flex-shrink:0}
.sec-num{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--ink40);display:block;margin-bottom:2px}
.sec-title{font-family:'Playfair Display',serif;font-size:21px;font-weight:700;color:var(--ink);letter-spacing:-.01em}
.sec-badge{padding:5px 12px;border-radius:6px;font-size:12px;font-weight:700;border:1px solid;white-space:nowrap;flex-shrink:0}
.abody{font-size:15px;line-height:1.85;color:var(--ink60)}
.abody p{margin-bottom:14px}
.abody strong{color:var(--ink);font-weight:600}
.abody ul{margin:10px 0 14px 20px}
.abody li{margin-bottom:6px}
.tbl-wrap{overflow-x:auto;margin:16px 0}
.tbl{width:100%;border-collapse:collapse;font-size:13px}
.tbl th,.tbl td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--ink20)}
.tbl th{background:var(--blue-bg);color:var(--blue);font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase}
.tbl tr:last-child td{border-bottom:none}
.tbl tr:hover td{background:var(--ink10)}

/* CONCLUSION */
.concl{background:var(--ink);border-radius:var(--r);padding:56px 64px;margin-bottom:64px;position:relative;overflow:hidden}
.concl::before{content:'"';position:absolute;top:-20px;left:44px;font-family:'Playfair Display',serif;font-size:240px;color:rgba(255,255,255,.04);line-height:1;pointer-events:none}
.clbl{font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#60A5FA;margin-bottom:22px;display:flex;align-items:center;gap:8px}
.clbl::before{content:'';display:block;width:24px;height:1px;background:#60A5FA}
.ctitle2{font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:#fff;line-height:1.2;margin-bottom:24px;letter-spacing:-.02em}
.cbody2{font-size:15px;color:#CBD5E1;line-height:1.85;max-width:720px}
.cbody2 p{margin-bottom:16px}
.vgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;border-top:1px solid rgba(255,255,255,.1);padding-top:36px;margin-top:36px}
.vlbl{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:8px}
.vval{font-size:15px;font-weight:600;color:#fff}
.tag{display:inline-block;padding:4px 12px;border-radius:4px;font-size:12px;font-weight:700;margin-top:8px;letter-spacing:.04em;text-transform:uppercase}
.tag-buy{background:rgba(16,185,129,.2);color:#34D399;border:1px solid rgba(16,185,129,.3)}
.tag-watch{background:rgba(251,191,36,.15);color:#FBBF24;border:1px solid rgba(251,191,36,.25)}
.tag-neutral{background:rgba(148,163,184,.15);color:#94A3B8;border:1px solid rgba(148,163,184,.2)}
.footer{border-top:1px solid var(--ink20);padding:28px 48px;max-width:1120px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--ink40)}

@media(max-width:900px){
  .kgrid{grid-template-columns:repeat(2,1fr)}
  .grow{grid-template-columns:repeat(2,1fr)}
  .c2,.c3{grid-template-columns:1fr}
  .cover{padding:36px 24px}
  .content{padding:40px 20px}
  .ctitle{font-size:42px}
  .snum{font-size:60px}
  .concl{padding:36px 28px}
  .vgrid{grid-template-columns:1fr 1fr}
  .sec-block{padding:24px}
  .sec-hdr{flex-direction:column}
  .sstrip{grid-template-columns:repeat(2,1fr)}
}
"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{_h.escape(empresa.title())} · {_h.escape(periodo)} · FinAnalyzer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>{CSS}</style>
</head>
<body>

<button class="print-btn no-print" onclick="window.print()">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>Salvar PDF
</button>

<!-- CAPA -->
<div class="cover">
  <div class="cgrad"></div>
  <div class="chdr">
    <div class="brand">
      <div class="bcube">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22" fill="none" stroke="rgba(255,255,255,.5)" stroke-width="1.5"/>
        </svg>
      </div>
      <div><span class="bname">FinAnalyzer</span><span class="bsub">Análise Fundamentalista por IA</span></div>
    </div>
    <div class="ppill">{_h.escape(periodo)} · Resultados Trimestrais</div>
  </div>

  <div class="cbody">
    <div class="ceyebrow">Relatório de Análise Fundamentalista</div>
    <h1 class="ctitle">{_h.escape(empresa.title())}<br><span>{_h.escape(periodo)}</span></h1>
    <p class="cdesc">Relatório completo gerado por IA com base no release de resultados oficial. Avaliação de receita, margens, endividamento e rentabilidade com visão estratégica.</p>
    <div class="srow">
      <div style="display:flex;align-items:baseline;gap:6px;">
        <span class="snum" style="color:{sc['hex']};" id="scoreNum">0.0</span>
        <span class="sdenom">/5</span>
      </div>
      <div>
        <div class="slbl">Score IA — Média Ponderada</div>
        <div class="sdesc" style="color:{sc['hex']};">{sc['label']}</div>
      </div>
    </div>
  </div>

  <div class="cfooter">
    <span>Gerado automaticamente · Dados do release oficial</span>
    <div class="bwarn">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      Não é recomendação de investimento
    </div>
  </div>
</div>

<!-- CONTENT -->
<div class="content">

  <!-- KPIs -->
  <div style="margin-bottom:40px;">
    <div class="slabel">Avaliação Fundamentalista</div>
    <div class="stitle">Notas por Pilar</div>
  </div>
  <div class="kgrid">{kpis}</div>

  <!-- GAUGES -->
  <div class="slabel" style="margin-bottom:16px;">Visualização Radial dos Pilares</div>
  <div class="grow" id="gaugeRow"></div>

  <!-- STATS STRIP -->
  <div class="sstrip" id="statsStrip"></div>

  <!-- CHARTS LABEL -->
  <div class="slabel" style="margin-bottom:8px;">Desempenho Trimestral</div>
  <div class="stitle">Evolução dos Indicadores</div>

  <!-- CHARTS 2-col -->
  <div class="c2 avoid-break" id="c2block">
    <div class="ccard">
      <div class="ctit">Receita vs Lucro</div>
      <div class="csub">Evolução trimestral extraída do release</div>
      <div class="cleg">
        <div class="cleg-i"><div class="cdot" style="background:#003087"></div>Receita</div>
        <div class="cleg-i"><div class="cdot" style="background:#0A6640"></div>Lucro</div>
      </div>
      <div class="cwrap h220"><canvas id="cRecLuc"></canvas></div>
    </div>
    <div class="ccard">
      <div class="ctit">Margens (%)</div>
      <div class="csub">Margem bruta e líquida ao longo dos trimestres</div>
      <div class="cleg">
        <div class="cleg-i"><div class="cdot" style="background:#7C3AED"></div>Bruta</div>
        <div class="cleg-i"><div class="cdot" style="background:#D97706"></div>Líquida</div>
      </div>
      <div class="cwrap h220"><canvas id="cMargens"></canvas></div>
    </div>
  </div>

  <!-- CHART FULL -->
  <div class="ccard-full avoid-break" id="cfullblock">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px;">
      <div>
        <div class="ctit" style="font-size:16px;">Receita Total — Evolução Histórica</div>
        <div class="csub">Barras agrupadas por trimestre</div>
      </div>
      <div class="cleg">
        <div class="cleg-i"><div class="cdot" style="background:#C7D7F5"></div>Receita</div>
        <div class="cleg-i"><div class="cdot" style="background:#003087"></div>Lucro</div>
      </div>
    </div>
    <div class="cwrap h260"><canvas id="cArea"></canvas></div>
  </div>

  <!-- CHARTS 3-col -->
  <div class="c3 avoid-break" id="c3block">
    <div class="ccard">
      <div class="ctit">Spread de Margens</div>
      <div class="csub">Diferença entre margem bruta e líquida</div>
      <div class="cwrap h180"><canvas id="cSpread"></canvas></div>
    </div>
    <div class="ccard">
      <div class="ctit">Radar dos Fundamentos</div>
      <div class="csub">Visão comparativa dos 4 pilares (escala 0–5)</div>
      <div class="cwrap h180"><canvas id="cRadar"></canvas></div>
    </div>
    <div class="ccard">
      <div class="ctit">Composição do Score</div>
      <div class="csub">Peso relativo de cada dimensão avaliada</div>
      <div class="cwrap h180"><canvas id="cDonut"></canvas></div>
    </div>
  </div>

  <div class="divider page-break"></div>

  <!-- ANÁLISE -->
  <div style="margin-bottom:40px;">
    <div class="slabel">Análise Completa por IA</div>
    <div class="stitle">Leitura dos Resultados</div>
  </div>
  {secs_html}

  <div class="divider page-break"></div>

  <!-- CONCLUSÃO -->
  <div class="concl avoid-break">
    <div class="clbl">Tese de Investimento</div>
    <h2 class="ctitle2">Conclusão Estratégica e Outlook</h2>
    <div class="cbody2">{tese_html}</div>
    <div class="vgrid">
      <div>
        <div class="vlbl">Score Final</div>
        <div class="vval">{g:.1f} / 5</div>
        <span class="tag {vc}">{vt}</span>
      </div>
      <div>
        <div class="vlbl">Empresa · Período</div>
        <div class="vval">{_h.escape(empresa.title())}</div>
        <div style="font-size:13px;color:#64748B;margin-top:4px;">{_h.escape(periodo)}</div>
      </div>
      <div>
        <div class="vlbl">Aviso Legal</div>
        <div class="vval" style="font-size:13px;line-height:1.5;color:#94A3B8;">Gerado por IA. Não constitui recomendação de investimento.</div>
      </div>
    </div>
  </div>

</div>

<div class="footer no-print">
  <span>Gerado pelo FinAnalyzer · Dados do release oficial · Não é recomendação de investimento</span>
  <span style="font-weight:600;color:var(--ink60);">{_h.escape(empresa.title())} · {_h.escape(periodo)}</span>
</div>

<script>
const CD={charts};
const NOTAS={{receita:{rn},lucro:{ln},divida:{dn},roe:{ren},geral:{g}}};

/* score counter */
(()=>{{
  const el=document.getElementById('scoreNum');
  const tgt=NOTAS.geral; let st=null;
  const step=ts=>{{
    if(!st)st=ts;
    const p=Math.min((ts-st)/900,1);
    const e=1-Math.pow(1-p,3);
    el.textContent=(tgt*e).toFixed(1);
    if(p<1)requestAnimationFrame(step);
    else el.textContent=tgt.toFixed(1);
  }};
  setTimeout(()=>requestAnimationFrame(step),400);
}})();

/* gauges */
(()=>{{
  const pillars=[
    {{l:'Receita',v:NOTAS.receita,c:'#003087'}},
    {{l:'Margem', v:NOTAS.lucro,  c:'#0A6640'}},
    {{l:'Dívida', v:NOTAS.divida, c:'#DC2626'}},
    {{l:'ROE',    v:NOTAS.roe,    c:'#D97706'}},
  ];
  const row=document.getElementById('gaugeRow');
  const R=44,cx=52,cy=52,circ=2*Math.PI*R;
  pillars.forEach(p=>{{
    const dash=(p.v/5*circ).toFixed(2);
    const gap=(circ-p.v/5*circ).toFixed(2);
    const off=(circ*.25).toFixed(2);
    const div=document.createElement('div');
    div.className='gcard fade-in';
    div.innerHTML=`<svg style="display:block;margin:0 auto 12px" width="104" height="104" viewBox="0 0 104 104">
      <circle cx="52" cy="52" r="44" fill="none" stroke="#E2E8F0" stroke-width="9"/>
      <circle cx="52" cy="52" r="44" fill="none" stroke="${{p.c}}" stroke-width="9"
        stroke-dasharray="${{dash}} ${{gap}}" stroke-dashoffset="${{off}}"
        stroke-linecap="round" style="transition:stroke-dasharray 1.2s cubic-bezier(.4,0,.2,1);"/>
      <text x="52" y="48" text-anchor="middle" dominant-baseline="middle"
        style="font-family:'Playfair Display',serif;font-size:22px;font-weight:700;fill:${{p.c}}">${{p.v.toFixed(1)}}</text>
      <text x="52" y="65" text-anchor="middle"
        style="font-family:'DM Sans',sans-serif;font-size:11px;fill:#94A3B8;">/5</text>
    </svg>
    <div class="gval" style="color:${{p.c}}">${{p.v.toFixed(1)}}</div>
    <div class="glbl">${{p.l}}</div>`;
    row.appendChild(div);
  }});
}})();

/* stats strip */
(()=>{{
  const strip=document.getElementById('statsStrip');
  if(!CD.length){{strip.style.display='none';return;}}
  const last=CD[CD.length-1];
  const prev=CD.length>1?CD[CD.length-2]:null;
  const delta=(a,b)=>{{
    if(b==null||b===0)return'';
    const d=((a-b)/Math.abs(b)*100).toFixed(1);
    return`<span class="sdelta ${{d>=0?'dup':'ddn'}}">${{d>=0?'▲':'▼'}} ${{Math.abs(d)}}%</span>`;
  }};
  [
    {{v:last.receita,     l:'Receita (último tri)',d:delta(last.receita,prev?.receita)}},
    {{v:last.lucro,       l:'Lucro (último tri)', d:delta(last.lucro,prev?.lucro)}},
    {{v:last.margemBruta, l:'Margem Bruta (%)',   d:delta(last.margemBruta,prev?.margemBruta)}},
    {{v:last.margemLiquida,l:'Margem Líquida (%)',d:delta(last.margemLiquida,prev?.margemLiquida)}},
    {{v:NOTAS.geral,      l:'Score IA Final',     d:''}},
  ].forEach(it=>{{
    const c=document.createElement('div');
    c.className='scell';
    const suf=it.l.includes('%')?'%':'';
    c.innerHTML=`<div class="sval">${{it.v!=null?it.v+suf:'—'}}</div><div class="slab">${{it.l}}</div>${{it.d}}`;
    strip.appendChild(c);
  }});
}})();

/* charts */
(()=>{{
  if(!CD.length){{
    ['c2block','cfullblock','c3block'].forEach(id=>{{const e=document.getElementById(id);if(e)e.style.display='none';}});
    return;
  }}
  const labels=CD.map(d=>d.name||'');
  const rec=CD.map(d=>d.receita||0);
  const luc=CD.map(d=>d.lucro||0);
  const mB=CD.map(d=>d.margemBruta||0);
  const mL=CD.map(d=>d.margemLiquida||0);
  const xA={{grid:{{display:false}},ticks:{{color:'#94A3B8',font:{{size:11}}}},border:{{display:false}}}};
  const yA={{grid:{{color:'#F1F5F9'}},border:{{display:false}},ticks:{{color:'#94A3B8',font:{{size:11}}}}}};
  const tt={{backgroundColor:'#0F172A',titleColor:'#fff',bodyColor:'#CBD5E1',borderColor:'#334155',borderWidth:1,cornerRadius:8,padding:10}};
  const base={{responsive:true,maintainAspectRatio:false,animation:{{duration:900,easing:'easeOutQuart'}},plugins:{{legend:{{display:false}}}}}};

  new Chart(document.getElementById('cRecLuc'),{{type:'bar',
    data:{{labels,datasets:[
      {{label:'Receita',data:rec,backgroundColor:'#C7D7F5',borderRadius:5,maxBarThickness:36}},
      {{label:'Lucro',  data:luc,backgroundColor:'#0A6640',borderRadius:5,maxBarThickness:36}},
    ]}},
    options:{{...base,scales:{{x:xA,y:yA}},plugins:{{...base.plugins,tooltip:{{...tt}}}}}}}});

  new Chart(document.getElementById('cMargens'),{{type:'line',
    data:{{labels,datasets:[
      {{label:'Margem Bruta',   data:mB,borderColor:'#7C3AED',backgroundColor:'rgba(124,58,237,.08)',fill:true,borderWidth:2.5,pointBackgroundColor:'#7C3AED',pointRadius:4,tension:.35}},
      {{label:'Margem Líquida', data:mL,borderColor:'#D97706',backgroundColor:'transparent',borderWidth:2,borderDash:[5,3],pointBackgroundColor:'#D97706',pointRadius:4,tension:.35}},
    ]}},
    options:{{...base,scales:{{x:xA,y:{{...yA,ticks:{{...yA.ticks,callback:v=>v+'%'}}}}}},plugins:{{...base.plugins,tooltip:{{...tt}}}}}}}});

  new Chart(document.getElementById('cArea'),{{type:'bar',
    data:{{labels,datasets:[
      {{label:'Receita',data:rec,backgroundColor:'rgba(0,48,135,.15)',borderColor:'#003087',borderWidth:2,borderRadius:4,maxBarThickness:48}},
      {{label:'Lucro',  data:luc,backgroundColor:'rgba(10,102,64,.75)',borderRadius:4,maxBarThickness:48}},
    ]}},
    options:{{...base,scales:{{x:xA,y:yA}},plugins:{{...base.plugins,tooltip:{{...tt}}}}}}}});

  const spread=mB.map((b,i)=>parseFloat((b-mL[i]).toFixed(2)));
  new Chart(document.getElementById('cSpread'),{{type:'bar',
    data:{{labels,datasets:[{{label:'Spread',data:spread,
      backgroundColor:spread.map(v=>v>=0?'rgba(0,48,135,.7)':'rgba(220,38,38,.6)'),
      borderRadius:4,maxBarThickness:32
    }}]}},
    options:{{...base,scales:{{x:xA,y:{{...yA,ticks:{{...yA.ticks,callback:v=>v+'%'}}}}}},plugins:{{...base.plugins,tooltip:{{...tt,callbacks:{{label:c=>`Spread: ${{c.raw}}%`}}}}}}}}}});

  new Chart(document.getElementById('cRadar'),{{type:'radar',
    data:{{labels:['Receita','Margem','Dívida','ROE'],datasets:[{{
      data:[NOTAS.receita,NOTAS.lucro,NOTAS.divida,NOTAS.roe],
      backgroundColor:'rgba(0,48,135,.1)',borderColor:'#003087',
      pointBackgroundColor:'#003087',pointRadius:4,borderWidth:2,
    }}]}},
    options:{{responsive:true,maintainAspectRatio:false,animation:{{duration:900}},
      plugins:{{legend:{{display:false}},tooltip:{{...tt}}}},
      scales:{{r:{{min:0,max:5,ticks:{{stepSize:1,color:'#94A3B8',font:{{size:10}},backdropColor:'transparent'}},
        grid:{{color:'#E2E8F0'}},
        pointLabels:{{color:'#475569',font:{{size:11,weight:'500'}}}}
      }}}}
    }}}});

  const dcols=['#003087','#0A6640','#DC2626','#D97706'];
  new Chart(document.getElementById('cDonut'),{{type:'doughnut',
    data:{{labels:['Receita','Margem','Dívida','ROE'],datasets:[{{
      data:[NOTAS.receita,NOTAS.lucro,NOTAS.divida,NOTAS.roe],
      backgroundColor:dcols.map(c=>c+'CC'),borderColor:dcols,borderWidth:2,hoverOffset:6,
    }}]}},
    options:{{responsive:true,maintainAspectRatio:false,cutout:'68%',
      animation:{{duration:900,animateRotate:true}},
      plugins:{{legend:{{display:false}},tooltip:{{...tt,callbacks:{{label:c=>`${{c.label}}: ${{c.raw.toFixed(1)}}/5`}}}}}}
    }}}});
}})();

/* intersection observer for fade-in */
const io=new IntersectionObserver(entries=>entries.forEach(e=>{{if(e.isIntersecting)e.target.style.animationPlayState='running';}}),{{threshold:0.08}});
document.querySelectorAll('.fade-in').forEach(el=>{{el.style.animationPlayState='paused';io.observe(el);}});
</script>
</body>
</html>""".replace("{charts}", cj).replace("{rn}", str(rn)).replace("{ln}", str(ln)).replace("{dn}", str(dn)).replace("{ren}", str(ren)).replace("{g}", str(g))


# ─────────── endpoint ───────────

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