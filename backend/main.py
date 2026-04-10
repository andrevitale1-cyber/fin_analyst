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

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro na inicialização do banco: {e}")

init_db()

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

    conclusao_match = re.search(r'(?:Seção 5|Conclusão).*?[\:\–\-]\s*(.*?)(?=(?:Seção 6|Nota Final|Nota Geral|\*\*Nota Geral|$))', text, re.DOTALL | re.IGNORECASE)
    conclusao = conclusao_match.group(1).strip() if conclusao_match else "Ver análise completa no texto."

    return {
        "receita_nota": get_note(r'Seção 1.*?(\d(?:[\.,]\d)?)\/5', text),
        "rentabilidade_nota": get_note(r'Seção 2.*?(\d(?:[\.,]\d)?)\/5', text),
        "divida_nota": get_note(r'Seção 3.*?(\d(?:[\.,]\d)?)\/5', text),
        "lucro_nota": get_note(r'Seção 4.*?(\d(?:[\.,]\d)?)\/5', text),
        "nota_geral": get_note(r'Nota Geral.*?(\d(?:[\.,]\d)?)\/5', text),
        "tese_investimento": conclusao.replace('*', ''),
        "chart_data": get_chart_data(text),
    }

# --- CONFIGURAÇÃO GEMINI ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
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
    user_id: str = Form(...) 
):
    print(f"🔄 Análise para User {user_id}: {empresa}")
    
    if not model:
        raise HTTPException(status_code=500, detail="Erro: Chave Gemini não encontrada.")

    conn = None
    try:
        contents = await file.read()
        pdf_text = extract_text_from_pdf_bytes(contents)
        
        prompt = f"""
 REGRAS DE FORMATAÇÃO E ESTILO (Padrão Editorial / Equity Research Sênior):
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
Extraia o histórico financeiro dos trimestres disponíveis EXATAMENTE no formato de um array JSON dentro de um bloco de código markdown.
Chaves obrigatórias em todos os trimestres: 
"name" (nome do trimestre, ex: "3T25"), 
"receita" (valor financeiro ABSOLUTO. Ex: 664500000), 
"lucro" (Obrigatório. Valor do Lucro Líquido ABSOLUTO. Se prejuízo, negativo), 
"divida" (Obrigatório. Dívida Líquida ou Bruta. Se não houver = 0),
"ebitda" (Obrigatório. EBITDA ou Resultado Operacional. Se não houver = 0),
"margemBruta" (número percentual), 
"margemLiquida" (número percentual).

IMPORTANTE: Apenas no objeto do ÚLTIMO trimestre (o mais recente), inclua as seguintes chaves:
1. "composicao_receita": OBRIGATÓRIO. JSON detalhando a composição da receita. Subdivida se houver várias naturezas (ex: {{"Canais": {{"Físico": 100, "Web": 50}}, "Geografia": {{"Brasil": 150}}}}). Use valores absolutos.
2. "despesas_var": OBRIGATÓRIO. Lista de dicionários com a variação percentual A/A das linhas de despesa (SG&A, Administrativas, Vendas). Aumento = positivo, Queda = negativo. Se não achar no texto, extraia do DRE. Ex: [{{"nome": "Vendas", "var_pct": 5.2}}, {{"nome": "Administrativas", "var_pct": -1.5}}]. Se for impossível achar, retorne [{{"nome": "Despesas Gerais", "var_pct": 0.0}}].
    
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
            "INSERT INTO historico (empresa, ano, trimestre, data_criacao, resultado_json, user_id) VALUES (%s, %s, %s, NOW(), %s, %s) RETURNING id",
            (empresa, ano, trimestre, json.dumps(objeto_final), str(user_id))
        )
        inserted_id = cur.fetchone()[0]
        objeto_final["id"] = inserted_id
        
        conn.commit()
        cur.close()
        
        return objeto_final

    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.post("/api/analyze-call")
async def analyze_earnings_call(
    file: UploadFile = File(...),
    empresa: str = Form(...),
    ano: str = Form(...),
    trimestre: str = Form(...),
    user_id: str = Form(...)
):
    print(f"🎙️ A analisar Earnings Call (PDF) para {empresa} ({trimestre}/{ano})")
    
    if not model:
        raise HTTPException(status_code=500, detail="Erro: Chave Gemini não encontrada.")

    conn = None
    try:
        # 1. Lê o ficheiro PDF da transcrição que o utilizador enviou
        contents = await file.read()
        texto_transcricao = extract_text_from_pdf_bytes(contents)
        
        # 2. Prompt focado no "Tom" da diretoria e no Q&A
        prompt = f"""
Atue como um analista financeiro sénior. Analise a seguinte transcrição da teleconferência de resultados (Earnings Call) da empresa {empresa}.

Foque a sua análise nos seguintes pontos:
1. Tom da Administração (Otimista, Cauteloso, Pessimista) e principais mensagens.
2. Guidance e Projeções Futuras mencionadas pelos executivos.
3. Principais preocupações levantadas pelos analistas na sessão de Q&A (Perguntas e Respostas).

Texto da Transcrição:
{texto_transcricao[:50000]}
        """

        # 3. Envia para o Gemini
        response = await asyncio.to_thread(model.generate_content, prompt)
        
        objeto_final = {
            "metadata": { "empresa": empresa, "periodo": f"{trimestre}/{ano}", "tipo": "Earnings Call" },
            "analise_completa": response.text,
            "data": {} 
        }

        # 4. Salva no Banco de Dados
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
        
        return objeto_final

    except Exception as e:
        print(f"❌ Erro Crítico na análise do call: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
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