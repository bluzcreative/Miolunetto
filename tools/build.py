#!/usr/bin/env python3
"""Genera las páginas estáticas de Lunetto (HTML + lib/config.js + lib/menu-data.js).
Uso:  python3 tools/build.py      (desde la carpeta web/)
Todo lo editable (contacto, precios, sabores) está al inicio de este archivo."""
import json, os, html, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = "20260921"  # cache-buster: súbelo en cada despliegue

# ============ DATOS EDITABLES ============
CONFIG = {
    "whatsapp": "584242885763",
    "whatsappDisplay": "0424-2885763",
    "email": "info@miolunetto.com",
    "address": "Calle Cecilio Acosta, Chacao, Caracas, Venezuela",
    "hours": "Martes a Domingo · 9 am a 8 pm",
    "instagram": "https://www.instagram.com/miolunetto",
    "tiktok": "https://www.tiktok.com/@miolunetto",
    "appleMusic": "https://music.apple.com/us/playlist/lunetto/pl.u-KVXBkPLtLDd3qpJ",
    "mapsQuery": "Calle Cecilio Acosta, Chacao, Caracas, Venezuela",
    "mapsLink": "https://maps.app.goo.gl/u7E9B6WDisxr2Chk8",
    "deliveryEstimate": 3,
    "dubaiExtra": 1.00,                  # recargo por cada Chocolate Dubai en caja mixta (por confirmar)
    "menuUrl": "menu.html",
}
BOXES = {
    "c7": {4: 11, 8: 22, 16: 44},
    "m7": {4: 14, 8: 28, 16: 55},
    "c10": {2: 8.25, 4: 17, 8: 33},
    "s10": {2: 10, 4: 20, 8: 40},
}
# id, nombre, tamaño, categoría, precio, imagen, ilustración?, clásica?, dubai?
I = []
def add(id, name, size, cat, price, img, illus=False, classic=False, dubai=False, desc=""):
    I.append(dict(id=id, name=name, size=size, cat=cat, price=price, img=img, illus=illus, classic=classic, dubai=dubai, desc=desc))
add("c7-clasica", "Clásica", "7 cm", "dulce", 3.25, "assets/prod/clasica.jpg", classic=True)
add("d7-cafe", "Café", "7 cm", "dulce", 3.85, "assets/prod/cafe.jpg")
add("d7-merengue", "Merengue de limón", "7 cm", "dulce", 3.85, "assets/prod/merengue-limon.jpg")
add("d7-nutella", "Nutella", "7 cm", "dulce", 3.85, "assets/prod/nutella.jpg")
add("d7-pastelera", "Pastelera", "7 cm", "dulce", 3.85, "assets/prod/pastelera.jpg")
add("d7-dulce-leche", "Dulce de leche", "7 cm", "dulce", 3.85, "assets/prod/dulce-leche.jpg")
add("d7-fresa", "Mermelada de fresa", "7 cm", "dulce", 3.85, "assets/prod/fresa.jpg")
add("d7-parchita", "Mermelada de parchita", "7 cm", "dulce", 3.85, "assets/menu/mermelada-durazno.jpg", True)
add("d7-pistacho", "Pistacho", "7 cm", "dulce", 3.85, "assets/prod/pistacho.jpg")
add("d7-dubai", "Chocolate Dubai", "7 cm", "dulce", 4.85, "assets/prod/chocolate-dubai.jpg", dubai=True)
add("s7-jamon-queso", "Jamón y queso", "7 cm", "salado", 3.85, "assets/prod/jamon-queso.jpg")
add("s7-salmon", "Salmón ahumado", "7 cm", "salado", 4.00, "assets/prod/salmon.jpg")
add("s7-caprese", "Caprese", "7 cm", "salado", 3.85, "assets/prod/caprese.jpg")
add("s7-tlt", "TLT", "7 cm", "salado", 3.85, "assets/prod/tlt.jpg")
add("s7-mortadela", "Mortadela de pistacho", "7 cm", "salado", 3.85, "assets/prod/mortadela.jpg")
add("c10-clasica", "Lunetto Clásica", "10 cm", "salado10", 4.50, "assets/prod/clasica.jpg", classic=True)
add("s10-jamon-queso", "Jamón y queso", "10 cm", "salado", 5.25, "assets/prod/jamon-queso.jpg")
add("s10-tlt", "TLT", "10 cm", "salado", 5.25, "assets/prod/tlt.jpg")
add("s10-salmon", "Salmón ahumado", "10 cm", "salado", 5.25, "assets/prod/salmon.jpg")
add("s10-mortadela", "Mortadela de pistacho", "10 cm", "salado", 5.25, "assets/prod/mortadela.jpg")
add("s10-caprese", "Caprese", "10 cm", "salado", 5.25, "assets/prod/caprese.jpg")
add("a-alfajores", "Alfajores", "bolsa de 4", "alfajor", 5.00, "assets/img/alfajores.jpg")
for id, n, p in [("cf-expreso", "Expreso", 2.00), ("cf-americano", "Americano", 2.00), ("cf-capuchino", "Capuchino", 3.50),
                 ("cf-mocaccino", "Mocaccino", 3.50), ("cf-latte", "Latte", 3.50)]:
    add(id, n, "", "cafe", p, "")
for id, n, p in [("b-lata", "Refresco de lata", 2.00), ("b-1lt", "Refresco 1 L", 2.00), ("b-a355", "Agua 355 ml", 1.50),
                 ("b-a600", "Agua 600 ml", 2.00), ("b-a15", "Agua 1.5 L", 3.00), ("b-gas", "Agua gasificada 355 ml", 2.00),
                 ("b-lipton", "Lipton 500 ml", 3.00), ("b-natuflow", "Jugo Natuflow", 3.00)]:
    add(id, n, "", "bebida", p, "", desc="Jugo 100% natural · sin azúcar añadida" if id == "b-natuflow" else "")
ITEMS = I

# ============ PIEZAS ============
def ref(n): return "REF %.2f" % n
def e(s): return html.escape(s, quote=True)

ICON = {
 "bag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg>',
 "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
 "close": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
 "left": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
 "right": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>',
 "ig": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="1" fill="currentColor" stroke="none"/></svg>',
 "tt": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M16.6 5.8A4.3 4.3 0 0 1 15.5 3h-3.1v12.4a2.6 2.6 0 1 1-2.6-2.6c.3 0 .5 0 .8.1V9.7a5.7 5.7 0 1 0 5 5.6V9a7.5 7.5 0 0 0 4.3 1.4V7.3a4.4 4.4 0 0 1-3.3-1.5z"/></svg>',
 "am": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V6.5l10-2V16"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/></svg>',
 "wa": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15l-1.4 5 5.2-1.4A10 10 0 1 0 12 2zm0 18.2c-1.5 0-3-.4-4.2-1.2l-.3-.2-3 .8.8-3-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.700 6.700 0 0 1-3.300-2.900c-.2-.4.2-.4.7-1.300.1-.2 0-.3 0-.5l-.8-1.800c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.200c0 1.300.9 2.500 1 2.700.1.200 1.800 2.800 4.400 3.900 1.600.7 2.300.8 3.100.6.500-.1 1.500-.6 1.700-1.200.2-.6.2-1.100.2-1.200-.1-.1-.3-.2-.5-.3z"/></svg>',
 "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.500C5 14.800 12 21 12 21z"/><circle cx="12" cy="9.500" r="2.500"/></svg>',
 "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M4 7l8 6 8-6"/></svg>',
 "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
}
WA = "https://wa.me/" + CONFIG["whatsapp"]

NAV = [("index.html", "Inicio", "home"), ("menu.html", "Menú", "menu"), ("catering.html", "Catering", "catering"),
       ("contacto.html", "Ubícanos", "contacto")]

def head(title, desc, extra=""):
    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0C422A">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="assets/img/croissants-2.jpg">
<meta property="og:locale" content="es_VE">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="assets/img/favicon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="preload" href="assets/fonts/AlaChamp-demo.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="styles.css?v={V}">
{extra}</head>
<body>
'''

def header(active):
    def cls(k): return ' class="on"' if k == active else ""
    catering_on = ' class="on"' if active in ("catering", "cotizar", "pdf") else ""
    links = f'''<a href="index.html"{cls("home")}>Inicio</a>
      <a href="menu.html"{cls("menu")}>Menú</a>
      <div class="dd"><a href="catering.html"{catering_on}>Catering</a>
        <div class="dd-menu"><a href="catering.html">Nuestro catering</a><a href="cotizar.html">Cotizar</a><a href="catering-pdf.html">PDF de catering</a></div></div>
      <a href="contacto.html"{cls("contacto")}>Ubícanos</a>'''
    return f'''<a class="sr" href="#main">Saltar al contenido</a>
<header class="hdr"><div class="wrap hdr-in">
  <a class="logo" href="index.html" aria-label="Lunetto, inicio"><img src="assets/img/logo-verde.png" alt="Lunetto" width="144" height="34"></a>
  <nav class="nav" id="nav" aria-label="Principal">
      {links}
  </nav>
  <div class="hdr-actions">
    <button class="cart-btn" data-open-cart aria-label="Abrir carrito">{ICON["bag"]}<span class="lbl">Mi pedido</span><span class="cart-count" data-cart-count>0</span></button>
    <button class="burger" id="burger" aria-label="Menú" aria-expanded="false">{ICON["menu"]}</button>
  </div>
</div></header>
<main id="main">
'''

def footer():
    return f'''</main>
<footer class="ftr"><div class="wrap">
  <div class="ftr-top">
    <div class="ftr-brand"><img src="assets/img/logo-crema.png" alt="Lunetto" width="220" height="52">
      <p>Tu media luna. Horneamos a diario en Chacao, Caracas. Un bocado que enamora.</p>
      <div class="social">
        <a href="{CONFIG["instagram"]}" target="_blank" rel="noopener" aria-label="Instagram">{ICON["ig"]}</a>
        <a href="{CONFIG["tiktok"]}" target="_blank" rel="noopener" aria-label="TikTok">{ICON["tt"]}</a>
        <a href="{CONFIG["appleMusic"]}" target="_blank" rel="noopener" aria-label="Apple Music">{ICON["am"]}</a>
      </div></div>
    <div><h4>Explora</h4><ul><li><a href="index.html">Inicio</a></li><li><a href="menu.html">Menú</a></li><li><a href="menu.html#cajas">Arma tu caja</a></li><li><a href="contacto.html">Ubícanos</a></li></ul></div>
    <div><h4>Catering</h4><ul><li><a href="catering.html">Eventos</a></li><li><a href="cotizar.html">Cotizar</a></li><li><a href="catering-pdf.html">PDF de catering</a></li></ul></div>
    <div><h4>Escríbenos</h4><ul><li><a href="{WA}" target="_blank" rel="noopener">WhatsApp</a></li><li><a href="mailto:{CONFIG["email"]}">{CONFIG["email"]}</a></li><li><a href="contacto.html#mapa">Chacao, Caracas</a></li></ul></div>
  </div>
  <div class="ftr-bot"><span>© 2026 Lunetto · Tu Media Luna</span><span><a href="politicas.html">Políticas y precios</a></span></div>
</div></footer>
<a class="fab" href="{WA}" target="_blank" rel="noopener" aria-label="Escríbenos por WhatsApp">{ICON["wa"]}</a>

<div class="ov" id="ov"></div>
<aside class="drawer" id="drawer" aria-label="Carrito de pedido">
  <div class="dr-head"><h3>Tu pedido</h3><button class="dr-close" id="dr-close" aria-label="Cerrar">{ICON["close"]}</button></div>
  <div class="dr-body">
    <div id="dr-lines"></div>
    <div class="dr-form" id="dr-form" hidden>
      <h4>¿Cómo lo recibes?</h4>
      <div class="seg" id="dr-mode"><button type="button" data-mode="pickup">Pick up</button><button type="button" data-mode="delivery">Delivery</button></div>
      <div class="dr-note" id="dr-del-note" hidden>Delivery estimado: {ref(CONFIG["deliveryEstimate"])}. El costo final se confirma por WhatsApp.</div>
      <h4>Tus datos</h4>
      <div class="field"><label for="f-name">Nombre y apellido</label><input id="f-name" autocomplete="name"><span class="err">Escribe tu nombre</span></div>
      <div class="field"><label for="f-phone">Teléfono</label><input id="f-phone" type="tel" autocomplete="tel" inputmode="tel"><span class="err">Escribe tu teléfono</span></div>
      <div class="field"><label for="f-cedula">Cédula</label><input id="f-cedula" inputmode="numeric"><span class="err">Escribe tu cédula</span></div>
      <div class="field" id="f-zone-wrap"><label for="f-zone">Dirección corta</label><input id="f-zone" placeholder="Ej: Chacao, Altamira, Los Palos Grandes"><span class="err">Escribe tu zona</span></div>
      <div class="field" id="f-addr-wrap" hidden><label for="f-addr">Ubicación de entrega</label><textarea id="f-addr" placeholder="Dirección, punto de referencia o link de Google Maps"></textarea><span class="err">Indica dónde entregamos</span></div>
      <div class="field"><label for="f-notes">Notas (opcional)</label><textarea id="f-notes"></textarea></div>
    </div>
  </div>
  <div class="dr-foot" id="dr-foot" hidden>
    <div class="sum">
      <div><span>Subtotal</span><span id="s-sub"></span></div>
      <div id="s-del-row" hidden><span>Delivery (estimado)</span><span id="s-del"></span></div>
      <div class="tot"><span id="s-tot-lbl">Total</span><span id="s-tot"></span></div>
      <small>Precios en REF · euro a tasa BCV. El pedido se confirma por WhatsApp.</small>
    </div>
    <button class="btn wa" id="dr-send" type="button">{ICON["wa"]} Finalizar compra</button>
  </div>
</aside>
<div class="toast" id="toast" role="status"></div>
<script src="lib/config.js?v={V}"></script>
<script src="lib/menu-data.js?v={V}"></script>
<script src="main.js?v={V}" defer></script>
</body></html>
'''

def card(it, show_size=True):
    kind = {"dulce": "Dulce", "salado": "Salado", "salado10": "Clásica", "alfajor": "Alfajor"}.get(it["cat"], "")
    tag = f'{kind} · {it["size"]}'
    ic = " illus" if it["illus"] else (" photo" if it["img"].startswith("assets/prod/") else "")
    alt = f'Alfajores Lunetto, bolsa de 4' if it["cat"] == "alfajor" else f'Media luna {it["name"]} {it["size"]} — Lunetto'
    dcat = "salado" if it["cat"].startswith("salado") else ("dulce" if it["cat"] == "alfajor" else it["cat"])
    return f'''<article class="card" data-item="{it["id"]}" data-cat="{dcat}">
  <div class="card-img{ic}"><img src="{it["img"]}" alt="{e(alt)}" loading="lazy"></div>
  <div class="card-body"><span class="tag">{tag}</span><h3>{e(it["name"])}</h3>
    <div class="card-foot"><span class="price"><small>REF</small> {it["price"]:.2f}</span>
      <button class="add" type="button" data-add>Agregar</button>
      <span class="stepper"><button type="button" data-dec aria-label="Quitar">−</button><b data-q>0</b><button type="button" data-inc aria-label="Agregar">+</button></span></div></div>
</article>'''

def row(it):
    return f'''<div class="row" data-item="{it["id"]}"><div><h3>{e(it["name"])}</h3>{('<span class="note">' + e(it["desc"]) + '</span>') if it["desc"] else ""}<span class="price"><small>REF</small> {it["price"]:.2f}</span></div>
  <div class="ctrl"><button class="add" type="button" data-add>Agregar</button><span class="stepper"><button type="button" data-dec aria-label="Quitar">−</button><b data-q>0</b><button type="button" data-inc aria-label="Agregar">+</button></span></div></div>'''

def by(cat, size=None):
    return [i for i in ITEMS if i["cat"] == cat and (size is None or i["size"] == size)]

def marquee(words):
    seq = "".join(f'<span class="sym">{w}</span>' if NOSYM.search(w) else f"<span>{w}</span>" for w in words)
    return f'<div class="marquee" aria-hidden="true"><div class="marquee-track">{seq}{seq}</div></div>'

STAMP = '''<div class="stamp" aria-hidden="true"><svg viewBox="0 0 200 200"><defs><path id="c" d="M100,100 m-72,0 a72,72 0 1,1 144,0 a72,72 0 1,1 -144,0"/></defs><text font-family="Montserrat" font-weight="700" font-size="15.500" letter-spacing="4.300" fill="currentColor"><textPath href="#c">HORNEAMOS A DIARIO • EN CHACAO • </textPath></text></svg><span class="moon">Lunetto</span></div>'''

def jsonld():
    d = {"@context": "https://schema.org", "@type": "Bakery", "name": "Lunetto — Tu Media Luna",
         "description": "Medialunas artesanales dulces y saladas, café de especialidad y catering en Chacao, Caracas.",
         "servesCuisine": "Panadería, medialunas argentinas, café",
         "address": {"@type": "PostalAddress", "streetAddress": "Calle Cecilio Acosta", "addressLocality": "Chacao", "addressRegion": "Caracas", "addressCountry": "VE"},
         "telephone": "+" + CONFIG["whatsapp"], "email": CONFIG["email"], "hasMap": CONFIG["mapsLink"],
         "openingHours": "Tu-Su 09:00-20:00",
         "sameAs": [CONFIG["instagram"], CONFIG["tiktok"]], "priceRange": "REF 1.50 - REF 55"}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>\n"

NOSYM = re.compile(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]")
def symfix(h):
    """Ala Champ (demo) no tiene números ni signos: los títulos que los llevan usan Montserrat."""
    def one(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        plain = re.sub(r'<span class="script"[^>]*>.*?</span>', "", inner, flags=re.S)
        plain = html.unescape(re.sub(r"<[^>]+>", "", plain))
        if not NOSYM.search(plain): return m.group(0)
        if 'class="' in attrs: attrs = attrs.replace('class="', 'class="sym ', 1)
        else: attrs += ' class="sym"'
        return f"<{tag}{attrs}>{inner}</{tag}>"
    return re.sub(r"<(h[123]|blockquote)([^>]*)>(.*?)</\1>", one, h, flags=re.S)

# ============ PÁGINAS ============
def page_home():
    carousel = [i for i in ITEMS if (i["cat"] in ("dulce", "salado") and i["size"] == "7 cm") or i["cat"] == "alfajor"]
    cards = "\n".join(card(i) for i in carousel)
    box_card = f'''<article class="card box-cta" data-cat="caja"><div class="card-body"><span class="script">arma tu</span><h3>Caja Lunetto</h3>
      <p style="font-size:.9rem;opacity:.9">De 4, 8 o 16. El precio se ajusta solo según lo que elijas.</p><a class="btn cream" href="menu.html#cajas">Armar mi caja</a></div></article>'''
    h = head("Lunetto · Medialunas y café de especialidad en Chacao, Caracas",
             "Lunetto, tu media luna: medialunas dulces y saladas horneadas a diario, café de especialidad y catering para eventos en Chacao, Caracas. Pide por WhatsApp.",
             jsonld())
    h += header("home")
    h += f'''
<section class="hs" id="hs" aria-roledescription="carrusel" aria-label="Destacados">
  <div class="hs-track">
    <article class="slide on"><img class="bg" src="assets/img/hero-medialunas.jpg" alt="Medialunas Lunetto doradas recién horneadas"><div class="shade"></div>
      <div class="wrap"><div class="copy"><span class="kicker">Chacao · Caracas</span>
        <h1 class="h-xl">Tu media luna<span class="script">horneada a diario</span></h1>
        <p class="lead">La tentación que sí puedes morder. Medialunas dulces y saladas, café de especialidad y ese bocado que enamora.</p>
        <div class="cta-row"><a class="btn cream" href="#menu">Ver menú y pedir</a><a class="btn ghost" href="menu.html#cajas">Armar una caja</a></div></div></div></article>
    <article class="slide"><img class="bg pos-bottom" src="assets/img/cajas-evento-crop.jpg" alt="Cajas Lunetto apiladas para un evento"><div class="shade"></div>
      <div class="wrap"><div class="copy"><span class="kicker">Lunetto Box</span>
        <h2 class="h-xl">Cajas para regalar<span class="script">y compartir</span></h2>
        <p class="lead">De 4, 8 o 16 medialunas. Tú eliges los sabores y el precio se ajusta solo.</p>
        <div class="cta-row"><a class="btn cream" href="menu.html#cajas">Armar mi caja</a><a class="btn ghost" href="cotizar.html">Pedido para empresas</a></div></div></div></article>
    <article class="slide side"><img class="bg" src="assets/img/carrito-1.jpg" alt="Carrito Lunetto con toldo verde, máquina de espresso y vitrina de medialunas"><div class="shade"></div>
      <div class="wrap"><div class="copy"><span class="kicker">Catering &amp; eventos</span>
        <h2 class="h-xl">Llevamos Lunetto<span class="script">a tu evento</span></h2>
        <p class="lead">El carrito Lunetto y el Lunetto Bar, con medialunas, café y toppings al momento.</p>
        <div class="cta-row"><a class="btn cream" href="cotizar.html">Cotizar mi evento</a><a class="btn ghost" href="catering.html">Conocer el catering</a></div></div></div></article>
  </div>
  <div class="hs-ctrl"><button type="button" id="hs-prev" aria-label="Anterior">{ICON["left"]}</button><span class="hs-dots" id="hs-dots"><i class="on"></i><i></i><i></i></span><button type="button" id="hs-next" aria-label="Siguiente">{ICON["right"]}</button></div>
</section>
{marquee(["Horneamos a diario", "Medialunas dulces", "Medialunas saladas", "Café de especialidad", "Chacao, Caracas", "Cajas para regalar", "Catering para eventos"])}

<section class="sec on-light" id="menu"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">El menú</span><h2 class="h-lg">Elige tu tentación<span class="script"> y agrégala al pedido</span></h2></div>
    <div class="car-nav"><button id="car-prev" aria-label="Anterior">{ICON["left"]}</button><button id="car-next" aria-label="Siguiente">{ICON["right"]}</button></div></div>
  <div class="tabs reveal" style="margin-bottom:22px"><button class="tab on" data-tab="todo">Todo</button><button class="tab" data-tab="dulce">Dulces</button><button class="tab" data-tab="salado">Salados</button></div>
  <div class="car-wrap reveal"><div class="car" id="car">
{cards}
{box_card}
  </div></div>
  <div class="cta-row" style="margin-top:8px"><a class="btn" href="menu.html">Ver menú completo</a><a class="btn ghost" style="color:var(--forest)" href="menu.html#cafe">Café y bebidas</a></div>
</div></section>

<section class="sec cream on-light"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Lo nuestro</span><h2 class="h-lg">Tres maneras de<span class="script"> enamorarte</span></h2></div></div>
  <div class="banners">
    <a class="banner reveal" href="menu.html#cafe"><img src="assets/img/cafe-maquina.jpg" alt="Café de especialidad Lunetto saliendo de la máquina de espresso" loading="lazy"><div class="banner-in"><span class="tag">Barra de café</span><h3>Café de especialidad</h3><p>Expreso, capuchino, latte y mocaccino. El compañero perfecto de tu media luna.</p><span class="more">Ver café</span></div></a>
    <a class="banner reveal" href="menu.html#dulces"><img src="assets/img/croissants-2.jpg" alt="Medialunas Lunetto doradas" loading="lazy"><div class="banner-in"><span class="tag">Nuestra estrella</span><h3>Las medialunas</h3><p>De 7 y 10 cm, dulces y saladas. Hojaldradas, doradas y hechas hoy.</p><span class="more">Ver medialunas</span></div></a>
    <a class="banner reveal" href="menu.html#alfajores"><img src="assets/img/alfajores.jpg" alt="Alfajores Lunetto en bolsa con lazo verde" loading="lazy"><div class="banner-in"><span class="tag">Para endulzar</span><h3>Alfajores</h3><p>Bolsa de 4 alfajores, lista para regalar o para ti. REF 5.00.</p><span class="more">Ver alfajores</span></div></a>
  </div>
</div></section>

<section class="quote"><img class="bg" src="assets/img/vitrina-verde.jpg" alt="" loading="lazy"><div class="wrap reveal">
  <span class="kicker">Todos los días</span>
  <blockquote>Horneamos a diario <em>sin prisa</em> sin atajos</blockquote>
  <div class="phrases"><span>Hojaldre que cruje</span><span>Rellenos que enamoran</span><span>Un bocado y ya no hay vuelta atrás</span></div>
</div></section>

<section class="sec forest"><div class="wrap split">
  <div class="split-art reveal"><div class="frame arch2"><img src="assets/img/carrito-staff.jpg" alt="Equipo Lunetto atendiendo el carrito en un evento" loading="lazy"></div><div class="floaty">Carrito Lunetto + Lunetto Bar</div></div>
  <div class="split-copy reveal"><span class="kicker">Catering &amp; eventos</span>
    <h2 class="h-lg" style="margin-top:.4em">Te acompañamos<span class="script">en tus eventos</span></h2>
    <p>Llevamos tu carrito Lunetto y el Lunetto Bar hasta tu celebración: medialunas recién servidas, café y ese detalle que tus invitados van a recordar.</p>
    <div class="cta-row"><a class="btn cream" href="cotizar.html">Cotizar mi evento</a><a class="btn ghost" href="catering.html">Conoce el catering</a></div></div>
</div></section>

<section class="sec on-light"><div class="wrap chacao">
  <div class="reveal"><span class="kicker">Estamos en Chacao</span>
    <h2 class="h-lg">Medialunas artesanales en Chacao, Caracas</h2>
    <p>Lunetto es tu panadería de medialunas en <strong>Chacao, Caracas</strong>: hojaldre horneado a diario, rellenos dulces y salados, café de especialidad y cajas listas para regalar o compartir.</p>
    <p>Pasa por tu media luna, pide para llevar o coordina un delivery. Y si tienes un evento, nuestro catering llega hasta ti.</p>
    <ul class="checks"><li>Horneadas a diario, para llevar (take-out)</li><li>Cajas de 4, 8 y 16 para regalar</li><li>Café de especialidad y bebidas</li><li>Pick up en Chacao o delivery por WhatsApp</li></ul>
    <a class="btn" href="contacto.html">Cómo llegar</a></div>
  <div class="info-card reveal"><h3>Encuéntranos</h3><dl>
    <div><dt>Ubicación</dt><dd>{CONFIG["address"]}</dd></div>
    <div><dt>Horario</dt><dd>{CONFIG["hours"]}</dd></div>
    <div><dt>WhatsApp</dt><dd><a href="{WA}" target="_blank" rel="noopener">{CONFIG["whatsappDisplay"]}</a></dd></div>
    <div><dt>Instagram</dt><dd><a href="{CONFIG["instagram"]}" target="_blank" rel="noopener">@miolunetto</a></dd></div></dl></div>
</div></section>
'''
    return h + footer()

def page_menu():
    dulces = [i for i in by("dulce", "7 cm")]
    salados7 = [i for i in by("salado", "7 cm")]
    g10 = [i for i in ITEMS if i["size"] == "10 cm"]
    h = head("Menú · Medialunas dulces y saladas, cajas y café | Lunetto Chacao",
             "Menú de Lunetto en Chacao, Caracas: medialunas dulces y saladas de 7 y 10 cm, cajas para regalar, café y bebidas. Arma tu pedido y finaliza por WhatsApp.")
    h += header("menu")
    h += f'''
<section class="page-hero"><div class="wrap"><span class="crumbs"><a href="index.html">Inicio</a> / Menú</span>
  <h1>El menú<span class="script">de la casa</span></h1>
  <p>Dulces, salados, cajas y café. Todo horneado a diario. Los precios están en REF (euro a tasa BCV).</p></div></section>
<nav class="stickynav" aria-label="Secciones del menú"><div class="wrap"><a href="#dulces">Dulces 7 cm</a><a href="#salados">Salados 7 cm</a><a href="#grandes">Medialunas 10 cm</a><a href="#cajas">Cajas</a><a href="#alfajores">Alfajores</a><a href="#cafe">Café</a><a href="#bebidas">Bebidas</a></div></nav>
<div class="wrap on-light">
  <section class="menu-sec" id="dulces"><span class="kicker">Media lunas 7 cm</span><h2 class="h-lg">Dulces</h2><p class="sub">Las clásicas de siempre y las que te hacen volver.</p>
    <div class="grid">{"".join(card(i) for i in dulces)}</div></section>
  <section class="menu-sec" id="salados"><span class="kicker">Media lunas 7 cm</span><h2 class="h-lg">Salados</h2><p class="sub">Para el almuerzo, la merienda o cuando quieras.</p>
    <div class="grid">{"".join(card(i) for i in salados7)}</div></section>
  <section class="menu-sec" id="grandes"><span class="kicker">Media lunas 10 cm</span><h2 class="h-lg">Las grandes</h2><p class="sub">La Lunetto clásica y los salados en tamaño 10 cm.</p>
    <div class="grid">{"".join(card(i) for i in g10)}</div></section>
  <section class="menu-sec" id="cajas"><span class="kicker">Para regalar o compartir</span><h2 class="h-lg">Lunetto Box</h2>
    <p class="sub">Arma tu caja: elige el tamaño, la cantidad y los sabores. El precio se ajusta solo según lo que pongas dentro.</p>
    <div class="builder" id="builder">
      <div><span class="script">arma tu caja</span><h2 class="h-md">A tu manera</h2>
        <div class="b-step"><h4>1 · Tamaño</h4><div class="pills" id="b-size"></div></div>
        <div class="b-step"><h4>2 · Cantidad</h4><div class="pills" id="b-qty"></div></div>
        <div class="b-sum"><div class="tier" id="b-tier"></div><div class="tot" id="b-total"></div><div class="note" id="b-note"></div>
          <div class="b-prog"><i id="b-prog"></i></div><div class="b-count" id="b-count"></div>
          <div class="b-tools"><button class="btn cream" id="b-add" type="button" disabled>Agregar caja al carrito</button></div></div>
      </div>
      <div><div class="b-step" style="margin-top:0"><h4>3 · Elige tus sabores</h4>
        <div class="b-tools" style="margin:0 0 14px"><button class="pill" id="b-classic" type="button">Todas clásicas</button><button class="pill" id="b-clear" type="button">Vaciar</button></div>
        <div class="b-flav" id="b-flav"></div></div></div>
    </div>
    <div class="box-tables">
      <div class="bt"><h3>Clásica 7 cm</h3><p>Solo Lunettos clásicas.</p><ul><li>Caja de 4 <b>{ref(11)}</b></li><li>Caja de 8 <b>{ref(22)}</b></li><li>Caja de 16 <b>{ref(44)}</b></li></ul></div>
      <div class="bt"><h3>Mixta 7 cm</h3><p>Dulces, salados y clásicas al mismo precio. Solo sube con Chocolate Dubai.</p><ul><li>Caja de 4 <b>{ref(14)}</b></li><li>Caja de 8 <b>{ref(28)}</b></li><li>Caja de 16 <b>{ref(55)}</b></li></ul></div>
      <div class="bt"><h3>Clásica 10 cm</h3><p>Solo clásicas. Si incluyes salados aplica la caja de salados.</p><ul><li>Caja de 2 <b>{ref(8.25)}</b></li><li>Caja de 4 <b>{ref(17)}</b></li><li>Caja de 8 <b>{ref(33)}</b></li></ul></div>
      <div class="bt"><h3>Salados 10 cm</h3><p>Puede incluir clásicas al precio de esta caja.</p><ul><li>Caja de 2 <b>{ref(10)}</b></li><li>Caja de 4 <b>{ref(20)}</b></li><li>Caja de 8 <b>{ref(40)}</b></li></ul></div>
    </div></section>
  <section class="menu-sec" id="alfajores"><span class="kicker">Para acompañar</span><h2 class="h-lg">Alfajores</h2><p class="sub">Bolsa de 4 alfajores.</p>
    <div class="grid">{"".join(card(i) for i in by("alfajor"))}</div></section>
  <section class="menu-sec" id="cafe"><div class="cafe-grid">
    <div><span class="kicker">Barra</span><h2 class="h-lg">Café</h2><p class="sub">Café de especialidad para acompañar tu media luna.</p>
      <div class="list one">{"".join(row(i) for i in by("cafe"))}</div></div>
    <div class="cafe-stage reveal" aria-hidden="true"><img class="cup" src="assets/img/cafe-splash.webp" alt="" loading="lazy"></div>
  </div></section>
  <section class="menu-sec" id="bebidas"><span class="kicker">Para acompañar</span><h2 class="h-lg">Bebidas</h2><p class="sub">Refrescos, aguas, té y jugo.</p>
    <div class="list">{"".join(row(i) for i in by("bebida"))}</div></section>
</div>
<section class="sec cream on-light" style="padding:56px 0"><div class="wrap" style="text-align:center"><h2 class="h-md">¿Preparas un evento?</h2><p style="margin:.6em auto 1.6em;max-width:48ch">Llevamos el carrito Lunetto y el Lunetto Bar a tu celebración.</p><a class="btn" href="cotizar.html">Cotizar catering</a></div></section>
'''
    return h + footer()

def page_catering():
    h = head("Catering para eventos en Caracas · Carrito y Lunetto Bar | Lunetto",
             "Catering de Lunetto para eventos en Caracas: carrito con espresso y medialunas, Lunetto Bar con salsas y toppings al momento, y cajas. Cotiza por formulario o WhatsApp.")
    h += header("catering")
    h += f'''
<section class="page-hero"><div class="wrap"><span class="crumbs"><a href="index.html">Inicio</a> / Catering</span>
  <h1>Catering<span class="script">para tus eventos</span></h1>
  <p>Tu carrito Lunetto y el Lunetto Bar llegan a tu celebración. Medialunas, café y un detalle que se recuerda.</p>
  <div class="subnav"><a class="on" href="catering.html">Nuestro catering</a><a href="cotizar.html">Cotizar</a><a href="catering-pdf.html">PDF</a></div></div></section>
<section class="sec on-light"><div class="wrap">
  <div class="svc">
    <div class="svc-card reveal"><div class="im"><img src="assets/img/carrito-1.jpg" alt="Carrito Lunetto con toldo verde, máquina de espresso y vitrina de medialunas" loading="lazy"></div><div class="tx"><span class="kicker">Servicio</span><h3>Carrito Lunetto</h3><p>Un carrito con toldo verde, máquina de espresso y vitrina de medialunas, montado en tu evento y atendido por nuestro equipo.</p><a class="btn cream" href="cotizar.html">Cotizar</a></div></div>
    <div class="svc-card reveal"><div class="im"><img src="assets/img/bar-bandeja.jpg" alt="Lunetto Bar: bandeja con salsas para personalizar las medialunas" loading="lazy"></div><div class="tx"><span class="kicker">Servicio</span><h3>Lunetto Bar</h3><p>Medialunas armadas al momento: tus invitados eligen la salsa, como el dulce de leche o el chocolate, y el topping, como pistacho o chips de chocolate.</p><a class="btn cream" href="cotizar.html">Cotizar</a></div></div>
  </div>
</div></section>
<section class="sec forest"><div class="wrap split">
  <div class="split-art reveal" style="max-width:380px;justify-self:center;width:100%"><video class="bar-video" src="assets/video/lunetto-bar.mp4" poster="assets/img/bar-salsas.jpg" autoplay muted loop playsinline preload="metadata" aria-label="Video del Lunetto Bar"></video></div>
  <div class="split-copy reveal"><span class="kicker">Lunetto Bar</span>
    <h2 class="h-lg" style="margin-top:.4em">Míralo<span class="script">en acción</span></h2>
    <p>Una media luna calientita, una salsa que cae despacito y un topping que la termina. Es un momento que tus invitados van a querer grabar.</p>
    <div class="mini"><img src="assets/img/bar-salsas.jpg" alt="Servido del Lunetto Bar con salsa de dulce de leche" loading="lazy"><img src="assets/img/bar-pistacho.jpg" alt="Media luna con salsa de chocolate y pistacho del Lunetto Bar" loading="lazy"></div>
    <div class="cta-row"><a class="btn cream" href="cotizar.html">Cotizar el Lunetto Bar</a></div></div>
</div></section>
<section class="sec on-light"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Eventos</span><h2 class="h-lg">Así se ven<span class="script"> nuestros eventos</span></h2></div></div>
  <div class="gal">
    <figure class="reveal g-wide"><img src="assets/img/cajas-evento.jpg" alt="Pilas de cajas Lunetto listas para un evento" loading="lazy"></figure>
    <figure class="reveal"><img src="assets/img/carrito-staff.jpg" alt="Equipo Lunetto atendiendo el carrito" loading="lazy"></figure>
    <figure class="reveal"><img src="assets/img/carrito-2.jpg" alt="Carrito Lunetto en una terraza" loading="lazy"></figure>
  </div>
</div></section>
<section class="sec cream on-light"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Cómo funciona</span><h2 class="h-lg">Así de fácil</h2></div></div>
  <div class="steps">
    <div class="step reveal"><h3>Cuéntanos tu evento</h3><p>Fecha, número de personas y lugar. Llena el formulario o escríbenos por WhatsApp.</p></div>
    <div class="step reveal"><h3>Recibe tu cotización</h3><p>Te armamos una propuesta con el servicio que mejor se ajusta a tu celebración.</p></div>
    <div class="step reveal"><h3>Nosotros nos encargamos</h3><p>Horneamos, llegamos y servimos. Tú disfrutas de tu evento.</p></div>
  </div>
  <div class="cta-row" style="margin-top:36px"><a class="btn" href="cotizar.html">Cotizar ahora</a><a class="btn wa" href="{WA}" target="_blank" rel="noopener">{ICON["wa"]} WhatsApp</a><a class="btn ghost" style="color:var(--forest)" href="catering-pdf.html">Ver PDF</a></div>
</div></section>
'''
    return h + footer()

def page_cotizar():
    h = head("Cotizar catering · Lunetto Chacao, Caracas",
             "Solicita la cotización de catering para tu evento: formulario o WhatsApp. Carrito Lunetto y Lunetto Bar en Caracas.")
    h += header("cotizar")
    h += f'''
<section class="page-hero"><div class="wrap"><span class="crumbs"><a href="index.html">Inicio</a> / <a href="catering.html">Catering</a> / Cotizar</span>
  <h1>Cotiza<span class="script">tu evento</span></h1>
  <p>Cuéntanos los detalles y te respondemos con una propuesta.</p>
  <div class="subnav"><a href="catering.html">Nuestro catering</a><a class="on" href="cotizar.html">Cotizar</a><a href="catering-pdf.html">PDF</a></div></div></section>
<section class="sec on-light"><div class="wrap two">
  <div class="reveal"><span class="kicker">Rápido</span><h2 class="h-md" style="margin:.4em 0 .6em">¿Prefieres escribirnos directo?</h2><p style="margin-bottom:1.6em">Cuéntanos tu evento por WhatsApp y coordinamos todo por ahí.</p>
    <a class="btn wa" href="{WA}?text={html.escape("Hola Lunetto, quiero cotizar catering para un evento.")}" target="_blank" rel="noopener">{ICON["wa"]} Escribir por WhatsApp</a></div>
  <div class="form-shell reveal"><form class="form" id="quote-form" novalidate>
    <input type="text" name="company" id="q-company" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;top:-9999px">
    <div class="field"><label for="q-name">Nombre</label><input id="q-name" name="name" data-req autocomplete="name"><span class="err">Requerido</span></div>
    <div class="field"><label for="q-phone">Teléfono / WhatsApp</label><input id="q-phone" name="phone" type="tel" data-req><span class="err">Requerido</span></div>
    <div class="field"><label for="q-email">Correo (opcional)</label><input id="q-email" name="email" type="email"></div>
    <div class="field"><label for="q-event">Tipo de evento</label><select id="q-event" name="event" data-req><option value="">Selecciona</option><option>Cumpleaños</option><option>Boda / Pre-boda</option><option>Baby shower / Bridal shower</option><option>Evento corporativo</option><option>Otro</option></select><span class="err">Requerido</span></div>
    <div class="field"><label for="q-date">Fecha</label><input id="q-date" name="date" type="date" data-req><span class="err">Requerido</span></div>
    <div class="field"><label for="q-guests">Número de personas</label><input id="q-guests" name="guests" type="number" min="1" inputmode="numeric" data-req><span class="err">Requerido</span></div>
    <div class="field"><label for="q-service">Servicio</label><select id="q-service" name="service" data-req><option value="">Selecciona</option><option>Carrito Lunetto</option><option>Lunetto Bar</option><option>Carrito + Lunetto Bar</option><option>Cajas Lunetto</option><option>Aún no lo sé</option></select><span class="err">Requerido</span></div>
    <div class="field"><label for="q-place">Lugar del evento</label><input id="q-place" name="place"></div>
    <div class="field full"><label for="q-msg">Cuéntanos más</label><textarea id="q-msg" name="msg"></textarea></div>
    <div class="form-actions"><button class="btn wa" id="q-wa" type="button">{ICON["wa"]} Enviar por WhatsApp</button><button class="btn ghost" style="color:var(--forest)" id="q-mail" type="button">Enviar por correo</button></div>
    <p class="form-note">Por WhatsApp se abre la conversación lista para mandar. Por correo, tu cotización se envía directo, sin pasos extra.</p>
  </form></div>
</div></section>
'''
    return h + footer()

def page_pdf():
    h = head("PDF de catering · Lunetto", "Descarga el PDF de catering y menú de Lunetto en Chacao, Caracas.")
    h += header("pdf")
    h += f'''
<section class="page-hero"><div class="wrap"><span class="crumbs"><a href="index.html">Inicio</a> / <a href="catering.html">Catering</a> / PDF</span>
  <h1>Catering<span class="script">en PDF</span></h1>
  <p>Míralo aquí o descárgalo para compartirlo.</p>
  <div class="subnav"><a href="catering.html">Nuestro catering</a><a href="cotizar.html">Cotizar</a><a class="on" href="catering-pdf.html">PDF</a></div></div></section>
<section class="sec on-light" style="padding-top:44px"><div class="wrap">
  <div class="cta-row" style="margin-bottom:22px"><a class="btn" href="assets/catering-dossier.pdf" download>Descargar PDF</a><a class="btn ghost" style="color:var(--forest)" href="cotizar.html">Cotizar</a></div>
  <iframe class="pdf-frame" src="assets/catering-dossier.pdf#view=FitH" title="Dosier de catering Lunetto"></iframe>
  <p style="margin-top:14px;font-size:.85rem;opacity:.75">Si no se ve el visor, <a href="assets/catering-dossier.pdf" download>descarga el PDF</a>.</p>
</div></section>
'''
    return h + footer()

def page_contacto():
    q = CONFIG["mapsQuery"].replace(" ", "+")
    h = head("Ubícanos · Lunetto en Chacao, Caracas",
             "Ubicación, WhatsApp y correo de Lunetto en Chacao, Caracas. Medialunas, café y catering.", jsonld())
    h += header("contacto")
    h += f'''
<section class="page-hero"><div class="wrap"><span class="crumbs"><a href="index.html">Inicio</a> / Ubícanos</span>
  <h1>Ubícanos<span class="script">te esperamos</span></h1><p>Pasa por tu media luna, escríbenos o pide por WhatsApp.</p></div></section>
<section class="sec on-light" id="mapa"><div class="wrap ct-grid">
  <div class="ct-list">
    <div class="ct-item"><span class="ic">{ICON["pin"]}</span><div><small>Ubicación</small><strong>{CONFIG["address"]}</strong></div></div>
    <a class="ct-item" href="{WA}" target="_blank" rel="noopener"><span class="ic">{ICON["wa"]}</span><div><small>WhatsApp</small><strong>{CONFIG["whatsappDisplay"]}</strong></div></a>
    <a class="ct-item" href="mailto:{CONFIG["email"]}"><span class="ic">{ICON["mail"]}</span><div><small>Correo</small><strong>{CONFIG["email"]}</strong></div></a>
    <div class="ct-item"><span class="ic">{ICON["clock"]}</span><div><small>Horario</small><strong>{CONFIG["hours"]}</strong></div></div>
    <a class="ct-item" href="{CONFIG["instagram"]}" target="_blank" rel="noopener"><span class="ic">{ICON["ig"]}</span><div><small>Instagram</small><strong>@miolunetto</strong></div></a>
    <a class="btn" href="{CONFIG["mapsLink"]}" target="_blank" rel="noopener" style="justify-self:start">Abrir en Google Maps</a>
  </div>
  <div class="map"><iframe title="Mapa de Lunetto en Chacao, Caracas" src="https://www.google.com/maps?q={q}&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>
</div></section>
'''
    return h + footer()

def page_politicas():
    h = head("Políticas y precios · Lunetto", "Políticas de precios (REF a tasa BCV), pedidos, delivery y cajas de Lunetto.")
    h += header("politicas")
    h += f'''
<section class="page-hero"><div class="wrap"><span class="crumbs"><a href="index.html">Inicio</a> / Políticas</span><h1>Políticas<span class="script">y precios</span></h1></div></section>
<section class="sec on-light"><div class="wrap"><div class="prose">
  <h2>Precios</h2>
  <div class="callout"><strong>Los precios se muestran en REF.</strong> 1 REF equivale a 1 euro, y se cancela al valor de la tasa BCV del día del pago.</div>
  <h2>Pedidos</h2>
  <p>Al finalizar tu compra en la web, tu pedido se envía por WhatsApp con todos tus datos. El pedido queda confirmado cuando te respondemos por ese medio.</p>
  <h2>Pick up y delivery</h2>
  <ul><li><strong>Pick up:</strong> retiras tu pedido en nuestra tienda de Chacao (Calle Cecilio Acosta).</li><li><strong>Delivery:</strong> el costo mostrado ({ref(CONFIG["deliveryEstimate"])}) es un estimado. El monto final depende de la zona y se confirma por WhatsApp.</li></ul>
  <h2>Cajas Lunetto</h2>
  <ul><li><strong>Clásica 7 cm:</strong> solo lleva Lunettos clásicas.</li><li><strong>Mixta 7 cm:</strong> combina dulces, salados y clásicas al mismo precio; solo sube si incluye Chocolate Dubai.</li><li><strong>Clásica 10 cm:</strong> solo clásicas. Si incluye salados se aplica el precio de la caja de salados.</li><li><strong>Salados 10 cm:</strong> puede incluir clásicas, con el precio de esta caja.</li></ul>
  <h2>Catering</h2>
  <p>Las cotizaciones de catering se personalizan según fecha, número de personas y lugar. Solicítalas desde <a href="cotizar.html">Cotizar</a>.</p>
</div></div></section>
'''
    return h + footer()

# ============ ESCRITURA ============
def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if path.endswith(".html"): content = symfix(content)
    with open(full, "w", encoding="utf-8") as f: f.write(content)

if __name__ == "__main__":
    write("lib/config.js", "window.LUNETTO_CONFIG = " + json.dumps(CONFIG, ensure_ascii=False, indent=2) + ";\n")
    menu = {"items": [{k: i[k] for k in ("id", "name", "size", "cat", "price", "classic", "dubai")} for i in ITEMS],
            "boxes": BOXES}
    write("lib/menu-data.js", "window.LUNETTO_MENU = " + json.dumps(menu, ensure_ascii=False) + ";\n")
    for name, fn in [("index.html", page_home), ("menu.html", page_menu), ("catering.html", page_catering),
                     ("cotizar.html", page_cotizar), ("catering-pdf.html", page_pdf), ("contacto.html", page_contacto),
                     ("politicas.html", page_politicas)]:
        write(name, fn())
    write("robots.txt", "User-agent: *\nAllow: /\n")
    print("OK")
