document.querySelectorAll('[data-report-switch]').forEach(select => {
  select.addEventListener('change', () => {
    const locale = select.value === 'en' ? 'en' : 'pt';
    document.cookie = `NEXT_LOCALE=${locale}; Path=/; Max-Age=31536000; SameSite=Lax`;
    window.location.assign(`/published-reports/${select.dataset.reportSwitch}${locale === 'en' ? '-en' : ''}.html`);
  });
});
