import os
import json
import base64
from io import BytesIO
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import google.generativeai as genai
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Configuração do Roteador FastAPI
router = APIRouter()

# Configuração da API do Gemini (Certifique-se de definir a variável de ambiente)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
genai.configure(api_key=GOOGLE_API_KEY)

# --- DADOS BRUTOS DO RELEASE (Simulação - Em produção, viria do banco) ---
# Em um cenário real, esses dados seriam extraídos do PDF e passados para esta função.
data_2t25 = {
    "metadata": {"empresa": "Multiplan", "periodo": "2T2025", "ticker": "MULT3"},
    "kpis": {
        "vendas_totais": 6300.0,  # R$ Milhões
        "receita_bruta": 741.26,
        "noi": 496.76,
        "ebitda_operacional": 460.11,
        "lucro_liquido": 264.37,
        "ffo": 292.59,
        "despesa_financeira": 168.17,
        "ocupacao": 96.1  # %
    },
    "variacoes_anuais": { # % vs 2T24
        "vendas_totais": 12.8,
        "receita_bruta": 27.2,
        "noi": 14.3,
        "ebitda_operacional": 18.1,
        "lucro_liquido": -6.2,
        "ffo": -8.2,
        "despesa_financeira": 117.2
    },
    "composicao_receita": {
        "Locação": 427.53,
        "Venda de Imóveis": 171.30,
        "Estacionamento": 84.40,
        "Serviços": 42.90,
        "Outras": 15.13
    }
}

# --- FUNÇÕES AUXILIARES DE GERAÇÃO DE GRÁFICOS ---

def figure_to_base64(fig):
    """Converte uma figura Matplotlib em uma string Base64 para inserir no HTML."""
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', dpi=100)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig) # Importante para não vazar memória
    return f"data:image/png;base64,{image_base64}"

def gerar_grafico_comparativo(data):
    """Gera gráfico de barras comparando KPIs e suas variações."""
    # Prepara os dados
    metrics = ['Receita Bruta', 'EBITDA Oper.', 'Lucro Líquido', 'FFO']
    valores = [data['kpis']['receita_bruta'], data['kpis']['ebitda_operacional'], data['kpis']['lucro_liquido'], data['kpis']['ffo']]
    variacoes = [data['variacoes_anuais']['receita_bruta'], data['variacoes_anuais']['ebitda_operacional'], data['variacoes_anuais']['lucro_liquido'], data['variacoes_anuais']['ffo']]

    df = pd.DataFrame({'Métrica': metrics, 'Valor (R$ Mi)': valores, 'Variação (%)': variacoes})

    # Configura o Seaborn
    sns.set_theme(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Gráfico de Barras (Valores Absolutos)
    sns.barplot(x='Métrica', y='Valor (R$ Mi)', data=df, palette="Blues_d", ax=ax1)
    ax1.set_ylabel('R$ Milhões', fontsize=12, fontweight='bold')
    ax1.set_xlabel('', fontsize=1) # Esconde label X
    ax1.set_title(f"Desempenho Financeiro Principal - {data['metadata']['empresa']} ({data['metadata']['periodo']})", fontsize=14, fontweight='bold', pad=20)

    # Adiciona valores nas barras
    for p in ax1.patches:
        ax1.annotate(f'R$ {p.get_height():.1f}', (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', xytext=(0, 10), textcoords='offset points', fontsize=10, fontweight='bold')

    # Cria o segundo eixo Y (Variações %)
    ax2 = ax1.twinx()
    
    # Gráfico de Linha (Variações %)
    sns.lineplot(x='Métrica', y='Variação (%)', data=df, marker='o', color='orange', linewidth=3, markersize=10, ax=ax2, label='Variação Anual (%)')
    ax2.set_ylabel('Variação Anual (%)', fontsize=12, fontweight='bold', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')
    ax2.grid(False) # Remove grid do segundo eixo

    # Adiciona valores na linha
    for i, v in enumerate(variacoes):
        ax2.annotate(f'{v:+.1f}%', (i, v), xytext=(0, 15), textcoords='offset points', ha='center', color='orange', fontweight='bold')

    fig.tight_layout()
    return figure_to_base64(fig)

def gerar_grafico_pizza_receita(data):
    """Gera gráfico de pizza com a composição da receita."""
    comp_receita = data['composicao_receita']
    labels = list(comp_receita.keys())
    sizes = list(comp_receita.values())
    
    # Define cores (paleta azul profissional)
    colors = ['#1f77b4', '#4682b4', '#87ceeb', '#add8e6', '#b0c4de']

    fig, ax = plt.subplots(figsize=(8, 7))
    
    # Cria a pizza
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    
    # Formata os textos
    plt.setp(texts, size=11, fontweight='medium')
    plt.setp(autotexts, size=10, fontweight='bold', color='white')
    
    ax.set_title(f"Composição da Receita Bruta (Total: R$ {sum(sizes):.1f} Mi)", fontsize=13, fontweight='bold')
    fig.tight_layout()
    
    return figure_to_base64(fig)

# --- FUNÇÃO PRINCIPAL DE CHAMADA DO GEMINI ---

def obter_analise_gemini(data):
    """Envia os dados estruturados para o Gemini e retorna a análise em Markdown."""
    
    # Constrói o prompt (baseado no prompt definido na resposta do Claude)
    prompt = f"""
**Comando:** Atue como um Analista Financeiro Sênior especializado em Investimentos (CFA). Analise os dados financeiros e operacionais fornecidos abaixo, extraídos do release de resultados da {data['metadata']['empresa']} ({data['metadata']['ticker']}) referente ao {data['metadata']['periodo']}.

Sua análise deve ser estruturada e focar em interpretar os "porquês" por trás dos números, não apenas repeti-los.

**Dados do Trimestre ({data['metadata']['periodo']}):**
- Receita Bruta: R$ {data['kpis']['receita_bruta']:.2f} Mi ({data['variacoes_anuais']['receita_bruta']:+.1f}% vs 2T24)
- Vendas Totais nos Shoppings: R$ {data['kpis']['vendas_totais']/1000:.1f} Bi ({data['variacoes_anuais']['vendas_totais']:+.1f}% vs 2T24)
- NOI (Net Operating Income): R$ {data['kpis']['noi']:.2f} Mi ({data['variacoes_anuais']['noi']:+.1f}% vs 2T24)
- Margem NOI: {data['kpis']['noi']/data['kpis']['receita_bruta']*100:.1f}% (Recorde histórico)
- EBITDA de Propriedades: R$ {data['kpis']['ebitda_operacional']:.2f} Mi ({data['variacoes_anuais']['ebitda_operacional']:+.1f}% vs 2T24)
- Lucro Líquido: R$ {data['kpis']['lucro_liquido']:.2f} Mi ({data['variacoes_anuais']['lucro_liquido']:+.1f}% vs 2T24)
- FFO (Funds From Operations): R$ {data['kpis']['ffo']:.2f} Mi ({data['variacoes_anuais']['ffo']:+.1f}% vs 2T24)
- Despesas Financeiras Líquidas: R$ {data['kpis']['despesa_financeira']:.2f} Mi ({data['variacoes_anuais']['despesa_financeira']:+.1f}% vs 2T24)
- Taxa de Ocupação: {data['kpis']['ocupacao']:.1f}%

**Estrutura Obrigatória da Análise (Markdown):**

## 1. Destaques Operacionais e Eficiência
(Analise a força das vendas, a ocupação e como a empresa atingiu margens recordes, citando a queda de 30,8% nas despesas de propriedades).

## 2. Desempenho Financeiro e o Impacto do Juro
(Explique o paradoxo: por que a Receita e o EBITDA operacional cresceram forte, mas o Lucro Líquido e o FFO caíram? Foque no impacto do aumento das despesas financeiras).

## 3. Estratégia de Receitas e Geração de Valor
(Interprete o salto de 134,7% na venda de imóveis. É sustentável? Analise também o crescimento do Lucro por Ação (LPA) de 36,9% nos últimos 12 meses devido à recompra de ações).

## 4. Conclusão e Perspectivas
(Resuma se o trimestre foi bom ou ruim na ótica do investidor de longo prazo e quais os principais riscos e oportunidades para o próximo semestre).
"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash') # Modelo rápido e eficiente
        response = model.generate_content(prompt)
        
        # Converte Markdown para HTML básico (parágrafos e títulos)
        analise_html = response.text.replace("## ", "<h3>").replace("\n\n", "</p><p>").replace("**", "<strong>")
        # Fecha os títulos h3 que ficaram abertos
        analise_html = analise_html.replace("<h3>", "</h3><h3>").replace("</h3>", "", 1).replace("<h3>", "</h3><h3>")
        # Envolve tudo em parágrafos se não começar com título
        if not analise_html.startswith("<h3>"):
            analise_html = "<p>" + analise_html + "</p>"
            
        return analise_html

    except Exception as e:
        print(f"Erro na chamada do Gemini: {e}")
        return "<p>Erro ao gerar a análise analítica com a IA.</p>"

# --- ROTAS DA API ---

@router.get("/api/report/{item_id}", response_class=HTMLResponse)
async def generate_integrated_report(item_id: int):
    """
    Endpoint que gera o relatório executivo completo, concatenando gráficos Python e análise Gemini.
    Nota: Em produção, item_id buscaria dados do banco. Aqui usamos os dados simulados 'data_2t25'.
    """
    
    # Em produção, você faria: data = buscar_dados_no_banco(item_id)
    data = data_2t24_simulada = data_2t25 # Usando dados simulados

    if not data:
        raise HTTPException(status_code=404, detail="Análise não encontrada.")

    # 1. GERA OS GRÁFICOS (ETAPA 1 - PYTHON)
    grafico_comp_base64 = gerar_grafico_comparativo(data)
    grafico_pizza_base64 = gerar_grafico_pizza_receita(data)

    # 2. OBTÉM A ANÁLISE DA IA (ETAPA 2 - GEMINI)
    analise_ai_html = obter_analise_gemini(data)

    # 3. MONTA O HTML FINAL CONCATENADO (ETAPA 3)
    
    # Define o template HTML (estilo executivo, limpo e profissional)
    html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Executivo: {data['metadata']['empresa']} - {data['metadata']['periodo']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px;
            background-color: #f9f9f9;
        }}
        .container {{
            background-color: #fff;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }}
        .header {{
            border-b: 2px solid #e0e0e0;
            padding-bottom: 20px;
            margin-b: 30px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        .header-title {{
            margin: 0;
        }}
        .ticker {{
            font-size: 14px;
            color: #2563eb;
            font-weight: bold;
            text-transform: uppercase;
            background-color: #eff6ff;
            padding: 4px 10px;
            border-radius: 20px;
        }}
        h1 {{
            font-size: 32px;
            color: #111;
            margin: 10px 0 5px 0;
        }}
        .periodo {{
            color: #666;
            font-size: 18px;
            margin: 0;
        }}
        h2 {{
            font-size: 22px;
            color: #111;
            margin-top: 40px;
            margin-bottom: 15px;
            border-left: 5px solid #2563eb;
            padding-left: 15px;
        }}
        h3 {{
            font-size: 18px;
            color: #2563eb;
            margin-top: 30px;
            margin-bottom: 10px;
        }}
        p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        strong {{
            color: #111;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-top: 30px;
        }}
        .chart-box {{
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            background-color: #fff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }}
        .chart-box img {{
            width: 100%;
            height: auto;
        }}
        .kpi-panel {{
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 20px;
        }}
        .kpi-title {{
            font-size: 12px;
            font-weight: bold;
            color: #64748b;
            text-transform: uppercase;
            margin-bottom: 15px;
        }}
        .kpi-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        .kpi-item:last-child {{
            border-bottom: none;
        }}
        .kpi-label {{
            font-size: 14px;
            color: #1e293b;
        }}
        .kpi-value {{
            font-size: 16px;
            font-weight: bold;
            color: #111;
        }}
        .status-good {{
            color: #10b981;
        }}
        .status-warn {{
            color: #f59e0b;
        }}
        @media print {{
            body {{
                padding: 0;
                background-color: #fff;
            }}
            .container {{
                box-shadow: none;
                padding: 0;
            }}
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            .break-inside-avoid {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-title">
                <span class="ticker">{data['metadata']['ticker']}</span>
                <h1>Análise Executiva de Resultados</h1>
                <p className="periodo">{data['metadata']['empresa']} - {data['metadata']['periodo']}</p>
            </div>
            <div className="date">
                <p className="periodo">{pd.Timestamp.now().strftime('%d/%m/%Y')}</p>
            </div>
        </div>

        <p>Este documento apresenta uma análise integrada do release de resultados da {data['metadata']['empresa']}, combinando a visualização de dados operacionais státicos gerados pelo sistema com a interpretação analítica de Inteligência Artificial.</p>

        <h2>1. Visualização de Dados e KPIs Principais</h2>
        
        <div class="dashboard-grid">
            <div class="chart-box">
                <img src="{grafico_comp_base64}" alt="Gráfico Comparativo de Desempenho">
            </div>
            <div class="kpi-panel">
                <div class="kpi-title">Painel de Metas (2T25)</div>
                <div class="kpi-item">
                    <span class="kpi-label">Vendas Totais (Shoppings)</span>
                    <span class="kpi-value">R$ {data['kpis']['vendas_totais']/1000:.1f} Bi</span>
                </div>
                <div class="kpi-item">
                    <span class="kpi-label">Taxa de Ocupação</span>
                    <span class="kpi-value">{data['kpis']['ocupacao']:.1f}%</span>
                </div>
                 <div class="kpi-item">
                    <span class="kpi-label">Margem NOI</span>
                    <span class="kpi-value status-good">{data['kpis']['noi']/data['kpis']['receita_bruta']*100:.1f}%</span>
                </div>
                 <div class="kpi-item">
                    <span class="kpi-label">Margem EBITDA Prop.</span>
                    <span class="kpi-value status-good">84,6%</span>
                </div>
                 <div class="kpi-item">
                    <span class="kpi-label">Despesa Financ. (Custo)</span>
                    <span class="kpi-value status-warn">R$ {data['kpis']['despesa_financeira']:.1f} Mi</span>
                </div>
            </div>
        </div>

        <div class="dashboard-grid" style="grid-template-columns: 1fr 1fr; margin-top: 20px;">
             <div class="chart-box">
                <img src="{grafico_pizza_base64}" alt="Composição da Receita Bruta">
            </div>
            <div class="chart-box flex items-center justify-center p-8 bg-slate-50 border border-slate-100 rounded-xl">
                 <p style="text-align: center; color: #64748b; font-style: italic;">"A eficiência operacional atingiu nível histórico, com a queda de 30,8% nas despesas de propriedades, mas o cenário macroeconômico de juros altos pressionou o resultado financeiro final."</p>
            </div>
        </div>

        <div class="break-inside-avoid">
            <h2>2. Análise Analítica (Gemini AI)</h2>
            <div class="prose">
                {analise_ai_html}
            </div>
        </div>

        <div style="margin-top: 50px; border-top: 1px solid #e0e0e0; padding-top: 20px; text-align: center; color: #999; font-size: 12px;">
            Este relatório foi gerado automaticamente integrando análises státicas em Python e Inteligência Artificial Generativa. As opiniões expressas na seção 2 são geradas pela IA e não constituem recomendação de investimento.
        </div>

    </div>
</body>
</html>
"""
    return html_content