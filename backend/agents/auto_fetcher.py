import base64
from dataclasses import asdict
import json
import ipaddress
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from agents.search_client import SearchClient
from agents.sec_fetcher import FetchedDocument, SECFetcher
from openai_client import OpenAIClient, OpenAIError


class AutoFetcher:
    def __init__(self, cache_dir=None):
        base_dir = Path(__file__).resolve().parent.parent
        self.ir_urls = json.loads((base_dir / "data/ir_map.json").read_text(encoding="utf-8"))
        self.watchlist = [
            {"ticker": ticker, "mercado": "US" if re.fullmatch(r"[A-Z]{1,5}", ticker) else "B3", "ir_url": url}
            for ticker, url in self.ir_urls.items()
        ]
        self.search_client = SearchClient()
        self.cache_dir = Path(cache_dir or os.getenv("REPORT_CACHE_DIR", str(Path(tempfile.gettempdir()) / "finanalyzer-releases")))

    def resolve_ticker(self, ticker):
        """Accept common Brazilian symbols typed without their share-class suffix."""
        ticker = ticker.strip().upper()
        if ticker in self.ir_urls:
            return ticker
        if ticker.isalpha() and len(ticker) >= 3:
            matches = [symbol for symbol in self.ir_urls if symbol.startswith(ticker) and re.search(r"\d", symbol)]
            if matches:
                return sorted(matches, key=lambda symbol: (0 if symbol.endswith("4") else 1, len(symbol)))[0]
        return ticker

    @staticmethod
    def _valid_url(url):
        if not isinstance(url, str):
            return False
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username:
            return False
        host = parsed.hostname.lower()
        if host in ("localhost", "metadata.google.internal") or host.endswith((".local", ".localhost", ".internal")):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            return "." in host

    @staticmethod
    def _period_matches(text, year, quarter):
        text = unquote(text).upper()
        year_pattern = f"(?:{year}|{str(year)[-2:]})"
        if re.search(
            rf"(?<![A-Z0-9])(?:{quarter}[TQ]|[TQ]{quarter})[\s_./-]*{year_pattern}(?!\d)", text
        ):
            return True
        names = {1: ("PRIMEIRO", "FIRST", "MARCH", "MARÇO"),
                 2: ("SEGUNDO", "SECOND", "JUNE", "JUNHO"),
                 3: ("TERCEIRO", "THIRD", "SEPTEMBER", "SETEMBRO"),
                 4: ("QUARTO", "FOURTH", "DECEMBER", "DEZEMBRO")}
        pt, en, month_en, month_pt = names[quarter]
        return bool(re.search(
            rf"(?:{quarter}\s*(?:º|°)?\s*TRIMESTRE|{pt}\s+TRIMESTRE|{en}\s+QUARTER|"
            rf"(?:QUARTER|TRIMESTRE)\s+(?:ENDED?|ENCERRADO)?\s*(?:EM|DE)?\s*(?:{month_en}|{month_pt}))"
            rf".{{0,45}}{year}", text
        ))

    def fetch_result_pdf(self, ticker, ano, trimestre):
        ticker = self.resolve_ticker(ticker)
        if not re.fullmatch(r"[A-Z0-9]{1,10}", ticker):
            raise ValueError("Ticker inválido.")
        match = re.fullmatch(r"(?:([1-4])[TQ]?|[TQ]([1-4]))", str(trimestre).upper())
        if not match or not re.fullmatch(r"\d{4}", str(ano)) or not 1900 <= int(ano) <= 2100:
            raise ValueError("Ano ou trimestre inválido. Use ano com quatro dígitos e trimestre de 1T a 4T.")
        year, quarter = int(ano), int(match.group(1) or match.group(2))
        cache_path = self.cache_dir / f"{ticker}-{year}-{quarter}.json"
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            cached["pdf_bytes"] = base64.b64decode(cached["pdf_bytes"], validate=True)
            document = FetchedDocument(**cached)
            if document.pdf_bytes.startswith(b"%PDF-") or document.text.strip():
                return document
        except (OSError, ValueError, TypeError, KeyError):
            pass
        if re.fullmatch(r"[A-Z]{1,5}", ticker) and ticker not in self.ir_urls:
            document = SECFetcher().fetch(ticker, year, quarter)
        else:
            document = self._fetch_b3(ticker, year, quarter)
        if document:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                data = asdict(document)
                data["pdf_bytes"] = base64.b64encode(document.pdf_bytes).decode("ascii")
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.cache_dir, delete=False) as temp:
                    json.dump(data, temp)
                os.replace(temp.name, cache_path)
            except OSError:
                pass
        return document

    def _fetch_b3(self, ticker, year, quarter):
        ir_url = self.ir_urls.get(ticker)
        if ir_url and self._valid_url(ir_url):
            try:
                response = requests.get(ir_url, timeout=15)
                response.raise_for_status()
                if not self._valid_url(response.url):
                    raise requests.RequestException("Redirecionamento inválido")
                soup = BeautifulSoup(response.text, "html.parser")
                candidates = [{"title": a.get_text(" ", strip=True), "url": urljoin(response.url, a["href"])}
                              for a in soup.find_all("a", href=True)]
                for candidate in self._candidates(candidates, year, quarter)[:12]:
                    document = self._download_release(candidate["url"], year, quarter)
                    if document:
                        return document
            except requests.RequestException:
                pass
        results = self.search_client.search_financial_reports(ticker, year, f"{quarter}T")
        candidates = self._candidates(results, year, quarter)
        for candidate in candidates[:12]:
            document = self._download_release(candidate["url"], year, quarter)
            if document:
                return document
        return None

    def _candidates(self, results, year, quarter):
        candidates = []
        for result in results:
            url = result.get("url")
            title = result.get("title", "")
            evidence = f"{title} {result.get('content', '')} {url or ''}"
            if self._valid_url(url) and re.search(
                r"release|resultados?|results?|earnings|financial results|central de resultados|demonstra[cç][oõ]es|an[aá]lise gerencial|apresenta[cç][aã]o|relat[oó]rio.*trimestral|\.pdf",
                evidence, re.I,
            ):
                candidates.append({"title": title, "url": url, "content": result.get("content", "")})
        def rank(candidate):
            text = candidate["title"] + " " + candidate.get("content", "")
            standalone_statements = bool(re.search(
                r"financial statements|demonstra[cç][oõ]es cont[aá]beis|itr|10-q|10-k", text, re.I
            )) and not bool(re.search(r"an[aá]lise gerencial|management discussion and analysis|\bmd&a\b", text, re.I))
            return (
                not self._period_matches(text + " " + candidate["url"], year, quarter),
                standalone_statements,
                not bool(re.search(r"earnings release|press release|results presentation|apresenta[cç][aã]o.*resultado|an[aá]lise gerencial|coment[aá]rios? sobre os resultados", text, re.I)),
                not bool(re.search(r"\.pdf(?:$|[?#])", candidate["url"], re.I)),
            )
        return sorted(candidates, key=rank)

    def _download_release(self, url, year, quarter, depth=0):
        if not self._valid_url(url):
            return None
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            if not self._valid_url(response.url):
                return None
            if response.content.startswith(b"%PDF-"):
                text = OpenAIClient.extract_text(response.content)
                pdf_bytes = response.content
            else:
                content_type = response.headers.get("Content-Type", "")
                if "html" not in content_type.lower() and not response.text.lstrip().startswith(("<", "<!DOCTYPE")):
                    return None
                soup = BeautifulSoup(response.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                if depth == 0:
                    linked = [{"title": a.get_text(" ", strip=True), "url": urljoin(response.url, a["href"])}
                              for a in soup.find_all("a", href=True)]
                    for candidate in self._candidates(linked, year, quarter)[:8]:
                        if urlparse(candidate["url"]).netloc == urlparse(response.url).netloc:
                            document = self._download_release(candidate["url"], year, quarter, depth=1)
                            if document:
                                return document
                text = soup.get_text("\n", strip=True)
                pdf_bytes = b""
            if not self._period_matches(text[:4000], year, quarter):
                return None
            periods = re.findall(r"(?<![A-Z0-9])(?:[1-4][TQ]|[TQ][1-4])[\s_./-]*(?:20\d{2}|\d{2})(?!\d)", text[:4000].upper())
            if periods and not self._period_matches(periods[0], year, quarter):
                return None
            return FetchedDocument(response.url, "B3/RI", pdf_bytes=pdf_bytes, text="" if pdf_bytes else text[:180000])
        except (requests.RequestException, OpenAIError):
            return None
