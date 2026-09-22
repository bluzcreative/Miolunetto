/* Lunetto — carrito, cajas, formularios y efectos. Sin dependencias. */
(function () {
  'use strict';
  var CFG = window.LUNETTO_CONFIG || {};
  var MENU = window.LUNETTO_MENU || { items: [], boxes: {} };
  var KEY = 'lunetto-cart-v1';
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  function safe(fn, name) { try { fn(); } catch (e) { if (window.console) console.warn('[lunetto] ' + name, e); } }
  function ref(n) { return 'REF ' + (Math.round(n * 100) / 100).toFixed(2); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var byId = {};
  MENU.items.forEach(function (i) { byId[i.id] = i; });

  /* ================= ESTADO DEL CARRITO ================= */
  var state = { lines: [], mode: 'pickup', form: {} };
  function load() {
    try {
      var s = JSON.parse(localStorage.getItem(KEY) || '{}');
      if (s.lines) state.lines = s.lines;
      if (s.mode) state.mode = s.mode;
      if (s.form) state.form = s.form;
    } catch (e) {}
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }

  function unitQty(id) {
    var l = state.lines.filter(function (x) { return x.type === 'unit' && x.id === id; })[0];
    return l ? l.qty : 0;
  }
  function addUnit(id, d) {
    var it = byId[id]; if (!it) return;
    var l = state.lines.filter(function (x) { return x.type === 'unit' && x.id === id; })[0];
    if (!l) { if (d < 0) return; l = { type: 'unit', id: id, qty: 0 }; state.lines.push(l); }
    l.qty += d;
    if (l.qty <= 0) state.lines.splice(state.lines.indexOf(l), 1);
    commit();
  }
  function addBox(box) {
    var sig = box.name + '|' + JSON.stringify(box.flavors);
    var l = state.lines.filter(function (x) { return x.type === 'box' && x.sig === sig; })[0];
    if (l) l.qty += 1;
    else state.lines.push({ type: 'box', sig: sig, name: box.name, price: box.price, flavors: box.flavors, qty: 1 });
    commit();
    toast('Caja agregada al carrito');
  }
  function lineTotal(l) {
    return l.type === 'unit' ? byId[l.id].price * l.qty : l.price * l.qty;
  }
  function subtotal() { return state.lines.reduce(function (a, l) { return a + lineTotal(l); }, 0); }
  function count() { return state.lines.reduce(function (a, l) { return a + l.qty; }, 0); }
  function deliveryFee() { return state.mode === 'delivery' ? (CFG.deliveryEstimate || 3) : 0; }
  function commit() { save(); renderAll(); }

  /* ================= TARJETAS (sincroniza todas las que existan) ================= */
  function syncCards() {
    $$('[data-item]').forEach(function (el) {
      var q = unitQty(el.getAttribute('data-item'));
      el.classList.toggle('has-qty', q > 0);
      var b = $('[data-q]', el); if (b) b.textContent = q;
    });
    $$('[data-cart-count]').forEach(function (el) { el.textContent = count(); });
  }
  function bindCards() {
    document.addEventListener('click', function (e) {
      var t = e.target.closest('[data-add],[data-inc],[data-dec]');
      if (!t) return;
      var card = t.closest('[data-item]'); if (!card) return;
      var id = card.getAttribute('data-item');
      if (t.hasAttribute('data-add')) { addUnit(id, 1); toast('Agregado: ' + byId[id].name); }
      else if (t.hasAttribute('data-inc')) addUnit(id, 1);
      else addUnit(id, -1);
    });
  }

  /* ================= DRAWER ================= */
  var drawer, overlay;
  function openCart() { drawer.classList.add('open'); overlay.classList.add('open'); document.body.style.overflow = 'hidden'; }
  function closeCart() { drawer.classList.remove('open'); overlay.classList.remove('open'); document.body.style.overflow = ''; }

  function renderDrawer() {
    var body = $('#dr-lines'), foot = $('#dr-foot'), form = $('#dr-form');
    if (!body) return;
    if (!state.lines.length) {
      body.innerHTML = '<div class="dr-empty"><span class="script">tu bolsa está vacía</span><p>Elige tus medialunas y vuelve. Aquí te esperamos.</p><a class="btn" href="' + (CFG.menuUrl || 'menu.html') + '">Ver menú</a></div>';
      form.hidden = true; foot.hidden = true; return;
    }
    form.hidden = false; foot.hidden = false;
    body.innerHTML = state.lines.map(function (l, i) {
      var name, det = '';
      if (l.type === 'unit') { var it = byId[l.id]; name = it.name + (it.size ? ' · ' + it.size : ''); }
      else {
        name = l.name;
        det = '<div class="det">' + l.flavors.map(function (f) { return f.qty + '× ' + esc(byId[f.id].name); }).join(' · ') + '</div>';
      }
      return '<div class="line" data-line="' + i + '"><h4>' + esc(name) + '</h4><div class="lp">' + ref(lineTotal(l)) + '</div>' + det +
        '<div class="ctl"><span class="stepper"><button type="button" data-ldec aria-label="Quitar uno">−</button><b>' + l.qty + '</b><button type="button" data-linc aria-label="Agregar uno">+</button></span><button type="button" class="rm" data-lrm>Quitar</button></div></div>';
    }).join('');
    $$('#dr-mode button').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-mode') === state.mode); });
    var isDel = state.mode === 'delivery';
    $('#f-addr-wrap').hidden = !isDel;
    $('#f-zone-wrap').hidden = isDel;
    $('#dr-del-note').hidden = !isDel;
    var sub = subtotal(), fee = deliveryFee();
    $('#s-sub').textContent = ref(sub);
    $('#s-del-row').hidden = !isDel;
    $('#s-del').textContent = ref(fee);
    $('#s-tot').textContent = ref(sub + fee);
    $('#s-tot-lbl').textContent = isDel ? 'Total estimado' : 'Total';
  }
  function bindDrawer() {
    $$('[data-open-cart]').forEach(function (b) { b.addEventListener('click', openCart); });
    overlay.addEventListener('click', closeCart);
    $('#dr-close').addEventListener('click', closeCart);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeCart(); });
    $('#dr-lines').addEventListener('click', function (e) {
      var row = e.target.closest('[data-line]'); if (!row) return;
      var l = state.lines[+row.getAttribute('data-line')]; if (!l) return;
      if (e.target.closest('[data-linc]')) l.qty += 1;
      else if (e.target.closest('[data-ldec]')) l.qty -= 1;
      else if (e.target.closest('[data-lrm]')) l.qty = 0;
      else return;
      if (l.qty <= 0) state.lines.splice(state.lines.indexOf(l), 1);
      commit();
    });
    $$('#dr-mode button').forEach(function (b) {
      b.addEventListener('click', function () { state.mode = b.getAttribute('data-mode'); commit(); });
    });
    ['name', 'phone', 'cedula', 'zone', 'addr', 'notes'].forEach(function (k) {
      var el = $('#f-' + k); if (!el) return;
      el.value = state.form[k] || '';
      el.addEventListener('input', function () { state.form[k] = el.value; el.parentNode.classList.remove('bad'); save(); });
    });
    $('#dr-send').addEventListener('click', sendOrder);
  }

  function sendOrder() {
    var need = ['name', 'phone', 'cedula'];
    need.push(state.mode === 'delivery' ? 'addr' : 'zone');
    var ok = true;
    need.forEach(function (k) {
      var el = $('#f-' + k), bad = !(state.form[k] || '').trim();
      el.parentNode.classList.toggle('bad', bad);
      if (bad) ok = false;
    });
    if (!ok) { toast('Completa los datos marcados'); var f = $('.bad', drawer); if (f) f.scrollIntoView({ block: 'center', behavior: 'smooth' }); return; }
    var f = state.form, L = [];
    L.push('*Nuevo pedido · Lunetto*');
    L.push('');
    L.push('*Nombre:* ' + f.name.trim());
    L.push('*Teléfono:* ' + f.phone.trim());
    L.push('*Cédula:* ' + f.cedula.trim());
    L.push('*Modalidad:* ' + (state.mode === 'delivery' ? 'Delivery' : 'Pick up (retiro en tienda)'));
    L.push(state.mode === 'delivery' ? '*Ubicación:* ' + f.addr.trim() : '*Dirección corta:* ' + f.zone.trim());
    L.push('');
    L.push('*Pedido:*');
    state.lines.forEach(function (l) {
      if (l.type === 'unit') {
        var it = byId[l.id];
        L.push('• ' + l.qty + '× ' + it.name + (it.size ? ' (' + it.size + ')' : '') + ' — ' + ref(lineTotal(l)));
      } else {
        L.push('• ' + l.qty + '× ' + l.name + ' — ' + ref(lineTotal(l)));
        l.flavors.forEach(function (fl) { L.push('    ◦ ' + fl.qty + '× ' + byId[fl.id].name); });
      }
    });
    L.push('');
    L.push('Subtotal: ' + ref(subtotal()));
    if (state.mode === 'delivery') L.push('Delivery (estimado, por confirmar): ' + ref(deliveryFee()));
    L.push('*' + (state.mode === 'delivery' ? 'Total estimado: ' : 'Total: ') + ref(subtotal() + deliveryFee()) + '*');
    if ((f.notes || '').trim()) { L.push(''); L.push('*Notas:* ' + f.notes.trim()); }
    L.push('');
    L.push('Precios en REF (euro a tasa BCV).');
    var url = 'https://wa.me/' + (CFG.whatsapp || '') + '?text=' + encodeURIComponent(L.join('\n'));
    window.open(url, '_blank', 'noopener');
  }

  /* ================= CONSTRUCTOR DE CAJAS ================= */
  function initBuilder() {
    var root = $('#builder'); if (!root) return;
    var B = MENU.boxes;
    var SIZES = { '7': { label: '7 cm', qtys: [4, 8, 16] }, '10': { label: '10 cm', qtys: [2, 4, 8] } };
    var s = { size: '7', qty: 8, pick: {} };
    var pillsSize = $('#b-size'), pillsQty = $('#b-qty'), flav = $('#b-flav');

    function flavorList() {
      return MENU.items.filter(function (i) {
        if (s.size === '7') return i.size === '7 cm' && (i.cat === 'dulce' || i.cat === 'salado');
        return i.size === '10 cm';
      });
    }
    function total() { return Object.keys(s.pick).reduce(function (a, k) { return a + s.pick[k]; }, 0); }
    function pricing() {
      var ids = Object.keys(s.pick).filter(function (k) { return s.pick[k] > 0; });
      var onlyClassic = ids.every(function (k) { return byId[k].classic; });
      var price, tier, note = '';
      if (s.size === '7') {
        if (onlyClassic) { price = B.c7[s.qty]; tier = 'Caja Clásica 7 cm'; }
        else {
          price = B.m7[s.qty]; tier = 'Caja Mixta 7 cm';
          var dub = ids.reduce(function (a, k) { return a + (byId[k].dubai ? s.pick[k] : 0); }, 0);
          if (dub) { price += dub * (CFG.dubaiExtra || 0); note = 'Incluye recargo por Chocolate Dubai (' + dub + '×)'; }
        }
      } else {
        var hasSalty = ids.some(function (k) { return byId[k].cat === 'salado'; });
        if (hasSalty) { price = B.s10[s.qty]; tier = 'Caja Salados 10 cm'; note = 'Al incluir salados aplica el precio de caja de salados'; }
        else { price = B.c10[s.qty]; tier = 'Caja Clásica 10 cm'; }
      }
      return { price: price, tier: tier, note: note };
    }
    function renderPills() {
      pillsSize.innerHTML = Object.keys(SIZES).map(function (k) {
        return '<button type="button" class="pill' + (k === s.size ? ' on' : '') + '" data-size="' + k + '">Medialunas de ' + SIZES[k].label + '</button>';
      }).join('');
      pillsQty.innerHTML = SIZES[s.size].qtys.map(function (q) {
        return '<button type="button" class="pill' + (q === s.qty ? ' on' : '') + '" data-qty="' + q + '">Caja de ' + q + '</button>';
      }).join('');
    }
    function render() {
      var list = flavorList(), t = total(), full = t >= s.qty, html = '', lastCat = '';
      var names = { clasica: 'La clásica', dulce: 'Dulces', salado: 'Salados' };
      list.forEach(function (i) {
        var grp = i.classic ? 'clasica' : i.cat;
        if (grp !== lastCat) { html += '<div class="fl grp">' + names[grp] + '</div>'; lastCat = grp; }
        var q = s.pick[i.id] || 0;
        html += '<div class="fl' + (full && !q ? ' off' : '') + '" data-f="' + i.id + '"><span>' + esc(i.name) + '</span><span class="stepper"><button type="button" data-fdec aria-label="Quitar">−</button><b>' + q + '</b><button type="button" data-finc aria-label="Agregar">+</button></span></div>';
      });
      flav.innerHTML = html;
      $('#b-count').textContent = t + ' de ' + s.qty + ' elegidas';
      $('#b-prog').style.width = Math.min(100, t / s.qty * 100) + '%';
      var p = t > 0 ? pricing() : { price: (s.size === '7' ? B.c7 : B.c10)[s.qty], tier: 'Desde (caja clásica)', note: 'El precio se ajusta según lo que elijas' };
      $('#b-tier').textContent = p.tier;
      $('#b-total').textContent = ref(p.price);
      $('#b-note').textContent = p.note;
      $('#b-add').disabled = !full;
      $('#b-add').textContent = full ? 'Agregar caja al carrito' : 'Elige ' + (s.qty - t) + ' más';
    }
    function resetPick() { s.pick = {}; }
    root.addEventListener('click', function (e) {
      var t;
      if ((t = e.target.closest('[data-size]'))) { s.size = t.getAttribute('data-size'); s.qty = SIZES[s.size].qtys[1]; resetPick(); renderPills(); render(); return; }
      if ((t = e.target.closest('[data-qty]'))) { s.qty = +t.getAttribute('data-qty'); resetPick(); renderPills(); render(); return; }
      if ((t = e.target.closest('[data-finc],[data-fdec]'))) {
        var id = t.closest('[data-f]').getAttribute('data-f');
        if (t.hasAttribute('data-finc')) { if (total() < s.qty) s.pick[id] = (s.pick[id] || 0) + 1; }
        else if (s.pick[id]) { s.pick[id] -= 1; if (!s.pick[id]) delete s.pick[id]; }
        render(); return;
      }
      if (e.target.closest('#b-classic')) { resetPick(); s.pick['c' + s.size + '-clasica'] = s.qty; render(); return; }
      if (e.target.closest('#b-clear')) { resetPick(); render(); return; }
      if (e.target.closest('#b-add')) {
        if (total() !== s.qty) return;
        var p = pricing();
        var fl = Object.keys(s.pick).map(function (k) { return { id: k, qty: s.pick[k] }; });
        addBox({ name: 'Caja de ' + s.qty + ' · ' + p.tier.replace('Caja ', ''), price: p.price, flavors: fl });
        resetPick(); render(); openCart();
      }
    });
    renderPills(); render();
  }

  /* ================= FORMULARIO DE COTIZACIÓN ================= */
  function initQuote() {
    var f = $('#quote-form'); if (!f) return;
    function data() {
      var d = {}; $$('input,select,textarea', f).forEach(function (el) { d[el.name] = (el.value || '').trim(); });
      return d;
    }
    function valid() {
      var ok = true;
      $$('[data-req]', f).forEach(function (el) {
        var bad = !(el.value || '').trim();
        el.parentNode.classList.toggle('bad', bad); if (bad) ok = false;
      });
      if (!ok) { toast('Completa los campos marcados'); var b = $('.bad', f); if (b) b.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
      return ok;
    }
    function text() {
      var d = data(), L = [];
      L.push('*Solicitud de cotización · Catering Lunetto*'); L.push('');
      L.push('*Nombre:* ' + d.name); L.push('*Teléfono:* ' + d.phone);
      if (d.email) L.push('*Correo:* ' + d.email);
      L.push('*Tipo de evento:* ' + d.event);
      L.push('*Fecha:* ' + d.date);
      L.push('*Personas:* ' + d.guests);
      L.push('*Servicio:* ' + d.service);
      if (d.place) L.push('*Lugar:* ' + d.place);
      if (d.msg) { L.push(''); L.push('*Detalles:* ' + d.msg); }
      return L.join('\n');
    }
    function sendMail(btn) {
      if (!valid()) return;
      var payload = data();
      btn.disabled = true;
      var old = btn.textContent;
      btn.textContent = 'Enviando…';
      fetch('/api/cotizar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          if (res.ok && res.j && res.j.ok) { toast('Cotización enviada. Te contactaremos pronto.'); f.reset(); }
          else { toast('No se pudo enviar. Intenta por WhatsApp.'); }
        })
        .catch(function () { toast('No se pudo enviar. Intenta por WhatsApp.'); })
        .then(function () { btn.disabled = false; btn.textContent = old; });
    }
    f.addEventListener('click', function (e) {
      if (e.target.closest('#q-wa')) { if (valid()) window.open('https://wa.me/' + CFG.whatsapp + '?text=' + encodeURIComponent(text()), '_blank', 'noopener'); }
      var mb = e.target.closest('#q-mail'); if (mb) sendMail(mb);
    });
    f.addEventListener('submit', function (e) { e.preventDefault(); });
    $$('input,select,textarea', f).forEach(function (el) { el.addEventListener('input', function () { el.parentNode.classList.remove('bad'); }); });
  }

  /* ================= CARRUSEL HOME ================= */
  function initCarousel() {
    var car = $('#car'); if (!car) return;
    var step = function () { return Math.max(260, car.clientWidth * .8); };
    var prev = $('#car-prev'), next = $('#car-next');
    if (prev) prev.addEventListener('click', function () { car.scrollBy({ left: -step(), behavior: 'smooth' }); });
    if (next) next.addEventListener('click', function () { car.scrollBy({ left: step(), behavior: 'smooth' }); });
    $$('[data-tab]').forEach(function (t) {
      t.addEventListener('click', function () {
        var c = t.getAttribute('data-tab');
        $$('[data-tab]').forEach(function (x) { x.classList.toggle('on', x === t); });
        $$('#car .card').forEach(function (card) {
          var cat = card.getAttribute('data-cat');
          card.hidden = !(c === 'todo' || cat === c || cat === 'caja');
        });
        car.scrollTo({ left: 0, behavior: 'smooth' });
      });
    });
  }

  /* ================= UI GENERAL ================= */
  var toastEl, toastT;
  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg; toastEl.classList.add('show');
    clearTimeout(toastT); toastT = setTimeout(function () { toastEl.classList.remove('show'); }, 1800);
  }
  function initNav() {
    var b = $('#burger'), n = $('#nav'), h = $('.hdr');
    if (b && n) {
      b.addEventListener('click', function () {
        var o = n.classList.toggle('open'); b.setAttribute('aria-expanded', o); document.body.style.overflow = o ? 'hidden' : '';
      });
      $$('a', n).forEach(function (a) { a.addEventListener('click', function () { n.classList.remove('open'); document.body.style.overflow = ''; }); });
    }
    var onS = function () { if (h) h.classList.toggle('scrolled', window.scrollY > 8); };
    window.addEventListener('scroll', onS, { passive: true }); onS();
  }
  function initReveal() {
    var els = $$('.reveal'); if (!els.length) return;
    if (!('IntersectionObserver' in window)) { els.forEach(function (e) { e.classList.add('in'); }); return; }
    var io = new IntersectionObserver(function (en) {
      en.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add('in'); io.unobserve(x.target); } });
    }, { threshold: 0.05, rootMargin: '0px 0px -4% 0px' });
    els.forEach(function (e) { io.observe(e); });
    setTimeout(function () { els.forEach(function (e) { e.classList.add('in'); }); }, 6000);
  }
  function initParallax() {
    var im = $('.arch img'); if (!im) return;
    var ticking = false;
    function upd() { var y = Math.min(window.scrollY, 700); im.style.transform = 'translateY(' + (-y * 0.06) + 'px)'; ticking = false; }
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(upd); } }, { passive: true });
  }
  function initSlider() {
    var root = $('#hs'); if (!root) return;
    var slides = $$('.slide', root), dots = $$('#hs-dots i'), cur = 0, timer;
    function go(n) {
      cur = (n + slides.length) % slides.length;
      slides.forEach(function (s, i) { s.classList.toggle('on', i === cur); });
      dots.forEach(function (d, i) { d.classList.toggle('on', i === cur); });
    }
    function play() { stop(); timer = setInterval(function () { go(cur + 1); }, 6500); }
    function stop() { clearInterval(timer); }
    $('#hs-prev').addEventListener('click', function () { go(cur - 1); play(); });
    $('#hs-next').addEventListener('click', function () { go(cur + 1); play(); });
    dots.forEach(function (d, i) { d.addEventListener('click', function () { go(i); play(); }); });
    root.addEventListener('mouseenter', stop); root.addEventListener('mouseleave', play);
    play();
  }
  function initVideo() {
    $$('video[autoplay]').forEach(function (v) {
      v.muted = true;
      var p = v.play(); if (p && p.catch) p.catch(function () {});
    });
  }
  function renderAll() { safe(syncCards, 'syncCards'); safe(renderDrawer, 'renderDrawer'); }

  function init() {
    document.documentElement.classList.add('js');
    drawer = $('#drawer'); overlay = $('#ov'); toastEl = $('#toast');
    load();
    safe(initNav, 'nav');
    safe(bindCards, 'cards');
    if (drawer) safe(bindDrawer, 'drawer');
    safe(initBuilder, 'builder');
    safe(initQuote, 'quote');
    safe(initCarousel, 'carousel');
    safe(initReveal, 'reveal');
    safe(initSlider, 'slider');
    safe(initVideo, 'video');
    renderAll();
    if (location.hash === '#carrito' && drawer) openCart();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
