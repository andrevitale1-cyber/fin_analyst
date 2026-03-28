// app/dashboard/reportGenerator.ts (ou src/app/dashboard/reportGenerator.ts)

interface ReportParams {
  result: any;
  isPremium: boolean;
  user: any;
  downloadCount: number;
  setDownloadCount: (count: number) => void;
  setShowUpgradeModal: (show: boolean) => void;
  WEEKLY_DOWNLOAD_LIMIT: number;
}

export const generateAndPrintReport = ({
  result,
  isPremium,
  user,
  downloadCount,
  setDownloadCount,
  setShowUpgradeModal,
  WEEKLY_DOWNLOAD_LIMIT,
}: ReportParams) => {
  if (!isPremium && downloadCount >= WEEKLY_DOWNLOAD_LIMIT) {
    setShowUpgradeModal(true);
    return;
  }
  if (!result) return;

  const meta = result.metadata || {};
  const data = result.data || {};
  const empresa = (meta.empresa || "EMPRESA").toUpperCase();
  const trimestre = meta.trimestre || "";
  const ano = meta.ano || "";
  const periodo = trimestre ? `${trimestre} de ${ano}` : ano;
  const notaFinal = data.nota_geral ?? result.nota_geral ?? "—";
  const analise: string = result.analise_completa || "";

  const scoreColor = (n: number | string): string => {
    const num = Number(n);
    if (isNaN(num)) return "#9ca3af";
    if (num >= 4) return "#059669";
    if (num >= 3) return "#d97706";
    return "#dc2626";
  };

  const icons = {
    receita: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>`,
    lucro: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline></svg>`,
    divida: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
    rentabilidade: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2"><line x1="19" y1="5" x2="5" y2="19"></line><circle cx="6.5" cy="6.5" r="2.5"></circle><circle cx="17.5" cy="17.5" r="2.5"></circle></svg>`,
  };

  const sections = [
    { label: "Receita", nota: data.receita_nota ?? "—", icon: icons.receita, bg: "bg-blue" },
    { label: "Margem / Lucro", nota: data.lucro_nota ?? "—", icon: icons.lucro, bg: "bg-green" },
    { label: "Dívida", nota: data.divida_nota ?? "—", icon: icons.divida, bg: "bg-red" },
    { label: "Rentabilidade", nota: data.rentabilidade_nota ?? "—", icon: icons.rentabilidade, bg: "bg-yellow" },
  ];

  const cleanText = (raw: string) => raw.replace(/\*\*[^*]+\*\*/g, "").replace(/Nota Seção \d+:[^\n]*/g, "").trim();
  
  const introRaw = analise.match(/^[\s\S]*?(?=\*\*Seção 1)/);
  const introText = introRaw ? cleanText(introRaw[0]) : "";

  const rawSections = analise.match(/\*\*Seção \d+[^*]*\*\*[\s\S]*?(?=\*\*Seção \d+|\*\*Nota Geral|$)/g) || [];
  const bodies = rawSections.map(cleanText);

  const teseRaw = analise.match(/Seção 5[\s\S]*?(?=\*\*Seção 6|$)/);
  const teseBody = teseRaw ? cleanText(teseRaw[0]) : (data.tese_investimento || analise || "Nenhuma tese detalhada disponível.");
  const teseParagraphs = teseBody.split("\n\n").filter(Boolean).map((p: string) => `<p>${p.replace(/\*\*/g, "")}</p>`).join("");

  const formatText = (text: string) => {
    if (!text) return "";
    return text
      .replace(/\n\n/g, "</p><p>")
      .replace(/\|(.+)\|/g, "<div style='background:#f1f5f9; padding:8px; border-radius:4px; margin-top:4px; font-family:monospace; font-size:12px;'>|$1|</div>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  };

  const metricCards = sections.map((s) => `
    <div class="card-ind ${s.bg}">
      <div class="card-label"><span>${s.label}</span>${s.icon}</div>
      <div class="card-value">${s.nota}<span>/5</span></div>
    </div>
  `).join("");

  const detalhamentoHTML = bodies.slice(0, 4).map((body, i) => `
    <div class="text-block">
      <h3>Análise de ${sections[i].label}</h3>
      <p>${formatText(body) || "Métrica avaliada dentro da composição da nota geral."}</p>
    </div>
  `).join("");

  const css = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700;800&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #111827; 
      padding: 40px; display: flex; justify-content: center;
      -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important;
    }
    .report-container {
      width: 100%; max-width: 960px; background: #ffffff; border: 1px solid #e2e8f0;
      border-radius: 16px; padding: 50px 60px; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.05);
    }
    .top-nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid #f1f5f9; }
    .brand { font-weight: 700; font-size: 16px; color: #1e3a8a; display: flex; align-items: center; gap: 8px;}
    .brand span { color: #64748b; font-weight: 400; font-size: 14px;}
    .btn-print { background-color: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; }
    
    .hero { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 48px; }
    .hero-title .overline { font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; color: #d97706; font-weight: 700; margin-bottom: 8px; background: #fef3c7; display: inline-block; padding: 4px 12px; border-radius: 100px; }
    .hero-title h1 { font-family: 'Playfair Display', serif; font-size: 46px; font-weight: 800; color: #111827; line-height: 1.1; margin-bottom: 12px; }
    .hero-title p { font-size: 16px; color: #4b5563; max-width: 500px; line-height: 1.6; }
    .hero-score { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px 32px; text-align: right; min-width: 200px; }
    .hero-score .label { font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
    .hero-score .number { font-size: 42px; font-weight: 800; color: #2563eb; line-height: 1; margin-bottom: 8px; }
    .hero-score .number span { font-size: 20px; color: #94a3b8; }

    .section-title { font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 700; color: #111827; margin-bottom: 24px; padding-bottom: 12px; border-bottom: 2px solid #f1f5f9; margin-top: 40px; }
    
    .metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 40px; }
    .card-ind { padding: 20px; border-radius: 12px; border: 1px solid transparent; }
    .bg-blue { background-color: #eff6ff; border-color: #dbeafe; }
    .bg-green { background-color: #ecfdf5; border-color: #d1fae5; }
    .bg-red { background-color: #fef2f2; border-color: #fee2e2; }
    .bg-yellow { background-color: #fffbeb; border-color: #fef3c7; }
    .card-label { font-size: 13px; color: #4b5563; font-weight: 600; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .card-value { font-size: 32px; font-weight: 800; color: #111827; }
    .card-value span { font-size: 16px; color: #94a3b8; font-weight: 600; }

    /* ESTILOS DOS GRÁFICOS */
    .charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 48px; }
    .chart-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; }
    .chart-box h3 { font-size: 15px; font-weight: 600; color: #4b5563; margin-bottom: 16px; }
    .chart-container { position: relative; height: 200px; width: 100%; }

    .detalhamento { columns: 2; column-gap: 40px; margin-bottom: 48px; }
    .text-block { break-inside: avoid; margin-bottom: 24px; }
    .text-block h3 { font-size: 15px; font-weight: 700; color: #1f2937; margin-bottom: 8px; }
    .text-block p { font-size: 14px; line-height: 1.7; color: #4b5563; }

    .conclusao-box { background-color: #1d4ed8; border-radius: 16px; padding: 40px; margin-top: 40px; }
    .conclusao-box h2 { font-family: 'Playfair Display', serif; font-size: 28px; color: #ffffff; margin-bottom: 20px; }
    .conclusao-box p { font-size: 15px; line-height: 1.8; color: #e0e7ff; margin-bottom: 16px; }
    .conclusao-box p:last-child { margin-bottom: 0; }

    @media print {
      body { padding: 0; background: #fff; }
      .report-container { border: none; box-shadow: none; padding: 0; max-width: 100%; }
      .top-nav { display: none; }
      .detalhamento { columns: 1; }
      .chart-box { break-inside: avoid; }
    }
  `;

  const html = `
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8"/>
      <title>Análise ${empresa} - ${periodo}</title>
      <style>${css}</style>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
      <div class="report-container">
        <div class="top-nav">
          <div class="brand">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            FinAnalyzer.AI <span>| Relatório Gerado Automaticamente</span>
          </div>
          <button class="btn-print" onclick="window.print()">
            Baixar Relatório em PDF
          </button>
        </div>

        <div class="hero">
          <div class="hero-title">
            <div class="overline">${periodo}</div>
            <h1>Análise de Resultados<br/>${empresa}</h1>
            <p>Diagnóstico fundamentalista extraído via Inteligência Artificial estruturando rentabilidade, dívida e governança.</p>
          </div>
          <div class="hero-score">
            <div class="label">Score Financeiro</div>
            <div class="number">${notaFinal}<span>/5</span></div>
            <div class="label" style="text-transform: none; font-weight: 400;">Média ponderada</div>
          </div>
        </div>

        ${introText ? `
        <div style="background: #f8fafc; border-left: 4px solid #2563eb; padding: 24px 32px; border-radius: 0 12px 12px 0; margin-bottom: 40px; margin-top: -10px;">
          <p style="font-size: 16px; line-height: 1.8; color: #334155; font-weight: 500;">
            ${formatText(introText)}
          </p>
        </div>
        ` : ''}

        <h2 class="section-title">Principais Indicadores</h2>
        <div class="metrics-grid">
          ${metricCards}
        </div>

        <h2 class="section-title">Evolução Financeira (Exemplo)</h2>
        <div class="charts-grid">
          <div class="chart-box">
            <h3>Evolução da Receita e Lucro</h3>
            <div class="chart-container"><canvas id="chartEvolucao"></canvas></div>
          </div>
          <div class="chart-box">
            <h3>Margens Financeiras</h3>
            <div class="chart-container"><canvas id="chartMargens"></canvas></div>
          </div>
        </div>

        <h2 class="section-title">Análise Detalhada</h2>
        <div class="detalhamento">
          ${bodies.length > 0 ? detalhamentoHTML : `<div class="text-block"><p>O detalhamento por seção não foi fornecido separadamente pela IA nesta execução.</p></div>`}
        </div>

        <div class="conclusao-box">
          <h2>Conclusão Estratégica</h2>
          ${formatText(teseParagraphs)}
        </div>
      </div>

      <script>
        window.onload = function() {
          Chart.defaults.animation = false;
          
          const ctx1 = document.getElementById('chartEvolucao').getContext('2d');
          new Chart(ctx1, {
            type: 'bar',
            data: {
              labels: ['1T25', '2T25', '3T25', '4T25'],
              datasets: [
                { label: 'Receita', data: [120, 150, 180, 210], backgroundColor: '#3b82f6', borderRadius: 4 },
                { label: 'Lucro', data: [30, 45, 60, 80], backgroundColor: '#10b981', borderRadius: 4 }
              ]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true, grid: { display: false } }, x: { grid: { display: false } } } }
          });

          const ctx2 = document.getElementById('chartMargens').getContext('2d');
          new Chart(ctx2, {
            type: 'line',
            data: {
              labels: ['1T25', '2T25', '3T25', '4T25'],
              datasets: [
                { label: 'Margem Bruta (%)', data: [35, 38, 40, 42], borderColor: '#8b5cf6', backgroundColor: '#8b5cf6', tension: 0.4, borderWidth: 3 },
                { label: 'Margem Líquida (%)', data: [15, 18, 22, 25], borderColor: '#f59e0b', backgroundColor: '#f59e0b', tension: 0.4, borderWidth: 3 }
              ]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' } }, x: { grid: { display: false } } } }
          });

          setTimeout(() => { window.print(); }, 800);
        };
      </script>
    </body>
    </html>
  `;

  const win = window.open("", "_blank");
  if (win) {
    if (!isPremium) {
      const newDlCount = downloadCount + 1;
      setDownloadCount(newDlCount);
      localStorage.setItem(`downloads_${user?.id}`, newDlCount.toString());
    }
    win.document.write(html);
    win.document.close();
  }
};