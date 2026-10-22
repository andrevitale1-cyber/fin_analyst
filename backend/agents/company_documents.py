"""Bounded document hydration from verified issuer/SEC hosts; never fetch arbitrary model URLs."""
import json
import re
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

from agents.auto_fetcher import AutoFetcher
from openai_client import OpenAIClient, OpenAIError
from sector_research import is_petrobras


class FilingText(HTMLParser):
    """SEC annual HTML can exceed 9 MB; extract text without building a large DOM tree."""
    ignored_tags = {"script", "style", "nav", "footer", "aside", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignored = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.ignored_tags:
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in self.ignored_tags:
            self.ignored = max(0, self.ignored - 1)

    def handle_data(self, data):
        if not self.ignored and data.strip():
            self.parts.append(data.strip())


def filing_text(data):
    parser = FilingText()
    parser.feed(data.decode("utf-8", errors="replace"))
    parser.close()
    return "\n".join(parser.parts)


def collect_petrobras_filings(as_of):
    """Discover actual SEC primary filenames; never guess a translated release URL."""
    try:
        response = requests.get("https://data.sec.gov/submissions/CIK0001119639.json",
                                headers={"User-Agent": "FinAnalyzer contact@finanalyser.com.br"},
                                timeout=12, allow_redirects=False)
        response.raise_for_status()
        recent = response.json()["filings"]["recent"]
        selected, groups = [], set()
        for index, name in enumerate(recent["primaryDocument"]):
            if recent["filingDate"][index] > as_of:
                continue
            form, lower = recent["form"][index], name.lower()
            group = ("annual" if form == "20-F" else
                     "annual-brl" if re.search(r"pbrfs4q\d{2}rs", lower) else
                     "interim-brl" if re.search(r"pbrfs[1-3]q\d{2}rs", lower) else
                     "annual-performance" if re.search(r"pbrrmf4q\d{2}usd", lower) else
                     "interim-performance" if re.search(r"pbrrmf[1-3]q\d{2}usd", lower) else None)
            if group is None or group in groups or form not in ("20-F", "6-K", "6-K/A"):
                continue
            accession = recent["accessionNumber"][index].replace("-", "")
            if not re.fullmatch(r"\d{18}", accession) or not re.fullmatch(r"[A-Za-z0-9_.-]+\.htm", name):
                continue
            selected.append({"id": "IRSEC" + accession, "title": f"Petrobras {group} {recent['filingDate'][index]}",
                "url": f"https://www.sec.gov/Archives/edgar/data/1119639/{accession}/{name}",
                "basis": "web_research", "text": "", "document_type": "filing"})
            groups.add(group)
        return selected
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
        return []


def collect_petrobras_market_sources():
    """Read dated PETR4 observations from the exact BRL listing, without another model search."""
    sources = []
    for page in ("history", "forecast"):
        url = f"https://stockanalysis.com/quote/bvmf/PETR4/{page}/"
        try:
            with requests.get(url, headers={"User-Agent": "FinAnalyzer contact@finanalyser.com.br"},
                              timeout=(3, 12), allow_redirects=False, stream=True) as response:
                if response.status_code != 200:
                    continue
                data = bytearray()
                for chunk in response.iter_content(65536):
                    data.extend(chunk)
                    if len(data) > 2_000_000:
                        break
                if len(data) > 2_000_000:
                    continue
            text = filing_text(bytes(data))[:24000]
            if "PETR4" not in text or "BRL" not in text:
                continue
            sources.append({"id": "MKTPETR4-" + page, "url": url, "title": "StockAnalysis PETR4 " + page,
                            "text": text, "basis": "web_research", "document_type": "market_data"})
        except requests.RequestException:
            continue
    return sources


def collect_petrobras_calibration_sources():
    pages = [
        ("MKTGENIAL20260908", "Genial Petrobras valuation and peer-risk comparison, 2026-09-08",
         "https://analisa.genialinvestimentos.com.br/acoes/PETR4/petrobras-petr4-como-as-eleicoes-podem-afetar-a-avaliacao-da-petrobras/", "web_research", "market_data", "PETR4"),
        ("MKTBB2026Q2", "BB Investimentos Petrobras 2Q26 valuation",
         "https://investalk.bb.com.br/noticias/mercado/petrobras-PETR4-resultado-2T26", "web_research", "market_data", "PETR4"),
        ("IRPROD202502", "Petrobras official 2025 production and reserves announcement, 2026-02-10",
         "https://agencia.petrobras.com.br/w/produ%C3%A7%C3%A3o-de-petr%C3%B3leo-e-g%C3%A1s-da-petrobras-cresce-11-e-alcan%C3%A7a-3-milh%C3%B5es-de-barris-em-2025", "primary", "filing", "175%"),
    ]
    result = []
    for sid, title, url, basis, kind, marker in pages:
        try:
            with requests.get(url, timeout=(3, 12), allow_redirects=False, stream=True,
                              headers={"User-Agent": "FinAnalyzer contact@finanalyser.com.br"}) as response:
                if response.status_code != 200:
                    continue
                body = bytearray()
                for chunk in response.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > 2_000_000:
                        break
                if len(body) > 2_000_000:
                    continue
            text = filing_text(bytes(body))[:24000]
            if marker in text:
                result.append({"id": sid, "title": title, "url": url, "text": text, "basis": basis, "document_type": kind})
        except requests.RequestException:
            continue
    notes_path = Path(__file__).resolve().parents[1] / "research" / "petrobras-calibration-20261021.json"
    notes = json.loads(notes_path.read_text(encoding="utf-8"))
    downloaded = {s["id"] for s in result}
    result.extend(s for s in notes if s["id"] not in downloaded)
    return result


def collect_issuer_annual_sources(company, as_of):
    """Use verified issuer catalogues for annual comparisons, independently of web summaries."""
    fetcher = AutoFetcher()
    ticker = fetcher.resolve_ticker(company)
    catalog = fetcher.mziq_catalogs.get(ticker)
    if not catalog:
        return []
    cutoff = date.fromisoformat(as_of)

    def fetch(year):
        for candidate in fetcher._mziq_catalog_candidates(catalog[0], [catalog[1]], year, 4)[:1]:
            document = fetcher._download_release(candidate["url"], year, 4, depth=1, timeout=10)
            if not document:
                continue
            text = document.text or OpenAIClient.extract_text(document.pdf_bytes)
            if not fetcher._transcript_company_matches(text[:4000], ticker):
                continue
            # Retain opening annual comparisons and the closing financial statements.
            bounded = text if len(text) <= 32000 else text[:16000] + "\n[... excerpt omitted ...]\n" + text[-16000:]
            return {"id": f"IR{year}", "title": f"{ticker} annual results {year}", "url": document.url,
                    "text": bounded, "basis": "primary", "document_type": "filing"}
        return None

    # Before the annual reporting deadline use only completed years with published comparatives.
    latest = cutoff.year - (1 if cutoff.month >= 4 else 2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        return [source for source in pool.map(fetch, (latest, latest - 1)) if source]


def hydrate_company_documents(company, sources):
    catalog = json.loads((Path(__file__).resolve().parents[1] / "data/ir_map.json").read_text(encoding="utf-8"))
    issuer_host = urlsplit(catalog.get(company, "")).hostname
    tenant = AutoFetcher.mziq_catalogs.get(company, (None,))[0]
    official = next((s for s in sources if s.get("id") == "F1"), {})
    cik = re.search(r"CIK0*(\d+)\.json", official.get("url", ""))
    issuer_cik = int(cik[1]) if cik else (1119639 if is_petrobras(company) else None)
    candidates = []
    kinds = {}
    for source in sources:
        if source.get("basis") == "primary":
            continue
        url = source.get("url", "")
        parsed = urlsplit(url)
        host = parsed.hostname
        transcript = bool(re.search(r"transcript|transcri[cç][aã]o", source.get("title", "") + " " + parsed.path, re.I))
        kind = "transcript" if transcript else "filing"
        trusted_sec = host in ("www.sec.gov", "sec.gov") and issuer_cik and f"/data/{issuer_cik}/" in parsed.path
        trusted_issuer = (issuer_host and host == issuer_host) or (tenant and host in ("api.mziq.com", "filemanager-cdn.mziq.com") and tenant in parsed.path.split("/"))
        if is_petrobras(company):
            trusted_issuer = trusted_issuer or host in ("petrobras.com.br", "www.petrobras.com.br", "agencia.petrobras.com.br", "www.investidorpetrobras.com.br")
        trusted_transcript = transcript and host in ("stockanalysis.com", "www.stockanalysis.com")
        if (kinds.get(kind, 0) >= (6 if is_petrobras(company) and kind == "filing" else 1) or parsed.scheme != "https" or not (trusted_sec or trusted_issuer or trusted_transcript)
                or source.get("id") == "F1" or not AutoFetcher._valid_url(url)):
            continue
        if not transcript and not trusted_sec and not re.search(r"10-k|20-f|annual|anual|10-q|earnings|result|plano|business plan|dividend|estatuto|bylaws|shareholding|composi[cç][aã]o acion[aá]ria", source.get("title", ""), re.I):
            continue
        candidates.append((source, kind, bool(trusted_sec or trusted_issuer)))
        kinds[kind] = kinds.get(kind, 0) + 1
    def fetch(candidate):
        source, kind, primary = candidate
        try:
            with requests.get(source["url"], headers={"User-Agent": "FinAnalyzer contact@finanalyser.com.br"},
                              timeout=(3, 10), allow_redirects=False, stream=True) as response:
                if response.status_code != 200:
                    return source
                data = bytearray()
                for chunk in response.iter_content(65536):
                    data.extend(chunk)
                    if len(data) > (12_000_000 if is_petrobras(company) else 6_000_000):
                        return source
            if data.startswith(b"%PDF-"):
                text = OpenAIClient.extract_text(bytes(data))
            elif is_petrobras(company):
                text = filing_text(bytes(data))
            else:
                soup = BeautifulSoup(bytes(data), "html.parser")
                for node in soup(["script", "style", "nav", "footer", "aside"]):
                    node.decompose()
                text = (soup.find("article") or soup.find("main") or soup).get_text("\n", strip=True)
            if len(text) < 500:
                return source
            if kind == "transcript":
                period = AutoFetcher._transcript_period(text)
                if not period or not AutoFetcher()._valid_transcript(text, company, period[1], period[0]):
                    return source
            # Keep prepared remarks and Q&A rather than only the opening of a long transcript.
            bounded = text if len(text) <= 32000 else text[:20000] + "\n[... document excerpt omitted ...]\n" + text[-12000:]
            if is_petrobras(company) and kind == "filing":
                bounded = petrobras_document_excerpt(text)
            return {**source, "text": bounded, "basis": "primary" if primary else "transcript", "document_type": kind}
        except (requests.RequestException, ValueError, OpenAIError):
            return source
    with ThreadPoolExecutor(max_workers=2) as pool:
        hydrated = {s["id"]: s for s in pool.map(fetch, candidates)}
    return [{**source, **hydrated.get(source["id"], {}),
             "document_type": hydrated.get(source["id"], source).get("document_type",
                              "financials" if source.get("annual_financials") else "research")} for source in sources]


def petrobras_document_excerpt(text):
    """Retain middle-of-document capital/segment tables rather than only the cover and appendix."""
    if len(text) <= 90000:
        return text
    pieces = [text[:32000]]
    terms = (r"net debt|d[ií]vida l[ií]quida", r"non.?controlling|n[aã]o controladores", r"treasury shares|a[cç][oõ]es em tesouraria",
             r"preferred shares|a[cç][oõ]es preferenciais", r"share capital|capital social", r"segment information|informa[cç][oõ]es por segmento",
             r"lease liabilities|passivos de arrendamento", r"production|produ[cç][aã]o", r"reserves|reservas",
             r"shares outstanding|outstanding shares|number of shares")
    for term in terms:
        matches = list(re.finditer(term, text, re.I))
        # Later occurrences generally belong to statements rather than the table of contents.
        for match in matches[-2:]:
            pieces.append(text[max(0, match.start() - 450):match.start() + 1500])
    pieces.append(text[-8000:])
    return "\n[... excerpt boundary ...]\n".join(pieces)[:90000]


def with_petrobras_policy_evidence(sources):
    """Expand only immutable original policy notes; preserve every previously supplied excerpt."""
    from full_report_content import ReportValidationError
    from report_runtime import checkpoint
    result = []
    for source in sources:
        if source["id"] not in {"IRSEC000129281426002168", "IRSEC000129281426000708"}:
            result.append(source)
            continue
        url = urlsplit(source["url"])
        if url.hostname != "www.sec.gov" or not url.path.startswith("/Archives/edgar/data/1119639/") or source.get("basis") != "primary":
            raise ReportValidationError("Policy context requires the verified original Petrobras filing")
        def fetch():
            with requests.get(source["url"], timeout=(3, 20), allow_redirects=False, stream=True,
                              headers={"User-Agent": "FinAnalyzer contact@finanalyser.com.br"}) as response:
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > 12_000_000:
                        raise ReportValidationError("Original policy document exceeds its download budget")
            text = " ".join(filing_text(bytes(body)).split())
            matches = list(re.finditer(r"shareholders[’']? remuneration policy|distributions to shareholders|preferred shares participate in the distribution", text, re.I))
            if not matches:
                raise ReportValidationError("Original policy section could not be read")
            return "\n".join(text[max(0, m.start() - 1800):m.end() + 9000] for m in matches[-2:])
        appendix = checkpoint("petrobras-original-policy-v1", [source["id"], source["url"]], fetch)
        result.append({**source, "text": source["text"] + "\nORIGINAL POLICY EVIDENCE:\n" + appendix,
                       "policy_evidence": appendix})
    return result
