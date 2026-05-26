import os
import tweepy
from dotenv import load_dotenv

# Carrega as variáveis do .env do backend
load_dotenv()

consumer_key = os.getenv("X_CONSUMER_KEY")
consumer_secret = os.getenv("X_CONSUMER_SECRET")
access_token = os.getenv("X_ACCESS_TOKEN")
access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
bearer_token = os.getenv("X_BEARER_TOKEN")

print("Iniciando diagnostico do cliente X (Twitter)...")
print(f"Consumer Key: {consumer_key[:5]}...{consumer_key[-5:] if consumer_key else ''}")
print(f"Bearer Token: {bearer_token[:10]}...{bearer_token[-10:] if bearer_token else ''}")

try:
    client = tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    print("Cliente Tweepy instanciado com sucesso.")
    
    print("Tentando realizar busca de tweets recentes (search_recent_tweets)...")
    query = "Bolsa de Valores -is:retweet"
    response = client.search_recent_tweets(query=query, max_results=10)
    print("Sucesso na busca!")
    if response and response.data:
        print(f"Retornou {len(response.data)} tweets.")
        for t in response.data:
            print(f"- ID: {t.id} | Conteudo: {t.text[:50]}...")
    else:
        print("Busca retornou vazia (nenhum tweet recente encontrado).")
except Exception as e:
    print("\n[ERRO DETECTADO] Falha ao tentar buscar tweets:")
    print(f"Tipo do erro: {type(e)}")
    print(f"Detalhes: {e}")
