from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse 
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
import urllib.parse
from pypdf import PdfReader
from dotenv import load_dotenv
from fastapi_sso.sso.google import GoogleSSO 

# Carrega variáveis de ambiente
load_dotenv()

# Configuração Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY")

# --- CONFIGURAÇÃO DO GOOGLE SSO ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# URL de Callback (Deve ser igual ao configurado no Google Cloud)
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://api-finanalyzer.onrender.com/auth/google/callback")

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    google_sso = GoogleSSO(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
        allow_insecure_http=True 
    )
else:
    google_sso = None
    print("⚠️ Google SSO não configurado (CLIENT_ID ou CLIENT_SECRET ausentes).")

# --- CONFIGURAÇÕES DA APP ---
app = FastAPI(title="API Analisador Financeiro")

# CORS (Permitir acesso do Frontend)
origins = ["*"]  

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

# --- CONEXÃO COM BANCO DE DADOS ---
def get_db_connection():
    try:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(db_url, sslmode='require')
        else:
            conn = psycopg2.connect(host="localhost", database="dados_analise", user="postgres", password="password", port="5432")
        return conn
    except Exception as e:
        print(f"❌ Erro Crítico de Conexão: {e}")
        raise HTTPException(status_code=500, detail="Erro ao conectar no banco.")

def init_db():
    """Inicializa tabelas se não existirem"""
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
                user_id INTEGER
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

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Erro DB Init: {e}")

init_db()

# Segurança de Senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

# --- MODELOS ---
class UsuarioRegister(BaseModel):
    nome: str
    email: str
    senha: str

class UsuarioLogin(BaseModel):
    email: str
    senha: str

# --- FUNÇÕES AUXILIARES ---
def extract_text_from_pdf_bytes(file_bytes):
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler PDF: {str(e)}")

def parse_results(text):
    """Extrai notas do texto da IA via Regex"""
    def get_note(pattern, txt):
        match = re.search(pattern, txt, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', '.'))
            except:
                return 0.0
        return 0.0

    conclusao_match = re.search(r'(?:Seção 5|Conclusão).*?[\:\–\-]\s*(.*?)(?=(?:Seção 6|Nota Final|Nota Geral|\*\*Nota Geral|$))', text, re.DOTALL | re.IGNORECASE)
    conclusao = conclusao_match.group(1).strip() if conclusao_match else "Ver análise completa no texto."

    return {
        "receita_nota": get_note(r'Seção 1.*?(\d(?:[\.,]\d)?)\/5', text),
        "rentabilidade_nota": get_note(r'Seção 2.*?(\d(?:[\.,]\d)?)\/5', text),
        "divida_nota": get_note(r'Seção 3.*?(\d(?:[\.,]\d)?)\/5', text),
        "lucro_nota": get_note(r'Seção 4.*?(\d(?:[\.,]\d)?)\/5', text),
        "nota_geral": get_note(r'Nota Geral.*?(\d(?:[\.,]\d)?)\/5', text),
        "tese_investimento": conclusao.replace('*', ''),
    }

# ---------------------------------------------------
# ROTAS DE AUTENTICAÇÃO (GOOGLE + EMAIL)
# ---------------------------------------------------

@app.get("/auth/google/login")
async def google_login():
    if not google_sso:
        raise HTTPException(status_code=501, detail="Google SSO não configurado.")
    return await google_sso.get_login_redirect()

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    if not google_sso:
        raise HTTPException(status_code=501, detail="Google SSO não configurado.")
    try:
        user_google = await google_sso.verify_and_process(request)
        
        email = user_google.email
        nome = user_google.display_name or email.split("@")[0]
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verifica/Cria usuário
        cur.execute("SELECT id, nome, plano FROM usuarios WHERE email = %s", (email,))
        usuario_existente = cur.fetchone()
        
        user_id = None
        user_plano = 'free'
        
        if usuario_existente:
            user_id = usuario_existente[0]
            user_plano = usuario_existente[2] or 'free'
        else:
            # Cria conta com senha aleatória
            senha_random = os.urandom(24).hex()
            senha_hash = pwd_context.hash(senha_random)
            cur.execute(
                "INSERT INTO usuarios (nome, email, senha_hash, plano) VALUES (%s, %s, %s, 'free') RETURNING id",
                (nome, email, senha_hash)
            )
            user_id = cur.fetchone()[0]
            conn.commit()

        cur.close()
        conn.close()
        
        # Redireciona para o Frontend com os dados
        user_data = {"id": user_id, "nome": nome, "email": email, "plano": user_plano}
        user_encoded = urllib.parse.quote(json.dumps(user_data))
        
        # IMPORTANTE: URL do seu Frontend na Vercel
        FRONTEND_URL = "https://fin-analyst-olive.vercel.app" 
        return RedirectResponse(url=f"{FRONTEND_URL}/google-callback?data={user_encoded}")

    except Exception as e:
        print(f"Erro Google: {e}")
        return {"error": "Falha no login com Google"}

@app.post("/auth/register")
def registrar_usuario(usuario: UsuarioRegister):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        senha_hash = pwd_context.hash(usuario.senha)
        cur.execute("INSERT INTO usuarios (nome, email, senha_hash, plano) VALUES (%s, %s, %s, 'free') RETURNING id", (usuario.nome, usuario.email, senha_hash))
        novo_id = cur.fetchone()[0]
        conn.commit()
        return {"message": "Criado", "id": novo_id}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Email já cadastrado.")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.post("/auth/login")
def login_usuario(dados: UsuarioLogin):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nome, senha_hash, plano FROM usuarios WHERE email = %s", (dados.email,))
        usuario = cur.fetchone()
        if not usuario or not pwd_context.verify(dados.senha, usuario[2]):
            raise HTTPException(status_code=401, detail="Email ou senha incorretos.")
        
        return {"message": "OK", "usuario": {"id": usuario[0], "nome": usuario[1], "plano": usuario[3] or 'free'}}
    finally:
        cur.close()
        conn.close()

# ---------------------------------------------------
# ROTA PRINCIPAL DE ANÁLISE (IA + PROMPT)
# ---------------------------------------------------

@app.post("/api/analyze")
async def analyze_report(
    file: UploadFile = File(...),
    empresa: str = Form(...),
    ano: str = Form(...),
    trimestre: str = Form(...),
    user_id: int = Form(...) 
):
    if not model:
        raise HTTPException(status_code=500, detail="Erro: Chave API Gemini não configurada.")

    conn = None
    try:
        contents = await file.read()
        pdf_text = extract_text_from_pdf_bytes(contents)
        
        # --- PROMPT COMPLETO DA IA ---
        prompt = f"""
    Você é um analista sênior de Equity Research. Analise o resultado de: {empresa} ({trimestre}/{ano}).

    ### REGRAS DE FORMATAÇÃO E ESTILO:
    - Seja pragmático, direto e focado no "Bottom-line" (Lucro Líquido e Geração de Valor).
    - NÃO use LaTeX. Escreva números como texto normal (ex: "Receita de 10 bilhões", "Margem de 20%").
    - Use no máximo duas casas decimais.
    - Se for banco/seguradora, ignore EBITDA e use métricas do setor (Margem Financeira, Índice de Basileia, etc).
    - TODAS AS NOTAS DEVEM SER DADAS APENAS COM OS NÚMEROS INTEIROS: 1/2/3/4/5.

    ### ESTRUTURA OBRIGATÓRIA DE RESPOSTA:

    **Seção 1: Análise da Performance Core (Top Line)**
    (Analise a Receita Líquida. Cresceu? Caiu? Foi preço ou volume? O mix de produtos ajudou?)
    ...
    **Nota Seção 1: X/5**

    **Seção 2: Análise da Rentabilidade e Eficiência**
    (Analise EBITDA/Margens ou Resultado Operacional. Houve diluição de custos? Ganho de eficiência?)
    ...
    **Nota Seção 2: X/5**

    **Seção 3: Estrutura de Capital e Financeiro**
    (Analise Dívida Líquida/EBITDA, Despesas Financeiras ou Solvência/Basileia para bancos).
    ...
    **Nota Seção 3: X/5**

    **Seção 4: Análise do Lucro Líquido (Bottom-Line)**
    (Analise o Lucro Líquido. Foi limpo ou teve não-recorrentes? É sustentável?)
    ...
    **Nota Seção 4: X/5**

    **Seção 5: Conclusão - Tese e Outlook**
    (Sintetize: O resultado foi Bom, Neutro ou Ruim? Qual a perspectiva futura (Guidance)?)

    **Seção 6: Nota Final**
    (Dê uma nota geral baseada na tese).
    **Nota Geral: X/5**

    ---
    DADOS DO RELEASE (Use apenas o relevante):
    {pdf_text[:40000]}
        """

        response = await asyncio.to_thread(model.generate_content, prompt)
        dados_estruturados = parse_results(response.text)
        
        objeto_final = {
            "metadata": { "empresa": empresa, "periodo": f"{trimestre}/{ano}" },
            "data": dados_estruturados,
            "analise_completa": response.text
        }

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO historico (empresa, ano, trimestre, data_criacao, resultado_json, user_id) VALUES (%s, %s, %s, NOW(), %s, %s)",
            (empresa, ano, trimestre, json.dumps(objeto_final), user_id)
        )
        conn.commit()
        cur.close()
        
        return objeto_final

    except Exception as e:
        print(f"Erro IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

# --- DEMAIS ROTAS ---

@app.post("/api/create-checkout")
def create_checkout(dados: dict):
    # (Adicione sua lógica do Stripe aqui se necessário, mas estamos usando link direto no front)
    return {"message": "Use link direto"}

@app.get("/api/table-data")
def get_table_data(user_id: int): 
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT empresa, ano, trimestre, resultado_json FROM historico WHERE user_id = %s ORDER BY empresa, ano DESC, trimestre DESC", (user_id,))
        rows = cur.fetchall()
        grouped_data = {}
        
        for row in rows:
            empresa = row[0]
            try:
                conteudo = json.loads(row[3])
                data_content = conteudo.get('data', {})
                # ... (Lógica de processamento da tabela igual ao anterior)
                nota = data_content.get('nota_geral', 0)
                
                if empresa not in grouped_data:
                    grouped_data[empresa] = {
                        'id': empresa,
                        'empresa': empresa,
                        'nota_final': nota,
                        'notas': []
                        # ... Adicione os outros campos conforme necessário
                    }
                grouped_data[empresa]['notas'].append(nota)
            except: continue

        # Retorno simplificado para exemplo (copie sua lógica completa aqui se precisar)
        return [] 
    finally:
        cur.close()
        conn.close()

@app.get("/api/history")
def get_history(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, empresa, ano, trimestre, data_criacao, resultado_json FROM historico WHERE user_id = %s ORDER BY id DESC", (user_id,))
        rows = cur.fetchall()
        lista = []
        for row in rows:
            try:
                conteudo = json.loads(row[5])
                data_content = conteudo.get('data', {})
                lista.append({
                    "id": row[0],
                    "empresa": row[1],
                    "periodo": f"{row[3]}/{row[2]}",
                    "data": str(row[4]),
                    "nota": data_content.get("nota_geral", 0),
                    "conteudo": conteudo
                })
            except: pass
        return lista
    finally:
        cur.close()
        conn.close()

@app.delete("/api/history/{item_id}")
def delete_history(item_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM historico WHERE id = %s", (item_id,))
        conn.commit()
        return {"message": "OK"}
    finally:
        cur.close()
        conn.close()

# --- ROTA PARA CORRIGIR O BANCO (ADICIONAR PLANOS) ---
@app.get("/api/fix-database-plans")
def fix_database_plans():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Cria a coluna 'plano' se não existir
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS plano TEXT DEFAULT 'free';")
        # Cria a coluna 'plano_expira' se não existir
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS plano_expira TIMESTAMP;") 
        conn.commit()
        return {"message": "Sucesso! Tabela atualizada com colunas de plano."}
    except Exception as e:
        return {"error": f"Erro ao atualizar banco: {str(e)}"}
    finally:
        cur.close()
        conn.close()
        
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)