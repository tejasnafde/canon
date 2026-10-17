// Shared header and footer for the v2 mocks. data-nav on <body> picks the active menu item.
(function () {
  var on = document.body.dataset.nav || '';
  var items = [['home', 'Home', 'home.html'], ['ask', 'Ask why', 'ask.html'], ['decisions', 'Decisions', 'decisions.html'], ['agents', 'For agents', 'agent.html']];
  var nav = items.map(function (i) { return '<a href="' + i[2] + '"' + (i[0] === on ? ' class="on"' : '') + '>' + i[1] + '</a>'; }).join('');
  document.body.insertAdjacentHTML('afterbegin',
    '<header class="bar"><div class="wrap"><a class="mark" href="home.html">Canon</a><nav class="menu">' + nav +
    '</nav><span class="demo-tag" title="All data here is made up for the demo">Demo company: Northwind Labs (made up)</span></div></header>');
  document.body.insertAdjacentHTML('beforeend',
    '<footer class="foot"><div class="wrap"><span>Canon, the shared memory of a company. Built for the Google Cloud AI Builder Cup 2026.</span>' +
    '<span>All company data is made up.</span><a class="right" href="benchmark.html">How well does it work?</a></div></footer>');
})();
