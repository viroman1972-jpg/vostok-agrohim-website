/* Фильтры, сортировка и листание списка работают в браузере. Все карточки уже есть в HTML. */
(function () {
  var grid = document.getElementById('grid');
  var cards = Array.prototype.slice.call(grid.children);
  var side = document.getElementById('side');
  var chipsEl = document.getElementById('chips'), none = document.getElementById('none');
  var shown = document.getElementById('shown'), empty = document.getElementById('empty');
  var pager = document.getElementById('pager'), pages = document.getElementById('pages');
  var per = +pager.getAttribute('data-per'), page = 1, all = false;
  var boxes = Array.prototype.slice.call(document.querySelectorAll('#side input[type=checkbox]'));
  var pills = Array.prototype.slice.call(document.querySelectorAll('button.qpill[data-group]'));  // ссылки-входы (a.qpill) ведут на другие страницы, входы по территориям открывают форму — не фильтруют
  var pmin = document.getElementById('pmin'), pmax = document.getElementById('pmax');
  var sortEl = document.getElementById('sort');
  var attr = { cat: 'cat', dv: 'dv', crop: 'crop', pest: 'pest', maker: 'maker', action: 'action', term: 'term', pack: 'pack' };
  function pillBoxes(p) {  // кнопка может отмечать несколько значений группы: «Против злаковых сорняков» — однолетние и многолетние
    var vals = p.getAttribute('data-value').split(' ');
    return boxes.filter(function (b) { return b.getAttribute('data-group') === p.getAttribute('data-group') && vals.indexOf(b.value) >= 0; });
  }
  function allOn(list) { return list.length > 0 && list.every(function (b) { return b.checked; }); }
  var moreBtn = document.getElementById('more-filters'), moreLabel = moreBtn.textContent;
  var extras = Array.prototype.slice.call(side.querySelectorAll('.fgroup.extra'));
  function setMore(open) {  // ДМ23: группы под кнопкой «Ещё фильтры»
    extras.forEach(function (g) { g.hidden = !open; });
    moreBtn.textContent = open ? 'Свернуть фильтры' : moreLabel;
    moreBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  moreBtn.addEventListener('click', function () { setMore(moreBtn.getAttribute('aria-expanded') !== 'true'); });

  function num(el) { var v = parseInt((el.value || '').replace(/\D/g, ''), 10); return isNaN(v) ? null : v; }
  function selected() {
    var m = {};
    boxes.forEach(function (b) { if (b.checked) (m[b.getAttribute('data-group')] = m[b.getAttribute('data-group')] || []).push(b); });
    return m;
  }
  function matches(card, sel, lo, hi) {
    for (var g in sel) {
      var have = (card.getAttribute('data-' + attr[g]) || '').split(' ');
      var ok = sel[g].some(function (b) { return have.indexOf(b.value) >= 0; });
      if (!ok) return false;
    }
    var p = +card.getAttribute('data-price');
    if (lo !== null && p < lo) return false;
    if (hi !== null && p > hi) return false;
    return true;
  }
  function sortCards() {
    var v = sortEl.value;
    cards.sort(function (a, b) {
      if (v === 'name') return a.getAttribute('data-name').localeCompare(b.getAttribute('data-name'), 'ru');
      var d = (+a.getAttribute('data-price')) - (+b.getAttribute('data-price'));
      return v === 'price-asc' ? d : -d;
    });
    cards.forEach(function (c) { grid.appendChild(c); });
  }
  function renderChips(sel, lo, hi) {
    chipsEl.innerHTML = '';
    var n = 0;
    boxes.forEach(function (b) {
      if (!b.checked) return; n++;
      var g = b.getAttribute('data-group');
      var t = b.parentNode.querySelector('span').textContent;
      var c = document.createElement('button'); c.type = 'button'; c.className = 'chip';
      c.textContent = (g === 'dv' ? 'ДВ: ' : '') + t;
      c.addEventListener('click', function () { b.checked = false; update(true); });
      chipsEl.appendChild(c);
    });
    if (lo !== null || hi !== null) {
      n++;
      var c2 = document.createElement('button'); c2.type = 'button'; c2.className = 'chip';
      c2.textContent = 'Цена: ' + (lo !== null ? 'от ' + lo : '') + (lo !== null && hi !== null ? ' ' : '') + (hi !== null ? 'до ' + hi : '') + ' ₽';
      c2.addEventListener('click', function () { pmin.value = ''; pmax.value = ''; update(true); });
      chipsEl.appendChild(c2);
    }
    none.hidden = n > 0;
  }
  function update(resetPage) {
    if (resetPage) { page = 1; all = false; }
    var sel = selected(), lo = num(pmin), hi = num(pmax);
    pills.forEach(function (p) {
      p.setAttribute('aria-pressed', allOn(pillBoxes(p)) ? 'true' : 'false');
    });
    renderChips(sel, lo, hi);
    var hit = cards.filter(function (c) { return matches(c, sel, lo, hi); });
    var total = Math.ceil(hit.length / per) || 1;
    if (page > total) page = total;
    var from = all ? 0 : (page - 1) * per, to = all ? hit.length : page * per;
    cards.forEach(function (c) { c.hidden = true; });
    hit.forEach(function (c, i) { c.hidden = !(i >= from && i < to); });
    shown.textContent = 'Показано ' + Math.min(hit.length, to - from) + ' из ' + cards.length;
    empty.hidden = hit.length > 0;
    pager.hidden = hit.length <= per;
    pages.innerHTML = '';
    if (!all) {
      var mk = function (label, p, dis, cur) {
        var b = document.createElement('button'); b.type = 'button'; b.textContent = label; b.disabled = !!dis;
        if (cur) b.setAttribute('aria-current', 'true');
        b.addEventListener('click', function () { page = p; update(); grid.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
        pages.appendChild(b);
      };
      mk('‹ Пред', page - 1, page === 1);
      for (var i = 1; i <= total; i++) mk(String(i), i, false, i === page);
      mk('След ›', page + 1, page === total);
    }
    document.getElementById('show-all').hidden = all;
  }
  boxes.forEach(function (b) { b.addEventListener('change', function () { update(true); }); });
  pills.forEach(function (p) {
    p.addEventListener('click', function () {
      var list = pillBoxes(p), on = !allOn(list);
      list.forEach(function (b) { b.checked = on; });
      var extra = on && list[0] && list[0].closest('.fgroup.extra');
      if (extra) setMore(true);
      update(true);
      if (extra) extra.scrollIntoView({ block: 'center' });  // галочка в свёрнутой группе должна быть видна; в закрытом мобильном окне ничего не делает
    });
  });
  [pmin, pmax].forEach(function (i) { i.addEventListener('change', function () { update(true); }); });
  sortEl.addEventListener('change', function () { sortCards(); update(true); });
  document.getElementById('reset').addEventListener('click', function () {
    boxes.forEach(function (b) { b.checked = false; }); pmin.value = ''; pmax.value = ''; update(true);
  });
  document.getElementById('show-all').addEventListener('click', function () { all = true; update(); });
  document.querySelectorAll('.showmore').forEach(function (btn) {
    btn.addEventListener('click', function () {
      btn.parentNode.querySelectorAll('.more').forEach(function (l) { l.hidden = false; }); btn.hidden = true;
    });
  });
  var openF = document.getElementById('open-filters'), closeF = document.getElementById('close-filters');
  if (openF) openF.addEventListener('click', function () { side.classList.add('open'); });
  if (closeF) closeF.addEventListener('click', function () { side.classList.remove('open'); });
  // SEO-текст (ДМ37): заголовок и два абзаца видны всегда, остальное сворачивается; на телефоне свёрнуто сразу. Без скрипта текст виден целиком.
  var seo = document.querySelector('main .seo');
  if (seo) {
    var kids = [].slice.call(seo.children), cut = 1;
    while (cut < 3 && kids[cut] && kids[cut].tagName !== 'H2') cut++;
    if (kids[cut]) {
      var rest = document.createElement('div'), more = document.createElement('button');
      rest.className = 'seo-rest'; rest.id = 'seo-rest';
      kids.slice(cut).forEach(function (k) { rest.appendChild(k); });
      more.className = 'seo-toggle'; more.type = 'button'; more.setAttribute('aria-controls', 'seo-rest');
      function setSeo(open) {
        rest.hidden = !open;
        more.setAttribute('aria-expanded', open ? 'true' : 'false');
        more.textContent = open ? 'Свернуть' : 'Читать дальше';
      }
      more.addEventListener('click', function () {
        setSeo(rest.hidden);
        if (rest.hidden) more.scrollIntoView({ block: 'center' });  // текст исчез, кнопка не должна оказаться выше экрана
      });
      seo.appendChild(rest); seo.appendChild(more);
      setSeo(!window.matchMedia('(max-width:639px)').matches);
    }
  }
  sortCards(); update(true);
})();
