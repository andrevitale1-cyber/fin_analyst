from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from passlib.context import CryptContext
import google.generativeai as genai
import psycopg2
import os
import json
import re
import io
import asyncio
import stripe
from pypdf import PdfReader
from dotenv import load_dotenv
from report_generator import router as report_router
from agents.auto_fetcher import AutoFetcher
from agents.prompt_builder import PromptBuilder

stripe.api_key = os.getenv("STRIPE_API_KEY")
# Carrega variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÕES GERAIS ---
app = FastAPI(title="API Analisador Financeiro")

app.include_router(report_router)

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
            conn = psycopg2.connect(db_url, sslmode='require')
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
        print(f"❌ Erro Crítico de Conexão com Banco: {e}")
        raise HTTPException(status_code=500, detail="Erro ao conectar no banco de dados.")

def init_db():
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

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro na inicialização do banco: {e}")

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

# --- CONFIGURAÇÃO GEMINI ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

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
    
    if not model:
        raise HTTPException(status_code=500, detail="Erro: Chave Gemini não encontrada.")

    conn = None
    try:
        print("📄 [PASSO 2] Extraindo texto do Relatório (Limite de 30 páginas)...")
        contents = await file.read()
        pdf_text = extract_text_from_pdf_bytes(contents, max_pages=30)
        print(f"✅ [PASSO 3] Texto lido! Foram extraídos {len(pdf_text)} caracteres.")
        
        language_instruction = "IMPORTANT: Write the ENTIRE analysis in English. All section titles, labels, scores, text and conclusions must be in English.\n\n" if locale == "en" else ""

        prompt = f"""
 {language_instruction}REGRAS DE FORMATAÇÃO E ESTILO (Padrão Editorial / Equity Research Sênior):
Tom de Voz: Seja profissional, elegante, analítico e jornalístico. Crie uma narrativa fluida em vez de apenas jogar dados. Foque na geração de valor.

Formatação Visual: Utilize Tabelas em Markdown (ex: Segmento | 3T24 | 3T25 | Variação) sempre que houver quebra de receitas por segmento, linhas de crédito ou revisão de Guidance. Use bullet points para listar destaques operacionais.

Apresentação Numérica: Escreva os números por extenso com até duas casas decimais (ex: "R$ 11,87 bilhões", "aumento de 13,1%", "expansão de 0,6 p.p."). NÃO use LaTeX.

SISTEMA DE NOTAS: Todas as notas devem ser estritamente números inteiros (1, 2, 3, 4 ou 5) e seguir exatamente o formato Nota Seção X: Y/5.

ESTRUTURA OBRIGATÓRIA DE RESPOSTA:
[Parágrafo Introdutório]
(Resuma o trimestre da empresa).

Seção 1: Evolução Operacional e Top Line
(Analise o crescimento da Receita Líquida. Desconstrua o crescimento por segmento em uma tabela Markdown).
Nota Seção 1: X/5

Seção 2: Rentabilidade e Margens
(Analise o EBITDA, Margens e Despesas Operacionais).
Nota Seção 2: X/5

Seção 3: Estrutura de Capital e Gestão de Risco
(Analise a Geração de Caixa Livre, Dívida).
Nota Seção 3: X/5

Seção 4: Sumário Executivo do Lucro Líquido
(Analise o Bottom-Line).
Nota Seção 4: X/5

Seção 5: Conclusão Estratégica e Outlook
(Sintetize a análise de forma coesa).

Seção 6: Nota Final
Nota Geral: X/5

**Seção 7: Dados Estruturados para Gráficos (OBRIGATÓRIO)**
Extraia o histórico financeiro dos trimestres disponíveis EXATAMENTE no formato de um array JSON dentro de um bloco de código markdown `json ... `. Não coloque NENHUM texto antes ou depois do bloco de código json.
Chaves obrigatórias em todos os trimestres: 
"name" (nome do trimestre, ex: "3T25"), 
"receita" (valor financeiro ABSOLUTO. Ex: 664500000), 
"lucro" (Obrigatório. Valor do Lucro Líquido ABSOLUTO. Se prejuízo, negativo), 
"divida" (Obrigatório. Dívida Líquida ou Bruta. Se não houver = 0),
"ebitda" (Obrigatório. EBITDA ou Resultado Operacional. Se não houver = 0),
"margemBruta" (número percentual como float, ex: 15.5), 
"margemLiquida" (número percentual como float, ex: 10.2).

IMPORTANTE: Apenas no objeto do ÚLTIMO trimestre (o mais recente), inclua as seguintes chaves:
1. "composicao_receita": OBRIGATÓRIO. JSON detalhando a composição da receita. Subdivida se houver várias naturezas (ex: {{"Canais": {{"Físico": 100, "Web": 50}}, "Geografia": {{"Brasil": 150}}}}). Use valores absolutos.
2. "despesas_var": OBRIGATÓRIO. Lista de dicionários com a variação percentual A/A das linhas de despesa (SG&A, Administrativas, Vendas). Aumento = positivo, Queda = negativo. Se não achar no texto, extraia do DRE. Ex: [{{"nome": "Vendas", "var_pct": 5.2}}, {{"nome": "Administrativas", "var_pct": -1.5}}]. Se for impossível achar, retorne [{{"nome": "Despesas Gerais", "var_pct": 0.0}}].
    
    DADOS DO RELEASE (Use apenas o relevante):
    {pdf_text[:100000]}
        """

        print("🧠 [PASSO 4] Enviando para o Google Gemini via Streaming (sem timeout fixo)...")
        
        def _gerar_via_streaming(p: str) -> str:
            """
            Usa generate_content_stream para receber tokens incrementalmente.
            Isso evita o timeout de 60s porque a resposta chega em pedaços.
            O timeout real do SDK do Gemini é de ~240s, muito mais genéroso.
            """
            full_text = ""
            for chunk in model.generate_content(
                p,
                stream=True,
                generation_config={"temperature": 0.7}
            ):
                try:
                    full_text += chunk.text
                except Exception:
                    pass  # chunks vazios ou de controle
            return full_text
        
        tarefa_gemini = asyncio.to_thread(_gerar_via_streaming, prompt)
        # Timeout generousíssimo de 180s como última linha de defesa
        response_text = await asyncio.wait_for(tarefa_gemini, timeout=180.0)
        print("✅ [PASSO 5] O Google Gemini respondeu com sucesso! Chars recebidos:", len(response_text))
        
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

    except asyncio.TimeoutError:
        print("❌ [ERRO] Tempo limite de 180 segundos excedido!")
        raise HTTPException(status_code=504, detail="O servidor da IA demorou muito a responder. Tente com um PDF menor ou aguarde e tente novamente.")
    except Exception as e:
        erro_str = str(e)
        print(f"❌ [ERRO CRÍTICO] Falha na análise: {erro_str}")
        if "503" in erro_str or "high demand" in erro_str.lower() or "overloaded" in erro_str.lower():
            raise HTTPException(status_code=503, detail="Os servidores do Google estão temporariamente sobrecarregados. Aguarde 1 minuto e tente novamente.")
        raise HTTPException(status_code=500, detail=erro_str)
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
    
    fetcher = AutoFetcher()
    builder = PromptBuilder()
    
    # 1. Buscar PDF
    pdf_url = fetcher.fetch_result_pdf(ticker)
    if not pdf_url:
        raise HTTPException(status_code=404, detail=f"Não foi possível localizar o relatório de {ticker} automaticamente.")
    
    # 2. Download
    pdf_content = fetcher.download_pdf(pdf_url)
    if not pdf_content:
        raise HTTPException(status_code=500, detail="Erro ao baixar o relatório.")
    
    # 3. Extrair Texto
    pdf_text = extract_text_from_pdf_bytes(pdf_content, max_pages=30)
    
    # 4. Construir Prompt Profissional
    prompt = builder.build_prompt(ticker, pdf_text, locale=locale)
    
    # 5. Chamar Gemini (reutilizando a lógica de streaming)
    def _gerar_auto(p: str) -> str:
        full_text = ""
        for chunk in model.generate_content(p, stream=True, generation_config={"temperature": 0.7}):
            try: full_text += chunk.text
            except: pass
        return full_text

    try:
        tarefa_gemini = asyncio.to_thread(_gerar_auto, prompt)
        response_text = await asyncio.wait_for(tarefa_gemini, timeout=180.0)
        
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
        conn.close()
        
        return objeto_final
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    
    if not model:
        raise HTTPException(status_code=500, detail="Erro: Chave Gemini não encontrada.")

    conn = None
    try:
        print("📄 [PASSO 2] Extraindo texto do PDF (Sem limite de páginas estrito)...")
        contents = await file.read()
        texto_transcricao = extract_text_from_pdf_bytes(contents, max_pages=100)
        print(f"✅ [PASSO 3] PDF lido com sucesso! Foram extraídos {len(texto_transcricao)} caracteres.")
        
        language_instruction_call = "IMPORTANT: Write the ENTIRE summary in English. All text, labels, timestamps, insights and conclusions must be in English.\n\n" if locale == "en" else ""

        prompt = f"""
{language_instruction_call}Atue como um Analista Financeiro Sênior. Resuma o Earnings Call da {empresa} de forma ultra-objetiva.
Para cada insight, indique obrigatoriamente o minuto/timestamp aproximado extraído do texto (ex: [12:45]).

Foque exclusivamente em:
1. Expansões e Crescimento: Planos de novas lojas/unidades, entrada em novos mercados e CAPEX destinado a expansão.
2. Projeções e Guidance: Números específicos para os próximos meses/trimestres (Receita, Margens, EBITDA).
3. Tom da Gestão e Q&A: Sentimento dos executivos e as 3 perguntas mais críticas feitas pelos analistas.

Texto da Transcrição:
{texto_transcricao[:250000]}
        """

        print("🧠 [PASSO 4] Enviando para o Google Gemini via Streaming (sem timeout fixo)...")
        
        def _gerar_call_via_streaming(p: str) -> str:
            full_text = ""
            for chunk in model.generate_content(
                p,
                stream=True,
                generation_config={"temperature": 0.5}
            ):
                try:
                    full_text += chunk.text
                except Exception:
                    pass
            return full_text
        
        tarefa_gemini = asyncio.to_thread(_gerar_call_via_streaming, prompt)
        response_text = await asyncio.wait_for(tarefa_gemini, timeout=180.0)
        print("✅ [PASSO 5] O Google Gemini respondeu com sucesso! Chars:", len(response_text))
        
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

    except asyncio.TimeoutError:
        print("❌ [ERRO] Tempo limite de 60 segundos excedido!")
        raise HTTPException(status_code=504, detail="O servidor da IA demorou muito a responder. Tente novamente.")
    except Exception as e:
        erro_str = str(e)
        print(f"❌ [ERRO CRÍTICO] Falha na análise: {erro_str}")
        if "503" in erro_str or "high demand" in erro_str.lower() or "overloaded" in erro_str.lower():
            raise HTTPException(status_code=503, detail="Os servidores do Google estão temporariamente sobrecarregados. Aguarde 1 minuto e tente novamente.")
        raise HTTPException(status_code=500, detail=erro_str)
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)