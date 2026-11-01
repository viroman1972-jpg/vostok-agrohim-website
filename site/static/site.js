/* Общие скрипты: заявка, «наверх», фото на карточке. Без внешних библиотек. */
(function () {
  var lead = document.getElementById('lead');
  var form = document.getElementById('lead-form');
  var done = document.getElementById('lead-done');
  var msg = document.getElementById('lead-msg');
  var msgHint = msg ? msg.placeholder : '';
  function openLead(product, territory) {
    if (!lead || !lead.showModal) { location.href = '/contacts/'; return; }
    form.hidden = false; done.hidden = true;
    var ref = document.getElementById('lead-ref');
    document.getElementById('lead-product').value = product || '';
    document.getElementById('lead-territory').value = territory || '';
    form.elements.page.value = location.pathname;
    ref.hidden = !(product || territory);
    ref.querySelector('span').textContent = territory ? 'Тип территории:' : 'По препарату:';
    ref.querySelector('strong').textContent = territory || product || '';
    msg.placeholder = territory ? 'Площадь, основные виды растительности, объём препарата' : msgHint;
    lead.showModal();
  }
  document.querySelectorAll('[data-open-lead]').forEach(function (b) {
    b.addEventListener('click', function () { openLead(b.getAttribute('data-product'), b.getAttribute('data-territory')); });
  });
  document.querySelectorAll('dialog').forEach(function (d) {
    d.addEventListener('click', function (e) { if (e.target === d) d.close(); });
    d.querySelectorAll('[data-close]').forEach(function (b) { b.addEventListener('click', function () { d.close(); }); });
  });
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    var fd = new FormData(form);
    fetch(form.action, { method: 'POST', body: fd }).then(function (r) {
      if (!r.ok) throw new Error('bad');
      form.hidden = true; done.hidden = false; form.reset();
    }).catch(function () {
      alert('Не удалось отправить заявку. Позвоните нам по телефону в шапке сайта.');
    });
  });

  var top = document.getElementById('totop');
  if (top) {
    window.addEventListener('scroll', function () { top.classList.toggle('on', window.scrollY > 600); }, { passive: true });
    top.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  }

  // Фото карточки: переключение сторон, увеличение при наведении, окно с крупным фото
  var photo = document.getElementById('photo');
  if (photo) {
    var img = document.getElementById('photo-img');
    var side = 'front';
    var lb = document.getElementById('lightbox');
    var big = document.getElementById('lb-big');
    function set(s) {
      side = s;
      var src = photo.getAttribute('data-' + s) || photo.getAttribute('data-front');
      img.src = src; img.alt = photo.getAttribute('data-alt-' + s) || img.alt;
      big.style.backgroundImage = 'url(' + src + ')';
      document.querySelectorAll('[data-side]').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-side') === s ? 'true' : 'false'); });
    }
    document.querySelectorAll('[data-side]').forEach(function (b) { b.addEventListener('click', function () { set(b.getAttribute('data-side')); }); });
    var fine = window.matchMedia('(hover:hover) and (min-width:640px)');
    img.addEventListener('mousemove', function (e) {
      if (!fine.matches) return;
      var r = img.getBoundingClientRect();
      img.style.transformOrigin = ((e.clientX - r.left) / r.width * 100) + '% ' + ((e.clientY - r.top) / r.height * 100) + '%';
      img.style.transform = 'scale(2.3)';
    });
    img.addEventListener('mouseleave', function () { img.style.transform = ''; });
    document.getElementById('photo-zoom').addEventListener('click', function () { set(side); big.classList.remove('z'); if (lb.showModal) lb.showModal(); });
    big.addEventListener('click', function () { big.classList.toggle('z'); });
    set('front');
  }
  // Вкладки регламента (ДМ31). Без скрипта обе таблицы видны одна под другой.
  var regTabs = document.getElementById('reg-tabs');
  if (regTabs) {
    var tabs = regTabs.querySelectorAll('[role=tab]');
    function pick(tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        if (on) t.removeAttribute('tabindex'); else t.setAttribute('tabindex', '-1');
        document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
      });
    }
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { pick(t); });
      t.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
        e.preventDefault();
        var next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
        pick(next); next.focus();
      });
    });
    regTabs.classList.add('on');
    regTabs.querySelector('[role=tablist]').hidden = false;
    pick(tabs[0]);
  }
  // Окно про cookie. Статистика (Метрика) подключается только после «Принять»; сейчас подключения нет.
  var ck = document.getElementById('cookie');
  if (ck) {
    var saved = null;
    try { saved = localStorage.getItem('cookie-choice'); } catch (e) {}
    if (!saved) ck.classList.add('on');
    ck.querySelectorAll('[data-cookie]').forEach(function (b) {
      b.addEventListener('click', function () {
        try { localStorage.setItem('cookie-choice', b.getAttribute('data-cookie')); } catch (e) {}
        ck.classList.remove('on');
      });
    });
  }
})();
