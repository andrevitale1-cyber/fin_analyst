(() => {
  const root = document.documentElement;
  const tools = document.querySelector('.report-reading-tools');
  const contents = document.querySelector('.toc details');
  if (!tools || !contents) return;
  let size = 15;
  tools.addEventListener('click', event => {
    const button = event.target.closest('button[data-reading]');
    if (!button) return;
    const action = button.dataset.reading;
    if (action === 'highlights') {
      const off = document.body.classList.toggle('report-no-highlights');
      button.setAttribute('aria-pressed', String(!off));
    } else if (action === 'serif' || action === 'sans') {
      root.style.setProperty('--report-font', action === 'serif' ? 'ReportLora, Georgia, serif' : 'Arial, Helvetica, sans-serif');
      for (const choice of tools.querySelectorAll('[data-reading="serif"], [data-reading="sans"]')) {
        choice.setAttribute('aria-pressed', String(choice === button));
      }
    } else {
      size = Math.max(14, Math.min(19, size + (action === 'larger' ? 1 : -1)));
      root.style.setProperty('--report-size', `${size}px`);
      tools.querySelector('[data-reading="smaller"]').disabled = size === 14;
      tools.querySelector('[data-reading="larger"]').disabled = size === 19;
    }
  });
  contents.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (!link) return;
    contents.open = false;
    const section = document.getElementById(link.hash.slice(1));
    if (section) {
      section.setAttribute('tabindex', '-1');
      section.focus({ preventScroll: true });
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && contents.open) {
      contents.open = false;
      contents.querySelector('summary').focus();
    }
  });
  document.addEventListener('click', event => {
    if (!contents.contains(event.target)) contents.open = false;
  });
})();
