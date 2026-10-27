(() => {
  const sources = '<a href="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm" target="_blank" rel="noopener">NVIDIA Form 10-K FY2026</a>';
  for (const figure of document.querySelectorAll('[data-evidence-chart]')) {
    const en = figure.dataset.locale === 'en';
    const kind = figure.dataset.evidenceChart;
    const configs = {
      mix: {
        title: en ? 'Where FY2026 revenue came from' : 'De onde veio a receita FY2026',
        description: en ? 'Data Center compute 75.2%; networking 14.5%; gaming 7.4%; other 2.9%. Percentages of total revenue; rounded.' : 'Computação de Data Center 75,2%; rede 14,5%; games 7,4%; outros 2,9%. Percentuais da receita total; valores arredondados.',
        labels: en ? ['Data Center compute', 'Networking', 'Gaming', 'Other'] : ['Computação de Data Center', 'Networking', 'Games', 'Outros'],
        values: [75.2,14.5,7.4,2.9], type: 'doughnut',
      },
      moat: {
        title: en ? 'Evidence behind the competitive advantage' : 'Evidências da vantagem competitiva',
        description: en ? 'Qualitative assessment: integrated system and supply scale are well supported; switching costs are partly supported. This is not a measured score or the company quality rating.' : 'Leitura qualitativa: sistema integrado e escala de oferta têm evidência forte; custos de troca têm evidência parcial. Não são medições nem a nota de qualidade da empresa.',
        labels: en ? ['Integrated system', 'Supply scale', 'Switching costs'] : ['Sistema integrado', 'Escala de oferta', 'Custos de troca'],
        values: [2,2,1], type: 'radar',
      },
      cash: {
        title: en ? 'Operating cash flow and net income' : 'Caixa operacional e lucro líquido',
        description: en ? 'Reported full fiscal years FY2022–FY2026, US$ billions. The gap can reflect noncash gains and working capital.' : 'Exercícios completos FY2022–FY2026, em US$ bilhões. A diferença pode refletir ganhos não caixa e capital de giro.',
        labels: ['FY22','FY23','FY24','FY25','FY26'], values: [9.1,5.6,28.1,64.1,102.7], other: [9.8,4.4,29.8,72.9,120.1], type: 'line',
      },
    };
    const data = configs[kind];
    if (!data) continue;
    const id = `evidence-${kind}`;
    const rows = data.labels.map((label, i) => `<tr><th scope="row">${label}</th><td>${data.type === 'radar' ? (data.values[i] === 2 ? (en ? 'Well supported' : 'Evidência forte') : (en ? 'Partly supported' : 'Evidência parcial')) : data.values[i].toLocaleString(en ? 'en-US' : 'pt-BR') + (kind === 'mix' ? '%' : '')}</td>${data.other ? `<td>${data.other[i].toLocaleString(en ? 'en-US' : 'pt-BR')}</td>` : ''}</tr>`).join('');
    figure.innerHTML = `<h3>${data.title}</h3><p class="chart-description">${data.description}</p><div class="evidence-chart-canvas"><canvas id="${id}" role="img" aria-label="${data.description}"></canvas></div><details class="evidence-chart-data"><summary>${en ? 'Data and source' : 'Dados e fonte'}</summary><div class="tw" tabindex="0"><table><thead><tr><th scope="col">${en ? 'Category' : 'Categoria'}</th><th scope="col">${kind === 'cash' ? (en ? 'Operating cash flow' : 'Caixa operacional') : (en ? 'Assessment / share' : 'Avaliação / participação')}</th>${data.other ? `<th scope="col">${en ? 'Net income' : 'Lucro líquido'}</th>` : ''}</tr></thead><tbody>${rows}</tbody></table></div><p>${sources} · ${en ? 'reporting date Jan 25, 2026' : 'exercício encerrado em 25/01/2026'}</p></details>`;
    if (typeof Chart === 'undefined') continue;
    const colors = ['#258e65','#6e81d2','#50a9b7','#d4dce5'];
    const datasets = kind === 'mix' ? [{data:data.values,backgroundColor:colors,borderColor:'#fff',borderWidth:2}] : kind === 'moat' ? [{label:en ? 'Evidence' : 'Evidência',data:data.values,backgroundColor:'rgba(46,151,105,.13)',borderColor:'#30976b',pointBackgroundColor:'#258e65',pointRadius:5,borderWidth:2}] : [{label:en ? 'Operating cash flow' : 'Caixa operacional',data:data.values,borderColor:'#258e65',backgroundColor:'#258e65',tension:.25,pointRadius:3},{label:en ? 'Net income' : 'Lucro líquido',data:data.other,borderColor:'#6e81d2',backgroundColor:'#6e81d2',tension:.25,pointRadius:3}];
    new Chart(figure.querySelector('canvas'), {
      type:data.type, data:{labels:data.labels,datasets},
      options:{responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{display:kind!=='moat',position:'bottom',labels:{boxWidth:10,font:{size:11}}},tooltip:{callbacks: kind === 'moat' ? {label: ctx => ctx.raw === 2 ? (en ? 'Well supported' : 'Evidência forte') : (en ? 'Partly supported' : 'Evidência parcial')} : {}}},scales: kind === 'moat' ? {r:{min:0,max:2,ticks:{stepSize:1,display:false},pointLabels:{font:{size:11}},grid:{color:'#e2e8f0'},angleLines:{color:'#e2e8f0'}}} : kind === 'cash' ? {x:{grid:{display:false}},y:{beginAtZero:true,grid:{color:'#eef2f5'},ticks:{font:{size:10}}}} : {}}
    });
  }
})();
