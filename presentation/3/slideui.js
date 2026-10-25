/* Estimation & Filtering slide runtime (SlideUI).
   One fixed 1280x720 canvas per slide, scaled to the window.
   Steps live in data-step="N" (same N appears together) and data-steps="K" on the
   slide. The runtime keeps data-build and the .on class in sync, so the CSS of each
   slide can react to the current build.
   At the last step it asks the parent player to move on: a slide never loads another
   file by itself. In the editor preview window.__SLIDEUI.showAll shows every step. */
(function () {
  'use strict';

  var opts = window.__SLIDEUI || {};
  /* Freeze transitions before the body is parsed (the CSS reads this attribute). */
  document.documentElement.setAttribute('data-slideui-init', '');
  var layout = null;
  var section = null;
  var steps = 1;
  var startMatch = location.hash.match(/^#(\d+)$/);
  var build = 1;
  var fit = 1;
  var robotFrame = null;
  var ukfFlying = false;
  var robot = null;
  var ukf = null;
  var mathLoading = false;

  var reducedMotion = function () { return matchMedia('(prefers-reduced-motion: reduce)').matches; };
  var find = function (root, selector) { return root.matches(selector) ? root : root.querySelector(selector); };
  var notify = function (action) {
    if (window.parent !== window) window.parent.postMessage({ slideui: action }, '*');
  };
  // F: schermo intero. Dentro un iframe (player, anteprima) la richiesta va inoltrata
  // alla pagina che lo contiene, che è l'unica autorizzata a entrare in fullscreen.
  var toggleFullscreen = function () {
    if (window.parent !== window) { notify('fullscreen'); return; }
    if (document.fullscreenElement) { document.exitFullscreen(); return; }
    if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
  };

  /* --------------------------------------------------------------- geometry */
  function fitWindow() {
    var scale = Math.min(window.innerWidth / 1280, window.innerHeight / 720);
    document.documentElement.style.setProperty('--slide-scale', String(scale));
  }

  function scaleFactor() {
    var rect = section.getBoundingClientRect();
    return section.offsetWidth ? rect.width / section.offsetWidth : 1;
  }

  /* If a slide is a little taller than 720 px, shrink it just enough to fit. The
     scale is locked at the tallest build, so text does not jump between steps. */
  function fitTo(height, width, exact) {
    var availableH = section.clientHeight;
    var availableW = section.clientWidth;
    var needed = 1;
    if (height > availableH && availableH > 0) needed = Math.min(needed, availableH / height);
    if (width > availableW && availableW > 0) needed = Math.min(needed, availableW / width);
    if (needed < 1) needed *= 0.995;
    if (exact) fit = needed;
    else if (needed < fit) fit = needed;
    section.style.setProperty('--slide-fit', fit.toFixed(4));
  }

  function autoFit() {
    if (!section) return;
    fitTo(section.scrollHeight, section.scrollWidth, false);
  }

  /* Each build can be a different height (captions swap, blocks appear), so the
     scale is the one of the tallest build. The slide is hidden and restored in the
     same task, so this probe is never painted. A full measurement resets the scale,
     so a transient layout (MathJax mid-typeset) cannot shrink the slide for good. */
  function measureBuilds() {
    if (!section) return;
    var wanted = build;
    var tallest = 0;
    var widest = 0;
    section.style.visibility = 'hidden';
    for (var b = 1; b <= steps; b++) {
      build = b;
      paint();
      tallest = Math.max(tallest, section.scrollHeight);
      widest = Math.max(widest, section.scrollWidth);
    }
    build = wanted;
    paint();
    section.style.visibility = '';
    fitTo(tallest, widest, true);
  }

  /* ------------------------------------------------------------ slide parts */
  function initChart(slide) {
    var costSlide = find(slide, '.cost-slide');
    if (!costSlide) return;
    var radarChart = costSlide.querySelector('.body > svg');
    if (!radarChart) return;
    var svgNS = 'http://www.w3.org/2000/svg';
    var axes = radarChart.querySelector('g');
    if (!axes) return;
    var series = Array.prototype.slice.call(radarChart.children)
      .filter(function (el) { return el.tagName.toLowerCase() === 'g'; }).slice(1);
    var makeSvg = function (name, attrs, text) {
      var el = document.createElementNS(svgNS, name);
      Object.keys(attrs).forEach(function (key) { el.setAttribute(key, attrs[key]); });
      if (text !== undefined) el.textContent = text;
      return el;
    };
    var chartDefs = makeSvg('defs', {});
    var plotClip = makeSvg('clipPath', { id: 'radar-chart-clip' });
    plotClip.append(makeSvg('rect', { x: 100, y: 65, width: 850, height: 300 }));
    chartDefs.append(plotClip);
    radarChart.prepend(chartDefs);
    var chartMarks = [];
    var fromOriginal = function (x, y) { return [25 + (x - 100) * 1175 / 850, (365 - y) * 850 / 300]; };
    series.forEach(function (group) {
      group.removeAttribute('data-step');
      var clipped = makeSvg('g', { 'clip-path': 'url(#radar-chart-clip)' });
      Array.prototype.forEach.call(group.children, function (el) {
        if (el.matches('polygon, polyline')) {
          var points = el.getAttribute('points').trim().split(/\s+/).map(function (pair) {
            return fromOriginal.apply(null, pair.split(',').map(Number));
          });
          chartMarks.push({ el: el, points: points });
          clipped.append(el);
        } else if (el.matches('circle')) {
          var cx = Number(el.getAttribute('cx')), cy = Number(el.getAttribute('cy'));
          chartMarks.push({ el: el, points: [fromOriginal(cx, cy)] });
          clipped.append(el);
        }
      });
      group.prepend(clipped);
    });
    var chartRange = [25, 1200, 0, 850];
    function drawRadarChart() {
      var xmin = chartRange[0], xmax = chartRange[1], ymin = chartRange[2], ymax = chartRange[3];
      var px = function (x) { return 100 + (x - xmin) / (xmax - xmin) * 850; };
      var py = function (y) { return 365 - (y - ymin) / (ymax - ymin) * 300; };
      var format = function (value) {
        return Number(value.toFixed(xmax - xmin < 10 || ymax - ymin < 10 ? 2 : 1)).toString();
      };
      axes.replaceChildren();
      var xticks = xmin === 25 && xmax === 1200
        ? [25, 200, 400, 600, 800, 1000, 1200]
        : Array.from({ length: 6 }, function (_, i) { return xmin + (xmax - xmin) * i / 5; });
      var yticks = ymin === 0 && ymax === 850
        ? [0, 200, 400, 600, 800]
        : Array.from({ length: 6 }, function (_, i) { return ymin + (ymax - ymin) * i / 5; });
      yticks.forEach(function (y) {
        axes.append(makeSvg('path', { d: 'M100 ' + py(y) + ' H950', stroke: 'var(--line)' }));
        axes.append(makeSvg('text', { x: 80, y: py(y) + 7, 'text-anchor': 'end' }, format(y)));
      });
      xticks.forEach(function (x) {
        axes.append(makeSvg('text', { x: px(x), y: 398, 'text-anchor': 'middle' }, format(x)));
      });
      axes.append(makeSvg('text', { x: 100, y: 30 }, 'Position RMSE (m), first 30 updates'));
      axes.append(makeSvg('text', { x: 525, y: 437, 'text-anchor': 'middle' },
        'Initial position standard deviation per axis (m)'));
      chartMarks.forEach(function (mark) {
        var el = mark.el, points = mark.points;
        if (el.tagName.toLowerCase() === 'circle') {
          el.setAttribute('cx', px(points[0][0]));
          el.setAttribute('cy', py(points[0][1]));
        } else {
          el.setAttribute('points', points.map(function (p) { return px(p[0]) + ',' + py(p[1]); }).join(' '));
        }
      });
    }
    function zoomRadarChart(factor, ax, ay) {
      ax = ax === undefined ? .5 : ax;
      ay = ay === undefined ? .5 : ay;
      var width = Math.max(.5, Math.min(2350, (chartRange[1] - chartRange[0]) * factor));
      var height = Math.max(.05, Math.min(1700, (chartRange[3] - chartRange[2]) * factor));
      var x = chartRange[0] + ax * (chartRange[1] - chartRange[0]);
      var y = chartRange[2] + ay * (chartRange[3] - chartRange[2]);
      chartRange = [x - ax * width, x + (1 - ax) * width, y - ay * height, y + (1 - ay) * height];
      drawRadarChart();
    }
    function resetRadarChart() {
      chartRange = [25, 1200, 0, 850];
      drawRadarChart();
    }
    var chartPoint = function (event) {
      return new DOMPoint(event.clientX, event.clientY).matrixTransform(radarChart.getScreenCTM().inverse());
    };
    radarChart.addEventListener('wheel', function (event) {
      var p = chartPoint(event);
      if (p.x < 100 || p.x > 950 || p.y < 65 || p.y > 365) return;
      event.preventDefault();
      zoomRadarChart(Math.exp(Math.max(-.3, Math.min(.3, event.deltaY * .002))),
        (p.x - 100) / 850, (365 - p.y) / 300);
    }, { passive: false });
    var chartDrag = null;
    radarChart.addEventListener('pointerdown', function (event) {
      if (event.button !== 0) return;
      var p = chartPoint(event);
      if (p.x < 100 || p.x > 950 || p.y < 65 || p.y > 365) return;
      event.preventDefault();
      chartDrag = { point: p, range: chartRange.slice() };
      radarChart.setPointerCapture(event.pointerId);
    });
    radarChart.addEventListener('pointermove', function (event) {
      if (!chartDrag) return;
      var p = chartPoint(event);
      var r = chartDrag.range;
      var dx = (p.x - chartDrag.point.x) / 850 * (r[1] - r[0]);
      var dy = (p.y - chartDrag.point.y) / 300 * (r[3] - r[2]);
      chartRange = [r[0] - dx, r[1] - dx, r[2] + dy, r[3] + dy];
      drawRadarChart();
    });
    radarChart.addEventListener('pointerup', function () { chartDrag = null; });
    radarChart.addEventListener('pointercancel', function () { chartDrag = null; });
    radarChart.addEventListener('lostpointercapture', function () { chartDrag = null; });
    radarChart.addEventListener('dblclick', resetRadarChart);
    drawRadarChart();
  }

  function initRadar(slide) {
    var radarScene = find(slide, '.radar-setup');
    if (!radarScene) return;
    radarScene.classList.add('radar-active');
  }

  function initRobot(slide) {
    var scene = find(slide, '.robot-scene');
    if (!scene) return;
    var driving = scene.querySelector('.scene-driving');
    var path = scene.querySelector('#robot-drive-path');
    if (!driving || !path) return;
    robot = {
      scene: scene,
      driving: driving,
      rays: scene.querySelector('#robot-sensor-rays'),
      origin: scene.querySelector('#robot-sensor-origin'),
      path: path,
      length: path.getTotalLength()
    };
  }

  function initModelReveal(slide) {
    var modelGroup = slide.querySelector('.model-group');
    if (!modelGroup) return;
    modelGroup.classList.remove('model-enter');
    void modelGroup.getBoundingClientRect();
    modelGroup.classList.add('model-enter');
  }

  function initCkfQuestion(slide) {
    var question = find(slide, '.ckf-question');
    if (!question) return;
    question.classList.add('question-visible');
  }

  function initSlide(slide) {
    initChart(slide);
    initRadar(slide);
    initRobot(slide);
    initModelReveal(slide);
    initCkfQuestion(slide);
    var scene = find(slide, '.ukf-scene');
    ukf = scene ? { scene: scene, fly: scene.querySelector('#ukf-fly') } : null;
  }

  /* ------------------------------------------------------------- animations */
  function setSensorPosition(x, y) {
    if (!robot || !robot.rays || !robot.origin) return;
    robot.rays.setAttribute('d', 'M' + x + ' ' + y + ' L405 91 M' + x + ' ' + y + ' L800 80');
    robot.origin.setAttribute('cx', x);
    robot.origin.setAttribute('cy', y);
  }

  function updateRobotAnimation(slide) {
    if (!robot) return;
    if (robotFrame !== null) cancelAnimationFrame(robotFrame);
    robotFrame = null;
    robot.driving.setAttribute('transform', 'translate(0 0)');
    var step = Number(slide.dataset.build);
    setSensorPosition(step >= 3 ? 635.75 : 525, step >= 3 ? 186.65 : 214);
    if (step !== 4 || reducedMotion()) return;
    var start;
    function frame(time) {
      if (start === undefined) start = time;
      var distance = ((time - start) % 8000) / 8000 * robot.length;
      var position = robot.path.getPointAtLength(distance);
      var dx = position.x - 630;
      var dy = position.y - 220;
      robot.driving.setAttribute('transform', 'translate(' + dx + ' ' + dy + ')');
      setSensorPosition(635.75 + dx, 186.65 + dy);
      robotFrame = requestAnimationFrame(frame);
    }
    robotFrame = requestAnimationFrame(frame);
  }

  function updateUkfAnimation(slide) {
    if (!ukf || !ukf.fly) return;
    var on = Number(slide.dataset.build) === 4 && !reducedMotion();
    if (on && !ukfFlying) { ukf.fly.beginElement(); ukfFlying = true; }
    else if (!on && ukfFlying) { ukf.fly.endElement(); ukfFlying = false; }
  }

  function updateSplitLists(slide) {
    var list = slide.querySelector('.split-text');
    if (!list) return;
    var k = scaleFactor() || 1;
    var items = Array.prototype.slice.call(list.querySelectorAll('.step'));
    items.forEach(function (el) { el.classList.remove('on'); el.classList.remove('current'); });
    var visible = items.filter(function (el) { return parseInt(el.dataset.n, 10) <= build; });
    visible.forEach(function (el) { el.classList.add('on'); });
    if (visible.length) visible[visible.length - 1].classList.add('current');
    var rail = list.querySelector('.rail');
    var railActive = list.querySelector('.rail-active');
    if (!rail) return;
    if (!visible.length) {
      rail.style.height = '0px';
      if (railActive) railActive.style.opacity = '0';
      return;
    }
    var current = visible[visible.length - 1];
    var textTop = list.getBoundingClientRect().top;
    var box = current.getBoundingClientRect();
    rail.style.height = Math.max(0, (box.bottom - textTop) / k - 14) + 'px';
    if (railActive) {
      railActive.style.opacity = '1';
      railActive.style.top = (box.top - textTop) / k + 'px';
      railActive.style.height = box.height / k + 'px';
    }
  }

  /* --------------------------------------------------------------- painting */
  function paint() {
    section.dataset.build = String(build);
    Array.prototype.forEach.call(section.querySelectorAll('[data-step]'), function (el) {
      el.classList.toggle('on', parseInt(el.dataset.step, 10) <= build);
    });
    updateSplitLists(section);
    updateRobotAnimation(section);
    updateUkfAnimation(section);
  }

  function apply() {
    if (!section) return;
    paint();
    autoFit();
  }

  /* ---------------------------------------------------------------- mathjax */
  function typeset() {
    if (!window.MathJax || !MathJax.typesetPromise) return;
    MathJax.typesetPromise([section]).then(function () {
      // let MathJax's own layout settle, then measure again: typesetting changes
      // the height of every build, and the scale is reset from the tallest one.
      requestAnimationFrame(measureBuilds);
      setTimeout(measureBuilds, 200);
    }).catch(function () {});
  }

  function loadMath() {
    var html = document.body.innerHTML;
    if (html.indexOf('\\(') < 0 && html.indexOf('\\[') < 0) return;
    if (window.MathJax) { typeset(); return; }
    if (mathLoading) return;
    mathLoading = true;
    window.MathJax = {
      tex: { inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]']] },
      svg: { fontCache: 'local' },
      startup: { typeset: false }
    };
    var script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js';
    script.async = true;
    script.onload = function () {
      if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
        MathJax.startup.promise.then(typeset);
      } else {
        typeset();
      }
    };
    document.head.appendChild(script);
  }

  /* ----------------------------------------------------------------- input */
  function next() {
    if (build < steps) { build++; apply(); }
    else notify('next');
  }

  function prev() {
    if (build > 1) { build--; apply(); }
    else notify('prev');
  }

  function jumpTo(value) {
    if (value >= 1 && value <= steps && value !== build) { build = value; apply(); }
  }

  function handleKey(key) {
    if (key === 'f' || key === 'F') { toggleFullscreen(); return true; }
    if (!section || opts.showAll) return false;
    if (key === 'ArrowRight' || key === ' ' || key === 'PageDown' || key === 'Enter') { next(); return true; }
    if (key === 'ArrowLeft' || key === 'PageUp') { prev(); return true; }
    if (key === 'Home') { jumpTo(1); return true; }
    if (key === 'End') { jumpTo(steps); return true; }
    if (key === 'Escape') { notify('exit'); return true; }
    return false;
  }

  document.addEventListener('keydown', function (event) {
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    if (handleKey(event.key)) event.preventDefault();
  });

  document.addEventListener('click', function (event) {
    if (!section || opts.showAll) return;
    if (event.target.closest('a, button, input, textarea, select, svg')) return;
    next();
  });

  window.addEventListener('message', function (event) {
    var data = event.data;
    if (data && data.slideui === 'key') handleKey(data.key);
  });

  window.addEventListener('resize', function () { fitWindow(); });

  /* ----------------------------------------------------------------- counter */
  /* The player tells the runtime its global position, so the number lives inside
     the scaled canvas (same proportions as deck-draft.html at any window size). */
  function renderCounter() {
    if (opts.index == null || !opts.total) return;
    var host = layout || document.body;
    var el = host.querySelector('.slideui-counter');
    if (!el) {
      el = document.createElement('div');
      el.className = 'slideui-counter';
      el.setAttribute('aria-hidden', 'true');
      el.innerHTML = '<span class="current-slide"></span><span class="total-slides"></span>';
      host.appendChild(el);
    }
    el.querySelector('.current-slide').textContent = String(opts.index + 1);
    el.querySelector('.total-slides').textContent = ' / ' + opts.total;
  }

  /* ------------------------------------------------------------------ start */
  function start() {
    layout = document.querySelector('.slide-layout');
    section = layout && layout.querySelector('.slide');
    if (!section) return;
    renderCounter();
    steps = Math.max(1, parseInt(section.dataset.steps || '1', 10));
    build = startMatch ? Math.max(1, Math.min(steps, Number(startMatch[1])))
      : (opts.showAll || opts.atEnd ? steps : 1);
    fitWindow();
    initSlide(section);
    measureBuilds();
    loadMath();
    var release = function () {
      document.documentElement.removeAttribute('data-slideui-init');
    };
    requestAnimationFrame(function () { requestAnimationFrame(release); });
    setTimeout(release, 400);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
