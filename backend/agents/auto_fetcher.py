import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class AutoFetcher:
    def __init__(self):
        # Mapeamento expandido para o site
        self.ir_urls = {
            "WEGE3": "https://ri.weg.net/informacoes-financeiras/central-de-resultados/",
            "ITUB4": "https://www.itau.com.br/relacoes-com-investidores/resultados-e-relatorios/central-de-resultados",
            "VALE3": "https://www.vale.com/pt/investidores/comunicados-resultados-e-relatorios",
            "PETR4": "https://www.investidorpetrobras.com.br/informacoes-ao-mercado/central-de-resultados/",
            "TOTS3": "https://ri.totvs.com/informacoes-financeiras/central-de-resultados/",
            "B3SA3": "https://ri.b3.com.br/informacoes-financeiras/central-de-resultados/",
            "BBAS3": "https://ri.bb.com.br/informacoes-financeiras/central-de-resultados/",
            "MGLU3": "https://ri.magazineluiza.com.br/informacoes-financeiras/central-de-resultados/",
            "LREN3": "https://lojasrenner.mzweb.com.br/informacoes-financeiras/central-de-resultados/",
            "ABEV3": "https://ri.ambev.com.br/informacoes-financeiras/central-de-resultados/"
        }

    def fetch_result_pdf(self, ticker):
        ticker = ticker.upper()
        url = self.ir_urls.get(ticker)
        
        if not url:
            return None

        try:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href'].lower()
                text = link.get_text().lower()
                if ('.pdf' in href) and ('release' in href or 'resultado' in href or 'release' in text or 'resultado' in text):
                    pdf_url = urljoin(url, link['href'])
                    return pdf_url
            return None
        except:
            return None
            
    def download_pdf(self, pdf_url):
        try:
            response = requests.get(pdf_url, timeout=30)
            return response.content
        except:
            return None
