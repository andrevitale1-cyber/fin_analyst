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

stripe.api_key = os.getenv("STRIPE_API_KEY")

# Carrega variáveis de ambiente (para rodar localmente)
load_dotenv()

# --- CONFIGURAÇÕES GERAIS ---
app = FastAPI(title="API Analisador Financeiro")

# --- CONFIGURAÇÃO DO CORS ---
origins = ["*"]  # Libera acesso total (Vercel -> Render)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Permite todos os cabeçalhos
)
# ---------------------------------------------------

# --- ROTA: CRIAR LINK DE PAGAMENTO ---
@app.post("/api/create-checkout")
def create_checkout(dados: dict):
    user_id = dados.get("user_id")
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': os.getenv("STRIPE_PRICE_ID"), # ID que você pegou no site do Stripe
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url='https://seu-site.vercel.app/dashboard?success=true',
            cancel_url='https://seu-site.vercel.app/pricing?canceled=true',
            client_reference_id=str(user_id), # Para sabermos quem pagou depois
        )
        return {"url": checkout_session.url}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Erro ao criar pagamento")

# --- ROTA TEMPORÁRIA: ATIVAR PLANO (SIMPLIFICADA) ---
# O jeito certo é usar Webhooks, mas para começar rápido:
@app.post("/api/activate-pro-temp")
def activate_pro(dados: dict):
    # ATENÇÃO: Em produção real, isso deve ser protegido ou feito via Webhook do Stripe
    user_id = dados.get("user_id")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE usuarios SET plano = 'pro' WHERE id = %s", (user_id,))
        conn.commit()
        return {"message": "Plano ativado!"}
    finally:
        cur.close()
        conn.close()

@app.get("/")
def read_root():
    return {"message": "FinAnalyst Backend está Online 🚀"}

# Segurança de Senha (Hash)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    print("⚠️ AVISO: GEMINI_API_KEY não encontrada. A análise de IA falhará.")
    model = None

# --- CONEXÃO INTELIGENTE COM O BANCO DE DADOS ---
def get_db_connection():
    try:
        # Verifica se estamos na nuvem (Render)
        db_url = os.getenv("DATABASE_URL")
        
        if db_url:
            # Conexão Nuvem
            conn = psycopg2.connect(db_url, sslmode='require')
        else:
            # Conexão Local (Docker no seu PC ou Fallback)
            conn = psycopg2.connect(
                host="localhost",
                database="dados_analise",
                user="postgres", # Ajuste comum local
                password="password", # Ajuste comum local
                port="5432"
            )
        return conn
    except Exception as e:
        print(f"❌ Erro Crítico de Conexão com Banco: {e}")
        raise HTTPException(status_code=500, detail="Erro ao conectar no banco de dados.")

def init_db():
    """Cria as tabelas se elas não existirem"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Tabela de Histórico
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

        # Tabela de Usuários
        cur.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                nome TEXT
            );
        ''')

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro na inicialização do banco (pode ser ignorado se já existir): {e}")

# Inicializa o banco ao ligar o servidor
init_db()

# --- MODELOS DE DADOS (Pydantic) ---

class UsuarioRegister(BaseModel):
    nome: str
    email: str
    # --- ATUALIZAÇÃO DE SEGURANÇA E CORREÇÃO DO ERRO 72 BYTES ---
    senha: str = Field(..., min_length=8, max_length=72, description="Senha segura entre 8 e 72 caracteres")

    @validator('senha')
    def validar_complexidade(cls, v):
        # Regras de mercado padrão
        if not re.search(r'[A-Z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra maiúscula.')
        if not re.search(r'[a-z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra minúscula.')
        if not re.search(r'[0-9]', v):
            raise ValueError('A senha deve conter pelo menos um número.')
        if not re.search(r'[\W_]', v):
            raise ValueError('A senha deve conter pelo menos um caractere especial (ex: !@#$).')
        return v

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
    """Extrai as notas do texto gerado pela IA usando Regex"""
    def get_note(pattern, txt):
        match = re.search(pattern, txt, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                # Troca vírgula por ponto para o Python entender
                return float(match.group(1).replace(',', '.'))
            except:
                return 0.0
        return 0.0

    # Tenta achar a conclusão no texto
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

# --- ROTAS DE AUTENTICAÇÃO (CORRIGIDAS PARA /auth) ---

@app.post("/auth/register")
def registrar_usuario(usuario: UsuarioRegister):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        senha_hash = pwd_context.hash(usuario.senha)
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s) RETURNING id",
            (usuario.nome, usuario.email, senha_hash)
        )
        novo_id = cur.fetchone()[0]
        conn.commit()
        return {"message": "Usuário criado!", "id": novo_id}
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
        cur.execute("SELECT id, nome, senha_hash FROM usuarios WHERE email = %s", (dados.email,))
        usuario = cur.fetchone()
        
        # Verifica se usuário existe E se a senha bate
        if not usuario or not pwd_context.verify(dados.senha, usuario[2]):
            raise HTTPException(status_code=401, detail="Email ou senha incorretos.")
        
        return {"message": "Login OK", "usuario": {"id": usuario[0], "nome": usuario[1]}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# --- ROTA DE ANÁLISE (O CÉREBRO DA IA) ---

@app.post("/api/analyze")
async def analyze_report(
    file: UploadFile = File(...),
    empresa: str = Form(...),
    ano: str = Form(...),
    trimestre: str = Form(...),
    user_id: int = Form(...) 
):
    print(f"🔄 Iniciando análise para User {user_id}: {empresa} - {trimestre}/{ano}")
    
    if not model:
        raise HTTPException(status_code=500, detail="Erro de configuração: Chave API do Gemini não encontrada.")

    conn = None
    try:
        # 1. Ler o PDF
        contents = await file.read()
        pdf_text = extract_text_from_pdf_bytes(contents)
        
        # 2. O PROMPT COMPLETO (Instrução para o Gemini)
        prompt = f"""
    Você é um analista sênior de Equity Research. Analise o resultado de: {empresa} ({trimestre}/{ano}).

    ### REGRAS DE FORMATAÇÃO E ESTILO:
    - Seja pragmático, direto e focado no "Bottom-line" (Lucro Líquido e Geração de Valor).
    - NÃO use LaTeX. Escreva números como texto normal (ex: "Receita de 10 bilhões", "Margem de 20%").
    - Use no máximo duas casas decimais.
    - Se for banco/seguradora, ignore EBITDA e use métricas do setor (Margem Financeira, Índice de Basileia, etc).
    - AS NOTAS DEVEM SER DADAS APENAS COM NÚMEROS INTEIROS (1,2,3,4,5)
    
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

        # 3. Chamar a IA
        response = await asyncio.to_thread(model.generate_content, prompt)
        
        # 4. Processar a resposta (Extrair notas)
        dados_estruturados = parse_results(response.text)
        
        objeto_final = {
            "metadata": { "empresa": empresa, "periodo": f"{trimestre}/{ano}" },
            "data": dados_estruturados,
            "analise_completa": response.text
        }

        # 5. Salvar no Banco
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
        print(f"❌ Erro na análise: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

# --- ROTA DE LEITURA DA TABELA (FILTRADA POR USUÁRIO) ---
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
            
            # --- FUNÇÃO DE PROTEÇÃO ---
            def safe_float(val):
                try:
                    if val is None or val == "": return 0.0
                    if isinstance(val, (int, float)): return float(val)
                    clean = str(val).replace(',', '.').replace('R$', '').replace('%', '').strip()
                    return float(clean)
                except:
                    return 0.0

            try:
                conteudo = json.loads(row[3])
                data_content = conteudo.get('data', {})
                
                nota_geral = safe_float(data_content.get('nota_geral'))
                receita = safe_float(data_content.get('receita_nota'))
                lucro = safe_float(data_content.get('lucro_nota'))
                divida = safe_float(data_content.get('divida_nota'))
                roe = safe_float(data_content.get('rentabilidade_nota'))
                
                if empresa not in grouped_data:
                    grouped_data[empresa] = {
                        'id': empresa,
                        'empresa': empresa,
                        'ano': data_content.get('ano', row[1]),
                        'trimestre': data_content.get('trimestre', row[2]),
                        'ultimo_ano': row[1],
                        'ultimo_trimestre': row[2],
                        'ultima_nota': nota_geral,
                        'last_receita': receita,
                        'last_lucro': lucro,
                        'last_divida': divida,
                        'last_roe': roe,
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
            media = soma / qtde if qtde > 0 else 0
            
            table_data.append({
                'id': empresa,
                'empresa': empresa,
                'ano': data['ultimo_ano'],
                'trimestre': data['ultimo_trimestre'],
                'nota_final': data['ultima_nota'],
                'soma_total': round(soma, 2),
                'qtde_tri': qtde,
                'media': round(media, 2),
                'last_analysed_quarter': f"{data['ultimo_trimestre']}/{data['ultimo_ano']}",
                'receita_nota': data['last_receita'],
                'lucro_nota': data['last_lucro'],
                'divida_nota': data['last_divida'],
                'rentabilidade_nota': data['last_roe']
            })
        
        return table_data
    except Exception as e:
        print(f"Erro ao ler tabela: {e}")
        return []
    finally:
        cur.close()
        conn.close()

# --- ROTA DE HISTÓRICO (FILTRADA POR USUÁRIO) ---
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
                
                nota_raw = data_content.get("nota_geral", 0)
                try: 
                    if isinstance(nota_raw, str): nota = float(nota_raw.replace(',', '.'))
                    else: nota = float(nota_raw)
                except: nota = 0.0

                lista.append({
                    "id": row[0],
                    "empresa": row[1],
                    "periodo": f"{row[3]}/{row[2]}",
                    "data": str(row[4]),
                    "nota": nota,
                    "conteudo": conteudo
                })
            except:
                pass
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
        return {"message": "Deletado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# --- ROTA TEMPORÁRIA PARA ARRUMAR O BANCO ---
@app.get("/api/fix-database")
def fix_database():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Adiciona a coluna user_id se ela não existir
        cur.execute("ALTER TABLE historico ADD COLUMN IF NOT EXISTS user_id INTEGER;")
        conn.commit()
        return {"message": "Banco de dados atualizado com sucesso! Coluna user_id criada."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    # Pega a porta do ambiente (Render) ou usa 10000 como padrão
    port = int(os.environ.get("PORT", 10000))
    # '0.0.0.0' é essencial para funcionar no Docker e no Render
    uvicorn.run(app, host="0.0.0.0", port=port)
@app.get("/api/fix-database-plans")
def fix_database_plans():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 'free' ou 'pro'
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS plano TEXT DEFAULT 'free';")
        # Data que o plano expira
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS plano_expira TIMESTAMP;") 
        conn.commit()
        return {"message": "Tabela preparada para assinaturas!"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()
