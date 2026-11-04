"""Quarterly score parsing and validation, independent of storage and API startup."""
import json
import re
from fastapi import HTTPException

def quarterly_thesis(text):
    prefix = r"^[ \t]*(?:#{1,6}[ \t]*)?\*{0,2}"
    section = r"(?:Se[cç][aã]o|Section)[ \t]*"
    match = re.search(
        rf"{prefix}{section}5[ \t]*[:–-][^\n]*\n(.*?)(?={prefix}{section}[67]\b|{prefix}(?:Nota\s+Geral|Overall\s+Score)\b|^```|\Z)",
        text or "", re.DOTALL | re.IGNORECASE | re.MULTILINE,
    )
    if match and match[1].strip():
        return match[1].strip()
    prose = re.sub(r"```[\s\S]*?```", "", text or "").strip()
    intro = re.split(rf"{prefix}{section}1\b", prose, maxsplit=1, flags=re.IGNORECASE | re.MULTILINE)[0].strip()
    return intro or prose


def parse_results(text):
    def get_note(pattern, txt):
        match = re.search(pattern, re.sub(r'\*\*|__', '', txt or ''), re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except:
                return 0.0
        return 0.0

    def get_chart_data(txt):
        try:
            m = re.search(r"```json\s*([\s\S]*?)\s*```", txt or "", re.IGNORECASE)
            if not m: return []
            raw = json.loads(m.group(1))
            if not isinstance(raw, list): return []
            cleaned = []
            for item in raw:
                if not isinstance(item, dict): continue
                def to_float(v, default=0.0):
                    try:
                        s = str(v).strip()
                        if not s or s.lower() == 'null' or s.lower() == 'none': return default
                        return float(s.replace(',', '.'))
                    except: return default
                
                receita = to_float(item.get("receita"))
                if receita == 0: continue
                
                cleaned.append({
                    "name": item.get("name") or item.get("periodo") or item.get("label") or "",
                    "receita": receita,
                    "lucro": to_float(item.get("lucro")),
                    "divida": to_float(item.get("divida")),
                    "ebitda": to_float(item.get("ebitda")),
                    "margemBruta": to_float(item.get("margemBruta")),
                    "margemLiquida": to_float(item.get("margemLiquida")),
                    "segmentos": item.get("segmentos", []),
                    "composicao_receita": item.get("composicao_receita", {}), 
                    "despesas_var": item.get("despesas_var", [])
                })
            return cleaned
        except: return []

    return {
        "receita_nota": get_note(r'(?:Nota Seção 1|Section Score 1):\s*([1-5])\s*/\s*5', text),
        "rentabilidade_nota": get_note(r'(?:Nota Seção 2|Section Score 2):\s*([1-5])\s*/\s*5', text),
        "divida_nota": get_note(r'(?:Nota Seção 3|Section Score 3):\s*([1-5])\s*/\s*5', text),
        "lucro_nota": get_note(r'(?:Nota Seção 4|Section Score 4):\s*([1-5])\s*/\s*5', text),
        "nota_geral": get_note(r'(?:Nota Geral|Overall Score):\s*([1-5])\s*/\s*5', text),
        "tese_investimento": quarterly_thesis(text),
        "chart_data": get_chart_data(text),
        "unrated_fundamentals": [key for i, key in enumerate(("receita_nota", "rentabilidade_nota", "divida_nota", "lucro_nota"), 1)
                                if re.search(rf'(?:Nota Seção {i}|Section Score {i}):\s*(?:N/A|Not rateable|Dados insuficientes)\b',
                                             re.sub(r'\*\*|__', '', text or ''), re.I)],
        "overall_unrated": bool(re.search(r'(?:Nota Geral|Overall Score):\s*(?:N/A|Not rateable|Dados insuficientes)\b', re.sub(r'\*\*|__', '', text or ''), re.I)),
    }


def validate_quarterly_result(data, locale):
    fields = ("receita_nota", "rentabilidade_nota", "divida_nota", "lucro_nota")
    valid = [key for key in fields if isinstance(data.get(key), (int, float)) and 1 <= data[key] <= 5]
    missing = [key for key in fields if key not in valid]
    if (len(valid) < 3 or any(key not in data.get('unrated_fundamentals', []) for key in missing)
            or not data.get('nota_geral') or not 1 <= data['nota_geral'] <= 5 or not data.get('tese_investimento', '').strip()):
        import logging
        logging.getLogger('uvicorn.error').warning('quarterly_validation stage=scores outcome=rejected missing=%s', ','.join(key for key in fields if key not in valid))
        insufficient = data.get('overall_unrated') or len(data.get('unrated_fundamentals', [])) > 1
        if insufficient:
            message = ("The verified release does not support enough categories for an overall assessment. No analysis was saved or charged. You can upload a fuller official document."
                       if locale == "en" else "O release validado não permite avaliar categorias suficientes para uma conclusão geral. Nenhuma análise foi salva ou cobrada. Você pode enviar um documento oficial mais completo.")
        else:
            message = ("The analysis returned an invalid score format. No analysis was saved or charged. Please try again."
                       if locale == "en" else "A análise retornou notas em um formato inválido. Nenhuma análise foi salva ou cobrada. Tente novamente.")
        raise HTTPException(422, message, headers={'X-Analysis-Stage':'scores','X-Error-Code':'analysis_incomplete' if insufficient else 'score_format_invalid'})
    for key in fields:
        if key not in valid:
            data[key] = None
    data['rated_fundamentals'] = len(valid)

