import sys
import os

# Adiciona o diretório backend ao path para poder importar agents
sys.path.append(os.path.join(os.getcwd(), "backend"))

from agents.auto_fetcher import AutoFetcher

def test_search():
    fetcher = AutoFetcher()
    ticker = "WEGE3"
    ano = "2024"
    trimestre = "4T"
    
    print(f"--- Testando busca para {ticker} {trimestre}/{ano} ---")
    url = fetcher.fetch_result_pdf(ticker, ano, trimestre)
    
    if url:
        print(f"OK: Sucesso! Link encontrado: {url}")
    else:
        print("FAIL: Nenhum link encontrado (verifique se a TAVILY_API_KEY está no .env)")

if __name__ == "__main__":
    test_search()
