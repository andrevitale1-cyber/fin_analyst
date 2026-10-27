"""Enrich the existing public editions with dated evidence and reusable visuals."""
from pathlib import Path
from urllib.parse import quote
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / 'public'
REPORTS = ROOT / 'published-reports'

# Data extracted from the supplied standalone NVIDIA report. These remain
# historical observations, not a new company valuation or quality score.
ADDITIONS = {
    'business_model': [
        ('Um sistema completo, com uma cadeia concentrada', 'A NVIDIA integra aceleradores, rede, software e sistemas. Ela projeta os produtos, mas depende de fabricantes e fornecedores externos para produção e memória. Esse modelo reduz a necessidade de fábricas próprias, enquanto os compromissos de fornecimento e capacidade chegaram a US$ 279 bi em julho de 2026. A escala pode assegurar acesso à oferta; uma queda abrupta da demanda também pode transformar compromissos em estoques ou perdas.', 'A complete system with a concentrated supply chain', 'NVIDIA combines accelerators, networking, software and systems. It designs products but depends on outside manufacturers and suppliers for production and memory. This model reduces the need for owned factories, while supply and capacity commitments reached $279 billion in July 2026. Scale can secure access to supply; an abrupt demand decline can also turn commitments into inventory or losses.'),
        ('Clientes e concentração', 'Três clientes diretos representaram 44% da receita no primeiro semestre do FY27. A empresa também vende a usuários finais por intermediários, portanto a composição dos compradores diretos não mede toda a concentração da demanda final. Cinco clientes diretos respondiam por 70% das contas a receber em julho de 2026. A evolução dos prazos e recebíveis merece acompanhamento junto com as vendas.', 'Customers and concentration', 'Three direct customers accounted for 44% of revenue in the first half of FY27. The company also sells to end users through intermediaries, so the direct-customer mix does not measure all end-demand concentration. Five direct customers represented 70% of accounts receivable in July 2026. Payment terms and receivables deserve monitoring alongside sales.'),
        ('Mudança na divulgação por mercado', 'No FY26, Data Center representou 89,7% da receita. A partir do FY27 a NVIDIA passou a apresentar Hyperscale, AI Clouds, Industrial & Enterprise e Edge Computing. No primeiro semestre do FY27, essas categorias representaram 51,6%, 40,8% e 7,6% da receita, respectivamente. Como a classificação mudou, os percentuais não devem ser tratados como uma série contínua por mercado.', 'A change in market reporting', 'Data Center represented 89.7% of revenue in FY26. From FY27 NVIDIA reported Hyperscale, AI Clouds, Industrial & Enterprise, and Edge Computing. In the first half of FY27 these categories represented 51.6%, 40.8% and 7.6% of revenue, respectively. Because the classification changed, the percentages should not be treated as one continuous market series.'),
    ],
    'competitive_advantage': [
        ('O que sustenta a vantagem', 'A plataforma reúne chips, rede e ferramentas em um sistema integrado. A empresa reporta mais de 7,5 milhões de desenvolvedores no ecossistema: isso demonstra escala de uso, mas não mede quantos são exclusivos nem o custo de migração. Networking representou 16,2% do Data Center no FY26, sinal de uma oferta que vai além do acelerador. As margens evidenciam captura de valor, sem separar quanto decorre do software e quanto da oferta restrita.', 'What supports the advantage', 'The platform combines chips, networking and tools in an integrated system. The company reports more than 7.5 million developers in its ecosystem: this shows scale, but does not measure exclusivity or migration cost. Networking represented 16.2% of Data Center in FY26, evidence of an offering beyond the accelerator. Margins show value capture without separating software effects from constrained supply.'),
        ('Pressão competitiva', 'AMD oferece aceleradores concorrentes; grandes clientes também desenvolvem chips próprios para cargas específicas. A comparação precisa observar desempenho, ferramentas, disponibilidade e custo total do sistema, não apenas o preço de um chip. Restrições de exportação limitam a presença em mercados como a China e podem dar espaço para ecossistemas locais. Nenhum desses fatores, isoladamente, demonstra perda atual da liderança.', 'Competitive pressure', 'AMD offers competing accelerators; large customers also develop their own chips for specific workloads. Comparison requires performance, tools, availability and total system cost, not just a chip price. Export restrictions limit access to markets including China and may allow local ecosystems to grow. None of these factors alone demonstrates a current loss of leadership.'),
    ],
    'historico': [
        ('Lucro versus caixa', 'O lucro líquido passou de US$ 9,8 bi no FY22 para US$ 120,1 bi no FY26; o caixa operacional foi de US$ 9,1 bi para US$ 102,7 bi. No primeiro semestre do FY27, o caixa operacional foi US$ 74,4 bi, ou 0,63 vez o lucro de US$ 118,0 bi. Ganhos não caixa com investimentos e uso de capital de giro ajudam a explicar a diferença. Uma diferença em um semestre não prova deterioração permanente, mas merece acompanhamento.', 'Earnings versus cash', 'Net income rose from $9.8 billion in FY22 to $120.1 billion in FY26; operating cash flow increased from $9.1 billion to $102.7 billion. In the first half of FY27, operating cash flow was $74.4 billion, or 0.63 times net income of $118.0 billion. Noncash investment gains and working-capital use help explain the gap. A one-half difference does not prove permanent deterioration, but warrants monitoring.'),
        ('Margens e ciclo', 'A margem operacional caiu de 37,3% no FY22 para 15,7% no FY23 e alcançou 60,4% no FY26. O histórico mostra tanto a expansão recente quanto a exposição ao ciclo. No primeiro semestre do FY27, a margem foi 65,9%; não é seguro extrapolar esse nível indefinidamente. Comparar exercícios completos e semestres equivalentes ajuda a evitar conclusões baseadas em períodos diferentes.', 'Margins and the cycle', 'Operating margin fell from 37.3% in FY22 to 15.7% in FY23 and reached 60.4% in FY26. The history shows both recent expansion and cyclical exposure. In the first half of FY27 the margin was 65.9%; extrapolating it indefinitely would be unsafe. Comparing complete years and equivalent half-year periods helps avoid mixing time bases.'),
    ],
    'management': [
        ('Recompras e diluição', 'As recompras pagas foram de US$ 40,1 bi no FY26 e US$ 39,0 bi no primeiro semestre do FY27. Parte das ações compradas compensou emissões: no FY26 foram recompradas 282 milhões de ações, enquanto as ações em circulação caíram 173 milhões. Autorização de recompra é capacidade aprovada, não desembolso efetivo. O benefício econômico depende também do preço pago e das alternativas de uso do caixa.', 'Buybacks and dilution', 'Cash spent on repurchases was $40.1 billion in FY26 and $39.0 billion in the first half of FY27. Some shares purchased offset issuance: in FY26 the company repurchased 282 million shares while shares outstanding declined by 173 million. A repurchase authorization is approved capacity, not cash already spent. Economic benefit also depends on the price paid and alternative uses of cash.'),
        ('Balanço e compromissos', 'As participações societárias e outros investimentos aumentaram, assim como compromissos ligados à infraestrutura e à cadeia de suprimentos. Esses valores têm naturezas, prazos e condições diferentes e não devem ser somados como se fossem perdas certas. A leitura exige acompanhar desembolsos, vencimentos e eventuais garantias separadamente, além do retorno dessas decisões de alocação.', 'Balance sheet and commitments', 'Equity holdings and other investments increased, as did commitments related to infrastructure and the supply chain. These amounts have different terms, timing and conditions and should not be added as though they were certain losses. Assessment requires monitoring cash outflows, maturities and guarantees separately, as well as returns on allocation decisions.'),
    ],
    'outlook': [
        ('Indicadores para os próximos resultados', 'A receita do primeiro semestre do FY27 foi US$ 177,8 bi, alta de 95,8% sobre o mesmo semestre anterior. Para o terceiro trimestre, a companhia projetou US$ 108,0 bi de receita, com margem bruta de 74,0%, ambas sujeitas às faixas divulgadas. Guidance é uma expectativa da gestão, não resultado realizado. O acompanhamento deve considerar a continuidade da demanda, a disponibilidade de infraestrutura e a evolução das margens.', 'Indicators for upcoming results', 'Revenue in the first half of FY27 was $177.8 billion, up 95.8% from the comparable half-year. For the third quarter, the company guided to $108.0 billion in revenue and a 74.0% gross margin, both subject to the disclosed ranges. Guidance is management expectation, not a reported result. Monitoring should include demand durability, infrastructure availability and margins.'),
    ],
    'risks': [
        ('Riscos que podem ocorrer juntos', 'Uma redução no investimento em infraestrutura de IA pode afetar pedidos, recebíveis, participações e compromissos com fornecedores ao mesmo tempo. Isso não significa que todos se converterão em perda, mas que não são riscos necessariamente independentes. Margem bruta, crescimento sequencial, recebíveis e eventuais baixas são sinais observáveis para acompanhar a tese.', 'Risks that may occur together', 'A reduction in AI infrastructure spending could affect orders, receivables, equity holdings and supplier commitments at the same time. This does not mean all will become losses, but they are not necessarily independent risks. Gross margin, sequential growth, receivables and any impairments are observable indicators to monitor.'),
    ],
}

def competitors(soup, company, locale):
    section = soup.select_one('#competitive_advantage')
    old = section.select_one('.report-competitors')
    if old: old.decompose()
    en = locale == 'en'
    items = [('AMD', 'AMD'), ('Alphabet', 'GOOG'), ('Amazon', 'AMZN')] if company == 'nvda' else [('Alphabet', 'GOOG'), ('Microsoft', 'MSFT')]
    block = soup.new_tag('aside', attrs={'class': 'report-competitors', 'aria-label': 'Competitors' if en else 'Concorrentes'})
    title = soup.new_tag('h3'); title.string = 'Competitors' if en else 'Concorrentes'; block.append(title)
    intro = soup.new_tag('p'); intro.string = ('Open a company to check report availability.' if en else 'Abra uma empresa para consultar a disponibilidade do relatório.'); block.append(intro)
    ul = soup.new_tag('ul')
    for name, ticker in items:
        li = soup.new_tag('li'); a = soup.new_tag('a', href=f'/{locale}/dashboard/reports?company={quote(ticker)}')
        img = soup.new_tag('img', src=f'/benefits/company-logos/{ticker}.webp', alt='', width='38', height='38', loading='lazy')
        text = soup.new_tag('span'); strong = soup.new_tag('strong'); strong.string = name
        small = soup.new_tag('small'); small.string = ticker
        text.extend([strong, small]); arrow = soup.new_tag('span', attrs={'aria-hidden':'true', 'class':'competitor-arrow'}); arrow.string = '›'
        a.extend([img,text,arrow]); li.append(a); ul.append(li)
    block.append(ul)
    section.select_one('.editorial-prose').insert_after(block)

def feedback(soup):
    frame = soup.select_one('iframe[src*="report-feedback"], iframe[data-feedback-src]')
    if not frame: return
    src = frame.get('data-feedback-src') or frame.attrs.pop('src')
    frame['data-feedback-src'] = src
    frame['data-report-id'] = src.split('report=', 1)[1]
    frame['hidden'] = ''
    frame['style'] = 'display:none;width:100%;height:250px;border:0'
    if not soup.select_one('script[src="/report-feedback.js"]'):
        soup.body.append(soup.new_tag('script', src='/report-feedback.js', defer=''))

def market_board(soup, locale):
    section = soup.select_one('#market_view')
    if section.select_one('.market-board'): return
    en = locale == 'en'
    title = 'Strong Buy' if en else 'Compra forte'
    labels = ('buy', 'hold', 'sell') if en else ('compra', 'neutras', 'venda')
    low, high, mean, spot = 180, 515, 328.72, 212.21
    marker = lambda value: f'{100*(value-low)/(high-low):.2f}%'
    html = f'''<div class="market-board"><div><span class="eyebrow">{'ANALYST CONSENSUS' if en else 'CONSENSO DE ANALISTAS'}</span><h3>{title}</h3><p>S&amp;P Global via StockAnalysis · {'as of Oct 22, 2026 · 62 analysts' if en else 'corte em 22/10/2026 · 62 analistas'}</p><div class="sentiment-bar" role="img" aria-label="59 {labels[0]}, 2 {labels[1]}, 1 {labels[2]}"><i style="width:{59/62*100:.4f}%;background:#18a875"></i><i style="width:{2/62*100:.4f}%;background:#b8c2ce"></i><i style="width:{1/62*100:.4f}%;background:#ed7b76"></i></div><div class="sentiment-labels"><span><b>59</b> {labels[0]}</span><span><b>2</b> {labels[1]}</span><span><b>1</b> {labels[2]}</span></div></div><div class="target-card"><small>{'AVERAGE TARGET · 12 MONTHS' if en else 'PREÇO-ALVO MÉDIO · 12 MESES'}</small><strong>{'$328.72' if en else 'US$ 328,72'}</strong><span class="positive">{' +54.9% versus $212.21' if en else '+54,9% versus US$ 212,21'}</span><div class="target-track" role="img" aria-label="{'Low $180, high $515, average $328.72, share price $212.21' if en else 'Mínimo US$ 180, máximo US$ 515, média US$ 328,72, cotação US$ 212,21'}"><i style="left:0%"></i><i class="mean" style="left:{marker(mean)}"></i><i class="spot" style="left:{marker(spot)}"></i></div><div class="target-labels"><span>{'$180<br/>Low' if en else 'US$ 180<br/>Mínimo'}</span><span>{'$515<br/>High' if en else 'US$ 515<br/>Máximo'}</span></div><p>{'Average' if en else 'Média'} <i class="target-key"></i> · {'Share price' if en else 'Cotação'} <i class="target-key spot"></i></p></div></div>'''
    soup.select_one('#market_view .editorial-prose').insert_after(BeautifulSoup(html, 'html.parser'))
    for item in section.select(':scope > .target, :scope > .target-labels'): item.decompose()

def add_nvda(soup, locale):
    en = locale == 'en'
    for sid, paragraphs in ADDITIONS.items():
        section = soup.select_one('#'+sid)
        for old in section.select('.nvda-added'): old.decompose()
        prose = section.select_one('.editorial-prose')
        for heading_pt, text_pt, heading_en, text_en in paragraphs:
            block = soup.new_tag('div', attrs={'class':'nvda-added'})
            h = soup.new_tag('h3', attrs={'class':'sub'}); h.string = heading_en if en else heading_pt
            p = soup.new_tag('p'); p.string = text_en if en else text_pt
            block.extend([h,p]); prose.append(block)
    for sid, kind in [('business_model','mix'),('competitive_advantage','moat'),('historico','cash')]:
        section = soup.select_one('#'+sid)
        for old in section.select('.report-evidence-chart'): old.decompose()
        figure = soup.new_tag('figure', attrs={'class':'report-evidence-chart visual-panel', 'data-evidence-chart':kind, 'data-locale':locale})
        section.select_one('.editorial-prose').insert_after(figure)
    market_board(soup, locale)
    if not soup.select_one('script[src="/report-evidence-charts.js"]'):
        soup.body.append(soup.new_tag('script', src='/report-evidence-charts.js', defer=''))

def main():
    for p in sorted(REPORTS.glob('*.html')):
        soup = BeautifulSoup(p.read_text(encoding='utf8'), 'html.parser')
        company = p.name[:4]; locale = 'en' if '-en.' in p.name else 'pt'
        feedback(soup); competitors(soup, company, locale)
        if company == 'nvda': add_nvda(soup, locale)
        p.write_text(str(soup), encoding='utf8')
        print(p.name, 'enhanced')

if __name__ == '__main__': main()
