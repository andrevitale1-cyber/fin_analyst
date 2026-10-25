"""Apply the Apple reader's visual system to both published company editions."""
from copy import deepcopy
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

PUBLIC=Path(__file__).resolve().parents[1]/'public'
REPORTS=PUBLIC/'published-reports'


def apply_layout():
    for locale in ('pt','en'):
        suffix='-en' if locale=='en' else ''
        apple=BeautifulSoup((REPORTS/f'aapl-20261022{suffix}.html').read_text(encoding='utf-8'),'html.parser')
        for company in ('aapl','nvda'):
            path=REPORTS/f'{company}-20261022{suffix}.html'
            soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            paragraphs=[p.get_text() for p in soup.select('main section p')]
            if company=='nvda' and soup.select_one('aside'):
                soup.body['class']=['nvda-edition']
                for style in soup.select('style'):style.decompose()
                for style in apple.select('style'):soup.head.append(deepcopy(style))
                old=soup.select_one('aside');nav=deepcopy(apple.select_one('.toc'))
                nav['aria-label']='In this report' if locale=='en' else 'Neste relatório'
                contents=nav.select_one('ol');contents.clear()
                for i,link in enumerate(old.select('nav a'),1):
                    link=link.extract();title=apple.select('.toc ol a')[i-1].select('span')[-1].get_text();link.clear()
                    index=soup.new_tag('span',attrs={'class':'nav-index'});index.string=f'{i:02}'
                    text=soup.new_tag('span');text.string=title;link.extend([index,text])
                    li=soup.new_tag('li');li.append(link);contents.append(li)
                old.replace_with(nav)
                wrap=soup.new_tag('div',attrs={'class':'wrap'})
                soup.body.insert(0,wrap);wrap.append(nav.extract());wrap.append(soup.select_one('main').extract())
                hero=soup.select_one('header.hero');hero['class']=['top']
                soup.select_one('.languages')['class']=['report-languages']
                logo=soup.select_one('.identity>img');logo_box=soup.new_tag('div',attrs={'class':'company-logo'});logo.wrap(logo_box)
                identity=soup.select_one('.identity')
                eyebrow=identity.select_one('small.eyebrow');eyebrow.name='span'
                ticker=identity.select_one('h1 small');ticker.name='span'
                highlights=soup.select_one('.hero .grid') if soup.select_one('.hero') else hero.select_one('.grid')
                highlights['class']=['hero-highlights']
                for metric in highlights.select('.metric'):metric['class']=[]
                # The existing quality highlight becomes the same linked badge used by Apple.
                quality=highlights.select_one('div:last-child');grade=quality.select_one('b').get_text();quality.decompose()
                badge=soup.new_tag('a',href='#scorecard',attrs={'class':'hero-score'})
                badge.append(BeautifulSoup('<small>'+('QUALITY' if locale=='en' else 'QUALIDADE')+'</small><strong>'+grade.split('/')[0]+'<em>/5</em></strong><span class="score-dots" aria-hidden="true">'+'<i class="on"></i>'*5+'</span>','html.parser'))
                identity.append(badge)
                meta=hero.select_one('.meta');meta['class']=['hero-meta']
                for section in soup.select('main>section'):
                    section['class']=['sec'];heading=section.find('h2',recursive=False)
                    sh=soup.new_tag('header',attrs={'class':'sh'});heading.wrap(sh)
                    reference=apple.select_one(f'#{section["id"]} .sh h2 svg') or apple.select_one('.sh h2 svg')
                    if reference:heading.insert(0,deepcopy(reference))
                    prose=soup.new_tag('div',attrs={'class':'editorial-prose'})
                    sh.insert_after(prose)
                    for p in list(section.find_all('p',recursive=False)):prose.append(p.extract())
                    if prose.p:prose.p['class']=['summary']
                    if section['id']=='indicadores_resumo':
                        grid=section.select_one('.grid');grid['class']=['metric-grid']
                        group=soup.new_tag('div',attrs={'class':'metric-group numbers-board'});grid.wrap(group)
                        for b in grid.select('b'):b.name='strong'
                    if section['id']=='scorecard':
                        grid=section.select_one('.scores');grid['class']=['quality-grid']
                        board=soup.new_tag('div',attrs={'class':'quality-board'});grid.wrap(board)
                        head=deepcopy(apple.select_one('.quality-head'));head.select_one('h3').string='NVIDIA'
                        head.select_one('p').string='32/7 = 4.57 → 5/5' if locale=='en' else '32/7 = 4,57 → 5/5'
                        head.select_one('.quality-number>strong').string='5'
                        dots=head.select_one('.score-dots');dots.clear();dots.append(BeautifulSoup('<i class="on"></i>'*5,'html.parser'))
                        board.insert(0,head)
                        for card in grid.select('.reason'):
                            card['class']=['quality-card'];card.h3.name='h4';card.select_one('.badge').name='b'
                    if section.select_one('.chart'):
                        chart=section.select_one('.chart');chart['class']=['visual-chart']
                        chart.wrap(soup.new_tag('div',attrs={'class':'visual-panel'}))
            if not soup.select_one('link[href="/report-layout.css"]'):
                soup.head.append(soup.new_tag('link',rel='stylesheet',href='/report-layout.css'))
            if company=='nvda' and not soup.select_one('script[src="/report-navigation.js"]'):
                soup.body.append(soup.new_tag('script',src='/report-navigation.js',defer=''))
            assert Counter(paragraphs)<=Counter(p.get_text() for p in soup.select('main section p')),f'{company}: narrative changed'
            assert len(soup.select('.sec'))==11
            assert soup.select_one('.toc .brand')['href']==f'/{locale}'
            assert soup.select_one('iframe')
            path.write_text(str(soup),encoding='utf-8')
            print(path.name,'shared layout applied; narrative unchanged')


if __name__=='__main__':apply_layout()
