import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from agents.search_client import SearchClient

class AutoFetcher:
    def __init__(self):
        # Carrega o mapa de RI do arquivo JSON
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ir_map_path = os.path.join(base_dir, "data", "ir_map.json")
        self.ir_urls = self._load_ir_map()
        self.search_client = SearchClient()

    def _load_ir_map(self):
        if os.path.exists(self.ir_map_path):
            with open(self.ir_map_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def fetch_result_pdf(self, ticker, ano, trimestre):
        ticker = ticker.upper()
        url = self.ir_urls.get(ticker)
        
        # Se não estiver no mapa, tenta uma busca heurística
        if not url:
            if ticker.isalpha() and len(ticker) <= 4:
                # Padrão provável de US Stocks (ex: MSFT, AAPL)
                url = f"https://ir.{ticker.lower()}.com/"
            else:
                # Padrão provável de empresas brasileiras
                url = f"https://ri.{ticker.lower()[:4]}.com.br/informacoes-financeiras/central-de-resultados/"
            print(f"[{ticker}] Ticker não mapeado. Tentando URL heurística: {url}")

        try:
            # Tenta acessar o portal de RI
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, timeout=15, headers=headers)
            
            if response.status_code != 200 and not ticker.isalpha():
                # Tenta uma segunda variação comum para empresas BR
                url = f"https://{ticker.lower()[:4]}.mzweb.com.br/informacoes-financeiras/central-de-resultados/"
                response = requests.get(url, timeout=15, headers=headers)
            
            if response.status_code != 200:
                # Última tentativa genérica
                url = f"https://www.google.com/search?q={ticker}+investor+relations+results+pdf"
                # Nota: Raspar o Google é complexo, aqui apenas evitamos o erro imediato 
                # ou retornamos None para o usuário saber que falhou.
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Busca por links de PDF que pareçam releases de resultados
            links = soup.find_all('a', href=True)
            
            # Filtros de busca (ex: 4T24, 4Q24, 2024)
            short_year = str(ano)[-2:]
            q_num = trimestre[0] # Pega '4' de '4T'
            patterns = [
                f"{trimestre}{short_year}", # 4T24
                f"{q_num}Q{short_year}",    # 4Q24
                f"{q_num}Q {ano}",          # 4Q 2024
                f"Q{q_num} {ano}",          # Q4 2024
                f"quarter {q_num}",         # quarter 4
                f"resultado {trimestre}",   # resultado 4T
                f"{trimestre} {ano}"        # 4T 2024
            ]

            for link in links:
                href = link['href'].lower()
                text = link.get_text().lower()
                
                # Critério base: ser PDF e conter 'release' ou 'resultado'
                is_release = ('.pdf' in href) and ('release' in href or 'resultado' in href or 'release' in text or 'resultado' in text)
                
                if is_release:
                    # Critério extra: bater com o ano/trimestre
                    if any(p.lower() in href or p.lower() in text for p in patterns) or (str(ano) in href or str(ano) in text):
                        pdf_url = urljoin(url, link['href'])
                        return pdf_url
            
            # Se não achou com filtro, pega o primeiro release que ver (fallback)
            for link in links:
                href = link['href'].lower()
                text = link.get_text().lower()
                if ('.pdf' in href) and ('release' in href or 'resultado' in href or 'release' in text or 'resultado' in text):
                    return urljoin(url, link['href'])
            
            # --- NOVO: BUSCA INTELIGENTE AUTÔNOMA ---
            print(f"SEARCH: [{ticker}] Tentando busca autônoma via Search API...")
            pdf_url = self.fetch_via_search(ticker, ano, trimestre)
            return pdf_url
        except Exception as e:
            print(f"ERROR: Erro no fetch_result_pdf: {e}")
            return None

    def fetch_via_search(self, ticker, ano, trimestre):
        """
        Usa o SearchClient para encontrar o PDF se a heurística falhar.
        """
        results = self.search_client.search_financial_reports(ticker, ano, trimestre)
        
        # Filtra os resultados para encontrar PDFs
        for res in results:
            url = res.get("url", "")
            title = res.get("title", "").lower()
            
            if url.lower().endswith(".pdf"):
                # Verifica se parece um release
                if "release" in url.lower() or "resultado" in url.lower() or "release" in title or "resultado" in title:
                    print(f"OK: [{ticker}] Encontrado via busca: {url}")
                    return url
        
        # Se não achou PDF explícito, retorna o primeiro resultado que pareça relevante
        if results:
            print(f"INFO: [{ticker}] Nenhum PDF direto no search, mas há resultados. Link Picker (Phase 2) ajudará aqui.")
            
        return None
            
    def download_pdf(self, pdf_url):
        try:
            response = requests.get(pdf_url, timeout=30)
            if response.status_code == 200:
                return response.content
            return None
        except:
            return None
