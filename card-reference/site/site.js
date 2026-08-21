/* MTG Card Reference — static site behaviour.
   Copied to /docs/assets/site.js by card-reference/build_site.py.
   No dependencies; degrades to a plain readable page if JS is off. */
(function () {
  'use strict';

  /* ---- card filtering (set pages only) ---- */
  var input = document.getElementById('q');
  if (!input) return;

  var tiles = Array.prototype.slice.call(document.querySelectorAll('.tile'));
  var sections = Array.prototype.slice.call(document.querySelectorAll('.cardsection'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-rarity]'));
  var counter = document.getElementById('count');
  var empty = document.querySelector('.empty');
  var total = tiles.length;
  var rarity = '';

  // Full-text haystack is built lazily on the first query: card name, stats and
  // every expert note. One pass over ~350 tiles, then cached on the element.
  function hay(el) {
    if (el._q === undefined) el._q = (el.textContent || '').toLowerCase();
    return el._q;
  }

  function apply() {
    var q = input.value.trim().toLowerCase();
    var terms = q ? q.split(/\s+/) : [];
    var shown = 0;

    for (var i = 0; i < tiles.length; i++) {
      var el = tiles[i];
      var ok = !rarity || el.dataset.rarity === rarity;
      if (ok && terms.length) {
        var name = el.dataset.name || '';
        var text = null;
        for (var t = 0; t < terms.length; t++) {
          if (name.indexOf(terms[t]) !== -1) continue;
          if (text === null) text = hay(el);
          if (text.indexOf(terms[t]) === -1) { ok = false; break; }
        }
      }
      el.hidden = !ok;
      if (ok) shown++;
    }

    for (var s = 0; s < sections.length; s++) {
      var sec = sections[s];
      var vis = sec.querySelectorAll('.tile:not([hidden])').length;
      sec.hidden = vis === 0;
      var n = sec.querySelector('h2 .n');
      if (n) n.textContent = vis === Number(sec.dataset.total) ? vis : vis + ' / ' + sec.dataset.total;
    }

    var filtering = !!terms.length || !!rarity;
    if (counter) counter.textContent = filtering ? shown + ' / ' + total + ' cards' : total + ' cards';
    if (empty) empty.classList.toggle('show', shown === 0);

    // Jump-strip counts follow the filter too.
    document.querySelectorAll('.jump a[data-c]').forEach(function (a) {
      var sec2 = document.getElementById(a.getAttribute('href').slice(1));
      if (sec2) a.style.opacity = sec2.hidden ? '.35' : '';
    });
  }

  var timer;
  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(apply, 110);
  });

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      var val = chip.dataset.rarity;
      rarity = rarity === val ? '' : val;
      chips.forEach(function (c) {
        c.setAttribute('aria-pressed', String(c.dataset.rarity === rarity && rarity !== ''));
      });
      apply();
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== input) {
      e.preventDefault();
      input.focus();
      input.select();
    } else if (e.key === 'Escape' && document.activeElement === input) {
      input.value = '';
      apply();
      input.blur();
    }
  });

  apply();
})();
