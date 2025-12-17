from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from passlib.context import CryptContext
import google.generativeai as genai
import psycopg2
import os
import json
import re
import io
import asyncio
from pypdf import PdfReader
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÕES GERAIS ---
app = FastAPI(title="API Analisador Financeiro")

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de Segurança (Senha)
# Requer bcrypt==4.0.1 para funcionar sem erros
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

# --- BANCO DE DADOS (POSTGRESQL - Docker) ---
DB_HOST = "localhost"
DB_NAME = "dados_analise"
DB_USER = "andrevitale"
DB_PASS = "palmeiras"
DB_PORT = "5432"

# --- MODELOS DE DADOS ---
class UsuarioRegister(BaseModel):
    nome: str
    email: str
    senha: str

class UsuarioLogin(BaseModel):
    email: str
    senha: str

# --- FUNÇÕES DE BANCO DE DADOS ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar no banco: {e}")
        raise HTTPException(status_code=500, detail="Erro de conexão com banco de dados")

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Tabela Histórico
        cur.execute('''
            CREATE TABLE IF NOT EXISTS historico (
                id SERIAL PRIMARY KEY,
                empresa TEXT,
                ano TEXT,
                trimestre TEXT,
                data_criacao TEXT,
                resultado_json TEXT
            );
        ''')

        # Tabela Usuários
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
        print("Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"Erro na inicialização: {e}")

init_db()

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

# --- ROTAS DE AUTENTICAÇÃO ---

@app.post("/api/register")
def registrar_usuario(usuario: UsuarioRegister):
    conn = None
    try:
        # AQUI OCORRE O ERRO SE O BCRYPT ESTIVER NA VERSÃO ERRADA
        senha_hash = pwd_context.hash(usuario.senha)
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
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
        finally:
            cur.close()
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Erro no Registro: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.post("/api/login")
def login_usuario(dados: UsuarioLogin):
    print(f"--- TENTATIVA DE LOGIN: {dados.email} ---")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, nome, senha_hash FROM usuarios WHERE email = %s", (dados.email,))
        usuario = cur.fetchone()
        cur.close()
        
        if not usuario:
            print("Resultado: Email não encontrado.")
            raise HTTPException(status_code=401, detail="Email não cadastrado.")
        
        id_db, nome_db, senha_hash_db = usuario
        
        # Verifica a senha
        senha_valida = pwd_context.verify(dados.senha, senha_hash_db)
        
        if not senha_valida:
            print("Resultado: SENHA INCORRETA.")
            raise HTTPException(status_code=401, detail="Senha incorreta.")

        print("Resultado: LOGIN SUCESSO.")
        return {"message": "Login OK", "usuario": {"id": id_db, "nome": nome_db}}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERRO CRÍTICO NO LOGIN: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

# --- ROTAS DE ANÁLISE ---

@app.post("/api/analyze")
async def analyze_report(
    file: UploadFile = File(...),
    empresa: str = Form(...),
    ano: str = Form(...),
    trimestre: str = Form(...)
):
    print(f"Recebendo análise para: {empresa} - {trimestre}/{ano}")
    conn = None
    try:
        contents = await file.read()
        pdf_text = extract_text_from_pdf_bytes(contents)
        
        # PROMPT COMPLETO DO GEMINI
        prompt = f"""
    Você é um analista sênior. Analise o resultado de: {empresa} ({trimestre}/{ano}).
    ### 📈 Prompt: Análise Pragmática de Resultados Trimestrais (Foco no Bottom-Line & Outlook)

    REGRAS DE FORMATAÇÃO:
    - NÃO use formatação LaTeX ou símbolos matemáticos (como $ valor $) para números.
    - Escreva os números como texto normal. e porcentagens com o "%"
    - Exemplo Errado: A receita foi de $10M (+20\%)$.
    - Exemplo Correto: A receita foi de 10M (+20%).
    - use no maximo duas casas decimais (915.504.525 milhares de Dólares Taiwaneses deve virar: "915.5 bilhões de NTD")

**👨‍💼 Papel do Modelo:**
Você é um Analista de Equity Research sênior, pragmático e focado em resultados. Sua análise deve ser concisa (aprox. 20 a 30 linhas de texto corrido + tópicos), balanceada, mas com foco na tese de investimento que justifica o "bottom line" (o lucro líquido) reportado pela companhia. Sua principal habilidade é desconstruir os números (operacional, financeiro, não recorrentes) para entender como a empresa chegou ao resultado final e qual narrativa (positiva ou negativa) ele suporta para o mercado.

**🎯 Objetivo:**
Gerar uma análise de resultados para o **{empresa}** referente ao **{trimestre}** de **{ano}**, que identifique as principais alavancas (positivas ou negativas) do trimestre. A análise deve ir além dos números principais, usando-os para construir a tese principal que o mercado irá repercutir.

**🧠 Calibração Setorial Mandatória (Etapa 0):**
Antes de aplicar o roteiro, identifique o setor da empresa. O roteiro de análise deve ser adaptado:
* **Empresas Não-Financeiras (Indústria, Varejo, Comm.):** Foco no EBITDA e na separação clara entre performance operacional (custos, despesas) e resultado financeiro (dívida).
* **Empresas Financeiras (Bancos, Seguradoras, Holdings):**
    * *Métrica de Rentabilidade:* Não use EBITDA. Utilize métricas específicas (ex: Resultado Operacional, Margem Financeira/NII, Índice Combinado para seguradoras).
    * *Resultado Financeiro:* Reconheça que as receitas de investimentos/float são parte operacional do negócio.
    * *Solvência:* Foque em índices regulatórios (ex: Basileia, Solvência).

**📥 Fonte de Dados:**
Utilize o texto fornecido abaixo (Release de Resultados/ITR).

---

**⚙️ Roteiro de Análise Estruturada:**

**Seção 1: Análise da Performance Core (Top Line)**
(Apresente a Receita Líquida ou Prêmios/Margem Financeira e sua variação YoY/QoQ. Desconstrua o crescimento por segmento ou unidade de negócio. O volume/preço ou mix ajudou? Conecte com o cenário macro se relevante.)
...
**Nota Seção 1: X/5**

**Seção 2: Análise da Rentabilidade e Eficiência Operacional**
(Apresente a métrica de rentabilidade adequada: EBITDA ou Resultado Operacional e sua variação. Analise a Margem correspondente. Decomponha a margem: O que pressionou ou aliviou os custos e despesas? Houve ganho de eficiência?)
...
**Nota Seção 2: X/5**

**Seção 3: Estrutura de Capital e Resultado Financeiro**
(Para Não-Financeiras: Analise o peso da dívida, despesas com juros e alavancagem (Dívida Líq./EBITDA). Para Financeiras: Analise a solidez patrimonial, PDD (Provisão para Devedores Duvidosos) e índices de capital.)
...
**Nota Seção 3: X/5**

**Seção 4: Análise do Lucro Líquido (Bottom-Line)**
(Apresente o Lucro Líquido e sua variação. Identifique os Drivers conectando às seções anteriores. **Crucial:** Qualifique a qualidade do lucro. Foi limpo? Foi impulsionado por não-recorrentes (ex: créditos fiscais, venda de ativos) ou é um lucro operacional sustentável?)
...
**Nota Seção 4: X/5**

**Seção 5: Conclusão - Tese e Outlook (Perspectivas)**
(Sintetize a análise de forma coesa em dois blocos:
1.  **A Tese do Trimestre:** Resuma se o resultado foi bom, neutro ou ruim e o porquê, coloque os números para justificar
2.  **Outlook e Guidance:** Analise o que a gestão falou sobre o futuro. O *guidance* (metas anuais) foi mantido, elevado ou revisado para baixo? O tom para os próximos trimestres é otimista ou cauteloso? O resultado atual facilita ou dificulta o atingimento das metas do ano?)

**Seção 6: Nota Final (Nota IA do Trimestre)**
(Com base na sua conclusão e no outlook, atribua uma nota final (ELA DEVE SER UM NUMERO INTEIRO DE 1 A 5).)
**Nota Geral: X/5** (Adjetivo)
*(Escala: 1 = Muito Ruim 🔴, 2 = Ruim 🟠, 3 = Regular 🟡, 4 = Bom 🟢, 5 = Excelente 🚀)*
    
    TEXTO DO DOCUMENTO:
    {pdf_text[:30000]}
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
            "INSERT INTO historico (empresa, ano, trimestre, data_criacao, resultado_json) VALUES (%s, %s, %s, NOW(), %s)",
            (empresa, ano, trimestre, json.dumps(objeto_final))
        )
        conn.commit()
        cur.close()
        
        return objeto_final

    except Exception as e:
        print(f"Erro na análise: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

# --- ROTAS DE LEITURA ---

@app.get("/api/history")
def get_history():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, empresa, ano, trimestre, data_criacao, resultado_json FROM historico ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()

        lista = []
        for row in rows:
            try:
                conteudo_json = json.loads(row[5])
                dados = conteudo_json.get("data", {})
                nota = dados.get("nota_geral") or 0
                lista.append({
                    "id": row[0],
                    "empresa": row[1],
                    "periodo": f"{row[3]}/{row[2]}",
                    "data": str(row[4]),
                    "nota": nota,
                    "conteudo": conteudo_json
                })
            except:
                pass
        return lista
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.get("/api/table-data")
def get_table_data():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Busca o JSON (a mala cheia de dados)
        cur.execute("SELECT empresa, ano, trimestre, resultado_json FROM historico ORDER BY empresa, ano DESC, trimestre DESC")
        rows = cur.fetchall()
        cur.close()

        print(f"--- DEBUG TABELA: Encontrei {len(rows)} registros no banco. ---")

        grouped_data = {}
        
        for row in rows:
            empresa = row[0]
            # Funçãozinha interna para garantir que NADA quebre se o numero vier estranho
            def safe_float(val):
                try:
                    if val is None: return 0.0
                    if isinstance(val, (int, float)): return float(val)
                    # Troca virgula por ponto e remove letras se tiver
                    clean_str = str(val).replace(',', '.')
                    return float(clean_str)
                except:
                    return 0.0

            try:
                # Tenta abrir a mala (JSON)
                conteudo = json.loads(row[3])
                data_content = conteudo.get('data', {})
                
                # Extrai as notas com segurança total
                nota_geral = safe_float(data_content.get('nota_geral'))
                receita = safe_float(data_content.get('receita_nota'))
                lucro = safe_float(data_content.get('lucro_nota'))
                divida = safe_float(data_content.get('divida_nota'))
                roe = safe_float(data_content.get('rentabilidade_nota'))
                
                # Agrupa os dados (Lógica de Tabela Agregada)
                if empresa not in grouped_data:
                    grouped_data[empresa] = {
                        'empresa': empresa,
                        'notas': [],
                        'ultimo_ano': row[1],
                        'ultimo_trimestre': row[2],
                        'ultima_nota': nota_geral,
                        'last_receita': receita,
                        'last_lucro': lucro,
                        'last_divida': divida,
                        'last_roe': roe
                    }
                grouped_data[empresa]['notas'].append(nota_geral)
                
            except Exception as e:
                print(f"ERRO CRÍTICO ao processar empresa {empresa}: {e}")
                # Mesmo com erro, vamos tentar mostrar o que deu (Opcional: continue)
                continue

        # Formata para o Frontend
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
        
        print(f"--- DEBUG TABELA: Retornando {len(table_data)} linhas para o site. ---")
        return table_data

    except Exception as e:
        print(f"ERRO GERAL NA TABELA: {e}")
        return []
    finally:
        if conn: conn.close()

@app.delete("/api/history/{item_id}")
def delete_history_item(item_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM historico WHERE id = %s", (item_id,))
        conn.commit()
        cur.close()
        return {"message": "Deletado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.get("/api/users_debug")
def list_users():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, senha_hash FROM usuarios")
        users = cur.fetchall()
        cur.close()
        return {"usuarios_cadastrados": users}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)