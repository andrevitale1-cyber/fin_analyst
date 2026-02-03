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

# Carrega variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÕES GERAIS ---
app = FastAPI(title="API Analisador Financeiro")

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
        
        # IMPORTANTE: user_id agora é TEXT para suportar Clerk
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

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro na inicialização do banco: {e}")

init_db()

# --- MODELOS ---
class UsuarioLogin(BaseModel):
    email: str
    senha: str

# --- AUXILIARES ---
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

# --- CONFIGURAÇÃO GEMINI ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

# --- ROTAS ---

@app.get("/")
def read_root():
    return {"message": "FinAnalyst Backend está Online (Clerk Compatible) 🚀"}

@app.post("/api/analyze")
async def analyze_report(
    file: UploadFile = File(...),
    empresa: str = Form(...),
    ano: str = Form(...),
    trimestre: str = Form(...),
    user_id: str = Form(...)  # ALTERADO PARA STRING (CLERK)
):
    print(f"🔄 Análise para User {user_id}: {empresa}")
    
    if not model:
        raise HTTPException(status_code=500, detail="Erro: Chave Gemini não encontrada.")

    conn = None
    try:
        contents = await file.read()
        pdf_text = extract_text_from_pdf_bytes(contents)
        
        prompt = f"""
    Você é um analista sênior de Equity Research. Analise o resultado de: {empresa} ({trimestre}/{ano}) Sua nota deve avaliar o resultado. Se a empresa for boa e o resultado ruim, a nota deverá ser penalisada. 



    ### REGRAS DE FORMATAÇÃO E ESTILO:

    - Seja pragmático, direto e focado no "Bottom-line" (Lucro Líquido e Geração de Valor).

    - NÃO use LaTeX. Escreva números como texto normal (ex: "Receita de 10 bilhões", "Margem de 20%").

    - Use no máximo duas casas decimais.

    - Se for banco/seguradora, ignore EBITDA e use métricas do setor (Margem Financeira, Índice de Basileia, etc). Reconheça que o "Resultado Financeiro" (receitas de investimentos/float) é uma parte core e operacional do negócio.

    - TODAS AS NOTAS DEVEM SER DADAS APENAS COM OS NÚMEROS INTEIROS: 1/2/3/4/5.



    ### ESTRUTURA OBRIGATÓRIA DE RESPOSTA:



    **Seção 1: Análise da Performance Core (Top Line)**

    (Analise a Receita Líquida. Cresceu? Caiu? Foi preço ou volume? O mix de produtos ajudou?)

    Apresente a Receita Líquida (Não-Financeiras) ou Prêmios Emitidos / Margem Financeira (Financeiras) e sua variação.

    Desconstrua o crescimento por segmento.

    Conecte a receita com os indicadores operacionais do setor (ex: Vendas Mesmas Lojas; Volume vs. Preço; Sinistralidade). O operacional foi um ponto forte ou fraco?

    (Para aquisições): Se relevante, identifique o crescimento orgânico.

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

    Indentifique os Drivers: Conecte o lucro final aos componentes das seções 1, 2 e 3.

    Qualifique o Lucro: Identifique fatores não recorrentes, não-caixa ou cíclicos (ex: créditos tributários, deflação/inflação de índices, Selic) que tenham impulsionado ou prejudicado o resultado.

    **Nota Seção 4: X/5**



    **Seção 5: Conclusão - Tese e Outlook**

    (Sintetize: O resultado foi Bom, Neutro ou Ruim? Qual a perspectiva futura (Guidance)?)

    Sintetize a análise de forma coesa. Comece pela conclusão principal (ex: "A empresa entregou um resultado forte/recorde..." ou "O resultado foi fraco...").

    Em seguida, explique os drivers, balanceando os fatores (ex: "...apesar de um operacional modesto, isso foi impulsionado por um resultado financeiro excepcional..." ou "...o forte crescimento operacional foi consumido por despesas financeiras...").

    Conclua sobre a tese principal que o resultado do trimestre suporta.

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
        # Salva user_id como TEXTO agora
        cur.execute(
            "INSERT INTO historico (empresa, ano, trimestre, data_criacao, resultado_json, user_id) VALUES (%s, %s, %s, NOW(), %s, %s)",
            (empresa, ano, trimestre, json.dumps(objeto_final), str(user_id))
        )
        conn.commit()
        cur.close()
        
        return objeto_final

    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.get("/api/table-data")
def get_table_data(user_id: str): # ALTERADO PARA STRING
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Busca tratando o ID como texto
        cur.execute("SELECT empresa, ano, trimestre, resultado_json FROM historico WHERE CAST(user_id AS TEXT) = %s ORDER BY empresa, ano DESC, trimestre DESC", (str(user_id),))
        rows = cur.fetchall()

        grouped_data = {}
        
        for row in rows:
            empresa = row[0]
            try:
                conteudo = json.loads(row[3])
                data_content = conteudo.get('data', {})
                
                # Helpers
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
def get_history(user_id: str): # ALTERADO PARA STRING
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

# --- ROTA DE CORREÇÃO DO BANCO (CLERK MIGRATION) ---
@app.get("/api/fix-database-clerk")
def fix_database_clerk():
    """Converte a coluna user_id de INTEGER para TEXT para aceitar IDs do Clerk"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Tenta converter a coluna. O 'USING user_id::text' garante que IDs antigos (1, 2) virem strings ("1", "2")
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