"""Quarterly statements filed with CVM (ITR open data), for issuers that publish no earnings release."""
import csv
from datetime import date, timedelta
import io
import logging
from pathlib import Path
import re
import tempfile
import time
import zipfile

import requests

BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS"
logger = logging.getLogger("uvicorn.error")
STATEMENTS = (("DRE", "Demonstração do resultado"), ("BPA", "Balanço patrimonial: ativo"),
              ("BPP", "Balanço patrimonial: passivo e patrimônio líquido"), ("DFC_MI", "Fluxo de caixa (acumulado no ano)"),
              ("DFC_MD", "Fluxo de caixa (acumulado no ano)"))


def _archive(year):
    cache = Path(tempfile.gettempdir()) / "finanalyser-cvm-itr"
    cache.mkdir(exist_ok=True)
    target = cache / f"itr-{year}.zip"
    if not target.exists() or time.time() - target.stat().st_mtime > 12 * 3600:
        with requests.get(f"{BASE}/itr_cia_aberta_{year}.zip", timeout=(4, 60), stream=True, allow_redirects=False) as response:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("CVM ITR archive unavailable")
            with tempfile.NamedTemporaryFile(dir=cache, suffix=".part", delete=False) as handle:
                pending, size = Path(handle.name), 0
                try:
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 150_000_000:
                            raise ValueError("CVM ITR archive exceeds limit")
                        handle.write(chunk)
                except Exception:
                    handle.close()
                    pending.unlink(missing_ok=True)
                    raise
        pending.replace(target)
    return zipfile.ZipFile(target)


def _rows(zipped, name):
    if name not in zipped.namelist() or zipped.getinfo(name).file_size > 600_000_000:
        return
    with zipped.open(name) as stream:
        yield from csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace"), delimiter=";")


def _number(row):
    try:
        value = float(row["VL_CONTA"])
    except (KeyError, ValueError):
        return None
    return value * (1000 if row.get("ESCALA_MOEDA") == "MIL" else 1)


def _money(value):
    return f"{value / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def quarterly_statements(cnpj, quarter_end, label, cvm_code=None):
    """Return (link, text) for the issuer's latest ITR version of the quarter, or None."""
    digits = re.sub(r"\D", "", str(cnpj or ""))
    code = int(cvm_code) if str(cvm_code or "").strip().isdigit() else None
    if (len(digits) != 14 and not code) or quarter_end.month == 12:
        return None  # The fourth quarter is reported in the annual DFP, not in an ITR.
    quarter_start = date(quarter_end.year, quarter_end.month - 2, 1)
    year_ago = (quarter_start.replace(year=quarter_start.year - 1), quarter_end.replace(year=quarter_end.year - 1))
    with _archive(quarter_end.year) as zipped:
        # B3's catalogue may omit the CNPJ, so the CVM code identifies the issuer as well.
        filings = [row for row in _rows(zipped, f"itr_cia_aberta_{quarter_end.year}.csv")
                   if row.get("DT_REFER") == quarter_end.isoformat()
                   and ((len(digits) == 14 and re.sub(r"\D", "", row.get("CNPJ_CIA") or "") == digits)
                        or (code and (row.get("CD_CVM") or "").strip().isdigit() and int(row["CD_CVM"]) == code))]
        if not filings:
            return None
        filing = max(filings, key=lambda row: int(row.get("VERSAO") or 0))
        digits = re.sub(r"\D", "", filing.get("CNPJ_CIA") or "")
        link = (filing.get("LINK_DOC") or "").replace("http://", "https://", 1)
        if not link.startswith("https://www.rad.cvm.gov.br/"):
            return None
        sections = []
        for statement, title in STATEMENTS:
            for scope in ("con", "ind"):  # holdings such as Bradespar may file only individual statements
                lines = {}
                for row in _rows(zipped, f"itr_cia_aberta_{statement}_{scope}_{quarter_end.year}.csv"):
                    if (re.sub(r"\D", "", row.get("CNPJ_CIA") or "") != digits or row.get("VERSAO") != filing.get("VERSAO")
                            or row.get("DT_REFER") != quarter_end.isoformat() or row.get("CD_CONTA", "").count(".") > 2):
                        continue
                    start, end = row.get("DT_INI_EXERC", ""), row.get("DT_FIM_EXERC", "")
                    if statement == "DRE":
                        column = 0 if (start, end) == (quarter_start.isoformat(), quarter_end.isoformat()) else \
                                 1 if (start, end) == tuple(d.isoformat() for d in year_ago) else None
                    else:
                        column = 0 if (row.get("ORDEM_EXERC") or "").upper().startswith("ÚLTIMO") or (row.get("ORDEM_EXERC") or "").upper().startswith("ULTIMO") else 1
                    value = _number(row)
                    if column is None or value is None:
                        continue
                    entry = lines.setdefault(row["CD_CONTA"], [row.get("DS_CONTA", "").strip(), None, None])
                    entry[1 + column] = value
                if lines:
                    head = f"{label} | {'mesmo trimestre do ano anterior' if statement == 'DRE' else 'período comparativo'}"
                    body = [f"{code} {name} | {_money(a) if a is not None else '-'} | {_money(b) if b is not None else '-'}"
                            for code, (name, a, b) in sorted(lines.items(), key=lambda item: [int(p) for p in item[0].split('.') if p.isdigit()])]
                    sections.append(f"{title} ({'consolidado' if scope == 'con' else 'individual'}, R$ milhões) | {head}\n" + "\n".join(body))
                    break
            if statement == "DFC_MI" and sections and sections[-1].startswith("Fluxo"):
                break
        if not sections:
            return None
        header = (f"{filing.get('DENOM_CIA', '').strip()} — Informações Trimestrais (ITR) {label}, "
                  f"período encerrado em {quarter_end.strftime('%d/%m/%Y')}, versão {filing.get('VERSAO')}, "
                  f"entregue à CVM em {filing.get('DT_RECEB', '')}. Fonte: dados abertos da CVM.")
        return link, header + "\n\n" + "\n\n".join(sections)
