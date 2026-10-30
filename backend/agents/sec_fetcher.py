"""Balanços e releases SEC pelo trimestre fiscal do emissor."""
from dataclasses import dataclass
from datetime import date, timedelta
import re
import time
import unicodedata
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class FetchedDocument:
    url: str
    source: str
    pdf_bytes: bytes = b""
    text: str = ""


class SECFetcher:
    headers = {"User-Agent": "FinAnalyzer contact@finanalyser.com.br"}
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

    def fetch(self, ticker, year, quarter):
        try:
            company = next((c for c in self._catalog() if c.get("ticker") == ticker), None)
            if not company:
                return None
            cik = int(company["cik_str"])
            filings = self._get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()["filings"]
            facts = self._get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json").json().get("facts", {})
            fiscal_period = f"Q{quarter}" if quarter < 4 else "FY"
            fiscal_filings = set()
            for taxonomy in facts.values():
                for fact in taxonomy.values():
                    for entries in fact.get("units", {}).values():
                        for entry in entries:
                            if (entry.get("fy") == year and entry.get("fp") == fiscal_period
                                    and entry.get("form") in ("10-Q", "10-Q/A", "10-K", "10-K/A")):
                                fiscal_filings.add((entry.get("accn"), entry.get("end")))
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
                        if document and self._mentions_quarter(document.text, year, quarter):
                            return document
                if quarter < 4:
                    document = self._filing_document(batch, index, cik)
                    if document:
                        return document
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
            return None
        return None

    @staticmethod
    def _mentions_quarter(text, year, quarter):
        if not text:
            return False
        head = text[:10000]
        if re.search(rf"(?:{quarter}[TQ]|[TQ]{quarter})\s*{year}", head, re.I):
            return True
        ordinal = ("first", "second", "third", "fourth")[quarter - 1]
        return bool(re.search(rf"\b{ordinal}\s+(?:fiscal\s+)?quarter\b.{{0,80}}\b(?:fiscal\s+)?{year}\b", head, re.I))

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
        if exhibit and re.search(r"results of operations|financial results|earnings|quarterly results", text, re.I):
            for link in soup.find_all("a", href=True):
                if not re.search(r"99|exhibit|earnings|release", link["href"] + link.get_text(), re.I):
                    continue
                exhibit_url = urljoin(url, link["href"])
                if urlparse(exhibit_url).netloc != "www.sec.gov" or not exhibit_url.startswith(url.rsplit("/", 1)[0] + "/"):
                    continue
                exhibit_response = self._get(exhibit_url)
                if exhibit_response.content.startswith(b"%PDF-"):
                    return FetchedDocument(exhibit_url, "SEC", pdf_bytes=exhibit_response.content)
                exhibit_soup = BeautifulSoup(exhibit_response.text, "html.parser")
                for tag in exhibit_soup(["script", "style"]):
                    tag.decompose()
                text += "\n" + exhibit_soup.get_text("\n", strip=True)
                break
        return FetchedDocument(url, "SEC", text=text[:180000])
