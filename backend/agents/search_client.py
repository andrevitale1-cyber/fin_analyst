import os
import requests
from dotenv import load_dotenv
from openai_client import OpenAIClient, OpenAIError

load_dotenv()

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
                    return results
            except (requests.RequestException, ValueError):
                pass
        try:
            return OpenAIClient().search_pdf_links(query)
        except (OpenAIError, TimeoutError):
            return []
