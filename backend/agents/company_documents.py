"""Bounded document hydration from verified issuer/SEC hosts; never fetch arbitrary model URLs."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

from agents.auto_fetcher import AutoFetcher
from openai_client import OpenAIClient, OpenAIError


def hydrate_company_documents(company, sources):
    catalog = json.loads((Path(__file__).resolve().parents[1] / "data/ir_map.json").read_text(encoding="utf-8"))
    issuer_host = urlsplit(catalog.get(company, "")).hostname
    official = next((s for s in sources if s.get("id") == "F1"), {})
    cik = re.search(r"CIK0*(\d+)\.json", official.get("url", ""))
    candidates = []
    kinds = set()
    for source in sources:
        url = source.get("url", "")
        parsed = urlsplit(url)
        host = parsed.hostname
        transcript = bool(re.search(r"transcript|transcri[cç][aã]o", source.get("title", "") + " " + parsed.path, re.I))
        kind = "transcript" if transcript else "filing"
        trusted_sec = host in ("www.sec.gov", "sec.gov") and cik and f"/data/{int(cik[1])}/" in parsed.path
        trusted_issuer = issuer_host and host == issuer_host
        trusted_transcript = transcript and host in ("stockanalysis.com", "www.stockanalysis.com")
        if (kind in kinds or parsed.scheme != "https" or not (trusted_sec or trusted_issuer or trusted_transcript)
                or source.get("id") == "F1" or not AutoFetcher._valid_url(url)):
            continue
        if not transcript and not trusted_sec and not re.search(r"10-k|20-f|annual|anual|10-q|earnings|result", source.get("title", ""), re.I):
            continue
        candidates.append((source, kind, bool(trusted_sec or trusted_issuer)))
        kinds.add(kind)
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
                    if len(data) > 6_000_000:
                        return source
            if data.startswith(b"%PDF-"):
                text = OpenAIClient.extract_text(bytes(data))
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
            return {**source, "text": bounded, "basis": "primary" if primary else "transcript", "document_type": kind}
        except (requests.RequestException, ValueError, OpenAIError):
            return source
    with ThreadPoolExecutor(max_workers=2) as pool:
        hydrated = {s["id"]: s for s in pool.map(fetch, candidates)}
    return [{**source, **hydrated.get(source["id"], {}),
             "document_type": hydrated.get(source["id"], source).get("document_type",
                              "financials" if source.get("annual_financials") else "research")} for source in sources]
