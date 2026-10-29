const versions = await fetch('/mobile-redesign-preview/review-versions.json').then(response => { if (!response.ok) throw new Error('Не загружен список версий'); return response.json(); });
const frame = document.getElementById('prototype');
const links = [...document.querySelectorAll('[data-version]')];
const findVersion = () => versions.versions.find(v => v.id === new URLSearchParams(location.search).get('version')) || versions.versions.find(v => v.id === versions.default_version);
let selected;
function render() {
  const version = findVersion();
  const route = location.hash.startsWith('#/') ? location.hash : '#/';
  links.forEach(link => { if (link.dataset.version === version.id) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current'); link.href = '/mobile-redesign-preview/?version=' + link.dataset.version + route; });
  document.title = 'DonorSearch · ' + version.label + ' · дизайн не утверждён';
  frame.title = 'DonorSearch · интерактивный вариант ' + version.label + ' · дизайн не утверждён';
  if (selected !== version.id) { selected = version.id; frame.src = version.url + '?width=393' + route; }
  else if (frame.contentWindow && frame.contentWindow.location.hash !== route) frame.contentWindow.location.hash = route;
}
links.forEach(link => link.addEventListener('click', event => {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
  event.preventDefault();
  const target = new URL(link.href);
  const childRoute = frame.contentWindow.location.hash;
  if (childRoute.startsWith('#/')) target.hash = childRoute;
  history.pushState(null, '', target);
  render();
}));
frame.addEventListener('load', () => {
  const syncRoute = () => {
    const childHash = frame.contentWindow.location.hash;
    if (!childHash.startsWith('#/')) return;
    const url = new URL(location.href);
    url.searchParams.set('version', selected);
    url.hash = childHash;
    history.replaceState(null, '', url);
    links.forEach(link => { link.href = '/mobile-redesign-preview/?version=' + link.dataset.version + childHash; });
  };
  frame.contentWindow.addEventListener('hashchange', syncRoute);
  frame.contentDocument.addEventListener('click', () => requestAnimationFrame(syncRoute));
  syncRoute();
});
window.addEventListener('popstate', render);
window.addEventListener('hashchange', render);
render();
