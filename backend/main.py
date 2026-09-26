from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from passlib.context import CryptContext
from openai_client import OpenAIClient, OpenAIError
import psycopg2
import os
import json
import re
import io
import asyncio
import stripe
from pypdf import PdfReader
from dotenv import load_dotenv
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

# Carrega variáveis de ambiente
load_dotenv()

from report_generator import router as report_router
from agents.auto_fetcher import AutoFetcher
from agents.prompt_builder import PromptBuilder
from agents.x_bot_router import router as x_bot_router

stripe.api_key = os.getenv("STRIPE_API_KEY")

# --- CONFIGURAÇÕES GERAIS ---
app = FastAPI(title="API Analisador Financeiro")

app.include_router(report_router)
app.include_router(x_bot_router)

# --- CONFIGURAÇÃO DO CORS ---
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONEXÃO COM O BANCO DE DADOS ---
def get_db_connection():
    try:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            if "?schema=" in db_url:
                db_url = db_url.split("?schema=")[0]
            conn = psycopg2.connect(db_url)
        else:
            conn = psycopg2.connect(
                host="localhost",
                database="dados_analise",
                user="postgres",
                password="password",
                port="5432"
            )
        return conn
    except Exception as e:
        print(f"[DB] Erro Critico de Conexao com Banco: {e}")
        raise HTTPException(status_code=500, detail="Erro ao conectar no banco de dados.")

def init_db():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS historico (
                id SERIAL PRIMARY KEY,
                empresa TEXT,
                ano TEXT,
                trimestre TEXT,
                data_criacao TEXT,
                resultado_json TEXT,
                user_id TEXT 
            );
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                nome TEXT,
                plano TEXT DEFAULT 'free',
                plano_expira TIMESTAMP
            );
        ''')

        # Tabela de trial: registra o início do período gratuito por user_id (Clerk)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS trial_users (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                trial_start TIMESTAMP NOT NULL DEFAULT NOW()
            );
        ''')

        # Tabela de histórico do bot do X para evitar spam e duplicatas
        cur.execute('''
            CREATE TABLE IF NOT EXISTS x_bot_history (
                id SERIAL PRIMARY KEY,
                tweet_id TEXT UNIQUE NOT NULL,
                usuario_autor TEXT,
                texto_original TEXT,
                resposta_enviada TEXT,
                data_resposta TIMESTAMP DEFAULT NOW()
            );
        ''')

        conn.commit()
        print("[DB] Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"[DB] Erro na inicializacao do banco: {e}")
    finally:
        if cur:
            try: cur.close()
            except: pass
        if conn:
            try: conn.close()
            except: pass

init_db()

# --- AUXILIARES ---
def extract_text_from_pdf_bytes(file_bytes, max_pages=30):
    """
    Lê o PDF, mas limita-se às primeiras 'max_pages' para não explodir 
    a memória RAM (OOM Kill) nos servidores gratuitos do Render.
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        
        # Otimização: Lê apenas até ao limite de páginas estipulado
        for i, page in enumerate(reader.pages):
            if i >= max_pages:
                print(f"⚠️ Limite de {max_pages} páginas atingido. Ignorando o resto para poupar RAM.")
                break
            
            # Extrai o texto da página atual e adiciona
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
                
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao extrair texto do PDF: {str(e)}")
    
def parse_results(text):
    def get_note(pattern, txt):
        match = re.search(pattern, txt, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', '.'))
            except:
                return 0.0
        return 0.0

    def get_chart_data(txt):
        try:
            m = re.search(r"```json\s*([\s\S]*?)\s*```", txt or "", re.IGNORECASE)
            if not m: return []
            raw = json.loads(m.group(1))
            if not isinstance(raw, list): return []
            cleaned = []
            for item in raw:
                if not isinstance(item, dict): continue
                def to_float(v, default=0.0):
                    try:
                        s = str(v).strip()
                        if not s or s.lower() == 'null' or s.lower() == 'none': return default
                        return float(s.replace(',', '.'))
                    except: return default
                
                receita = to_float(item.get("receita"))
                if receita == 0: continue
                
                cleaned.append({
                    "name": item.get("name") or item.get("periodo") or item.get("label") or "",
                    "receita": receita,
                    "lucro": to_float(item.get("lucro")),
                    "divida": to_float(item.get("divida")),
                    "ebitda": to_float(item.get("ebitda")),
                    "margemBruta": to_float(item.get("margemBruta")),
                    "margemLiquida": to_float(item.get("margemLiquida")),
                    "segmentos": item.get("segmentos", []),
                    "composicao_receita": item.get("composicao_receita", {}), 
                    "despesas_var": item.get("despesas_var", [])
                })
            return cleaned
        except: return []

    # Captura a Conclusão/Tese de Investimento (Seção 5)
    conclusao_match = re.search(r'(?:Seção 5|Conclusão).*?[\:\–\-]?\s*(.*?)(?=(?:Seção 6|Nota Final|Nota Geral|\*\*Nota Geral|$))', text, re.DOTALL | re.IGNORECASE)
    conclusao = conclusao_match.group(1).strip() if conclusao_match else "Análise concluída. Ver detalhes no relatório."

    # Se a conclusão capturada for muito curta ou falhar, tenta pegar o parágrafo inicial
    if len(conclusao) < 10:
        intro_match = re.match(r'^(.*?)(?=Seção 1)', text, re.DOTALL | re.IGNORECASE)
        if intro_match:
            conclusao = intro_match.group(1).strip()

    return {
        "receita_nota": get_note(r'Nota Seção 1:.*?(\d(?:[\.,]\d)?)\/5', text) or get_note(r'Seção 1.*?(\d(?:[\.,]\d)?)\/5', text),
        "rentabilidade_nota": get_note(r'Nota Seção 2:.*?(\d(?:[\.,]\d)?)\/5', text) or get_note(r'Seção 2.*?(\d(?:[\.,]\d)?)\/5', text),
        "divida_nota": get_note(r'Nota Seção 3:.*?(\d(?:[\.,]\d)?)\/5', text) or get_note(r'Seção 3.*?(\d(?:[\.,]\d)?)\/5', text),
        "lucro_nota": get_note(r'Nota Seção 4:.*?(\d(?:[\.,]\d)?)\/5', text) or get_note(r'Seção 4.*?(\d(?:[\.,]\d)?)\/5', text),
        "nota_geral": get_note(r'Nota Geral:.*?(\d(?:[\.,]\d)?)\/5', text) or get_note(r'Nota Geral.*?(\d(?:[\.,]\d)?)\/5', text),
        "tese_investimento": conclusao.replace('*', '').strip(),
        "chart_data": get_chart_data(text),
    }

TRIAL_DAYS = 7  # Duração do trial gratuito em dias

# --- ROTAS ---
@app.get("/")
def read_root():
    return {"message": "FinAnalyst Backend está Online (Clerk Compatible) 🚀"}

@app.post("/api/register-trial")
def register_trial(user_id: str = Form(...)):
    """
    Registra o início do trial para um novo usuário.
    Se o usuário já tem trial registrado, apenas retorna os dados existentes.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Tenta inserir; se já existir, ignora (ON CONFLICT DO NOTHING)
        cur.execute(
            "INSERT INTO trial_users (user_id, trial_start) VALUES (%s, NOW()) ON CONFLICT (user_id) DO NOTHING",
            (str(user_id),)
        )
        conn.commit()
        
        # Busca a data de início do trial
        cur.execute("SELECT trial_start FROM trial_users WHERE user_id = %s", (str(user_id),))
        row = cur.fetchone()
        if row:
            trial_start = row[0]
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            trial_end = trial_start.replace(tzinfo=timezone.utc) + timedelta(days=TRIAL_DAYS)
            days_left = max(0, (trial_end - now).days)
            is_active = now < trial_end
            return {
                "trial_start": trial_start.isoformat(),
                "trial_end": trial_end.isoformat(),
                "days_left": days_left,
                "is_trial_active": is_active
            }
        return {"error": "Erro ao registrar trial"}
    except Exception as e:
        print(f"Erro ao registrar trial: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.get("/api/check-access")
def check_access(user_id: str, is_premium: bool = False):
    """
    Verifica se o usuário tem acesso à plataforma.
    Retorna: status (trial_active | trial_expired | premium), days_left, trial_start, trial_end
    """
    if is_premium:
        return {"status": "premium", "days_left": None, "has_access": True}
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT trial_start FROM trial_users WHERE user_id = %s", (str(user_id),))
        row = cur.fetchone()
        
        if not row:
            # Usuário nunca registrou trial — registra agora
            cur.execute(
                "INSERT INTO trial_users (user_id, trial_start) VALUES (%s, NOW()) ON CONFLICT (user_id) DO NOTHING",
                (str(user_id),)
            )
            conn.commit()
            cur.execute("SELECT trial_start FROM trial_users WHERE user_id = %s", (str(user_id),))
            row = cur.fetchone()
        
        from datetime import datetime, timezone, timedelta
        trial_start = row[0]
        now = datetime.now(timezone.utc)
        trial_end = trial_start.replace(tzinfo=timezone.utc) + timedelta(days=TRIAL_DAYS)
        days_left = max(0, (trial_end - now).days)
        is_active = now < trial_end
        
        return {
            "status": "trial_active" if is_active else "trial_expired",
            "has_access": is_active,
            "days_left": days_left,
            "trial_start": trial_start.isoformat(),
            "trial_end": trial_end.isoformat()
        }
    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.post("/api/analyze")
async def analyze_report(
    file: UploadFile = File(...),
    empresa: str = Form(...),
    ano: str = Form(...),
    trimestre: str = Form(...),
    user_id: str = Form(...),
    locale: str = Form(default="pt")
):
    print(f"🔄 [PASSO 1] Iniciando Análise de Relatório (PDF) para User {user_id}: {empresa}")
    
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise HTTPException(status_code=500, detail="Chave OPENAI_API_KEY não encontrada")

    conn = None
    try:
        print("📄 [PASSO 2] Preparando Relatório para IA (Upload Direto)...")
        contents = await file.read()
        
        prompt = PromptBuilder().build_prompt(empresa, "[ARQUIVO PDF ANEXADO]", locale=locale)
        response_text = await asyncio.wait_for(
            asyncio.to_thread(OpenAIClient().analyze_document, prompt, pdf_bytes=contents),
            timeout=180.0,
        )

        if not response_text.strip():
            raise HTTPException(status_code=500, detail="A IA retornou uma resposta vazia. Tente novamente.")
        
        print("⚙️ [PASSO 6] Parseando os resultados para JSON...")
        dados_estruturados = parse_results(response_text)
        
        objeto_final = {
            "metadata": { "empresa": empresa, "periodo": f"{trimestre}/{ano}" },
            "data": dados_estruturados,
            "analise_completa": response_text
        }

        print("💾 [PASSO 7] Salvando no Banco de Dados...")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO historico (empresa, ano, trimestre, data_criacao, resultado_json, user_id) VALUES (%s, %s, %s, NOW(), %s, %s) RETURNING id",
            (empresa, ano, trimestre, json.dumps(objeto_final), str(user_id))
        )
        inserted_id = cur.fetchone()[0]
        objeto_final["id"] = inserted_id
        
        conn.commit()
        cur.close()
        
        print(f"🎉 [PASSO 8] Análise concluída! ID: {inserted_id}. Retornando ao Frontend.")
        return objeto_final

    except (asyncio.TimeoutError, TimeoutError):
        print("❌ [ERRO] Tempo limite de 180 segundos excedido!")
        raise HTTPException(status_code=504, detail="O servidor da IA demorou muito a responder. Tente com um PDF menor ou aguarde e tente novamente.")
    except HTTPException:
        raise
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    except Exception:
        raise HTTPException(status_code=500, detail="Não foi possível concluir a análise. Tente novamente.") from None
    finally:
        if conn: conn.close()

@app.post("/api/analyze-auto")
async def analyze_report_auto(
    ticker: str = Form(...),
    ano: str = Form(...),
    trimestre: str = Form(...),
    user_id: str = Form(...),
    locale: str = Form(default="pt")
):
    print(f"🚀 [AUTO] Iniciando Análise Automática para {ticker}")
    
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise HTTPException(status_code=500, detail="Chave OPENAI_API_KEY não encontrada")

    fetcher = AutoFetcher()
    builder = PromptBuilder()
    
    try:
        document = await asyncio.wait_for(
            asyncio.to_thread(fetcher.fetch_result_pdf, ticker, ano, trimestre), timeout=180.0,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except (asyncio.TimeoutError, TimeoutError):
        raise HTTPException(status_code=504, detail="A busca demorou muito. Faça o upload manual do PDF.") from None
    if not document:
        raise HTTPException(status_code=404, detail=f"Não foi possível localizar o relatório de {ticker}. Faça o upload manual do PDF.")
    
    prompt = builder.build_prompt(ticker, "[ARQUIVO PDF ANEXADO]", locale=locale)
    conn = None
    try:
        response_text = await asyncio.wait_for(
            asyncio.to_thread(OpenAIClient().analyze_document, prompt,
                              pdf_bytes=document.pdf_bytes, pdf_text=document.text),
            timeout=180.0,
        )

        # 6. Parse e Salvar
        dados_estruturados = parse_results(response_text)
        objeto_final = {
            "metadata": { "empresa": ticker, "periodo": f"{trimestre}/{ano}" },
            "data": dados_estruturados,
            "analise_completa": response_text
        }

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO historico (empresa, ano, trimestre, data_criacao, resultado_json, user_id) VALUES (%s, %s, %s, NOW(), %s, %s) RETURNING id",
            (ticker, ano, trimestre, json.dumps(objeto_final), str(user_id))
        )
        inserted_id = cur.fetchone()[0]
        objeto_final["id"] = inserted_id
        conn.commit()
        cur.close()
        
        # Fonte apenas na resposta HTTP; o formato persistido continua intacto.
        objeto_final["source"] = {"name": document.source, "url": document.url}
        return objeto_final
    except (asyncio.TimeoutError, TimeoutError):
        raise HTTPException(status_code=504, detail="O servidor da IA demorou muito a responder. Tente novamente.") from None
    except HTTPException:
        raise
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    except Exception:
        raise HTTPException(status_code=500, detail="Não foi possível concluir a análise. Tente novamente.") from None
    finally:
        if conn:
            conn.close()

@app.post("/api/analyze-call")
async def analyze_earnings_call(
    file: UploadFile = File(...),
    empresa: str = Form(...),
    ano: str = Form(...),
    trimestre: str = Form(...),
    user_id: str = Form(...),
    locale: str = Form(default="pt")
):
    print(f"🎙️ [PASSO 1] Iniciando análise de Call para {empresa} ({trimestre}/{ano})")
    
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise HTTPException(status_code=500, detail="Chave OPENAI_API_KEY não encontrada")

    conn = None
    try:
        print("📄 [PASSO 2] Preparando Transcrição para IA (Upload Direto)...")
        contents = await file.read()
        
        texto_transcricao = "[ARQUIVO PDF ANEXADO]"

        language_instruction_call = "IMPORTANT: Write the ENTIRE summary in English. All text, labels, timestamps, insights and conclusions must be in English.\n\n" if locale == "en" else ""

        prompt = f"""
{language_instruction_call}Atue como um Analista Financeiro Sênior. Resuma o Earnings Call da {empresa} de forma ultra-objetiva.
Para cada insight, indique obrigatoriamente o minuto/timestamp aproximado extraído do texto (ex: [12:45]).
Texto da Transcrição:
{texto_transcricao[:250000]}
        """

        response_text = await asyncio.wait_for(
            asyncio.to_thread(OpenAIClient().analyze_document, prompt, pdf_bytes=contents),
            timeout=180.0,
        )

        if not response_text.strip():
            raise HTTPException(status_code=500, detail="A IA retornou uma resposta vazia. Tente novamente.")
        
        objeto_final = {
            "metadata": { "empresa": empresa, "periodo": f"{trimestre}/{ano}", "tipo": "Earnings Call" },
            "analise_completa": response_text,
            "data": {} 
        }

        print("💾 [PASSO 6] Salvando no Banco de Dados...")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO historico (empresa, ano, trimestre, data_criacao, resultado_json, user_id) VALUES (%s, %s, %s, NOW(), %s, %s) RETURNING id",
            (empresa, ano, trimestre, json.dumps(objeto_final), str(user_id))
        )
        inserted_id = cur.fetchone()[0]
        objeto_final["id"] = inserted_id
        
        conn.commit()
        cur.close()
        
        print(f"🎉 [PASSO 7] Análise concluída! ID: {inserted_id}. Retornando ao Frontend.")
        return objeto_final

    except (asyncio.TimeoutError, TimeoutError):
        print("❌ [ERRO] Tempo limite de 180 segundos excedido!")
        raise HTTPException(status_code=504, detail="O servidor da IA demorou muito a responder. Tente novamente.")
    except HTTPException:
        raise
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    except Exception:
        raise HTTPException(status_code=500, detail="Não foi possível concluir a análise. Tente novamente.") from None
    finally:
        if conn: conn.close()
    
@app.get("/api/table-data")
def get_table_data(user_id: str): 
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT empresa, ano, trimestre, resultado_json FROM historico WHERE CAST(user_id AS TEXT) = %s ORDER BY empresa, ano DESC, trimestre DESC", (str(user_id),))
        rows = cur.fetchall()

        grouped_data = {}
        for row in rows:
            empresa = row[0]
            try:
                conteudo = json.loads(row[3])
                data_content = conteudo.get('data', {})
                
                def safe_float(val):
                    try:
                        if val is None or val == "": return 0.0
                        return float(str(val).replace(',', '.').replace('R$', '').replace('%', '').strip())
                    except: return 0.0

                nota_geral = safe_float(data_content.get('nota_geral'))
                
                if empresa not in grouped_data:
                    grouped_data[empresa] = {
                        'id': empresa,
                        'empresa': empresa,
                        'ano': data_content.get('ano', row[1]),
                        'trimestre': data_content.get('trimestre', row[2]),
                        'ultimo_ano': row[1],
                        'ultimo_trimestre': row[2],
                        'ultima_nota': nota_geral,
                        'last_receita': safe_float(data_content.get('receita_nota')),
                        'last_lucro': safe_float(data_content.get('lucro_nota')),
                        'last_divida': safe_float(data_content.get('divida_nota')),
                        'last_roe': safe_float(data_content.get('rentabilidade_nota')),
                        'notas': []
                    }
                grouped_data[empresa]['notas'].append(nota_geral)
            except Exception as e:
                continue

        table_data = []
        for empresa, data in grouped_data.items():
            notas = data['notas']
            soma = sum(notas)
            qtde = len(notas)
            
            table_data.append({
                'id': empresa,
                'empresa': empresa,
                'ano': data['ultimo_ano'],
                'trimestre': data['ultimo_trimestre'],
                'nota_final': data['ultima_nota'],
                'soma_total': round(soma, 2),
                'qtde_tri': qtde,
                'media': round(soma / qtde if qtde > 0 else 0, 2),
                'last_analysed_quarter': f"{data['ultimo_trimestre']}/{data['ultimo_ano']}",
                'receita_nota': data['last_receita'],
                'lucro_nota': data['last_lucro'],
                'divida_nota': data['last_divida'],
                'rentabilidade_nota': data['last_roe']
            })
        
        return table_data
    except Exception as e:
        print(f"Erro tabela: {e}")
        return []
    finally:
        cur.close()
        conn.close()

@app.get("/api/history")
def get_history(user_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, empresa, ano, trimestre, data_criacao, resultado_json FROM historico WHERE CAST(user_id AS TEXT) = %s ORDER BY id DESC", (str(user_id),))
        rows = cur.fetchall()
        
        lista = []
        for row in rows:
            try:
                conteudo = json.loads(row[5])
                data_content = conteudo.get('data', {})
                nota_raw = data_content.get("nota_geral", 0)
                try: nota = float(str(nota_raw).replace(',', '.'))
                except: nota = 0.0

                lista.append({
                    "id": row[0],
                    "empresa": row[1],
                    "periodo": f"{row[3]}/{row[2]}",
                    "data": str(row[4]),
                    "nota": nota,
                    "conteudo": conteudo
                })
            except: pass
        return lista
    finally:
        cur.close()
        conn.close()

@app.delete("/api/history/{item_id}")
def delete_history_item(item_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM historico WHERE id = %s", (item_id,))
        conn.commit()
        return {"message": "Deletado"}
    finally:
        cur.close()
        conn.close()

@app.get("/api/fix-database-clerk")
def fix_database_clerk():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE historico ALTER COLUMN user_id TYPE TEXT USING user_id::text;")
        conn.commit()
        return {"message": "Sucesso! Banco de dados atualizado para aceitar usuários do Clerk."}
    except Exception as e:
        return {"error": f"Erro ou coluna já convertida: {str(e)}"}
    finally:
        cur.close()
        conn.close()

# Rascunhos do X são gerados sob demanda; sem agendamento automático.

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
