import os
import requests
from dotenv import load_dotenv

load_dotenv()

class SearchClient:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com/search"

    def search_financial_reports(self, ticker, ano, trimestre):
        """
        Realiza uma busca por releases de resultados usando a API do Tavily.
        """
        if not self.api_key:
            print("WARN: TAVILY_API_KEY não configurada. Pulando busca inteligente.")
            return []

        query = f"release de resultados {ticker} {trimestre} {ano} filetype:pdf"
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "include_domains": [],
            "exclude_domains": [],
            "max_results": 5
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=15)
            if response.status_code == 200:
                results = response.json().get("results", [])
                # Retorna lista de dicts com title, url, content
                return results
            else:
                print(f"ERROR: Erro na busca Tavily: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"ERROR: Exceção na busca Tavily: {e}")
            return []
