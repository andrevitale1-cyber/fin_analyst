import os
import json
import base64
import re
from io import BytesIO
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import google.generativeai as genai
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import matplotlib
from database import get_db_connection # Certifique-se que o nome do arquivo/função está correto

# Configuração para ambiente servidor (sem monitor)
matplotlib.use('Agg')

router = APIRouter()

# Configuração da API do Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("A variável de ambiente GEMINI_API_KEY não foi definida.")
genai.configure(api_key=GEMINI_API_KEY)

# --- FUNÇÕES DE SUPORTE ---

def figure_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', dpi=100)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return f"data:image/png;base64,{image_base64}"

def extrair_json_da_analise(texto_analise):
    """Extrai o bloco JSON que a IA gera para os gráficos."""
    try:
        match = re.search(r'```json\s*([\s\S]*?)\s*```', texto_analise)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        print(f"Erro ao extrair JSON: {e}")
    return None

# --- GERAÇÃO DE GRÁFICOS DINÂMICOS ---

def gerar_grafico_dinamico(chart_data, empresa_nome):
    """Gera um gráfico baseado nos dados extraídos da análise."""
    if not chart_data: return None
    
    df = pd.DataFrame(chart_data)
    sns.set_theme(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Barras para Receita e Lucro
    df_melted = df.melt(id_vars='name', value_vars=['receita', 'lucro'], var_name='Métrica', value_name='Valor')
    sns.barplot(data=df_melted, x='name', y='Valor', hue='Métrica', palette=['#2563eb', '#10b981'], ax=ax1)
    
    ax1.set_title(f"Evolução Financeira: {empresa_nome}", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Valores")
    ax1.set_xlabel("Trimestres")

    return figure_to_base64(fig)

# --- ROTA DO RELATÓRIO ---

@router.get("/api/report/{item_id}", response_class=HTMLResponse)
async def generate_generic_report(item_id: int):
    # 1. BUSCA DADOS NO BANCO DE DADOS
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT empresa, periodo, conteudo FROM historico WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Análise não encontrada.")
        
        empresa, periodo, conteudo_json = row[0], row[1], row[2]
        # conteudo_json costuma ser um dict vindo do Postgres/JSONB
        analise_texto = conteudo_json.get('analise_completa', '')
        dados_notas = conteudo_json.get('data', {})
        
    finally:
        cur.close()
        conn.close()

    # 2. PROCESSA DADOS PARA GRÁFICOS
    chart_data = extrair_json_da_analise(analise_texto)
    grafico_base64 = gerar_grafico_dinamico(chart_data, empresa)

    # 3. LIMPA O TEXTO (Remove o bloco JSON do corpo do relatório HTML)
    texto_limpo = re.sub(r'```json\s*[\s\S]*?\s*```', '', analise_texto)
    texto_formatado = texto_limpo.replace("\n", "<br>").replace("**", "")

    # 4. MONTA O HTML FINAL
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Relatório: {empresa}</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; color: #1e293b; max-width: 850px; margin: 0 auto; padding: 40px; background: #f8fafc; }}
            .card {{ background: white; padding: 40px; border-radius: 12px; shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
            .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; }}
            h1 {{ color: #0f172a; margin: 0; }}
            .notas-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
            .nota-box {{ background: #f1f5f9; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e2e8f0; }}
            .nota-val {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
            .grafico {{ width: 100%; margin: 30px 0; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; }}
            .prose {{ text-align: justify; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <p style="color: #2563eb; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;">{periodo}</p>
                <h1>{empresa}</h1>
            </div>

            <div class="notas-grid">
                <div class="nota-box"><span>Receita</span><div class="nota-val">{dados_notas.get('receita_nota', '-')}</div></div>
                <div class="nota-box"><span>Lucro</span><div class="nota-val">{dados_notas.get('lucro_nota', '-')}</div></div>
                <div class="nota-box"><span>Dívida</span><div class="nota-val">{dados_notas.get('divida_nota', '-')}</div></div>
                <div class="nota-box"><span>Rentabilidade</span><div class="nota-val">{dados_notas.get('rentabilidade_nota', '-')}</div></div>
            </div>

            {f'<div class="grafico"><img src="{grafico_base64}" style="width:100%"></div>' if grafico_base64 else ''}

            <div class="prose">
                {texto_formatado}
            </div>
            
            <p style="margin-top:40px; font-size:12px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 20px;">
                Relatório gerado automaticamente por FinAnalyzer.AI. Não constitui recomendação de compra ou venda.
            </p>
        </div>
    </body>
    </html>
    """
    return html_content