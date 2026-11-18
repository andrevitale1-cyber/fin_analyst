"""Private, durable Premium quarterly expansions using the saved detailed analyst."""
import hashlib
import json
import logging
import os
import uuid
from time import monotonic
from threading import Event, Thread
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from account_limits import plan_for, reserve_usage, complete_usage, cancel_usage
from report_auth import require_report_user

AGENT_ID = 'agent_7685ffaa065e40e9af807b73f00b1fe9a3d76fd716a847ee84'
stop = Event()
# Versioned with the code so the saved agent never runs on stale market or content rules.
DETAILED_REQUIREMENTS_PT = """Estas exigências complementam suas instruções salvas e prevalecem em caso de conflito. Use somente o documento e o contexto de mercado verificado fornecidos; não invente números, consenso, metas ou citações. Escreva entre 1.000 e 3.000 palavras, proporcional ao material do documento; fique abaixo de 1.000 apenas quando a fonte for limitada, sem preencher espaço com repetições.
Use exatamente estas seções, nesta ordem, com títulos Markdown (##): Resumo em números; Visão geral do trimestre; Receita e indicadores operacionais; Margens e custos; Resultado financeiro, impostos e lucro; Caixa, capital de giro e endividamento; Alocação de capital e remuneração ao acionista; Comentários da gestão; Guidance e perspectivas; Nuances e pontos de atenção; Métricas para acompanhar nos próximos resultados; Conclusão. Entre Métricas e Conclusão, a reação do mercado não usa título ##: comece-a exatamente com a linha **Reação do mercado:** (em inglês, **Market reaction:**), pois o sistema insere a tabela de preços logo abaixo dela.
Resumo em números: tabela Markdown curta (6 a 8 linhas) com receita, principal segmento ou KPI do negócio, margem bruta, lucro operacional, lucro líquido e lucro por ação diluído. Ponha moeda e escala no cabeçalho (por exemplo Indicador (US$ bi)) e use a mesma escala em todas as linhas. Quando a empresa divulgar medidas ajustadas/não-GAAP, use as colunas Indicador | GAAP | Não-GAAP | Var. anual | Var. trimestral (variações da medida GAAP, ou das duas quando divergirem); sem medidas ajustadas, use Indicador | Trimestre | Var. anual | Var. trimestral. Caixa, FCL e dívida ficam na seção de caixa. Quando o documento trouxer a série de 4 a 8 trimestres, inclua em Receita ou em Margens uma tabela curta de tendência (receita, margem, KPI principal) para mostrar se o trimestre é ponto fora da curva.
Números: em português, use vírgula decimal e escala em bilhões ou milhões com 1 ou 2 casas (US$ 57,0 bi, nunca 57,006); traga os valores do trimestre com comparação anual e, quando divulgada, trimestral; margens em p.p.; acumulado do ano ou LTM só quando identificado. Em toda tabela e texto informe moeda, escala (por exemplo R$ milhões), período e base de comparação, e confira que o mesmo número bate em todas as seções. Use tabelas Markdown quando houver pelo menos três linhas comparáveis (segmentos, KPIs, DRE resumida); fora delas, escreva parágrafos que expliquem causa e consequência, não listas de números.
KPIs: escolha-os pelo modelo de negócio da empresa.
{metric_menu}
Margens e custos: explique o que pressionou ou ajudou SG&A, pessoal, matéria-prima, energia, frete e inflação, separando efeito preço, volume e mix quando o documento permitir.
Resultado financeiro, impostos e lucro: decomponha o resultado financeiro (juros, câmbio, derivativos, ganhos com participações), a alíquota efetiva e créditos fiscais, e diga quanto da variação do lucro vem da operação e quanto vem dessas linhas. Quando houver medidas não-GAAP com diferença relevante, apresente aqui a ponte em tabela Markdown, com colunas Item | Lucro operacional | Lucro líquido (e LPA quando divulgado): a linha GAAP, cada item da conciliação da empresa com sinal e valor (SBC, amortização de intangíveis adquiridos, ganhos ou perdas com participações, reestruturação, efeito fiscal) e a linha não-GAAP em negrito. Depois, um parágrafo dizendo quais ajustes são recorrentes (o SBC contínuo é custo real) e quais são pontuais, e por que o não-GAAP ficou acima ou abaixo do GAAP.
Caixa, capital de giro e endividamento: abra com uma tabela Markdown com colunas para o trimestre e o mesmo trimestre do ano anterior e as linhas Fluxo de caixa operacional, Fluxo de caixa de investimento (capex, aquisições, títulos), Fluxo de caixa de financiamento (recompras, dividendos, dívida), Fluxo de caixa livre (na definição da empresa) e Variação do caixa, usando só as linhas divulgadas. Em seguida, um parágrafo sobre capital de giro (recebíveis, estoques, fornecedores) e um sobre balanço (caixa e aplicações, dívida bruta, caixa ou dívida líquida, alavancagem, custo, vencimentos e covenants quando divulgados). Caixa operacional abaixo do lucro não é negativo por si só: explique a diferença pelos componentes (capital de giro em fase de crescimento, ganhos sem efeito caixa, impostos) antes de qualquer juízo.
Alocação de capital: capex, expansão, M&A, dividendos, JCP e recompras, variação de ações e remuneração em ações (empresas americanas) e o retorno que a gestão atribui a eles; separe compromissos de intenções.
Comentários da gestão: reúna o que a administração disse sobre o trimestre, as causas apontadas para cada movimento, prioridades, investimentos, demanda, concorrência, preços e participação de mercado. Atribua explicitamente ("segundo a administração"), use citações curtas e literais apenas quando a redação importar e separe a visão da gestão da interpretação da IA. 
Guidance e perspectivas: quando houver guidance formal com pelo menos três itens, apresente uma tabela Markdown Item | GAAP | Não-GAAP | Faixa | vs trimestre atual. Converta todo intervalo do tipo "± X" em faixa com mínimo e máximo (US$ 65,0 bi ± 2% = US$ 63,7 a 66,3 bi; 74,8% ± 50 bps = 74,3% a 75,3%) e calcule a variação do ponto médio contra o trimestre atual. Quando GAAP e não-GAAP diferirem, explique em uma frase a origem da diferença segundo o documento. Depois, diferencie guidance formal de sinais qualitativos. Compare com guidance anterior ou com o entregue somente quando o documento trouxer essa comparação; caso contrário, não comente o tema nem acrescente ressalvas sobre premissas.
Nuances e pontos de atenção: não repita a ponte GAAP/não-GAAP; use a definição e a conciliação da empresa, não crie ajustes próprios, não trate o ajustado como superior ao reportado e omita o tema quando o ajuste for pequeno. Identifique efeitos não recorrentes, mudanças de base contábil ou de perímetro (IFRS 16, aquisições, descontinuadas), crescimento orgânico versus adquirido, sazonalidade, impairments, provisões, litígios e contingências, eventos subsequentes, ressalvas ou reapresentações, concentração em clientes, fornecedores, produtos ou regiões, e o que mudou em relação às tendências dos trimestres anteriores quando o documento permitir. Aponte o que os números principais escondem: compensações entre linhas, qualidade do lucro e conversão em caixa.
Métricas para acompanhar nos próximos resultados: tabela Markdown com 3 a 8 linhas e exatamente as colunas Indicador | Base atual | O que a gestão disse | Tipo | Horizonte | Como conferir no próximo trimestre. Cada linha é compromisso, meta, expectativa ou risco que o próximo resultado pode confirmar ou desmentir; Tipo é guidance formal, meta, expectativa qualitativa ou risco a monitorar; escreva "não quantificado" quando a gestão não der número. Ordene por relevância.
Conclusão: 150 a 220 palavras, nesta ordem: (1) veredito do trimestre em uma frase; (2) o motor principal, com dois ou três números; (3) a qualidade do resultado, com GAAP versus não-GAAP e conversão em caixa já explicadas; (4) o que o guidance indica para o próximo trimestre, em uma frase com números; (5) o item mais importante da tabela de métricas. Retome a reação do mercado em no máximo uma frase curta, sem ressalvas. Não repita tabelas, não recomende compra ou venda e não feche com advertências genéricas ("anúncios não equivalem a receita", "sem atribuição exclusiva").
Estilo: use **negrito** nos títulos e, de forma generosa, nos números, percentuais, datas, nomes de empresas e segmentos, metas, riscos e na frase-chave de cada parágrafo (dois a quatro trechos por parágrafo), nunca em frases inteiras. Aborde cada tema só quando o documento trouxer dado. Nunca escreva sobre dados ausentes: frases como "o release não informa", "não é possível identificar", "a fonte não quantifica", "não há decomposição" ou "condicionada à realização das premissas" são proibidas; se o dado não existe, o tema simplesmente não aparece (a única exceção é "não quantificado" na tabela de métricas). Todo juízo (margem menor, caixa abaixo do lucro) vem com a causa documentada; sem causa, descreva o número sem julgá-lo.
Conteúdo educativo e informativo: não faça recomendação de compra, venda ou manutenção, não indique preço-alvo e não use linguagem de promessa de retorno. Não inclua consenso de analistas nem avaliação por múltiplos, pois não há fonte verificada para eles.
O CONTEXTO DE MERCADO VERIFICADO citado abaixo é o campo verified_market_context_untrusted_data; se ele for null, escreva sob **Reação do mercado:** uma única frase dizendo que não foi possível avaliar a reação, sem buscar ou estimar preços.
"""
DETAILED_REQUIREMENTS_EN = """These requirements supplement your saved instructions and prevail in case of conflict. Use only the supplied document and verified market context; do not invent numbers, consensus, targets or quotes. Write 1,000–3,000 words, scaled to the material in the document; go below 1,000 only when the source is limited, never pad with repetition.
Use exactly these sections, in this order, as Markdown (##) headings: Key figures; Quarter overview; Revenue and operating metrics; Margins and costs; Financial result, taxes and net income; Cash, working capital and debt; Capital allocation and shareholder returns; Management commentary; Guidance and outlook; Nuances and points of attention; Metrics to follow in the next results; Conclusion. Between Metrics and Conclusion the market reaction has no ## heading: start it exactly with the line **Market reaction:** because the system inserts the price table right below it.
Key figures: a short Markdown table (6 to 8 rows) with revenue, the main segment or business KPI, gross margin, operating income, net income and diluted EPS. Put currency and scale in the header (for example Metric (US$ bn)) and use the same scale on every row. When the company discloses adjusted/non-GAAP measures, use the columns Metric | GAAP | Non-GAAP | YoY | QoQ (changes of the GAAP measure, or of both when they diverge); without adjusted measures, use Metric | Quarter | YoY | QoQ. Cash, FCF and debt belong in the cash section. When the document gives a series of 4 to 8 quarters, include in Revenue or Margins a short trend table (revenue, margin, main KPI) showing whether this quarter is an outlier.
Numbers: use one consistent scale in billions or millions with 1 or 2 decimals (US$ 57.0 bn, never 57,006); give the quarter's values with year-over-year and, when disclosed, quarter-over-quarter comparison; margins in p.p.; year-to-date or LTM only when identified. In every table and text state the currency, scale (for example US$ million), period and comparison basis, and check that the same number matches across sections. Use Markdown tables when there are at least three comparable rows (segments, KPIs, condensed income statement); otherwise write paragraphs that explain cause and consequence, not lists of numbers.
KPIs: choose them from how the company makes money.
{metric_menu}
Margins and costs: explain what pressured or helped SG&A, payroll, raw materials, energy, freight and inflation, separating price, volume and mix effects when the document allows.
Financial result, taxes and net income: break down the financial result (interest, FX, derivatives, gains on equity investments), the effective tax rate and tax credits, and say how much of the change in profit comes from operations versus these lines. When non-GAAP measures differ materially, present the bridge here as a Markdown table with columns Item | Operating income | Net income (and EPS when disclosed): the GAAP row, each item of the company's reconciliation with sign and value (SBC, amortization of acquired intangibles, gains or losses on investments, restructuring, tax effect) and the non-GAAP row in bold. Then one paragraph saying which adjustments recur (ongoing SBC is a real cost) and which are one-off, and why non-GAAP came in above or below GAAP.
Cash, working capital and debt: open with a Markdown table with columns for the quarter and the year-ago quarter and the rows Operating cash flow, Investing cash flow (capex, acquisitions, securities), Financing cash flow (buybacks, dividends, debt), Free cash flow (company definition) and Change in cash, using only disclosed rows. Then one paragraph on working capital (receivables, inventory, payables) and one on the balance sheet (cash and investments, gross debt, net cash or debt, leverage, cost, maturities and covenants when disclosed). Operating cash flow below net income is not negative in itself: explain the gap through its components (growth-phase working capital, non-cash gains, taxes) before any judgment.
Capital allocation: capex, expansion, M&A, dividends and buybacks, share count changes and stock-based compensation (US companies) and the return management attributes to them; separate commitments from intentions.
Management commentary: gather what management said about the quarter, the causes it gave for each movement, priorities, investments, demand, competition, pricing and market share. Attribute explicitly ("according to management"), use short literal quotes only when the wording matters, and keep management's view separate from AI interpretation. 
Guidance and outlook: when formal guidance has at least three items, present a Markdown table Item | GAAP | Non-GAAP | Range | vs current quarter. Convert every "± X" into a range with low and high (US$ 65.0 bn ± 2% = US$ 63.7 to 66.3 bn; 74.8% ± 50 bps = 74.3% to 75.3%) and compute the midpoint change versus the current quarter. When GAAP and non-GAAP differ, explain the source of the difference in one sentence as the document states it. Then distinguish formal guidance from qualitative clues. Compare with prior guidance or with what was delivered only when the document provides that comparison; otherwise do not comment on it or add caveats about assumptions.
Nuances and points of attention: do not repeat the GAAP/non-GAAP bridge; use the company's own definition and reconciliation, do not create your own adjustments, do not treat adjusted as superior to reported, and leave the topic out when the adjustment is small. Identify nonrecurring effects, accounting or perimeter changes (IFRS 16, acquisitions, discontinued operations), organic versus acquired growth, seasonality, impairments, provisions, litigation and contingencies, subsequent events, audit qualifications or restatements, concentration in customers, suppliers, products or regions, and what changed versus prior-quarter trends when the document allows. Point out what the headline numbers hide: offsets between lines, earnings quality and cash conversion.
Metrics to follow in the next results: a Markdown table with 3 to 8 rows and exactly the columns Metric | Current baseline | What management said | Type | Horizon | How to check next quarter. Each row is a commitment, target, expectation or risk the next results can confirm or refute; Type is formal guidance, target, qualitative expectation or risk to monitor; write "not quantified" when management gave no number. Order by materiality.
Conclusion: 150 to 220 words, in this order: (1) the quarter's verdict in one sentence; (2) the main driver, with two or three figures; (3) earnings quality, with GAAP versus non-GAAP and cash conversion already explained; (4) what guidance points to for next quarter, in one sentence with figures; (5) the most important item from the metrics table. Refer back to the market reaction in at most one short sentence, without caveats. Do not repeat tables, do not recommend buying or selling and do not close with generic caveats ("announcements are not revenue", "not solely attributable").
Style: use **bold** on headings and, generously, on figures, percentages, dates, company and segment names, targets, risks and each paragraph's key phrase (two to four spans per paragraph), never on whole sentences. Address each topic only when the document provides data. Never write about missing data: sentences like "the release does not disclose", "it is not possible to identify", "the source does not quantify", "there is no breakdown" or "subject to the assumptions materializing" are forbidden; if the data does not exist, the topic simply does not appear (the only exception is "not quantified" in the metrics table). Every judgment (lower margin, cash below profit) comes with its documented cause; without a cause, describe the number without judging it.
Educational and informational content: do not recommend buying, selling or holding, do not give price targets and do not use language promising returns. Do not include analyst consensus or multiples-based valuation, since there is no verified source for them.
The VERIFIED MARKET CONTEXT cited below is the field verified_market_context_untrusted_data; if it is null, write under **Market reaction:** a single sentence saying the reaction could not be assessed, without searching or estimating prices.
"""


def detailed_requirements(locale):
    from agents.prompt_builder import METRIC_MENU_EN, METRIC_MENU_PT
    en = locale == 'en'
    menu = (METRIC_MENU_EN.replace('the call does', 'the document does') if en
            else METRIC_MENU_PT.replace('a call não', 'o documento não'))
    return (DETAILED_REQUIREMENTS_EN if en else DETAILED_REQUIREMENTS_PT).replace('{metric_menu}', menu)


logger = logging.getLogger('uvicorn.error')


def private_response(response: Response):
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(prefix='/api/detailed-analysis', tags=['Detailed analysis'], dependencies=[Depends(private_response)])


def connection():
    from main import get_db_connection
    return get_db_connection()


def premium_user(user=Depends(require_report_user)):
    if plan_for(user) != 'premium':
        raise HTTPException(403, 'Análise detalhada é exclusiva do Premium. Detailed analysis requires Premium.')
    return user


def create_tables(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS detailed_analyses (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
        analysis_id INTEGER NOT NULL REFERENCES historico(id) ON DELETE CASCADE,
        locale TEXT NOT NULL, agent_id TEXT NOT NULL, source_hash TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('queued','running','completed','failed')),
        ticket TEXT, content TEXT, session_id TEXT, turn_id TEXT, error_code TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(user_id,analysis_id,locale,agent_id,source_hash))''')
    cur.execute('CREATE INDEX IF NOT EXISTS detailed_analyses_queue ON detailed_analyses(state,created_at)')


def source_record(cur, analysis_id, user):
    cur.execute('''SELECT h.empresa,h.ano,h.trimestre,h.resultado_json,d.source_text
        FROM historico h LEFT JOIN analysis_documents d ON d.analysis_id=h.id
        WHERE h.id=%s AND h.user_id=%s''', (analysis_id, str(user)))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, 'Analysis not found. Análise não encontrada.')
    company, year, quarter, raw, text = row
    original = json.loads(raw) if isinstance(raw, str) else raw
    if original.get('metadata', {}).get('tipo') == 'Earnings Call':
        raise HTTPException(422, 'Use a quarterly analysis. Selecione uma análise trimestral.')
    if not text or len(text.strip()) < 500:
        raise HTTPException(422, 'Refaça a análise trimestral para anexar o documento original. Reanalyze this quarter to attach its original document.')
    return {'company': company, 'year': year, 'quarter': quarter, 'text': text,
            'hash': hashlib.sha256(text.encode()).hexdigest()}


class StartDetailed(BaseModel):
    model_config = ConfigDict(extra='forbid')
    locale: Literal['pt', 'en'] = 'pt'


@router.post('/{analysis_id}')
def start(analysis_id: int, body: StartDetailed, user=Depends(premium_user)):
    ticket = None
    conn = connection()
    try:
        with conn.cursor() as cur:
            source = source_record(cur, analysis_id, user)
            agent_id = os.getenv('OPENAI_DETAILED_AGENT_ID', '').strip() or AGENT_ID
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (int(hashlib.sha256(f'detailed:{user}'.encode()).hexdigest()[:15], 16),))
            cur.execute('''SELECT id,state FROM detailed_analyses WHERE user_id=%s AND analysis_id=%s
                AND locale=%s AND agent_id=%s AND source_hash=%s''', (str(user), analysis_id, body.locale, agent_id, source['hash']))
            existing = cur.fetchone()
            if existing and existing[1] != 'failed':
                conn.commit()
                return {'id': existing[0], 'state': existing[1], 'reused': True}
            cur.execute("SELECT id FROM detailed_analyses WHERE user_id=%s AND state IN ('queued','running') LIMIT 1", (str(user),))
            if cur.fetchone():
                raise HTTPException(409, 'Aguarde a análise detalhada em andamento. Wait for your current detailed analysis.')
            ticket = reserve_usage(user, 'analysis', body.locale)
            job_id = str(uuid.uuid4())
            cur.execute('''INSERT INTO detailed_analyses(id,user_id,analysis_id,locale,agent_id,source_hash,state,ticket)
                VALUES(%s,%s,%s,%s,%s,%s,'queued',%s)
                ON CONFLICT(user_id,analysis_id,locale,agent_id,source_hash) DO UPDATE
                SET id=EXCLUDED.id,state='queued',ticket=EXCLUDED.ticket,content=NULL,error_code=NULL,session_id=NULL,turn_id=NULL,updated_at=NOW()''',
                (job_id, str(user), analysis_id, body.locale, agent_id, source['hash'], ticket))
        conn.commit()
        return {'id': job_id, 'state': 'queued', 'reused': False}
    except Exception:
        conn.rollback()
        cancel_usage(ticket)
        raise
    finally:
        conn.close()


@router.get('/{analysis_id}')
def get(analysis_id: int, locale: Literal['pt', 'en'] = 'pt', user=Depends(premium_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            source = source_record(cur, analysis_id, user)
            cur.execute('''SELECT id,state,content,error_code FROM detailed_analyses
                WHERE user_id=%s AND analysis_id=%s AND locale=%s AND source_hash=%s AND agent_id=%s
                ORDER BY created_at DESC LIMIT 1''', (str(user), analysis_id, locale, source['hash'],
                    os.getenv('OPENAI_DETAILED_AGENT_ID', '').strip() or AGENT_ID))
            row = cur.fetchone()
            return {'id': row[0], 'state': 'cancelled' if row[3] == 'cancelled' else row[1], 'content': row[2] if row[1] == 'completed' else None,
                    'error_code': row[3]} if row else {'state': 'not_started'}
    finally:
        conn.close()


class CancelDetailed(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str


def cancel_session(session_id):
    if not session_id:
        return
    from openai import OpenAI
    try:
        with OpenAI(api_key=os.environ['OPENAI_API_KEY'], timeout=10, max_retries=0) as client:
            client.beta.agents.sessions.events.create(session_id, events=[{'type': 'agent.session.input.cancel'}])
    except Exception as exc:
        logger.warning('detailed_analysis_provider_cancel_failed session=%s error_type=%s', session_id, type(exc).__name__)


@router.post('/{analysis_id}/cancel')
def cancel(analysis_id: int, body: CancelDetailed, user=Depends(premium_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""UPDATE detailed_analyses SET state='failed',error_code='cancelled',updated_at=NOW()
                WHERE id=%s AND analysis_id=%s AND user_id=%s AND state IN ('queued','running')
                RETURNING ticket,session_id""", (body.id, analysis_id, str(user)))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE account_usage SET state='failed' WHERE id=%s AND state='pending'", (row[0],))
            else:
                cur.execute('SELECT state,error_code FROM detailed_analyses WHERE id=%s AND analysis_id=%s AND user_id=%s', (body.id, analysis_id, str(user)))
                current = cur.fetchone()
                if not current:
                    raise HTTPException(404, 'Analysis not found.')
                if current[0] == 'completed':
                    raise HTTPException(409, 'A análise já foi concluída. The analysis has already completed.')
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    if row:
        cancel_session(row[1])
    return {'id': body.id, 'state': 'cancelled'}


def verified_market(source):
    from agents.auto_fetcher import AutoFetcher
    from market_data import reaction_prompt
    try:
        return reaction_prompt(AutoFetcher().resolve_ticker(source['company']), source['text'])
    except Exception as exc:  # prices are optional context; the analysis still runs and says it cannot judge the reaction
        logger.warning('detailed_analysis_market_unavailable error_type=%s', type(exc).__name__)
        return ''


def run_agent(agent_id, source, locale, remember, check_active=None, market=''):
    from openai import OpenAI
    from openai_client import OpenAIError
    from agents.prompt_builder import MARKET_REACTION_RULES
    from market_data import _reaction_window, with_reaction_table
    prompt = json.dumps({'task': 'Detailed quarterly result and management analysis. Return the complete analysis directly in this response as Markdown text. Do not create files, attachments, download links or a summary of work performed.',
                         'language': 'English' if locale == 'en' else 'Português',
                         'company': source['company'], 'fiscal_year': source['year'],
                         'fiscal_quarter': source['quarter'],
                         'requirements': detailed_requirements(locale) + '\n' + MARKET_REACTION_RULES.replace('Antes da Conclusão IA', 'Antes da Conclusão'),
                         'verified_market_context_untrusted_data': _reaction_window(market),
                         'source_document_untrusted_data': source['text']}, ensure_ascii=False)
    # Inherit saved instructions, model and tools. Never silently substitute a model or agent.
    session_id = None
    completed = False
    last_check = monotonic()
    with OpenAI(api_key=os.environ['OPENAI_API_KEY'], timeout=240, max_retries=0) as client:
        try:
            with client.beta.agents.sessions.create(agent_id=agent_id,
                    environment={'type': 'none'}, input=prompt, stream=True).with_result_collection() as stream:
                for event in stream:
                    if event.type == 'agent.session.created':
                        session_id = event.session.id
                        remember(session_id, None)
                    if check_active and monotonic() - last_check >= 5:
                        check_active()
                        last_check = monotonic()
                result = stream.get_final_result()
            session_id = result.session_id
            remember(session_id, result.turn_id)
            completed = result.turn.status == 'completed'
            if result.turn.status != 'completed' or len(result.output_text.split()) < 400:
                logger.warning('detailed_analysis_output_rejected session=%s status=%s words=%d', session_id, result.turn.status, len(result.output_text.split()))
                raise OpenAIError('Detailed analysis incomplete', code='output_short' if completed else 'turn_incomplete')
            return with_reaction_table(result.output_text.strip(), market)
        finally:
            if session_id:
                if not completed:
                    cancel_session(session_id)
                try:
                    client.beta.agents.sessions.delete(session_id)
                except Exception:
                    logger.warning('detailed_analysis_session_cleanup_failed session=%s', session_id)


def claim():
    conn = connection()
    try:
        with conn.cursor() as cur:
            # Never replay a paid turn after an uncertain interruption.
            cur.execute("""UPDATE detailed_analyses SET state='failed',error_code='interrupted',updated_at=NOW()
                WHERE state IN ('queued','running') AND updated_at<NOW()-INTERVAL '10 minutes' RETURNING ticket""")
            for row in cur.fetchall():
                cur.execute("UPDATE account_usage SET state='failed' WHERE id=%s AND state='pending'", (row[0],))
            cur.execute("SELECT id,user_id,analysis_id,locale,agent_id,source_hash,ticket FROM detailed_analyses WHERE state='queued' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED")
            job = cur.fetchone()
            if job:
                cur.execute("UPDATE account_usage SET expires_at=NOW()+INTERVAL '10 minutes' WHERE id=%s AND state='pending' AND expires_at>NOW() RETURNING id", (job[6],))
                if not cur.fetchone():
                    cur.execute("UPDATE detailed_analyses SET state='failed',error_code='quota_expired' WHERE id=%s", (job[0],))
                    job = None
                else:
                    cur.execute("UPDATE detailed_analyses SET state='running',updated_at=NOW() WHERE id=%s", (job[0],))
        conn.commit()
        return job
    finally:
        conn.close()


def process(job):
    job_id, user, analysis_id, locale, agent_id, source_hash, ticket = job
    try:
        conn = connection()
        try:
            with conn.cursor() as cur:
                source = source_record(cur, analysis_id, user)
        finally:
            conn.close()
        if source['hash'] != source_hash:
            raise ValueError('input_changed')

        def remember(session_id, turn_id):
            conn = connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE detailed_analyses SET session_id=%s,turn_id=COALESCE(%s,turn_id),updated_at=NOW() WHERE id=%s AND state='running' RETURNING id", (session_id, turn_id, job_id))
                    if not cur.fetchone():
                        raise ValueError('cancelled')
                conn.commit()
            finally:
                conn.close()

        def check_active():
            conn = connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM detailed_analyses WHERE id=%s AND state='running'", (job_id,))
                    if not cur.fetchone():
                        raise ValueError('cancelled')
            finally:
                conn.close()

        check_active()
        content = run_agent(agent_id, source, locale, remember, check_active, verified_market(source))
        conn = connection()
        try:
            with conn.cursor() as cur:
                if source_record(cur, analysis_id, user)['hash'] != source_hash:
                    raise ValueError('input_changed')
                cur.execute("UPDATE detailed_analyses SET state='completed',content=%s,updated_at=NOW() WHERE id=%s AND state='running' RETURNING id", (content, job_id))
                if not cur.fetchone():
                    raise ValueError('interrupted')
                complete_usage(cur, ticket)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception as exc:
        cancel_usage(ticket)
        conn = connection()
        try:
            with conn.cursor() as cur:
                code = getattr(exc, 'code', None) or 'generation_failed'
                cur.execute("UPDATE detailed_analyses SET state='failed',error_code=%s,updated_at=NOW() WHERE id=%s AND state='running'", (code, job_id))
            conn.commit()
        finally:
            conn.close()
        logger.warning('detailed_analysis_failed job=%s error_type=%s', job_id, type(exc).__name__)


def worker():
    while not stop.is_set():
        try:
            job = claim()
            if job:
                process(job)
                continue
        except Exception:
            logger.warning('detailed_analysis_queue_unavailable')
        stop.wait(3)


def start_worker():
    if os.getenv('DETAILED_ANALYSIS_WORKER', '1') != '0':
        stop.clear()
        Thread(target=worker, name='detailed-analysis-worker', daemon=True).start()
