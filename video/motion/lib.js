// Shared timeline for the motion clips. render.py calls __seek(t) for every frame, so the
// animation is frame-exact and never depends on wall-clock time.
window.tl = gsap.timeline({ paused: true, defaults: { ease: 'power3.out', duration: 0.8 } });
window.__seek = t => { tl.seek(t, false); };
window.__ready = () => Promise.all(['400 20px "IBM Plex Sans"','500 20px "IBM Plex Sans"','600 20px "IBM Plex Sans"',
  '400 20px "IBM Plex Mono"','500 20px "IBM Plex Mono"','500 20px Fraunces','italic 400 20px Fraunces']
  .map(f => document.fonts.load(f))).then(() => document.fonts.ready).then(() => true);
// Type `text` into el from `at`, at `cps` characters per second.
window.typeOn = (el, text, at, cps = 40) => {
  const o = { n: 0 };
  el.textContent = '';
  tl.to(o, { n: text.length, duration: text.length / cps, ease: 'none',
    onUpdate: () => { el.textContent = text.slice(0, Math.round(o.n)); } }, at);
  return at + text.length / cps;
};
// Draw an SVG path from its start: needs pathLength="1" on the element.
window.draw = (sel, at, dur = 0.7) =>
  tl.fromTo(sel, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: dur, ease: 'power2.inOut' }, at);
