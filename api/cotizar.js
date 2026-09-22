// api/cotizar.js — recibe el formulario de "Cotizar" y envía el correo con Resend.
// Requiere la variable de entorno RESEND_API_KEY (Vercel → Project → Settings → Environment Variables).
// No usa librerías externas: llama a la API de Resend directamente con fetch.

const TO = ['info@miolunetto.com'];
const FROM = 'Lunetto Web <onboarding@resend.dev>'; // ver LEEME.txt sobre verificar el dominio en Resend

function esc(s) {
  return String(s || '').replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') { res.status(405).json({ ok: false, error: 'method_not_allowed' }); return; }
  if (!process.env.RESEND_API_KEY) { res.status(500).json({ ok: false, error: 'missing_api_key' }); return; }

  var b = req.body || {};
  if (typeof b === 'string') { try { b = JSON.parse(b); } catch (e) { b = {}; } }

  // Honeypot anti-spam: si el campo oculto "company" viene lleno, es un bot. Se responde "ok" sin enviar nada.
  if (b.company) { res.status(200).json({ ok: true }); return; }

  var need = ['name', 'phone', 'event', 'date', 'guests', 'service'];
  for (var i = 0; i < need.length; i++) {
    if (!String(b[need[i]] || '').trim()) { res.status(400).json({ ok: false, error: 'missing_' + need[i] }); return; }
  }

  var rows = [
    ['Nombre', b.name], ['Teléfono', b.phone], ['Correo', b.email],
    ['Tipo de evento', b.event], ['Fecha', b.date], ['Personas', b.guests],
    ['Servicio', b.service], ['Lugar', b.place],
  ].filter(function (r) { return String(r[1] || '').trim(); });

  var html = '<div style="font-family:Arial,sans-serif;color:#1D1D1B">' +
    '<h2 style="color:#0C422A;margin:0 0 16px">Nueva cotización de catering · Lunetto</h2>' +
    '<table cellpadding="0" cellspacing="0">' +
    rows.map(function (r) {
      return '<tr><td style="padding:4px 14px 4px 0;color:#0C422A"><b>' + esc(r[0]) + '</b></td><td>' + esc(r[1]) + '</td></tr>';
    }).join('') +
    '</table>' +
    (String(b.msg || '').trim() ? '<p style="margin-top:16px"><b>Detalles:</b><br>' + esc(b.msg).replace(/\n/g, '<br>') + '</p>' : '') +
    '</div>';

  try {
    var r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + process.env.RESEND_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: FROM,
        to: TO,
        reply_to: String(b.email || '').trim() || undefined,
        subject: 'Cotización catering · ' + b.name,
        html: html,
      }),
    });
    if (!r.ok) { var t = await r.text(); res.status(502).json({ ok: false, error: t }); return; }
    res.status(200).json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, error: 'send_failed' });
  }
};
