// Prova veloce dell'app (Chromium già installato nell'ambiente cloud).
// Uso:  NODE_PATH=$(npm root -g) node tools/prova.js
const { chromium } = require('playwright');
const path = require('path');
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
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }).catch(() => chromium.launch());
  const p = await b.newPage({ viewport: { width: 400, height: 900 } });
  let ok = true; const check = (c, m) => { console.log((c ? 'OK   ' : 'ERRORE ') + m); ok = ok && c; };
  p.on('pageerror', e => check(false, 'errore JS: ' + e.message));
  await p.clock.setFixedTime(new Date('2026-09-29T22:40:00'));
  await p.goto('file://' + path.resolve(__dirname, '../index.html'));
  await p.fill('#src', ESEMPIO);
  let out = await p.$eval('#out', e => e.value);
  check(out.startsWith('*Report turno 14-22 del 29/09*'), 'turno e data dall\'ora (22:40 → 14-22)');
  check(!/Buongiorno/.test(out), 'saluto ignorato');
  check(/Bramme tagliate: 9/.test(out), 'vecchio "Reparto taglio bramme : 9" letto');
  await p.click('#toggle');
  await p.click('#ck-prod'); await p.fill('#in-prod', '420');
  await p.click('#ck-montalbetti'); await p.fill('#in-montalbetti', '2');
  const li = p.locator('li', { has: p.locator('#ck-montalbetti') });
  await li.locator('.cas .fix').nth(0).getByRole('button', { name: 'pieno' }).click();
  await li.locator('.cas .fix').nth(1).getByRole('button', { name: 'metà' }).click();
  await p.click('#ck-nearmiss'); await p.click('#ck-nearmiss');   // ✎ poi ✕ = tolto
  out = await p.$eval('#out', e => e.value);
  check(/Produzione 420 ton/.test(out), 'modifica produzione');
  check(/Cassone Montalbetti: 2 \(pieno, metà\)/.test(out), 'cassoni');
  check(!/near miss/.test(out), 'campo tolto con ✕');
  await p.fill('#src', out);
  check((await p.$eval('#out', e => e.value)) === out, 'messaggio nuovo riletto identico');
  await b.close();
  process.exit(ok ? 0 : 1);
})();
