(() => {
  const en = document.documentElement.lang.startsWith('en');
  for (const frame of document.querySelectorAll('iframe[data-feedback-src][data-report-id]')) {
    const url = new URL(frame.dataset.feedbackSrc, location.href);
    if (url.origin !== location.origin || !/^\/(pt|en)\/report-feedback$/.test(url.pathname) || url.searchParams.get('report') !== frame.dataset.reportId) continue;
    const fallback = document.createElement('div');
    fallback.setAttribute('role', 'status');
    fallback.style.cssText = 'margin:24px 0;padding:16px 18px;border:1px solid #e8eaed;border-radius:10px;background:#fff;color:#657184;font:13px/1.7 Arial,sans-serif';
    const message = document.createElement('span');
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.textContent = en ? 'Try again' : 'Tentar novamente';
    retry.style.cssText = 'display:block;margin-top:8px;padding:8px 12px;min-height:44px;border:1px solid #dbe5df;border-radius:7px;background:#f5f8f6;color:#247552;font:600 12px Arial,sans-serif;cursor:pointer';
    fallback.append(message, retry);
    frame.before(fallback);
    let timer;
    let ready = false;
    function hide() {
      ready = false;
      frame.hidden = true;
      frame.style.display = 'none';
      fallback.hidden = false;
    }
    function unavailable() {
      hide();
      clearTimeout(timer);
      message.textContent = en ? 'Feedback is temporarily unavailable. You can continue reading the report.' : 'A avaliação está temporariamente indisponível. Você pode continuar lendo o relatório.';
      retry.hidden = false;
    }
    function reveal(height) {
      if (!Number.isFinite(height)) return;
      ready = true;
      clearTimeout(timer);
      frame.style.height = `${Math.max(160, Math.min(600, height))}px`;
      frame.hidden = false;
      frame.style.display = 'block';
      fallback.hidden = true;
    }
    function load() {
      hide();
      retry.hidden = true;
      message.textContent = en ? 'Loading report feedback…' : 'Carregando avaliação do relatório…';
      clearTimeout(timer);
      timer = setTimeout(unavailable, 15000);
      frame.src = url.href;
    }
    window.addEventListener('message', event => {
      if (event.origin !== location.origin || event.source !== frame.contentWindow) return;
      const data = event.data;
      if (data?.type !== 'finanalyser:feedback-ready' || data.reportId !== frame.dataset.reportId) return;
      reveal(data.height);
    });
    frame.addEventListener('load', () => {
      // A successful iframe load can still contain a raw server error document.
      try {
        const section = frame.contentDocument?.querySelector('[data-feedback-ready="true"]');
        if (section?.dataset.feedbackReport === frame.dataset.reportId) {
          reveal(Math.ceil(section.getBoundingClientRect().height + 40));
        } else if (ready) {
          unavailable();
        }
      } catch { unavailable(); }
    });
    frame.addEventListener('error', unavailable);
    retry.addEventListener('click', load);
    // Hidden lazy iframes never enter the viewport; loading is gated by readiness instead.
    frame.loading = 'eager';
    load();
  }
})();
