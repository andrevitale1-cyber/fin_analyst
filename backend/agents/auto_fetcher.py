import base64
import hashlib
from dataclasses import asdict
import json
import ipaddress
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from agents.search_client import SearchClient, SearchError
from agents.sec_fetcher import FetchedDocument, SECFetcher
from openai_client import OpenAIClient, OpenAIError


class AutoFetcher:
    transcript_issuers = {
        "AAPL": ("Apple",), "MSFT": ("Microsoft",), "GOOGL": ("Alphabet", "Google"),
        "AMZN": ("Amazon",), "META": ("Meta", "Facebook"), "NVDA": ("Nvidia",), "TSLA": ("Tesla",),
        "ITUB4": ("Itaú Unibanco", "Itaú"), "ITSA4": ("Itaúsa",), "BBAS3": ("Banco do Brasil",),
        "BBDC4": ("Bradesco",), "SANB11": ("Santander Brasil", "Santander"),
        "PETR4": ("Petrobras",), "VALE3": ("Vale",), "ABEV3": ("Ambev",), "WEGE3": ("WEG",),
        "RENT3": ("Localiza",), "LREN3": ("Lojas Renner",), "B3SA3": ("B3",),
    }
    def __init__(self, cache_dir=None):
        base_dir = Path(__file__).resolve().parent.parent
        self.ir_urls = json.loads((base_dir / "data/ir_map.json").read_text(encoding="utf-8"))
        self.watchlist = [
            {"ticker": ticker, "mercado": "US" if re.fullmatch(r"[A-Z]{1,5}", ticker) else "B3", "ir_url": url}
            for ticker, url in self.ir_urls.items()
        ]
        self.search_client = SearchClient()
        self.cache_dir = Path(cache_dir or os.getenv("REPORT_CACHE_DIR", str(Path(tempfile.gettempdir()) / "finanalyzer-releases")))
        self._transcript_download_failed = False

    def resolve_ticker(self, ticker):
        """Accept common Brazilian symbols typed without their share-class suffix."""
        ticker = ticker.strip().upper()
        company_aliases = {
            "ITAU": "ITUB4", "ITAU UNIBANCO": "ITUB4", "ITAU UNIBANCO HOLDING": "ITUB4",
            "PETROBRAS": "PETR4", "PETROLEO BRASILEIRO": "PETR4", "VALE": "VALE3",
            "AMBEV": "ABEV3", "BRADESCO": "BBDC4", "BANCO DO BRASIL": "BBAS3",
            "ITAUSA": "ITSA4", "SANTANDER BRASIL": "SANB11", "WEG": "WEGE3",
            "LOCALIZA": "RENT3", "LOJAS RENNER": "LREN3", "B3": "B3SA3",
            "APPLE": "AAPL", "MICROSOFT": "MSFT", "GOOGLE": "GOOGL", "ALPHABET": "GOOGL",
            "AMAZON": "AMZN", "META": "META", "FACEBOOK": "META", "NVIDIA": "NVDA", "TESLA": "TSLA",
        }
        normalized = " ".join("".join(c for c in unicodedata.normalize("NFKD", ticker) if not unicodedata.combining(c)).split())
        if normalized in company_aliases:
            return company_aliases[normalized]
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
        text = " ".join(unquote(text).upper().split())
        year_pattern = f"(?:{year}|{str(year)[-2:]})"
        if AutoFetcher._transcript_period_matches(text, year, quarter):
            return True
        if re.search(
            rf"(?<![A-Z0-9])(?:{quarter}[TQ]|[TQ]{quarter})[\s_./-]*(?:FY|FISCAL(?:\s+YEAR)?)?[\s_./-]*{year_pattern}(?!\d)", text
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
        if not re.fullmatch(r"[\w .&'-]{1,100}", ticker, re.UNICODE):
            raise ValueError("Informe um nome de empresa ou ticker válido.")
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
        if re.fullmatch(r"[A-Z]{1,5}", ticker):
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

    def fetch_transcript(self, company, ano, trimestre):
        match = re.fullmatch(r"(?:([1-4])[TQ]?|[TQ]([1-4]))", str(trimestre).upper())
        if not match or not re.fullmatch(r"\d{4}", str(ano)) or not 1900 <= int(ano) <= 2100:
            raise ValueError("Ano ou trimestre inválido.")
        company = company.strip()
        if not re.fullmatch(r"[\w .&'-]{1,100}", company, re.UNICODE):
            raise ValueError("Informe um nome de empresa ou ticker válido.")
        year, quarter = int(ano), int(match.group(1) or match.group(2))
        issuer = self.resolve_ticker(company)
        query_name = self.transcript_issuers.get(issuer, (company,))[0]
        cache_key = hashlib.sha256(issuer.encode("utf-8")).hexdigest()[:24]
        cache_path = self.cache_dir / f"transcript-v2-{cache_key}-{year}-{quarter}.json"
        try:
            document = FetchedDocument(**json.loads(cache_path.read_text(encoding="utf-8")))
            if self._valid_url(document.url) and self._valid_transcript(document.text, company, year, quarter):
                return document
        except (OSError, ValueError, TypeError):
            pass
        self._transcript_download_failed = False
        document = self._fetch_transcript_ir(issuer, company, year, quarter)
        seen = set()
        for allow_openai in (False, True):
            if document:
                break
            try:
                results = self.search_client.search_transcripts(query_name, year, quarter, allow_openai=allow_openai)
            except SearchError:
                if allow_openai:
                    raise
                continue
            for item in results[:8]:
                url = item.get("url", "")
                evidence = f"{item.get('title', '')} {url}"
                if not self._valid_url(url) or url in seen:
                    continue
                if self._transcript_period(evidence) and not self._transcript_period_matches(evidence, year, quarter):
                    continue
                if not re.search(r"transcript|transcri[cç][aã]o|teleconfer[eê]ncia|earnings.call", evidence + " " + str(item.get("content") or ""), re.I):
                    continue
                seen.add(url)
                document = self._download_transcript(url, year, quarter, company)
                if document:
                    break
        if document:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                # Only verified text is cached; analysis never needs a second PDF copy.
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.cache_dir, delete=False) as temp:
                    json.dump({"url": document.url, "source": document.source, "text": document.text}, temp)
                os.replace(temp.name, cache_path)
            except OSError:
                pass
            return document
        if self._transcript_download_failed:
            raise SearchError("Não foi possível acessar as fontes de transcrição. Tente novamente ou envie o PDF.")
        return None

    @staticmethod
    def _transcript_period(text):
        text = unquote(text[:12000]).upper()
        periods = []
        for match in re.finditer(r"(?<![A-Z0-9])(?:([1-4])\s*[TQ]|[TQ]\s*([1-4]))[\s_./'-]*(?:FY|FISCAL(?:\s+YEAR)?)?[\s_./'’-]*((?:19|20)\d{2}|\d{2})(?!\d)", text):
            periods.append((match.start(), int(match[1] or match[2]), int(match[3])))
        for match in re.finditer(r"(?:FY|FISCAL(?:\s+YEAR)?)[\s_./'’-]*((?:19|20)\d{2}|\d{2})[\s_./-]*(?:([1-4])[TQ]|[TQ]([1-4]))", text):
            periods.append((match.start(), int(match[2] or match[3]), int(match[1])))
        names = {"FIRST": 1, "SECOND": 2, "THIRD": 3, "FOURTH": 4,
                 "PRIMEIRO": 1, "SEGUNDO": 2, "TERCEIRO": 3, "QUARTO": 4}
        year_pattern = r"(?:(?:FY|FISCAL(?:\s+YEAR)?)[\s_./'’-]*((?:19|20)\d{2}|\d{2})(?!\d)|((?:19|20)\d{2}))"
        for match in re.finditer(r"(FIRST|SECOND|THIRD|FOURTH|PRIMEIRO|SEGUNDO|TERCEIRO|QUARTO|[1-4](?:ST|ND|RD|TH|º|°)?)\s+(?:QUARTER|TRIMESTRE)", text):
            after = re.search(year_pattern, text[match.end():match.end()+50])
            before = list(re.finditer(year_pattern, text[max(0,match.start()-40):match.start()]))
            found = after or (before[-1] if before else None)
            if found:
                number = names.get(match[1]) or int(match[1][0])
                periods.append((match.start(), number, int(found[1] or found[2])))
        if not periods:
            return None
        _, found_quarter, found_year = min(periods)
        return found_quarter, found_year

    @staticmethod
    def _transcript_period_matches(text, year, quarter):
        period = AutoFetcher._transcript_period(text)
        return period in ((quarter, year), (quarter, year % 100))

    def _transcript_company_matches(self, text, company):
        issuer = self.resolve_ticker(company)
        aliases = (*self.transcript_issuers.get(issuer, (company,)), issuer)
        normalize = lambda value: "".join(c for c in unicodedata.normalize("NFKD", value).upper() if not unicodedata.combining(c))
        return any(re.search(r"(?<!\w)" + re.escape(normalize(name)) + r"(?!\w)", normalize(text)) for name in aliases)

    def _valid_transcript(self, text, company, year, quarter):
        if not isinstance(text, str) or len(text.strip()) < 500 or not self._transcript_period_matches(text, year, quarter):
            return False
        if company:
            if not self._transcript_company_matches(text[:2500], company):
                return False
            title = text.strip().splitlines()[0]
            if (any(self._transcript_company_matches(title, issuer) for issuer in self.transcript_issuers)
                    and not self._transcript_company_matches(title, company)):
                return False
        dialogue = re.search(r"\boperator\s*[:\n]|\bQ\s*&\s*A\b|questions?.{0,10}answers?|prepared remarks", text, re.I)
        speakers = set(re.findall(r"\b(?:[A-Z][A-Za-z'-]+ ){1,3}[A-Z][A-Za-z'-]+\s*:", text))
        return bool(re.search(r"transcript|transcri[cç][aã]o|teleconfer[eê]ncia|earnings.call|conference.call", text, re.I)
                    and (dialogue or len(speakers) >= 2))

    def _fetch_transcript_ir(self, issuer, company, year, quarter):
        if issuer == "MSFT":
            url = f"https://www.microsoft.com/en-us/investor/events/fy-{year}/earnings-fy-{year}-q{quarter}"
            if document := self._download_transcript(url, year, quarter, company):
                return document
        url = self.ir_urls.get(issuer)
        if self._valid_url(url):
            try:
                response = requests.get(url, timeout=8)
                response.raise_for_status()
                if self._valid_url(response.url):
                    soup = BeautifulSoup(response.text, "html.parser")
                    links = [(a.get_text(" ", strip=True), urljoin(response.url, a["href"])) for a in soup.find_all("a", href=True)]
                    links = [(title, href) for title, href in links if re.search(r"transcript|transcri[cç][aã]o", title + " " + href, re.I)]
                    links.sort(key=lambda link: not self._period_matches(" ".join(link), year, quarter))
                    for _, href in links[:2]:
                        if document := self._download_transcript(href, year, quarter, company):
                            return document
            except requests.RequestException:
                pass
        # A public text archive avoids paid web search when IR only offers audio.
        if issuer in self.transcript_issuers and re.fullmatch(r"[A-Z]{1,5}", issuer):
            return self._download_transcript(f"https://stockanalysis.com/stocks/{issuer.lower()}/transcripts/", year, quarter, company)
        return None

    def _download_transcript(self, url, year, quarter, company=None, depth=0):
        if not self._valid_url(url):
            return None
        try:
            response = requests.get(url, timeout=12)
            response.raise_for_status()
            if not self._valid_url(response.url):
                return None
            if response.content.startswith(b"%PDF-"):
                text = OpenAIClient.extract_text(response.content)
            else:
                if "html" not in response.headers.get("Content-Type", "").lower() and not response.text.lstrip().startswith("<"):
                    return None
                soup = BeautifulSoup(response.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "aside"]):
                    tag.decompose()
                region = soup.find("article") or soup.find("main") or soup
                text = region.get_text("\n", strip=True)
                if not self._valid_transcript(text, company, year, quarter) and depth == 0:
                    links = [(a.get_text(" ", strip=True), urljoin(response.url, a["href"])) for a in soup.find_all("a", href=True)]
                    links = [(title, href) for title, href in links if re.search(r"transcript|transcri[cç][aã]o", title + " " + href, re.I) and self._valid_url(href) and urlparse(href).hostname == urlparse(response.url).hostname]
                    links.sort(key=lambda link: not self._period_matches(" ".join(link), year, quarter))
                    for _, href in links[:2]:
                        if href != response.url and (document := self._download_transcript(href, year, quarter, company, depth=1)):
                            return document
            if self._valid_transcript(text, company, year, quarter):
                return FetchedDocument(response.url, "Earnings Call Transcript", text=text[:180000])
        except requests.RequestException as exc:
            if not isinstance(exc, requests.HTTPError) or exc.response is None or exc.response.status_code != 404:
                self._transcript_download_failed = True
        except OpenAIError:
            return None
        return None

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
            evidence = candidate["title"] + " " + candidate["url"]
            mentioned_quarters = re.findall(r"(?<![A-Z0-9])([1-4][TQ]|[TQ][1-4])[\s_./-]*(?:20\d{2}|\d{2})", evidence.upper())
            if mentioned_quarters and not self._period_matches(evidence, year, quarter):
                continue
            if re.search(r"20\d{2}", evidence) and not self._period_matches(evidence, year, quarter):
                continue
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
            if re.search(r"annual report|annual accounts|form 10-k", evidence, re.I) and not re.search(
                r"quarterly|earnings release|quarterly results|resultados trimestrais|central de resultados", evidence, re.I
            ):
                continue
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
