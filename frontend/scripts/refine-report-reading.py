"""Apply the shared reading structure without rewriting research or chart data."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from bs4 import BeautifulSoup

REPORTS = Path(__file__).resolve().parents[1] / 'public' / 'published-reports'


def refine(path):
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    paragraphs = Counter(p.get_text() for p in soup.select('main p'))
    scripts = [s.string for s in soup.select('script:not([src])')]
    tables = [t.get_text() for t in soup.select('main table')]
    sources = Counter(a['href'] for a in soup.select('main a[href^="https:"]'))
    en = soup.html.get('lang', '').startswith('en')
    signals = soup.select_one('.signal-grid')
    if signals and not signals.has_attr('data-compact'):
        short = (['Strong', 'Exceptional', 'In transition', 'Moderate', 'Positive, cooling'] if en else
                 ['Forte', 'Excepcional', 'Em transição', 'Moderado', 'Positivo, esfriando'])
        for index, (signal, label) in enumerate(zip(signals.select('.signal'), short)):
            signal['title'] = signal.get_text(' ', strip=True)
            signal['aria-label'] = signal['title']
            signal.select_one('strong').string = label
            if index >= 2: signal['class'].append('caution')
        # A dated multiple is available; do not invent a fair-value judgment.
        metric = next(m for m in soup.select('.metric') if ('P/L' in m.get_text() or 'P/E' in m.get_text()))
        value = deepcopy(signals.select_one('.signal'))
        value['class'] = ['signal', 'neutral']
        value['href'] = '#indicadores_resumo'
        value['title'] = metric.get_text(' ', strip=True)
        value['aria-label'] = value['title']
        value.select_one('small').string = 'Valuation'
        value.select_one('strong').string = metric.select_one('strong').get_text() + (' P/E' if en else ' P/L')
        signals.select('.signal')[-1].insert_before(value)
        signals['data-compact'] = ''
    elif not signals:
        # Summary links quote the report's existing factor scores, without new ratings.
        signals = soup.new_tag('div', attrs={'class': 'signal-grid', 'data-compact': ''})
        for card in soup.select('.quality-card')[:6]:
            heading = card.select_one('h4')
            grade = heading.select_one('b').get_text()
            label = heading.get_text(' ', strip=True).replace(grade, '').strip()
            link = soup.new_tag('a', href='#scorecard', attrs={'class': ['signal'], 'title': card.get_text(' ', strip=True)})
            icon = soup.new_tag('span', attrs={'class': 'signal-icon', 'aria-hidden': 'true'})
            icon.string = '◇'
            box = soup.new_tag('div'); small = soup.new_tag('small'); small.string = label
            strong = soup.new_tag('strong'); strong.string = grade
            box.extend([small, strong]); link.extend([icon, box]); signals.append(link)
        soup.select_one('header.top').insert_after(signals)
    nav = soup.select_one('.toc')
    nav.select_one('details').attrs.pop('open', None)
    languages = soup.select_one('.report-languages')
    nav.append(languages.extract())
    price = soup.select_one('main > .price-panel')
    if price:
        soup.select_one('#indicadores_resumo .sh').insert_after(price.extract())
    score = soup.select_one('#scorecard')
    soup.select_one('#indicadores_resumo').insert_after(score.extract())
    # Follow the actual reading sequence rather than preserving stale numbering.
    links = {a['href']: a.parent for a in nav.select('ol a')}
    contents = nav.select_one('ol')
    for index, section in enumerate(soup.select('main > .sec'), 1):
        item = links['#' + section['id']]
        item.select_one('.nav-index').string = f'{index:02}'
        contents.append(item.extract())
    highlights = soup.select_one('header.top .hero-highlights')
    if highlights:
        quote = highlights.select_one('b')
        identity = soup.select_one('.identity > div:nth-child(2)')
        price = soup.new_tag('div', attrs={'class': 'hero-price'})
        price.string = quote.get_text()
        identity.append(price)
        soup.select_one('#indicadores_resumo .sh').insert_after(highlights.extract())
    if not soup.select_one('.report-reading-tools'):
        labels = (['Reading preferences', 'Toggle highlights', 'Serif font', 'Sans-serif font', 'Smaller text', 'Larger text'] if en else
                  ['Preferências de leitura', 'Alternar destaques', 'Fonte com serifa', 'Fonte sem serifa', 'Diminuir texto', 'Aumentar texto'])
        toolbar = soup.new_tag('div', attrs={'class': 'report-reading-tools', 'role': 'group', 'aria-label': labels[0]})
        for action, text, label in zip(['highlights', 'serif', 'sans', 'smaller', 'larger'], ['✎', 'A', 'A', 'A−', 'A+'], labels[1:]):
            button = soup.new_tag('button', attrs={'type': 'button', 'data-reading': action, 'aria-label': label, 'title': label})
            button.string = text
            if action in ('highlights', 'serif', 'sans'):
                button['aria-pressed'] = 'false' if action == 'sans' else 'true'
            if action == 'serif': button['class'] = ['serif-choice']
            toolbar.append(button)
        nav.append(toolbar)
    else:
        nav.append(soup.select_one('.report-reading-tools').extract())
    if not soup.select_one('script[src="/report-reading.js"]'):
        soup.body.append(soup.new_tag('script', src='/report-reading.js', defer=''))
    assert paragraphs == Counter(p.get_text() for p in soup.select('main p'))
    assert scripts == [s.string for s in soup.select('script:not([src])')]
    assert Counter(tables) == Counter(t.get_text() for t in soup.select('main table'))
    assert sources == Counter(a['href'] for a in soup.select('main a[href^="https:"]'))
    assert len(soup.select('main > .sec')) == 11
    assert all(soup.select_one(a['href']) for a in nav.select('ol a'))
    path.write_text(str(soup), encoding='utf-8')
    print(path.name + ': layout updated; narrative, tables, sources and chart scripts preserved')


if __name__ == '__main__':
    for path in sorted(REPORTS.glob('*.html')):
        refine(path)
