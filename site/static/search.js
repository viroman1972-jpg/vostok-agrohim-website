/* Поиск по каталогу (ДМ38). Индекс собирается при сборке и загружается при первом обращении; цен в нём нет. */
(function () {
  var STOP = { 'от': 1, 'на': 1, 'для': 1, 'против': 1, 'по': 1, 'и': 1, 'в': 1, 'с': 1, 'к': 1, 'при': 1, 'препарат': 1, 'препараты': 1, 'препарата': 1, 'препаратов': 1, 'средство': 1, 'средства': 1, 'купить': 1, 'цена': 1 };
  var ENDING = /(ами|ями|ого|его|ому|ему|ыми|ими|ых|их|ой|ей|ую|юю|ая|яя|ое|ее|ые|ие|ый|ий|ов|ев|ом|ем|ах|ях|ам|ям|а|я|ы|и|е|у|ю|о|ь)$/;
  var PRODUCTS = 6, SECTIONS = 3;
  var index = null, loading = null;

  function norm(t) { return t.toLowerCase().replace(/ё/g, 'е').replace(/[^0-9a-zа-я]+/g, ' ').trim(); }  // как search_norm в build.py
  function stem(w) {  // «на пшенице» находит «Пшеница»; основа короче трёх букв нашла бы лишнее
    var s = w.replace(ENDING, '');
    return s.length >= 3 ? s : w;
  }
  function has(words, t) { return words.some(function (w) { return w.indexOf(t) === 0; }); }
  function tokens(q) { return norm(q).split(' ').filter(function (w) { return w && !STOP[w]; }).map(stem); }

  function load() {
    if (!loading) {
      loading = fetch('/static/search-index.json').then(function (r) {
        if (!r.ok) throw new Error('index');
        return r.json();
      }).then(function (d) {
        d.products.forEach(function (p) { p.wa = p.a.split(' '); p.wb = p.b.split(' '); p.wc = p.c.split(' '); });
        d.sections.forEach(function (x) { x.wa = x.a.split(' '); });
        index = d;
      }).catch(function (e) { loading = null; throw e; });
    }
    return loading;
  }
  // Совпасть должны все слова запроса; выше те, где слово нашлось в названии, затем в ДВ и категории
  function find(q) {
    var ts = tokens(q), products = [], sections = [];
    if (!ts.length || norm(q).length < 2 || !index) return { empty: true, products: products, sections: sections };
    index.products.forEach(function (p) {
      var score = 0;
      for (var i = 0; i < ts.length; i++) {
        var s = has(p.wa, ts[i]) ? 3 : has(p.wb, ts[i]) ? 2 : has(p.wc, ts[i]) ? 1 : 0;
        if (!s) return;
        score += s;
      }
      products.push({ p: p, score: score });
    });
    products.sort(function (x, y) { return y.score - x.score || x.p.name.localeCompare(y.p.name, 'ru'); });
    index.sections.forEach(function (x) {
      if (ts.every(function (t) { return has(x.wa, t); })) sections.push(x);
    });
    sections.sort(function (x, y) { return x.wa.length - y.wa.length || x.name.localeCompare(y.name, 'ru'); });
    return { products: products.map(function (x) { return x.p; }), sections: sections };
  }
  window.catalogSearch = { load: load, find: find, none: function () {
    return document.getElementById('search-none').content.cloneNode(true);
  } };

  function row(url, name, about) {
    var a = document.createElement('a'), n = document.createElement('span'), m = document.createElement('span');
    a.href = url; n.className = 'n'; n.textContent = name; m.className = 'm'; m.textContent = about;
    a.appendChild(n); a.appendChild(m);
    return a;
  }
  function render(box, q) {
    var res = find(q);
    box.innerHTML = '';
    box.hidden = !!res.empty;
    if (res.empty) return;
    if (!res.products.length && !res.sections.length) { box.appendChild(window.catalogSearch.none()); return; }
    res.products.slice(0, PRODUCTS).forEach(function (p) { box.appendChild(row(p.url, p.name, p.about)); });
    res.sections.slice(0, SECTIONS).forEach(function (x) { box.appendChild(row(x.url, x.name, x.label)); });
    if (res.products.length) {
      var all = document.createElement('a');
      all.className = 'all'; all.href = '/catalog/all/?q=' + encodeURIComponent(q);
      all.textContent = 'Все результаты: ' + res.products.length + ' →';
      box.appendChild(all);
    }
  }
  document.querySelectorAll('form[data-search]').forEach(function (form) {
    var input = form.querySelector('input'), box = form.querySelector('.sres');
    function close() { box.hidden = true; }
    function show() {
      var q = input.value;
      load().then(function () { if (input.value === q) render(box, q); }).catch(close);  // индекс не загрузился: Enter всё равно ведёт на страницу результатов
    }
    input.addEventListener('focus', function () { load().catch(function () {}); if (input.value) show(); });
    input.addEventListener('input', show);
    form.addEventListener('keydown', function (e) {
      var links = [].slice.call(box.querySelectorAll('a')), i = links.indexOf(document.activeElement);
      if (e.key === 'Escape') { close(); input.focus(); }
      else if (e.key === 'ArrowDown' && links.length) { e.preventDefault(); links[Math.min(i + 1, links.length - 1)].focus(); }
      else if (e.key === 'ArrowUp' && i >= 0) { e.preventDefault(); (i ? links[i - 1] : input).focus(); }
    });
    document.addEventListener('click', function (e) { if (!form.contains(e.target)) close(); });
  });

  // Значок в шапке: без скрипта это обычная ссылка на страницу с полем поиска
  var open = document.getElementById('search-open'), bar = document.getElementById('search-bar');
  function setBar(on) {
    bar.hidden = !on;
    open.setAttribute('aria-expanded', on ? 'true' : 'false');
    if (on) bar.querySelector('input').focus();
  }
  open.addEventListener('click', function (e) { e.preventDefault(); setBar(bar.hidden); });
  bar.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !bar.querySelector('input').value) { setBar(false); open.focus(); }
  });
  document.addEventListener('click', function (e) {
    if (!bar.hidden && !bar.contains(e.target) && !open.contains(e.target)) setBar(false);
  });
})();
