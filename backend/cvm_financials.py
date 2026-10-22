"""Consolidated CVM annual statements, filtered by issuer, filing date and version."""
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import io
import logging
from pathlib import Path
import re
import tempfile
import unicodedata
import zipfile

import requests

from agents.auto_fetcher import AutoFetcher
from company_financials import _format

BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA"
# B3 issuer 9512: distinguish the listed parent from other Petrobras-named entities.
ISSUER_CNPJS = {"PETR3": "33.000.167/0001-01", "PETR4": "33.000.167/0001-01"}
logger = logging.getLogger("uvicorn.error")
ACCOUNTS = {"DRE": {"3.01": "Revenue", "3.03": "Gross profit", "3.05": "Operating income",
                    "3.11": "Net income", "3.11.01": "Net income attributable to parent",
                    "3.99.02.01": "Diluted EPS"},
            "BPA": {"1.01.01": "Cash and cash equivalents"},
            "BPP": {"2.01.04": "Current long-term debt", "2.02.01": "Noncurrent long-term debt", "2.03": "Book equity"},
            "DFC_MI": {"6.01": "Operating cash flow"}}


def normalized(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().upper()


@lru_cache(maxsize=32)
def issuer_cnpj(company):
    fetcher = AutoFetcher()
    ticker = fetcher.resolve_ticker(company)
    aliases = fetcher.transcript_issuers.get(ticker, ()) if re.fullmatch(r"[A-Z]{4}\d{1,2}", ticker) else ()
    expected_cnpj = ISSUER_CNPJS.get(ticker)
    if not aliases and not expected_cnpj:
        return None
    response = requests.get(BASE + "/CAD/DADOS/cad_cia_aberta.csv", timeout=10, allow_redirects=False)
    response.raise_for_status()
    if response.status_code != 200 or len(response.content) > 5_000_000:
        return None
    text = response.content.decode("utf-8-sig", errors="replace")
    if expected_cnpj:
        return next((row["CNPJ_CIA"] for row in csv.DictReader(io.StringIO(text), delimiter=";")
                     if row.get("SIT") == "ATIVO" and row.get("CNPJ_CIA") == expected_cnpj), None)
    matches = [row for row in csv.DictReader(io.StringIO(text), delimiter=";")
               if row.get("SIT") == "ATIVO" and any(re.search(r"\b" + re.escape(normalized(a)) + r"\b",
                  normalized(row.get("DENOM_SOCIAL", ""))) for a in aliases if len(a) >= 4)]
    return matches[0]["CNPJ_CIA"] if len(matches) == 1 else None


def archive(year):
    cache = Path(tempfile.gettempdir()) / "finanalyzer-cvm"
    cache.mkdir(exist_ok=True)
    target = cache / f"dfp-{year}-{date.today().isoformat()}.zip"
    if not target.exists():
        url = f"{BASE}/DOC/DFP/DADOS/dfp_cia_aberta_{year}.zip"
        with requests.get(url, timeout=(4, 35), stream=True, allow_redirects=False) as response:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("CVM archive unavailable")
            with tempfile.NamedTemporaryFile(dir=cache, suffix=".part", delete=False) as handle:
                pending = Path(handle.name)
                try:
                    size = 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 48_000_000:
                            raise ValueError("CVM archive exceeds limit")
                        handle.write(chunk)
                except Exception:
                    handle.close()
                    pending.unlink(missing_ok=True)
                    raise
        pending.replace(target)
    return zipfile.ZipFile(target)


def rows(zipped, name):
    info = zipped.getinfo(name)
    if info.file_size > 250_000_000:
        raise ValueError("CVM member exceeds limit")
    with zipped.open(name) as stream:
        yield from csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace"), delimiter=";")


def parse_archive(zipped, year, cnpj, as_of, share_class="ON"):
    filings = {}
    for row in rows(zipped, f"dfp_cia_aberta_{year}.csv"):
        if row.get("CNPJ_CIA") != cnpj or row.get("DT_RECEB", "9999") > as_of:
            continue
        key = row["DT_REFER"], row["VERSAO"]
        filings[key] = row["DT_RECEB"]
    periods, capex = {}, {}
    for statement, codes in ACCOUNTS.items():
        name = f"dfp_cia_aberta_{statement}_con_{year}.csv"
        if name not in zipped.namelist():
            continue
        for row in rows(zipped, name):
            key = row.get("DT_REFER"), row.get("VERSAO")
            if row.get("CNPJ_CIA") != cnpj or key not in filings or row.get("MOEDA") != "REAL":
                continue
            end = row.get("DT_FIM_EXERC", "")
            if not end or end > as_of:
                continue
            if statement in ("DRE", "DFC_MI"):
                try:
                    if not 300 <= (date.fromisoformat(end) - date.fromisoformat(row["DT_INI_EXERC"])).days <= 380:
                        continue
                except (KeyError, ValueError):
                    continue
            code = row.get("CD_CONTA", "")
            label = codes.get(code)
            desc = normalized(row.get("DS_CONTA", ""))
            if statement == "DRE" and code.startswith("3.99.02."):
                label = "Diluted EPS" if desc == share_class else None
            is_capex = statement == "DFC_MI" and code.startswith("6.02.") and re.search(r"AQUISI|COMPRA|ADIC", desc) and re.search(r"IMOBILIZ|INTANG", desc)
            if not label and not is_capex:
                continue
            try:
                value = Decimal(row["VL_CONTA"])
            except (InvalidOperation, KeyError):
                continue
            if not value.is_finite() or row.get("ESCALA_MOEDA") not in ("MIL", "UNIDADE"):
                continue
            # CVM EPS cells are per share even when monetary statements use thousands.
            scale = 1 if label == "Diluted EPS" or row["ESCALA_MOEDA"] == "UNIDADE" else 1000
            value = float(value * scale)
            stamp = filings[key], int(row["VERSAO"]), row["DT_REFER"]
            bucket = periods.setdefault(end, {})
            if label and (label not in bucket or stamp > bucket[label][0]):
                bucket[label] = stamp, value
            elif is_capex:
                capex.setdefault((end, stamp), {})[code] = abs(value)
    for (end, stamp), entries in capex.items():
        total = sum(v for code, v in entries.items() if not any(other.startswith(code + ".") for other in entries))
        if "Capital expenditures" not in periods[end] or stamp > periods[end]["Capital expenditures"][0]:
            periods[end]["Capital expenditures"] = stamp, total
    return periods


def get_cvm_company_source(company, as_of):
    try:
        cnpj = issuer_cnpj(company)
        if not cnpj:
            return None
        cutoff = date.fromisoformat(as_of)
        latest = cutoff.year - 1
        combined = {}
        for year in range(latest, latest - 5, -1):
            with archive(year) as zipped:
                ticker = AutoFetcher().resolve_ticker(company)
                share_class = "ON" if ticker.endswith("3") else "PN" if ticker.endswith("4") else None
                incoming = parse_archive(zipped, year, cnpj, as_of, share_class)
            for period, values in incoming.items():
                bucket = combined.setdefault(period, {})
                for label, item in values.items():
                    if label not in bucket or item[0] > bucket[label][0]:
                        bucket[label] = item
        history, lines = [], [f"CVM consolidated annual statements for {company}; CNPJ {cnpj}. Currency BRL; full units, EPS per {share_class or 'verified'} share class."]
        for period, cells in sorted(combined.items(), reverse=True):
            values = {label: item[1] for label, item in cells.items()}
            if "Revenue" not in values or "Net income" not in values:
                continue
            if all(k in values for k in ("Operating cash flow", "Capital expenditures")):
                values["Free cash flow (calculated)"] = values["Operating cash flow"] - values["Capital expenditures"]
            for label, numerator in (("Operating margin (calculated)", "Operating income"), ("Gross margin (calculated)", "Gross profit")):
                if values["Revenue"] > 0 and numerator in values:
                    values[label] = values[numerator] / values["Revenue"] * 100
            history.append({"period": period, "currency": "BRL", "values": values,
                            "filed": max(item[0][0] for item in cells.values()),
                            "provenance": {label: {"filing_date": item[0][0], "version": item[0][1],
                                "url": f"{BASE}/DOC/DFP/DADOS/dfp_cia_aberta_{item[0][2][:4]}.zip"} for label, item in cells.items()},
                            "value_units": {k: "percent" for k in values if "margin" in k}})
            for label, value in values.items():
                unit = "percent" if "margin" in label else "BRL/shares" if label == "Diluted EPS" else "BRL"
                lines.append(f"For the full year ended {period}, {label} {unit} {_format(value)}.")
            if "Diluted EPS" in values:
                lines.append(f"For the full year ended {period}, diluted earnings per share BRL/shares {_format(values['Diluted EPS'])}.")
            if len(history) == 5:
                break
        if not history:
            return None
        return {"id": "F1", "title": f"CVM — {company} consolidated annual financials", "basis": "primary", "document_type": "financials",
                "url": f"{BASE}/DOC/DFP/DADOS/", "text": "\n".join(lines), "annual_financials": history}
    except (requests.RequestException, ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as exc:
        logger.warning("company_cvm_unavailable company=%s error_type=%s", company, type(exc).__name__)
        return None
