"""Earnings releases filed with CVM (IPE dataset): an official source for every B3-listed issuer."""
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

BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS"
logger = logging.getLogger("uvicorn.error")
RELEASE = re.compile(r"press[- ]?release|release de resultado|release|divulga.{0,6} de resultado|resultados? d[oe] \d|earnings", re.I)
NOT_RELEASE = re.compile(r"convite|teleconfer|webcast|calend|transcri|agenda|aviso aos|data de divulga", re.I)


def _archive(year):
    cache = Path(tempfile.gettempdir()) / "finanalyser-cvm-ipe"
    cache.mkdir(exist_ok=True)
    target = cache / f"ipe-{year}.zip"
    # The IPE file is republished daily; six hours keeps new releases visible without re-downloading per lookup.
    if not target.exists() or time.time() - target.stat().st_mtime > 6 * 3600:
        with requests.get(f"{BASE}/ipe_cia_aberta_{year}.zip", timeout=(4, 40), stream=True, allow_redirects=False) as response:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("CVM IPE archive unavailable")
            with tempfile.NamedTemporaryFile(dir=cache, suffix=".part", delete=False) as handle:
                pending, size = Path(handle.name), 0
                try:
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 80_000_000:
                            raise ValueError("CVM IPE archive exceeds limit")
                        handle.write(chunk)
                except Exception:
                    handle.close()
                    pending.unlink(missing_ok=True)
                    raise
        pending.replace(target)
    return zipfile.ZipFile(target)


def _rows(year):
    with _archive(year) as zipped:
        name = next((n for n in zipped.namelist() if n.lower().endswith(".csv")), None)
        if not name or zipped.getinfo(name).file_size > 400_000_000:
            raise ValueError("CVM IPE member unavailable")
        with zipped.open(name) as stream:
            yield from csv.DictReader(io.TextIOWrapper(stream, encoding="latin-1"), delimiter=";")


def release_candidates(cvm_code, cnpj, year, quarter, period_matches):
    """Return the issuer's CVM-filed release links for the quarter, most specific first."""
    code = int(cvm_code) if str(cvm_code or "").strip().isdigit() else None
    digits = re.sub(r"\D", "", str(cnpj or ""))
    if not code and len(digits) != 14:
        return []
    quarter_end = date(year, quarter * 3, 30 if quarter in (2, 3) else 31)
    window = (quarter_end + timedelta(days=5), quarter_end + timedelta(days=150))
    found = []
    for archive_year in sorted({window[0].year, window[1].year}):
        try:
            found.extend(_matches(_rows(archive_year), code, digits, window, year, quarter, period_matches))
        except (requests.RequestException, ValueError, OSError, zipfile.BadZipFile, csv.Error) as exc:
            logger.info("cvm_ipe_lookup year=%s outcome=unavailable reason=%s", archive_year, type(exc).__name__)
    # Releases naming the quarter first, then press-release filings, earliest delivery first (later ones are often re-filings).
    return [item for _, item in sorted(found, key=lambda pair: pair[0])]


def _matches(rows, code, digits, window, year, quarter, period_matches):
    # Streams the year's filings (hundreds of thousands of rows) without holding them in memory.
    for row in rows:
        row_code = (row.get("Codigo_CVM") or "").strip()
        if not ((code and row_code.isdigit() and int(row_code) == code)
                or (len(digits) == 14 and re.sub(r"\D", "", row.get("CNPJ_Companhia") or "") == digits)):
            continue
        label = " ".join(row.get(k) or "" for k in ("Categoria", "Tipo", "Especie", "Assunto"))
        delivered = (row.get("Data_Entrega") or "")[:10]
        if not RELEASE.search(label) or NOT_RELEASE.search(row.get("Assunto") or "") or not (window[0].isoformat() <= delivered <= window[1].isoformat()):
            continue
        url = (row.get("Link_Download") or "").strip()
        if url.startswith("https://www.rad.cvm.gov.br/") or url.startswith("http://www.rad.cvm.gov.br/"):
            rank = (0 if period_matches(row.get("Assunto") or "", year, quarter) else 1,
                    0 if re.search(r"press", row.get("Tipo") or "", re.I) else 1, delivered)
            yield rank, {"title": (row.get("Assunto") or row.get("Tipo") or "").strip(), "url": url.replace("http://", "https://", 1)}
