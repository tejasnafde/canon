// ponytail: mock-only shared top bar, the real app renders this in React.
(function () {
  const here = location.pathname.split('/').pop() || 'home.html';
  const links = [['home.html','Home'],['decision.html','Decisions'],['ask.html','Ask why'],['ingest.html','Ingest'],['agents.html','Agents'],['benchmark.html','Benchmark']];
  document.write(`<header class="bar">
    <a class="mark" href="home.html"><i></i>Canon</a>
    <nav class="nav">${links.map(([h,t]) => `<a href="${h}" class="${h===here?'on':''}">${t}</a>`).join('')}</nav>
    <div class="right">
      <span class="ws">Workspace <b>Northwind Labs</b> / synthetic data</span>
      <span class="live">3 agents connected</span>
    </div>
  </header>`);
})();
