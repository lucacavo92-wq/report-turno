// Prova veloce dell'app (Playwright + Chromium). Apre l'app da un server locale (non file://).
// Uso:  NODE_PATH=$(npm root -g) node tools/prova.js
// Equivalente in Python (usata su Windows): tools/prova.py
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const MIME = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.png':'image/png', '.svg':'image/svg+xml', '.webmanifest':'application/manifest+json' };
const server = http.createServer((q, r) => {
  const u = q.url.split('?')[0];
  const f = path.join(ROOT, u === '/' ? 'index.html' : decodeURIComponent(u));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' }); r.end(d); } });
});
const ESEMPIO = `Buongiorno
*Report turno 14-22 del 28/09
Produzione 398 ton
Ritardo 15 min terzo turno pe4 perdita banco valvola 1
Copertura schede fino alle 7.30

Reparto taglio bramme : 9

Sicurezza
• Tutti i dipendenti hanno indossato correttamente i DPI e rispettato le procedure di sicurezza.
• Pulizia: nessuna segnalazione.
• Nessun atto di violenza nè fisica nè verbale.
• Nessun near miss.

Qualità
• estetica conforme
• planarità sul 25 mm accettabile.
• larghezze, lunghezze e spessori conformi
• Segni spianatrice ambo i lati.

Ambiente
Scrubber in marcia.
Emissioni convogliate nella norma
Emissioni diffuse (discagliatore, spianatrice, taglio lamiere e treno di laminazione): nella norma

Segnalazioni:
Nessuna`;
const MAG = `Buongiorno,
*Controllo magazzino*

• Totale pacchi in magazzino: 21
• Pacchi spedibili: 13
• 8 fasce di intestature a terra

• 1 cassone Risaliti vuoto appena cambiato
• 1 bat

*Scoria*
• Mag. Lamiere: 4 cassoni pieni
• Taglio bramme: cassone grande vuoto, piccolo pieno

*Controllo qualità pacchi*
• Superficie conforme
• Superficie inferiore conforme
• I tagli sono abbastanza puliti
• Nessun segno dei cilindri di laminazione
• Visibili segni della spianatrice lato strada e lato ferrovia`;
const LAM1 = `*Controllo lamiere*
Lotto 19223
Spessori testa: 25.7 25.9 25.3
Spessori coda: 25.3 25.5 25.4
Lunghezza: 12285 12280
Larghezza: 2064 2064`;
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }).catch(() => chromium.launch());
  const p = await b.newPage({ viewport: { width: 400, height: 900 } });
  let ok = true; const check = (c, m) => { console.log((c ? 'OK   ' : 'ERRORE ') + m); ok = ok && c; };
  p.on('pageerror', e => check(false, 'errore JS: ' + e.message));
  await p.clock.setFixedTime(new Date('2026-09-29T22:40:00'));
  await p.goto(`http://127.0.0.1:${server.address().port}/index.html`);
  const val = s => p.$eval(s, e => e.value);
  const vai = async n => { await p.click(`[data-go=${n}]`); await p.waitForSelector(`#v-${n}`, { state: 'visible' }); };
  const home = async () => { await p.click('#back'); await p.waitForSelector('#v-home', { state: 'visible' }); };

  // home
  check((await p.textContent('#hTitle')) === 'Reportistica', 'home: titolo Reportistica');
  const tiles = await p.$$eval('.tile', els => els.map(e => [e.textContent.split('work')[0].trim(), e.disabled]));
  check(JSON.stringify(tiles.map(t => t[0])) === JSON.stringify(['Report turno','Controllo magazzino','Controllo lamiere','Logistica','Manutenzione']), "home: 5 tasti nell'ordine giusto");
  check(JSON.stringify(tiles.map(t => t[1])) === '[false,false,false,true,true]', 'home: Logistica e Manutenzione disabilitati');

  // Report turno: le 7 prove di prima
  await vai('turno');
  await p.fill('#src', ESEMPIO);
  let out = await val('#out');
  check(out.startsWith('*Report turno 14-22 del 29/09*'), "turno e data dall'ora (22:40 → 14-22)");
  check(!/Buongiorno/.test(out), 'saluto ignorato');
  check(/Bramme tagliate: 9/.test(out), 'vecchio "Reparto taglio bramme : 9" letto');
  await p.click('#toggle');
  await p.click('#ck-prod'); await p.fill('#in-prod', '420');
  await p.click('#ck-montalbetti'); await p.fill('#in-montalbetti', '2');
  const li = p.locator('li', { has: p.locator('#ck-montalbetti') });
  await li.locator('.cas .fix').nth(0).getByRole('button', { name: 'pieno' }).click();
  await li.locator('.cas .fix').nth(1).getByRole('button', { name: 'metà' }).click();
  await p.click('#ck-nearmiss'); await p.click('#ck-nearmiss');   // ✎ poi ✕ = tolto
  out = await val('#out');
  check(/Produzione 420 ton/.test(out), 'modifica produzione');
  check(/Cassone Montalbetti: 2 \(pieno, metà\)/.test(out), 'cassoni');
  check(!/near miss/.test(out), 'campo tolto con ✕');
  await p.fill('#src', out);
  check((await val('#out')) === out, 'messaggio nuovo riletto identico');
  await home();
  check(await p.isVisible('#v-home'), 'freccia indietro: torna alla home');

  // Controllo magazzino
  await vai('mag');
  check(await p.isVisible('#mg-gen'), 'magazzino: senza testo c\'è "Genera messaggio"');
  await p.fill('#mg-src', MAG);
  check((await val('#mg-out')) === MAG, 'magazzino: report incollato → messaggio identico');
  await p.click('#mg-toggle');
  await p.click('#mg-ck-risaliti'); await p.click('#mg-ck-risaliti');
  await p.click('#mg-ck-q3'); await p.click('#mg-ck-q3');
  await p.click('#mg-ck-scM'); await p.fill('#mg-in-scM', '2');
  out = await val('#mg-out');
  check(!/Risaliti/.test(out) && /bat/.test(out) && !/tagli/.test(out), 'magazzino: voci tolte con ✕');
  check(/Mag\. Lamiere: 2 cassoni pieni/.test(out), 'magazzino: modifica cassoni scoria');
  await p.fill('#mg-src', out);
  check((await val('#mg-out')) === out, 'magazzino: dopo modifiche, riletto identico');
  await home();

  // Controllo lamiere
  await vai('lam');
  await p.fill('#la-num-0', '19223');
  const set = { testa:['25.7','25.9','25.3'], coda:['25.3','25.5','25.4'], lung:['12285','12280'], larg:['2064','2064'] };
  for (const k in set) for (let i = 0; i < set[k].length; i++) await p.fill(`#la-${k}-0-${i}`, set[k][i]);
  check((await val('#la-out')) === LAM1, 'lamiere: messaggio nel formato proposto');
  await p.click('#la-add'); await p.fill('#la-num-1', '19224'); await p.fill('#la-testa-1-0', '25.1');
  out = await val('#la-out');
  check(out === LAM1 + '\n\nLotto 19224\nSpessori testa: 25.1', 'lamiere: secondo lotto');
  await p.fill('#la-src', out);
  check((await val('#la-out')) === out && (await p.locator('#la-lots .group').count()) === 2, 'lamiere: messaggio riletto identico');

  await b.close(); server.close();
  process.exit(ok ? 0 : 1);
})();
