/* Плохой пример (ДМ40 п. 5): Вебвизор включён, счётчик без согласия, нет цели заявки, нет trackLinks */
(function () {
  function startYm() {
    var k = document.createElement('script'); k.src = 'https://mc.yandex.ru/metrika/tag.js'; document.head.appendChild(k);
    ym(1, 'init', { webvisor: true });
  }
  startYm();
})();
