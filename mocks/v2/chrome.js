// Shared header and footer for the v2 mocks. data-nav on <body> picks the active menu item.
(function () {
  var on = document.body.dataset.nav || '';
  var items = [['home', 'Home', 'home.html'], ['ask', 'Ask why', 'ask.html'], ['decisions', 'Decisions', 'decisions.html'], ['agents', 'For agents', 'agent.html'], ['bench', 'How well does it work?', 'benchmark.html', 'far']];
  var nav = items.map(function (i) {
    var cls = [i[3] || '', i[0] === on ? 'on' : ''].join(' ').trim();
    return '<a href="' + i[2] + '"' + (cls ? ' class="' + cls + '"' : '') + '>' + i[1] + '</a>';
  }).join('');
  document.body.insertAdjacentHTML('afterbegin',
    '<header class="bar"><div class="wrap"><a class="mark" href="home.html">Canon</a><nav class="menu">' + nav + '</nav></div></header>');
  document.body.insertAdjacentHTML('beforeend',
    '<footer class="foot"><div class="wrap"><span>Canon is the shared memory of a company. Built for the Google Cloud AI Builder Cup 2026.</span>' +
    '<span>Northwind Labs is a made-up company. Every name, customer and quote is invented.</span></div></footer>');
})();
