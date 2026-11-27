"""Balanços e releases SEC pelo trimestre fiscal do emissor."""
from dataclasses import dataclass, field
from datetime import date, timedelta
import re
import time
import unicodedata
from urllib.parse import quote, urljoin, urlparse

import requests
import logging
from bs4 import BeautifulSoup
from openai_client import OpenAIClient, OpenAIError


@dataclass
class FetchedDocument:
    url: str
    source: str
    pdf_bytes: bytes = b""
    text: str = ""
    sources: list = field(default_factory=list)
    fiscal_year: int | None = None
    fiscal_quarter: int | None = None
    issuer_cik: str | None = None


logger = logging.getLogger("uvicorn.error")


class SECFetcher:
    headers = {"User-Agent": "FinAnalyser contact@finanalyser.com.br"}
    _company_catalog = None
    _catalog_expires = 0

    @staticmethod
    def _company_name(value):
        value = re.sub(r"\s*/(?:NEW|DE|MD|NV|CO)/?\s*$", "", value, flags=re.I)
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().upper()
        value = re.sub(r"[^A-Z0-9]+", " ", value).strip()
        return re.sub(r"\s+(?:INCORPORATED|INC|CORPORATION|CORP|COMPANY|CO|LTD|LIMITED|PLC)$", "", value).strip()

    def _catalog(self):
        if SECFetcher._company_catalog is None or time.monotonic() >= SECFetcher._catalog_expires:
            data = self._get("https://www.sec.gov/files/company_tickers.json").json()
            if not isinstance(data, dict):
                return []
            SECFetcher._company_catalog = list(data.values())
            SECFetcher._catalog_expires = time.monotonic() + 86400
        return SECFetcher._company_catalog

    def resolve_name(self, name):
        """Resolve only an unambiguous exact issuer name, never a partial match."""
        try:
            if not self._catalog():
                return None
            target = self._company_name(name)
            symbols = {item.get("ticker") for item in SECFetcher._company_catalog if isinstance(item, dict)}
            if name in symbols:
                return name
            matches = {item.get("ticker") for item in SECFetcher._company_catalog
                       if isinstance(item, dict) and self._company_name(str(item.get("title", ""))) == target}
            matches = {ticker for ticker in matches if isinstance(ticker, str) and re.fullmatch(r"[A-Z]{1,5}(?:[-.][A-Z])?", ticker)}
            return next(iter(matches)) if len(matches) == 1 else None
        except (requests.RequestException, ValueError, TypeError):
            return None

    def _get(self, url):
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response

    @staticmethod
    def _quarter_ends(period_ends, year, quarter):
        if (year, quarter) in period_ends:
            return [date.fromisoformat(period_ends[(year, quarter)])]
        if not period_ends:
            return [date(year, quarter * 3, 30 if quarter in (2, 3) else 31)]
        (known_year, known_quarter), known_end = max(period_ends.items(), key=lambda item: item[1])
        estimate = date.fromisoformat(known_end) + timedelta(days=round(((year * 4 + quarter) - (known_year * 4 + known_quarter)) * 91.31))
        return [estimate, estimate - timedelta(days=365)]

    def latest_fiscal_period(self, cik):
        """(fiscal year, quarter, period end) of the issuer's latest 10-Q/10-K, in the issuer's own XBRL labels."""
        facts = self._get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json").json().get("facts", {})
        latest = {}
        for taxonomy in facts.values():
            for fact in taxonomy.values():
                for entries in fact.get("units", {}).values():
                    for entry in entries:
                        if entry.get("form") in ("10-Q", "10-K") and entry.get("fp") in ("Q1", "Q2", "Q3", "FY") and entry.get("fy"):
                            key = (entry.get("filed", ""), entry["fy"], entry["fp"])
                            if entry.get("start") and key >= latest.get("key", ("",)):
                                if key != latest.get("key"):
                                    latest = {"key": key, "end": ""}
                                latest["end"] = max(latest["end"], entry.get("end", ""))
        if not latest:
            return None
        _, fy, fp = latest["key"]
        return fy, 4 if fp == "FY" else int(fp[1]), date.fromisoformat(latest["end"])

    def fetch(self, ticker, year, quarter):
        try:
            company = next((c for c in self._catalog() if c.get("ticker") == ticker), None)
            if not company:
                return None
            cik = int(company["cik_str"])
            filings = self._get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()["filings"]
            try:
                facts = self._get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json").json().get("facts", {})
            except (requests.RequestException, ValueError):
                facts = {}  # A delayed XBRL endpoint must not hide an already published 8-K.
            fiscal_period = f"Q{quarter}" if quarter < 4 else "FY"
            fiscal_filings = set()
            period_ends = {}  # (fiscal year, quarter) -> period end, in the issuer's XBRL labels
            for taxonomy in facts.values():
                for fact in taxonomy.values():
                    for entries in fact.get("units", {}).values():
                        for entry in entries:
                            if entry.get("form") not in ("10-Q", "10-Q/A", "10-K", "10-K/A"):
                                continue
                            if entry.get("fy") == year and entry.get("fp") == fiscal_period:
                                fiscal_filings.add((entry.get("accn"), entry.get("end")))
                            if entry.get("fp") in ("Q1", "Q2", "Q3", "FY") and entry.get("fy") and entry.get("start") and entry.get("end"):
                                label = (entry["fy"], 4 if entry["fp"] == "FY" else int(entry["fp"][1]))
                                period_ends[label] = max(period_ends.get(label, ""), entry["end"])
            batches = [filings["recent"]]
            for archive in filings.get("files", []):
                if archive["filingFrom"] <= f"{year + 1}-12-31" and archive["filingTo"] >= f"{year - 1}-01-01":
                    batches.append(self._get(f"https://data.sec.gov/submissions/{quote(archive['name'], safe='')}").json())
            matching = []
            for batch in batches:
                for i, form in enumerate(batch.get("form", [])):
                    if form not in (("10-Q", "10-Q/A") if quarter < 4 else ("10-K", "10-K/A")):
                        continue
                    report_dates = batch.get("reportDate", [])
                    if i < len(report_dates) and (batch["accessionNumber"][i], report_dates[i]) in fiscal_filings:
                        matching.append((batch, i, report_dates[i]))
            if not matching:
                # Earnings releases can precede the 10-Q/10-K and its XBRL fiscal tags.
                candidates = [(batch, i) for batch in batches for i, form in enumerate(batch.get("form", []))
                              if (form == "6-K" or (form == "8-K" and "2.02" in batch.get("items", [""] * len(batch["form"]))[i]))
                              and year - 1 <= date.fromisoformat(batch["filingDate"][i]).year <= year + 1]
                # Look first inside the release window of the requested quarter. Its end comes from the issuer's own
                # fiscal calendar (Walmart's Q3 FY2027 ends October 2026); a label one year ahead of the XBRL tags is
                # also covered, and the release text must still name the quarter.
                quarter_ends = self._quarter_ends(period_ends, year, quarter)
                in_window = [row for row in candidates if any(
                    end + timedelta(days=5) <= date.fromisoformat(row[0]["filingDate"][row[1]]) <= end + timedelta(days=120)
                    for end in quarter_ends)]
                candidates.sort(key=lambda row: row[0]["filingDate"][row[1]], reverse=True)
                in_window.sort(key=lambda row: row[0]["filingDate"][row[1]])
                tried = in_window[:12] + [row for row in candidates[:8] if row not in in_window[:12]]
                heads = []
                for batch, i in tried:
                    document = self._filing_document(batch, i, cik, exhibit=True)
                    if document and self._release_matches(document, year, quarter):
                        return document
                    if document and (batch, i) in in_window:
                        heads.append(f'{batch["filingDate"][i]}:{" ".join((document.text or "")[:160].split())}')
                logger.info("sec_release_not_matched cik=%s year=%s quarter=%s candidates=%s filed=%s heads=%r", cik, year, quarter,
                            len(tried), ",".join(batch["filingDate"][i] for batch, i in tried[:12]), heads[:4])
                return None
            # An annual filing is not a standalone fourth-quarter result; require an explicit release.
            for batch, index, report_date in matching:
                period_end = date.fromisoformat(report_date)
                for release_batch in batches:
                    for i, form in enumerate(release_batch.get("form", [])):
                        if form not in ("8-K", "6-K"):
                            continue
                        filed = date.fromisoformat(release_batch["filingDate"][i])
                        if not period_end <= filed <= period_end + timedelta(days=100):
                            continue
                        items = release_batch.get("items", [""] * len(release_batch["form"]))[i]
                        if form == "8-K" and "2.02" not in items:
                            continue
                        document = self._filing_document(release_batch, i, cik, exhibit=True)
                        if document and self._release_matches(document, year, quarter):
                            return document
                logger.info("sec_release_not_matched cik=%s year=%s quarter=%s periodic_report=%s", cik, year, quarter, report_date)
                if quarter < 4:
                    document = self._filing_document(batch, index, cik)
                    if document:
                        # Preserve the XBRL fiscal mapping: a Q1 FY2027 filing can end in September 2026.
                        document.fiscal_year, document.fiscal_quarter = year, quarter
                        document.issuer_cik = str(cik).zfill(10)
                        return document
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
            return None
        return None

    def _release_matches(self, document, year, quarter):
        try:
            text = document.text or OpenAIClient.extract_text(document.pdf_bytes)
            return self._mentions_quarter(text, year, quarter)
        except OpenAIError:
            return False

    @staticmethod
    def _mentions_quarter(text, year, quarter):
        if not text:
            return False
        head = " ".join(text[:10000].split())
        periods = []
        for match in re.finditer(r"\b(?:([1-4])[TQ]|[TQ]([1-4]))\s*(?:FY\s*)?(20\d{2})\b", head, re.I):
            periods.append((match.start(), int(match[3]), int(match[1] or match[2])))
        for match in re.finditer(r"\b(first|second|third|fourth)\s+(?:fiscal\s+)?quarter\b.{0,80}?\b(20\d{2})\b", head, re.I):
            periods.append((match.start(), int(match[2]), ("first","second","third","fourth").index(match[1].lower()) + 1))
        return bool(periods and min(periods)[1:] == (year, quarter))

    def _filing_document(self, batch, i, cik, exhibit=False):
        accession = batch["accessionNumber"][i].replace("-", "")
        primary = quote(batch["primaryDocument"][i], safe="")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary}"
        response = self._get(url)
        if response.content.startswith(b"%PDF-"):
            return FetchedDocument(url, "SEC", pdf_bytes=response.content)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)
        if not text.strip():
            return None
        if exhibit:
            return self.fetch_earnings_exhibit(url, soup)
        return FetchedDocument(url, "SEC", text=text[:180000])

    @staticmethod
    def has_financial_results(text):
        return bool(re.search(r"(?:net sales|total revenue|net revenue|revenues|net income|operating income)[\s\S]{0,150}\d", text, re.I))

    def fetch_earnings_exhibit(self, url, soup):
        # An 8-K notice is not the earnings release; follow actual exhibit files, not TOC anchors.
        links = sorted(soup.find_all("a", href=True), key=lambda a: not bool(re.search(r"(?:ex)?99[-_.]?1", a["href"], re.I)))
        seen = {urlparse(url)._replace(fragment="").geturl()}
        for link in links:
            if not re.search(r"99|exhibit|earnings|release", link["href"] + link.get_text(), re.I):
                continue
            target = urlparse(urljoin(url, link["href"]))._replace(fragment="").geturl()
            if target in seen or urlparse(target).netloc != "www.sec.gov" or not target.startswith(url.rsplit("/", 1)[0] + "/"):
                continue
            seen.add(target)
            try:
                response = self._get(target)
                if response.content.startswith(b"%PDF-"):
                    return FetchedDocument(target, "SEC", pdf_bytes=response.content)
                exhibit = BeautifulSoup(response.text, "html.parser")
                for tag in exhibit(["script", "style"]):
                    tag.decompose()
                text = exhibit.get_text("\n", strip=True)
                if self.has_financial_results(text):
                    return FetchedDocument(target, "SEC", text=text[:180000])
            except requests.RequestException:
                continue
        text = soup.get_text("\n", strip=True)
        return FetchedDocument(url, "SEC", text=text[:180000]) if self.has_financial_results(text) else None
