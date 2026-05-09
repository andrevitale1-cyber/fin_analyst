import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class AutoFetcher:
    def __init__(self):
        # Carrega o mapa de RI do arquivo JSON
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ir_map_path = os.path.join(base_dir, "data", "ir_map.json")
        self.ir_urls = self._load_ir_map()

    def _load_ir_map(self):
        if os.path.exists(self.ir_map_path):
            with open(self.ir_map_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def fetch_result_pdf(self, ticker):
        ticker = ticker.upper()
        url = self.ir_urls.get(ticker)
        
        # Se não estiver no mapa, tenta uma busca heurística
        if not url:
            url = f"https://ri.{ticker.lower()[:4]}.com.br/informacoes-financeiras/central-de-resultados/"
            print(f"[{ticker}] Ticker não mapeado. Tentando URL heurística: {url}")

        try:
            # Tenta acessar o portal de RI
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                # Tenta uma segunda variação comum
                url = f"https://{ticker.lower()[:4]}.mzweb.com.br/informacoes-financeiras/central-de-resultados/"
                response = requests.get(url, timeout=15)
            
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Busca por links de PDF que pareçam releases de resultados
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href'].lower()
                text = link.get_text().lower()
                # Critérios: conter 'release' ou 'resultado' e ser .pdf
                if ('.pdf' in href) and ('release' in href or 'resultado' in href or 'release' in text or 'resultado' in text):
                    pdf_url = urljoin(url, link['href'])
                    return pdf_url
            return None
        except:
            return None
            
    def download_pdf(self, pdf_url):
        try:
            response = requests.get(pdf_url, timeout=30)
            if response.status_code == 200:
                return response.content
            return None
        except:
            return None
