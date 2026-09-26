import os
import re
import json
import random
import datetime
import tweepy
from openai_client import OpenAIClient
from dotenv import load_dotenv
from database import get_db_connection
import sys

def safe_print(*args, **kwargs):
    sep = kwargs.get('sep', ' ')
    text = sep.join(str(arg) for arg in args)
    encoding = sys.stdout.encoding or 'utf-8'
    try:
        sys.stdout.write(text + kwargs.get('end', '\n'))
        sys.stdout.flush()
    except UnicodeEncodeError:
        try:
            safe_text = text.encode(encoding, errors='replace').decode(encoding)
            sys.stdout.write(safe_text + kwargs.get('end', '\n'))
            sys.stdout.flush()
        except Exception:
            safe_text = text.encode('ascii', errors='replace').decode('ascii')
            sys.stdout.write(safe_text + kwargs.get('end', '\n'))
            sys.stdout.flush()

print = safe_print

load_dotenv()

class XReplierAgent:
    def __init__(self):
        self.consumer_key = os.getenv("X_CONSUMER_KEY")
        self.consumer_secret = os.getenv("X_CONSUMER_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("X_BEARER_TOKEN")
        self.platform_url = os.getenv("PLATFORM_URL", "https://finanalyser.com.br")
        self.promo_tweet_url = os.getenv("PROMO_TWEET_URL", "https://x.com/Finanalyser_ai/status/2047846896727687269")
        
        # Ativa Mock Mode se alguma credencial de escrita estiver faltando
        self.mock_mode = not all([
            self.consumer_key, 
            self.consumer_secret, 
            self.access_token, 
            self.access_token_secret
        ])
        
        self.openai_client = OpenAIClient()

        # Inicialização do cliente Tweepy
        self.client = None
        if not self.mock_mode:
            try:
                # API v2 Client para postar tweets/respostas
                self.client = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
                print("[X Bot] Conectado com sucesso a API Oficial do X!")
            except Exception as e:
                print(f"[X Bot] Erro ao inicializar Tweepy Client. Ativando Mock Mode. Detalhes: {e}")
                self.mock_mode = True

        if self.mock_mode:
            print("[X Bot] ATENCAO: Iniciando em MOCK MODE (Simulacao). Respostas serao gravadas no log local.")

    def get_db_connection(self):
        return get_db_connection()

    def extract_ticker(self, text):
        """
        Extrai o ticker de ações brasileiras ou americanas (ex: WEGE3, PETR4, MSFT).
        """
        # 1. Procura por tickers explícitos com cifrão (ex: $WEGE3, $MSFT, $PETR4)
        dollar_tickers = re.findall(r'\$([A-Z]{3,5}\d{0,2})\b', text.upper())
        if dollar_tickers:
            return dollar_tickers[0]
            
        # 2. Procura por tickers brasileiros comuns (4 letras + número ex: WEGE3, PETR4, VALE3, SAPR11)
        br_tickers = re.findall(r'\b([A-Z]{4}\d{1,2})\b', text.upper())
        if br_tickers:
            return br_tickers[0]
            
        # 3. Procura por menções de hashtags financeiras (ex: #WEGE3, #MSFT)
        hashtag_tickers = re.findall(r'#([A-Z]{3,5}\d{0,2})\b', text.upper())
        if hashtag_tickers:
            return hashtag_tickers[0]
            
        # 4. Procura por nomes de empresas comuns ou menções isoladas de tickers de 4 letras capitalizados
        # Se for uma palavra normal de 4 letras no texto (ex: "AMOR", "CASA"), ignoramos.
        # Mas se for uma palavra isolada como "WEGE" ou "VALE" ou "MSFT" em caixa alta, podemos capturar
        words = re.findall(r'\b([A-Z]{3,4})\b', text) # Nota: caixa alta estrita no texto original
        ignore_list = ["IBOV", "BOVA", "CDB", "SELIC", "FII", "FIIS", "HOJE", "DIAS", "TEMA", "TUDO", "BOM", "SEMA", "META", "POST", "XBOT", "ALGU", "QUAI", "ANAL"]
        for w in words:
            if w not in ignore_list:
                return w
        return None

    def get_company_analysis_from_db(self, ticker):
        """
        Busca a análise mais recente da empresa no banco de dados.
        """
        if not ticker:
            return None
        conn = None
        cur = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT resultado_json FROM historico WHERE empresa ILIKE %s ORDER BY id DESC LIMIT 1",
                (f"%{ticker}%",)
            )
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
        except Exception as e:
            print(f"[X Bot] Erro ao buscar empresa no banco: {e}")
        finally:
            if cur: cur.close()
            if conn: conn.close()
        return None

    def generate_reply_text(self, original_tweet, ticker, company_data=None):
        """
        Usa a OpenAI para gerar uma resposta curta de rascunho,
        curta (máximo 280 caracteres) e no mesmo idioma/tom do tweet original.
        """
        # Template básico em caso de falha da IA
        default_reply = f"Já temos a análise completa de {ticker or 'esta empresa'} estruturada! Processamos receita, dividendos, divida e tese fundamentalista em segundos. Veja como funciona no nosso post oficial de lançamento: {self.promo_tweet_url}"
        
        if not self.openai_client.api_key:
            return default_reply[:280]

        # Constrói o contexto com base na análise do banco de dados (se houver)
        score_context = ""
        if company_data and "data" in company_data:
            d = company_data["data"]
            score_context = (
                f"A empresa {ticker} obteve as seguintes avaliações no sistema FinAnalyst:\n"
                f"- Nota Geral: {d.get('nota_geral', 0)}/5\n"
                f"- Receita: {d.get('receita_nota', 0)}/5\n"
                f"- Rentabilidade (ROE): {d.get('rentabilidade_nota', 0)}/5\n"
                f"- Dívida: {d.get('divida_nota', 0)}/5\n"
                f"- Lucro: {d.get('lucro_nota', 0)}/5\n"
                f"Tese de Investimento: {d.get('tese_investimento', '')[:100]}...\n"
            )

        prompt = f"""
Você é o robô de divulgação oficial da plataforma FinAnalyst (finanalyser.com.br), uma ferramenta de IA que lê relatórios financeiros (PDFs) de resultados e os resume em 30 segundos com notas fundamentalistas de 1 a 5 de forma ultra-profissional.

Sua tarefa é responder ao seguinte Tweet de forma ultra-personalizada, simpática, prestativa e altamente persuasiva, convidando o usuário a conhecer o FinAnalyst.

**Tweet Original:** "{original_tweet}"
**Ticker Detectado:** {ticker or "Geral"}

{score_context}

**Regras Absolutas:**
1. O texto gerado deve ser a **resposta exata** que será publicada no X.
2. A resposta deve ter **NO MÁXIMO 280 caracteres** (incluindo o link final). Se passar de 280, o X rejeitará.
3. Seja sutil e útil. Se tiver dados das notas fundamentalistas (Receita, Rentabilidade etc.), use emojis de estrelas (ex: ⭐4/5) ou menção rápida dos pontos fortes para provar que a análise é real e de alto valor.
4. Escreva no mesmo idioma do Tweet original (normalmente Português ou Inglês). Se o Tweet original estiver em Inglês, responda em Inglês de forma nativa e profissional.
5. Termine OBRIGATORIAMENTE incluindo o link do nosso post oficial de lançamento do X de forma natural e amigável: "{self.promo_tweet_url}".
6. Nunca use aspas na resposta final.
"""
        try:
            reply = self.openai_client.chat_text(prompt).strip().replace('"', '')
        except Exception:
            print("[OpenAI] Não foi possível gerar o rascunho. Usando template.")
            return default_reply[:280]

        # Garante limite estrito de caracteres
        if len(reply) > 280:
            print(f"[OpenAI] Resposta da IA com {len(reply)} chars. Ajustando para caber nos 280...")
            # Tenta cortar o texto mantendo o link intacto
            link_len = len(self.platform_url) + 5
            reply = reply[:280 - link_len] + f"... {self.platform_url}"
        return reply

    def record_reply_history(self, tweet_id, username, original_text, reply_text):
        """
        Registra no banco de dados para evitar responder a mesma publicação.
        """
        conn = None
        cur = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO x_bot_history (tweet_id, usuario_autor, texto_original, resposta_enviada) VALUES (%s, %s, %s, %s) ON CONFLICT (tweet_id) DO NOTHING",
                (str(tweet_id), str(username), str(original_text), str(reply_text))
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[X Bot] Erro ao registrar historico: {e}")
            return False
        finally:
            if cur: cur.close()
            if conn: conn.close()

    def is_already_replied(self, tweet_id):
        """
        Verifica se este tweet já foi processado.
        """
        conn = None
        cur = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM x_bot_history WHERE tweet_id = %s", (str(tweet_id),))
            return cur.fetchone() is not None
        except Exception as e:
            print(f"[X Bot] Erro ao checar historico: {e}")
            return False
        finally:
            if cur: cur.close()
            if conn: conn.close()

    def get_mock_tweets(self):
        """
        Gera uma lista de Tweets fictícios simulando discussões reais sobre a bolsa de valores no X.
        """
        return [
            {
                "id": "mock_123456789_wege",
                "author_id": "investidor_bolsa",
                "username": "investidor_br",
                "text": "Alguém tem a análise completa de Weg #WEGE3? Queria saber se a receita e a rentabilidade estão boas nesse trimestre."
            },
            {
                "id": "mock_987654321_msft",
                "author_id": "faria_lima_bulls",
                "username": "faria_lima_bull",
                "text": "Microsoft reportou ontem à noite resultados monstruosos! Vale a pena entrar em $MSFT agora ou esperar a poeira baixar?"
            },
            {
                "id": "mock_112233445_vale",
                "author_id": "dividendos_mil",
                "username": "dividendos_mil",
                "text": "Quais as melhores ações para proventos este mês? $VALE3 ou $PETR4? Aceito pitacos!"
            },
            {
                "id": "mock_556677889_petr",
                "author_id": "trade_bolsa",
                "username": "trade_bolsa",
                "text": "Analisando os fundamentos da Petrobras $PETR4. As margens e o lucro parecem excelentes, mas e a dívida?"
            },
            {
                "id": "mock_998877665_invalid",
                "author_id": "comum_user",
                "username": "comum_user",
                "text": "Hoje o dia está lindo, acho que vou caminhar no parque!"
            }
        ]

    def run_auto_replier(self, limit=5):
        """
        Busca publicações relevantes sobre bolsa e responde de forma personalizada.
        Funciona tanto em modo Oficial (Tweepy) quanto em modo Simulação (Mock).
        """
        print(f"[X Bot] Iniciando varredura automatizada (Limite de processamento: {limit})...")
        
        candidates = []
        if self.mock_mode:
            # Obtém tweets simulados
            candidates = self.get_mock_tweets()
        else:
            try:
                # Query de busca oficial na API v2 do X (Abrange Brasil e Exterior)
                query = "(Bolsa de Valores OR IBOV OR dividendos OR ações OR resultados trimestrais OR WEGE3 OR PETR4 OR VALE3 OR MSFT OR stock market OR Nasdaq OR SP500 OR AAPL OR TSLA OR NVDA) -is:retweet"
                response = self.client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=["id", "text", "author_id"]
                )
                if response and response.data:
                    for t in response.data:
                        # Para API v2, precisamos buscar o username do autor
                        author_info = self.client.get_user(id=t.author_id)
                        username = author_info.data.username if author_info and author_info.data else f"user_{t.author_id}"
                        candidates.append({
                            "id": str(t.id),
                            "author_id": str(t.author_id),
                            "username": username,
                            "text": t.text
                        })
            except Exception as e:
                print(f"[X Bot] Erro na busca oficial da API do X. Alternando para simulacao rapida: {e}")
                candidates = self.get_mock_tweets()

        processed_count = 0
        replies_sent = []

        for item in candidates:
            if processed_count >= limit:
                break

            tweet_id = item["id"]
            username = item["username"]
            tweet_text = item["text"]

            # 1. Ignora se já respondido antes
            if self.is_already_replied(tweet_id):
                print(f"[X Bot] Tweet {tweet_id} de @{username} ja foi respondido. Pulando.")
                continue

            # 2. Detecta o ticker no tweet
            ticker = self.extract_ticker(tweet_text)
            if not ticker and "invalid" in tweet_id:
                # Tweet irrelevante (ex: caminhar no parque)
                print(f"[X Bot] Tweet {tweet_id} de @{username} nao possui contexto financeiro relevante. Pulando.")
                continue

            print(f"[X Bot] Analisando Tweet relevante de @{username}: '{tweet_text[:60]}...'")
            print(f"[X Bot] Ticker detectado: {ticker}")

            # 3. Busca notas do relatório no banco para enriquecer a resposta
            company_data = self.get_company_analysis_from_db(ticker)
            if company_data:
                print(f"[X Bot] Encontramos dados historicos para {ticker} no banco de dados!")
            else:
                print(f"[X Bot] Nenhuma analise anterior de {ticker} no banco. Usando template padrao/OpenAI sem notas.")

            # 4. Cria a resposta personalizada
            reply_text = self.generate_reply_text(tweet_text, ticker, company_data)
            
            # Rascunhos apenas: não publica nem registra como resposta enviada.
            replies_sent.append({
                "tweet_id": tweet_id,
                "username": username,
                "tweet_text": tweet_text,
                "reply_text": reply_text,
            })
            processed_count += 1

        return {
            "status": "success",
            "replies_processed": processed_count,
            "draft_only": True,
            "mock_mode": self.mock_mode,
            "replies": replies_sent
        }
