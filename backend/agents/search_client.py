import os
import logging
import requests
from dotenv import load_dotenv
from openai_client import OpenAIClient, OpenAIError

load_dotenv()
logger = logging.getLogger("uvicorn.error")

class SearchError(RuntimeError):
    pass

class SearchClient:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com/search"

    def search_financial_reports(self, ticker, ano, trimestre):
        """
        Busca releases via Tavily, ou pela pesquisa web da OpenAI quando não há Tavily.
        """
        issuers = {
            "ITUB4": "Itaú Unibanco",
            "ITSA4": "Itaúsa",
            "BBAS3": "Banco do Brasil",
            "BBDC4": "Bradesco",
            "SANB11": "Santander Brasil",
            "PETR4": "Petrobras",
            "VALE3": "Vale",
            "WEGE3": "WEG",
            "VIVA3": "Vivara",
        }
        issuer = issuers.get(ticker.upper(), "")
        query = f"{ticker} {issuer} {trimestre} {ano} earnings release resultados trimestrais central de resultados PDF RI"

        if self.api_key:
            payload = {
                "api_key": self.api_key, "query": query, "search_depth": "advanced",
                "max_results": 5,
            }
            try:
                response = requests.post(self.base_url, json=payload, timeout=15)
                response.raise_for_status()
                results = response.json().get("results", [])
                if results:
                    logger.info("release_search issuer=%s year=%s quarter=%s provider=tavily candidates=%d", ticker, ano, trimestre, len(results))
                    return results
            except (requests.RequestException, ValueError):
                pass
        try:
            results = OpenAIClient().search_pdf_links(query)
            logger.info("release_search issuer=%s year=%s quarter=%s provider=openai candidates=%d", ticker, ano, trimestre, len(results))
            return results
        except (OpenAIError, TimeoutError) as exc:
            raise SearchError("O serviço de busca de resultados está indisponível. Tente novamente em instantes ou envie o PDF oficial.") from exc

    def search_transcripts(self, company, year, quarter, allow_openai=False):
        if allow_openai:
            query = f'"{company}" Q{quarter} FY{year} {quarter}Q{str(year)[-2:]} {quarter}T{str(year)[-2:]} full earnings call transcript transcrição teleconferência'
            try:
                return OpenAIClient().search_pdf_links(query, document_type="transcript")
            except (OpenAIError, TimeoutError) as exc:
                raise SearchError("O serviço de pesquisa de transcrições está indisponível. Tente novamente ou envie o PDF.") from exc
        if not self.api_key:
            return []
        queries = [
            f'"{company}" Q{quarter} {year} earnings call transcript',
            f'"{company}" {quarter}T{str(year)[-2:]} transcrição teleconferência resultados',
        ]
        results, seen, failures = [], set(), 0
        for query in queries:
            try:
                response = requests.post(self.base_url, json={
                    "api_key": self.api_key, "query": query,
                    "search_depth": "advanced", "max_results": 5,
                }, timeout=10)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict) or not isinstance(data.get("results", []), list):
                    raise ValueError("Invalid search response")
                for item in data.get("results", []):
                    url = item.get("url") if isinstance(item, dict) else None
                    if isinstance(url, str) and url not in seen:
                        results.append(item)
                        seen.add(url)
            except (requests.RequestException, ValueError, TypeError):
                failures += 1
        if failures == len(queries):
            raise SearchError("O serviço de pesquisa de transcrições está indisponível.")
        return results
