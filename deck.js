/* Estimation & Filtering: one engine for both modes.
   - index.html: the browser never leaves the shell; each slide is fetched from
     slides/ and swapped into #stage with a fade. Changing slide is the shell's job
     and happens only here.
   - slides/NN-*.html: the same file runs standalone, showing its own build steps
     and nothing else. It never loads another slide file.
   Everything this file needs is embedded in the page that loads it. */

const DECK = [
  { file: '01-nonlinearity-big-picture.html', title: 'The nonlinearity big picture', steps: 1 },
  { file: '02-nonlinear-model.html', title: 'The nonlinear model', steps: 5 },
  { file: '03-four-filters-side-by-side.html', title: 'The four filters side by side', steps: 4 },
  { file: '04-nonlinear-transformation-of-the-mean.html', title: 'Nonlinear transformation of the mean', steps: 4 },
  { file: '05-target-observed-by-radar.html', title: 'A target observed by radar', steps: 3 },
  { file: '06-less-certain-about-position.html', title: 'Less certain about position', steps: 4 },
  { file: '07-when-does-linearization-matter.html', title: 'When does linearization matter?', steps: 2 },
  { file: '08-engineering-applications.html', title: 'Engineering applications', steps: 1 },
  { file: '09-example-application-kf.html', title: 'Example application: KF', steps: 4 },
  { file: '10-example-application-ekf.html', title: 'Example application: EKF', steps: 4 },
  { file: '11-example-application-ukf.html', title: 'Example application: UKF', steps: 4 },
  { file: '12-why-not-ckf.html', title: "But why didn't we choose CKF?", steps: 1 },
  { file: '13-ukf-or-ckf.html', title: 'UKF or CKF?', steps: 3 },
  { file: '14-right-choice.html', title: "So what's the right choice?", steps: 5 },
  { file: '15-limitations-of-kalman-filters.html', title: 'Limitations of Kalman filters', steps: 5 }
];

const stage = document.getElementById('stage');
const SHELL = !!stage;
const counter = document.getElementById('counter');
const cache = new Map();
const pageFile = decodeURIComponent((location.pathname.split('/').pop() || '').split('?')[0]);

let cur = SHELL ? -1 : Math.max(0, DECK.findIndex(entry => entry.file === pageFile));
let build = 1;
let steps = 1;
let busy = false;
let observers = [];
let robotFrame = null;
let ukfFlying = false;
let robot = null;
let ukf = null;

const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const nextFrame = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
const slideUrl = i => SHELL ? 'slides/' + DECK[i].file : DECK[i].file;
const sectionEl = () => SHELL ? stage.querySelector('.slide') : document.querySelector('.slide');
const clampBuild = (value, max) => Math.max(1, Math.min(max, Number.isFinite(value) && value >= 1 ? value : 1));

/* --------------------------------------------------------------- loading */
async function fetchSlide(i){
  if (cache.has(i)) return cache.get(i);
  const response = await fetch(slideUrl(i), { cache: 'no-cache' });
  if (!response.ok) throw new Error(response.status + ' ' + response.statusText + ' · ' + slideUrl(i));
  const html = await response.text();
  cache.set(i, html);
  return html;
}

function prefetch(i){
  if (!SHELL || i < 0 || i >= DECK.length || cache.has(i)) return;
  fetchSlide(i).catch(() => {});
}

function teardown(){
  observers.forEach(observer => observer.disconnect());
  observers = [];
  if (robotFrame !== null){ cancelAnimationFrame(robotFrame); robotFrame = null; }
  ukfFlying = false;
  robot = null;
  ukf = null;
}

/* ------------------------------------------------------------- slide parts */
function initChart(section){
  const costSlide = section.querySelector('.cost-slide');
  if (!costSlide) return;
  const radarChart = costSlide.querySelector('.body > svg');
  const svgNS = 'http://www.w3.org/2000/svg';
  const axes = radarChart.querySelector('g');
  const series = Array.from(radarChart.children).filter(el => el.tagName.toLowerCase() === 'g').slice(1);
  const makeSvg = (name, attrs, text) => {
    const el = document.createElementNS(svgNS, name);
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
    if (text !== undefined) el.textContent = text;
    return el;
  };
  const chartDefs = makeSvg('defs', {});
  const plotClip = makeSvg('clipPath', { id: 'radar-chart-clip' });
  plotClip.append(makeSvg('rect', { x: 100, y: 65, width: 850, height: 300 }));
  chartDefs.append(plotClip);
  radarChart.prepend(chartDefs);
  const chartMarks = [];
  const fromOriginal = (x, y) => [25 + (x - 100) * 1175 / 850, (365 - y) * 850 / 300];
  series.forEach(group => {
    group.removeAttribute('data-step');
    const clipped = makeSvg('g', { 'clip-path': 'url(#radar-chart-clip)' });
    Array.from(group.children).forEach(el => {
      if (el.matches('polygon, polyline')) {
        const points = el.getAttribute('points').trim().split(/\s+/).map(pair => fromOriginal(...pair.split(',').map(Number)));
        chartMarks.push({ el, points });
        clipped.append(el);
      } else if (el.matches('circle')) {
        chartMarks.push({ el, points: [fromOriginal(Number(el.getAttribute('cx')), Number(el.getAttribute('cy')))] });
        clipped.append(el);
      }
    });
    group.prepend(clipped);
  });
  let chartRange = [25, 1200, 0, 850];
  function drawRadarChart(){
    const [xmin, xmax, ymin, ymax] = chartRange;
    const px = x => 100 + (x - xmin) / (xmax - xmin) * 850;
    const py = y => 365 - (y - ymin) / (ymax - ymin) * 300;
    const format = value => Number(value.toFixed(xmax - xmin < 10 || ymax - ymin < 10 ? 2 : 1)).toString();
    axes.replaceChildren();
    const xticks = xmin === 25 && xmax === 1200 ? [25, 200, 400, 600, 800, 1000, 1200] : Array.from({ length: 6 }, (_, i) => xmin + (xmax - xmin) * i / 5);
    const yticks = ymin === 0 && ymax === 850 ? [0, 200, 400, 600, 800] : Array.from({ length: 6 }, (_, i) => ymin + (ymax - ymin) * i / 5);
    yticks.forEach(y => {
      axes.append(makeSvg('path', { d: `M100 ${py(y)} H950`, stroke: 'var(--line)' }));
      axes.append(makeSvg('text', { x: 80, y: py(y) + 7, 'text-anchor': 'end' }, format(y)));
    });
    xticks.forEach(x => axes.append(makeSvg('text', { x: px(x), y: 398, 'text-anchor': 'middle' }, format(x))));
    axes.append(makeSvg('text', { x: 100, y: 30 }, 'Position RMSE (m), first 30 updates'));
    axes.append(makeSvg('text', { x: 525, y: 437, 'text-anchor': 'middle' }, 'Initial position standard deviation per axis (m)'));
    chartMarks.forEach(({ el, points }) => {
      if (el.tagName.toLowerCase() === 'circle') {
        el.setAttribute('cx', px(points[0][0]));
        el.setAttribute('cy', py(points[0][1]));
      } else el.setAttribute('points', points.map(([x, y]) => `${px(x)},${py(y)}`).join(' '));
    });
  }
  function zoomRadarChart(factor, ax = .5, ay = .5){
    const [xmin, xmax, ymin, ymax] = chartRange;
    const width = Math.max(.5, Math.min(2350, (xmax - xmin) * factor));
    const height = Math.max(.05, Math.min(1700, (ymax - ymin) * factor));
    const x = xmin + ax * (xmax - xmin), y = ymin + ay * (ymax - ymin);
    chartRange = [x - ax * width, x + (1 - ax) * width, y - ay * height, y + (1 - ay) * height];
    drawRadarChart();
  }
  function resetRadarChart(){ chartRange = [25, 1200, 0, 850]; drawRadarChart(); }
  const chartPoint = event => new DOMPoint(event.clientX, event.clientY).matrixTransform(radarChart.getScreenCTM().inverse());
  radarChart.addEventListener('wheel', event => {
    const p = chartPoint(event);
    if (p.x < 100 || p.x > 950 || p.y < 65 || p.y > 365) return;
    event.preventDefault();
    zoomRadarChart(Math.exp(Math.max(-.3, Math.min(.3, event.deltaY * .002))), (p.x - 100) / 850, (365 - p.y) / 300);
  }, { passive: false });
  let chartDrag = null;
  radarChart.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    const p = chartPoint(event);
    if (p.x < 100 || p.x > 950 || p.y < 65 || p.y > 365) return;
    event.preventDefault();
    chartDrag = { point: p, range: [...chartRange] };
    radarChart.setPointerCapture(event.pointerId);
  });
  radarChart.addEventListener('pointermove', event => {
    if (!chartDrag) return;
    const p = chartPoint(event), r = chartDrag.range;
    const dx = (p.x - chartDrag.point.x) / 850 * (r[1] - r[0]);
    const dy = (p.y - chartDrag.point.y) / 300 * (r[3] - r[2]);
    chartRange = [r[0] - dx, r[1] - dx, r[2] + dy, r[3] + dy];
    drawRadarChart();
  });
  radarChart.addEventListener('pointerup', () => { chartDrag = null; });
  radarChart.addEventListener('pointercancel', () => { chartDrag = null; });
  radarChart.addEventListener('lostpointercapture', () => { chartDrag = null; });
  radarChart.addEventListener('dblclick', resetRadarChart);
  drawRadarChart();
}

function initRadar(section){
  const radarScene = section.querySelector('.radar-setup');
  if (!radarScene) return;
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => radarScene.classList.toggle('radar-active', entry.isIntersecting));
  }, { threshold: 0.35 });
  observer.observe(radarScene);
  observers.push(observer);
}

function initRobot(section){
  const scene = section.querySelector('.robot-scene');
  if (!scene) return;
  const driving = scene.querySelector('.scene-driving');
  const path = scene.querySelector('#robot-drive-path');
  if (!driving || !path) return;
  robot = {
    scene,
    driving,
    rays: scene.querySelector('#robot-sensor-rays'),
    origin: scene.querySelector('#robot-sensor-origin'),
    path,
    length: path.getTotalLength()
  };
}

function initModelReveal(section){
  const modelGroup = section.querySelector('.model-group');
  if (!modelGroup) return;
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting){
        modelGroup.classList.remove('model-enter');
        void modelGroup.getBoundingClientRect();
        modelGroup.classList.add('model-enter');
      } else {
        modelGroup.classList.remove('model-enter');
      }
    });
  }, { threshold: 0.55 });
  observer.observe(section);
  observers.push(observer);
}

function initCkfQuestion(section){
  const question = section.querySelector('.ckf-question');
  if (!question) return;
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => question.classList.toggle('question-visible', entry.isIntersecting));
  }, { threshold: 0.55 });
  observer.observe(question);
  observers.push(observer);
}

function initSlide(section){
  initChart(section);
  initRadar(section);
  initRobot(section);
  initModelReveal(section);
  initCkfQuestion(section);
  const scene = section.querySelector('.ukf-scene');
  ukf = scene ? { scene, fly: scene.querySelector('#ukf-fly') } : null;
}

/* ------------------------------------------------------------- animations */
function setSensorPosition(x, y){
  if (!robot || !robot.rays || !robot.origin) return;
  robot.rays.setAttribute('d', `M${x} ${y} L405 91 M${x} ${y} L800 80`);
  robot.origin.setAttribute('cx', x);
  robot.origin.setAttribute('cy', y);
}

function updateRobotAnimation(section){
  if (!robot) return;
  if (robotFrame !== null) cancelAnimationFrame(robotFrame);
  robotFrame = null;
  robot.driving.setAttribute('transform', 'translate(0 0)');
  const step = Number(section.dataset.build);
  setSensorPosition(step >= 3 ? 635.75 : 525, step >= 3 ? 186.65 : 214);
  if (step !== 4 || reducedMotion()) return;
  let start;
  function frame(time){
    if (start === undefined) start = time;
    const distance = ((time - start) % 8000) / 8000 * robot.length;
    const position = robot.path.getPointAtLength(distance);
    const dx = position.x - 630;
    const dy = position.y - 220;
    robot.driving.setAttribute('transform', `translate(${dx} ${dy})`);
    setSensorPosition(635.75 + dx, 186.65 + dy);
    robotFrame = requestAnimationFrame(frame);
  }
  robotFrame = requestAnimationFrame(frame);
}

function updateUkfAnimation(section){
  if (!ukf || !ukf.fly) return;
  const on = Number(section.dataset.build) === 4 && !reducedMotion();
  if (on && !ukfFlying){ ukf.fly.beginElement(); ukfFlying = true; }
  else if (!on && ukfFlying){ ukf.fly.endElement(); ukfFlying = false; }
}

function updateSplitLists(section){
  const list = section && section.querySelector('.split-text');
  if (!list) return;
  const items = Array.from(list.querySelectorAll('.step'));
  items.forEach(el => { el.classList.remove('on'); el.classList.remove('current'); });
  const visible = items.filter(el => parseInt(el.dataset.n, 10) <= build);
  visible.forEach(el => el.classList.add('on'));
  if (visible.length) visible[visible.length - 1].classList.add('current');
  const rail = list.querySelector('.rail');
  const railActive = list.querySelector('.rail-active');
  if (!rail) return;
  if (!visible.length){
    rail.style.height = '0px';
    if (railActive) railActive.style.opacity = '0';
    return;
  }
  const current = visible[visible.length - 1];
  const textTop = list.getBoundingClientRect().top;
  const box = current.getBoundingClientRect();
  rail.style.height = Math.max(0, box.bottom - textTop - 14) + 'px';
  if (railActive){
    railActive.style.opacity = '1';
    railActive.style.top = (box.top - textTop) + 'px';
    railActive.style.height = box.height + 'px';
  }
}

/* ----------------------------------------------------------------- engine */
function apply(){
  const section = sectionEl();
  if (!section || cur < 0) return;
  section.dataset.build = String(build);
  section.querySelectorAll('[data-step]').forEach(el => {
    el.classList.toggle('on', parseInt(el.dataset.step, 10) <= build);
  });
  updateSplitLists(section);
  updateRobotAnimation(section);
  updateUkfAnimation(section);
  if (counter){
    counter.innerHTML = '<span class="current-slide">' + (cur + 1) + '</span>'
      + '<span class="total-slides"> / ' + DECK.length + '</span>';
  }
  document.title = (cur + 1) + ' · ' + DECK[cur].title + ' · Estimation & Filtering';
  try {
    history.replaceState(null, '', SHELL ? '#' + (cur + 1) + '.' + build : '#' + build);
  } catch (e) { /* file:// may refuse; the deck still works */ }
}

function showError(error){
  const message = String(error.message).replace(/[<>&]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]));
  stage.innerHTML = '<div class="deck-error">'
    + '<h1>Cannot load the slides</h1>'
    + '<p>' + message + '</p>'
    + '<p>Serve this folder over HTTP, for example from a terminal:<br>'
    + '<code>python3 -m http.server 8765</code><br>then open '
    + '<code>http://localhost:8765/</code>.</p>'
    + '</div>';
}

/* ---------------------------------------------- shell mode: swap fragments */
async function goShell(i, wantedBuild, options = {}){
  if (busy || i < 0 || i >= DECK.length) return;
  busy = true;
  const first = cur < 0;
  const animate = options.animate !== false && !reducedMotion() && !first;
  try {
    const html = await fetchSlide(i);
    if (animate){
      stage.classList.add('fading');
      await wait(200);
    }
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const section = doc.querySelector('.slide');
    if (!section) throw new Error('No .slide element in ' + slideUrl(i));

    teardown();
    stage.replaceChildren(section);
    cur = i;
    steps = Math.max(1, parseInt(section.dataset.steps || '1', 10));
    build = clampBuild(wantedBuild === undefined ? 1 : wantedBuild, steps);

    initSlide(section);
    apply();
    typeset(section);

    if (first){
      stage.classList.add('appearing');
      setTimeout(() => stage.classList.remove('appearing'), 400);
    } else if (animate){
      await nextFrame();
      stage.classList.remove('fading');
    }
    prefetch(i + 1);
  } catch (error) {
    stage.classList.remove('fading', 'appearing');
    showError(error);
  } finally {
    busy = false;
  }
}

/* --------------------------------- page mode: a slide only steps its builds */
function go(i, wantedBuild, options){
  if (SHELL) goShell(i, wantedBuild, options);
}

function next(){
  if (busy || cur < 0) return;
  if (build < steps){ build++; apply(); }
}

function prev(){
  if (busy || cur < 0) return;
  if (build > 1){ build--; apply(); }
}

function jumpTo(value){
  if (!SHELL && value >= 1 && value <= steps && value !== build){ build = value; apply(); }
}

/* ---------------------------------------------------------------- mathjax */
function typeset(section){
  if (!window.MathJax || !MathJax.typesetPromise) return;
  MathJax.typesetPromise([section])
    .then(() => updateSplitLists(section))
    .catch(() => {});
}

/* ------------------------------------------------------------------ input */
document.addEventListener('keydown', event => {
  if (event.key === 'ArrowRight' || event.key === 'PageDown' || event.key === ' '){ event.preventDefault(); next(); }
  if (event.key === 'ArrowLeft' || event.key === 'PageUp'){ event.preventDefault(); prev(); }
  if (event.key === 'Home'){ if (SHELL) go(0, 1); else jumpTo(1); }
  if (event.key === 'End'){ if (SHELL) go(DECK.length - 1, DECK[DECK.length - 1].steps); else jumpTo(steps); }
  if ((event.key === 'f' || event.key === 'F') && !event.metaKey && !event.ctrlKey && !event.altKey){
    if (document.fullscreenElement) document.exitFullscreen?.();
    else document.documentElement.requestFullscreen?.();
  }
});

window.addEventListener('resize', () => {
  const section = sectionEl();
  if (section) updateSplitLists(section);
});

if (SHELL){
  window.addEventListener('hashchange', () => {
    const match = location.hash.match(/^#(\d+)(?:\.(\d+))?$/);
    if (!match) return;
    const target = Number(match[1]) - 1;
    const wanted = Number(match[2] || 1);
    if (target !== cur) goShell(target, wanted);
    else if (wanted !== build && wanted >= 1 && wanted <= steps){ build = wanted; apply(); }
  });
} else {
  window.addEventListener('hashchange', () => {
    const match = location.hash.match(/^#(\d+)(?:\.(\d+))?$/);
    if (!match) return;
    const wanted = Number(match[2] || match[1]);
    if (wanted !== build && wanted >= 1 && wanted <= steps){ build = wanted; apply(); }
  });
}

/* MathJax arrives after this script: typeset whatever is already on screen. */
window.addEventListener('load', () => {
  const section = sectionEl();
  if (section) typeset(section);
});

/* ------------------------------------------------------------------ start */
const startMatch = location.hash.match(/^#(\d+)(?:\.(\d+))?$/);

if (SHELL){
  if (startMatch) goShell(Number(startMatch[1]) - 1, Number(startMatch[2] || 1));
  else goShell(0, 1);
} else {
  const section = document.querySelector('.slide');
  steps = Math.max(1, parseInt(section.dataset.steps || '1', 10));
  build = clampBuild(startMatch ? Number(startMatch[2] || startMatch[1]) : 1, steps);
  initSlide(section);
  apply();
  typeset(section);
  document.documentElement.classList.add('deck-appearing');
  setTimeout(() => document.documentElement.classList.remove('deck-appearing'), 400);
}
