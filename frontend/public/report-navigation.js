const reportLinks = [...document.querySelectorAll('.toc ol a')];
function highlightReportSection(id) {
  reportLinks.forEach(link => link.classList.toggle('active', link.hash === `#${id}`));
}
if (reportLinks.length) highlightReportSection(location.hash.slice(1) || 'investment_thesis');
reportLinks.forEach(link => link.addEventListener('click', () => highlightReportSection(link.hash.slice(1))));
const reportObserver = new IntersectionObserver(entries => {
  const visible = entries.filter(entry => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
  if (visible.length) highlightReportSection(visible[0].target.id);
}, {rootMargin: '-5% 0px -65% 0px'});
document.querySelectorAll('main > .sec').forEach(section => reportObserver.observe(section));
