/* Shared game menu. Each page includes <div id="site-menu"></div> and <script src="menu.js"></script>. */
(function () {
  var ITEMS = [
    { f: 'index.html', l: 'Hub' },
    { f: 'flashcard.html', l: '01 / Face Match' },
    { f: 'teams.html', l: '02 / Logo Match' },
    { f: 'trivia.html', l: '03 / Stat Sheet Trivia' }
  ];

  var CSS = [
    ".site-menu{position:relative;margin:0 0 28px;font-family:'DM Mono',ui-monospace,monospace}",
    ".site-menu__bar{display:flex;align-items:center;gap:14px}",
    ".site-menu__hub{color:var(--coral-dark,#4f32d6);font-size:11px;letter-spacing:.08em;text-transform:uppercase;text-decoration:none}",
    ".site-menu__hub:hover{text-decoration:underline}",
    ".site-menu__toggle{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid var(--ink,#17222c);background:var(--white,#fffdf8);color:var(--ink,#17222c);font:12px 'DM Mono',ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;cursor:pointer}",
    ".site-menu__toggle:hover{border-color:var(--coral,#6d4cff);color:var(--coral-dark,#4f32d6)}",
    ".site-menu__chev{transition:transform .15s ease}",
    ".site-menu__toggle[aria-expanded='true'] .site-menu__chev{transform:rotate(180deg)}",
    ".site-menu__panel{position:absolute;top:calc(100% + 6px);left:0;z-index:50;min-width:240px;display:grid;gap:2px;padding:8px;border:1px solid var(--ink,#17222c);background:var(--white,#fffdf8);box-shadow:8px 8px 0 rgba(23,34,44,.12)}",
    ".site-menu__panel[hidden]{display:none}",
    ".site-menu__panel a{padding:9px 10px;color:var(--muted,#71808b);font-size:12px;letter-spacing:.06em;text-transform:uppercase;text-decoration:none}",
    ".site-menu__panel a:hover{background:var(--paper,#f3f1f7);color:var(--coral-dark,#4f32d6)}",
    ".site-menu__panel a.is-current{color:var(--ink,#17222c);border-left:3px solid var(--coral,#6d4cff);padding-left:7px}",
    "@media (max-width:560px){.site-menu{margin-bottom:16px}.site-menu__panel{min-width:min(280px,calc(100vw - 40px))}}"
  ].join('');

  function init() {
    var mount = document.getElementById('site-menu');
    if (!mount) return;

    var current = (location.pathname.split('/').pop() || 'index.html').toLowerCase() || 'index.html';

    if (!document.getElementById('site-menu-style')) {
      var style = document.createElement('style');
      style.id = 'site-menu-style';
      style.textContent = CSS;
      document.head.appendChild(style);
    }

    var bar = document.createElement('div');
    bar.className = 'site-menu';
    bar.innerHTML =
      '<div class="site-menu__bar">' +
        '<a class="site-menu__hub" href="index.html">← Hub</a>' +
        '<button type="button" class="site-menu__toggle" aria-haspopup="true" aria-expanded="false" aria-controls="siteMenuPanel">Menu <span class="site-menu__chev" aria-hidden="true">▾</span></button>' +
      '</div>' +
      '<div class="site-menu__panel" id="siteMenuPanel" role="menu" hidden></div>';

    var panel = bar.querySelector('#siteMenuPanel');
    ITEMS.forEach(function (item) {
      var a = document.createElement('a');
      a.href = item.f;
      a.textContent = item.l;
      a.setAttribute('role', 'menuitem');
      if (item.f.toLowerCase() === current) {
        a.className = 'is-current';
        a.setAttribute('aria-current', 'page');
      }
      panel.appendChild(a);
    });

    mount.replaceWith(bar);

    var toggle = bar.querySelector('.site-menu__toggle');
    function onDocClick(e) { if (!bar.contains(e.target)) close(); }
    function onKey(e) { if (e.key === 'Escape') { close(); toggle.focus(); } }
    function open() {
      panel.hidden = false;
      toggle.setAttribute('aria-expanded', 'true');
      document.addEventListener('click', onDocClick, true);
      document.addEventListener('keydown', onKey, true);
    }
    function close() {
      panel.hidden = true;
      toggle.setAttribute('aria-expanded', 'false');
      document.removeEventListener('click', onDocClick, true);
      document.removeEventListener('keydown', onKey, true);
    }
    toggle.addEventListener('click', function () { panel.hidden ? open() : close(); });
    panel.addEventListener('click', function (e) { if (e.target.tagName === 'A') close(); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
