(function () {
  var box = document.getElementById('hero-photo');
  if (!box) return;
  var imgs = box.querySelectorAll('img[data-slide]'), dots = box.querySelectorAll('[data-go]');
  dots.forEach(function (d) {
    d.addEventListener('click', function () {
      var n = +d.getAttribute('data-go');
      imgs.forEach(function (im, i) { im.hidden = i !== n; });
      dots.forEach(function (x, i) { x.setAttribute('aria-pressed', i === n ? 'true' : 'false'); });
    });
  });
})();
