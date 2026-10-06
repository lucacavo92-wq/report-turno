# Prova automatica (stessa di prova.js, per Python + Playwright + Chromium).
# Uso:  %LOCALAPPDATA%\Programs\Python\Python312\python.exe tools\prova.py
# Apre l'app da un server locale (non file://), con l'ora del telefono finta (29/09/2026 22:40).
import functools, http.server, pathlib, sys, threading
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
from playwright.sync_api import sync_playwright

R = pathlib.Path(__file__).resolve().parent.parent
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
handler = functools.partial(Quiet, directory=str(R))
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/index.html'

MAG = """Buongiorno,
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
• Visibili segni della spianatrice lato strada e lato ferrovia"""

ZERO = open(R / '..' / 'importato' / 'pacchetto-report-turno' / 'esempi' / '4_messaggio_generato_da_zero.txt', encoding='utf-8').read().strip()
MAG_ZERO = """Buongiorno,
*Controllo magazzino*

*Controllo qualità pacchi*
• Superficie conforme
• Superficie inferiore conforme
• I tagli sono abbastanza puliti
• Nessun segno dei cilindri di laminazione
• Visibili segni della spianatrice lato strada e lato ferrovia"""

LAM1 = """*Controllo lamiere*
Lotto 19223
Spessori testa: 25.7 25.9 25.3
Spessori coda: 25.3 25.5 25.4
Lunghezza: 12285 12280
Larghezza: 2064 2064"""

ok = True
def check(c, m):
    global ok
    print(('OK     ' if c else 'ERRORE ') + m); ok = ok and bool(c)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={'width': 400, 'height': 900})
    p.on('pageerror', lambda e: check(False, 'errore JS: ' + str(e)))
    p.clock.set_fixed_time(datetime(2026, 9, 29, 22, 40))
    p.goto(URL)
    out = lambda i='#out': p.eval_on_selector(i, 'e => e.value')

    # ---- home ----
    check(p.text_content('#hTitle') == 'Reportistica', 'home: titolo Reportistica')
    tiles = p.eval_on_selector_all('.tile', 'els => els.map(e => [e.textContent.replace(/\\s+/g," ").trim(), e.disabled])')
    check([t[0].split('work')[0].strip() for t in tiles] == ['Report turno', 'Controllo magazzino', 'Controllo lamiere', 'Logistica', 'Manutenzione'], 'home: 5 tasti nell\'ordine giusto')
    check([t[1] for t in tiles] == [False, False, False, True, True] and 'work in progress' in tiles[3][0], 'home: Logistica e Manutenzione disabilitati (work in progress)')
    check(p.title() == 'Reportistica FIL', 'titolo pagina Reportistica FIL')

    # ---- Report turno: campi visibili subito, niente casella di incolla ----
    p.click('[data-go=turno]'); p.wait_for_selector('#v-turno', state='visible')
    check(p.locator('#src').count() == 0 and p.locator('#gen').count() == 0 and p.locator('#toggle').count() == 0, 'turno: niente casella incolla, niente Genera, niente Modifica')
    check(p.is_visible('#in-prod') and p.is_visible('#in-dpi') and p.is_visible('#date'), 'turno: campi visibili subito')
    o = out()
    check(o == ZERO, 'turno: messaggio da zero identico a esempio 4 (turno/data da ora 22:40)')
    ids = p.eval_on_selector_all('#groups input.cb', 'els => els.map(e => e.checked)')
    check(len(ids) == 26 and all(ids), 'turno: 26 caselle (una per campo), tutte attive di partenza')
    p.fill('#in-prod', '420')
    p.fill('#in-montalbetti', '2')
    li = p.locator('li', has=p.locator('#in-montalbetti'))
    li.locator('.cas .fix').nth(0).get_by_role('button', name='pieno').click()
    li.locator('.cas .fix').nth(1).get_by_role('button', name='metà').click()
    p.click('#ck-nearmiss')
    p.click('#ck-pulizia'); p.click('#ck-pulizia')
    p.click('#shiftRow [data-i="2"]')
    o = out()
    check(o.startswith('*Report turno 22-6 del 29/09*'), 'turno: cambio turno')
    check('Produzione 420 ton' in o, 'turno: produzione')
    check('Cassone Montalbetti: 2 (pieno, metà)' in o, 'turno: cassoni')
    check('near miss' not in o and 'Pulizia: nessuna segnalazione.' in o, 'turno: casella spenta toglie la voce, due tocchi la rimettono')
    # caselle abilita/disabilita (Report turno)
    check(p.is_checked('#ck-nearmiss') is False and p.is_checked('#ck-pulizia') is True, 'turno: stato caselle (near miss spenta, pulizia riaccesa)')
    p.click('#ck-prod')
    o = out()
    check('Produzione' not in o and not p.is_visible('#in-prod'), 'turno: casella spenta toglie Produzione dal messaggio e nasconde il campo')
    p.click('#ck-prod')
    check('Produzione 420 ton' in out(), 'turno: casella riaccesa rimette Produzione')
    p.click('#ck-montalbetti')
    check('Montalbetti' not in out(), 'turno: casella spenta toglie il cassone Montalbetti')
    p.click('#ck-montalbetti')
    check('Cassone Montalbetti: 2 (pieno, metà)' in out(), 'turno: cassone Montalbetti di nuovo nel messaggio')
    for i in ['dpi', 'pulizia', 'violenza', 'nearmiss']:
        if p.is_checked('#ck-' + i): p.click('#ck-' + i)
    check('Sicurezza' not in out(), 'turno: gruppo tutto spento -> sparisce anche il titolo')
    p.click('#ck-dpi')
    check('Sicurezza' in out(), 'turno: gruppo con un campo attivo -> titolo torna')
    p.click('#back'); p.wait_for_selector('#v-home', state='visible')
    check(p.is_visible('#v-home') and p.text_content('#hTitle') == 'Reportistica', 'freccia indietro: torna alla home')
    p.click('[data-go=turno]'); p.wait_for_selector('#v-turno', state='visible')
    check(p.input_value('#in-prod') == '420', "tornando nel Report turno il lavoro e' ancora li")
    p.go_back(); p.wait_for_selector('#v-home', state='visible')
    check(p.is_visible('#v-home'), 'tasto indietro del telefono: torna alla home')

    # ---- Controllo magazzino ----
    p.click('[data-go=mag]'); p.wait_for_selector('#v-mag', state='visible')
    check(p.locator('#mg-src').count() == 0 and p.locator('#mg-gen').count() == 0 and p.locator('#mg-toggle').count() == 0, 'magazzino: niente casella incolla, Genera, Modifica')
    check(out('#mg-out') == MAG_ZERO, 'magazzino: da zero = saluto, titolo, frasi standard')
    check(p.locator('#mg-cass > *').count() == 0 and p.locator('#mg-in-risaliti').count() == 0, 'magazzino: parte con zero cassoni')
    check(p.locator('#mg-in-bat').count() == 1 and p.locator('#mg-in-bat').evaluate("e => e.closest('.group').querySelector('h3').textContent") == 'Bat', 'magazzino: bat è un campo suo, separato dai cassoni')
    p.fill('#mg-in-bat', '3')
    check('• 3 bat' in out('#mg-out').split(chr(10)) and 'cassone' not in out('#mg-out'), 'magazzino: bat da solo -> riga "• 3 bat", nessun cassone')
    for i, v in [('tot', '21'), ('sped', '13'), ('intest', '8'), ('bat', '1')]:
        p.fill(f'#mg-in-{i}', v)
    p.click('#mg-cass-add')
    p.locator('#mg-cass-st-0-vuoto').click()
    p.fill('#mg-cass-note-0', 'appena cambiato')
    p.fill('#mg-in-scM', '4')
    p.locator('li', has=p.locator('#mg-in-scM')).get_by_role('button', name='pieno').click()
    li = p.locator('li', has_text='Taglio bramme')
    li.locator('.fix').nth(0).get_by_role('button', name='vuoto').click()
    li.locator('.fix').nth(1).get_by_role('button', name='pieno').click()
    check(out('#mg-out') == MAG, "magazzino: campi compilati -> messaggio identico all'esempio")
    # cassoni: Montalbetti, Nostro, plurale, Togli
    p.click('#mg-cass-add'); p.click('#mg-cass-tipo-1-Montalbetti'); p.click('#mg-cass-st-1-pieno')
    p.click('#mg-cass-add'); p.click('#mg-cass-tipo-2-Nostro'); p.click('#mg-cass-st-2-metà'); p.fill('#mg-cass-n-2', '2')
    o = out('#mg-out').split(chr(10))
    check('• 1 cassone Risaliti vuoto appena cambiato' in o and '• 1 cassone Montalbetti pieno' in o and '• 2 cassoni Nostro metà' in o, 'magazzino: Risaliti / Montalbetti / Nostro nel messaggio, plurale giusto')
    check(o.index('• 1 cassone Risaliti vuoto appena cambiato') < o.index('• 1 cassone Montalbetti pieno') < o.index('• 2 cassoni Nostro metà') < o.index('• 1 bat'), 'magazzino: ordine cassoni poi bat')
    p.click('#mg-cass-st-2-metà'); p.fill('#mg-cass-n-2', '3')
    check('• 3 cassoni Nostro' in out('#mg-out').split(chr(10)), 'magazzino: stato spento e n=3')
    p.click('#mg-cass-rm-2'); p.click('#mg-cass-rm-1')
    check(p.locator('#mg-cass .cassbox').count() == 1 and 'Montalbetti' not in out('#mg-out') and 'Nostro' not in out('#mg-out'), 'magazzino: Togli cassone')
    check(out('#mg-out') == MAG, 'magazzino: dopo Togli torna al messaggio atteso')
    check(p.is_checked('#mg-ck-q3') is True, 'magazzino: caselle attive di partenza')
    p.click('#mg-ck-q3')
    p.fill('#mg-in-q5', 'Nessun segno della spianatrice')
    p.fill('#mg-in-scM', '2')
    o = out('#mg-out')
    check('tagli' not in o, 'magazzino: casella spenta toglie la frase')
    check('• Nessun segno della spianatrice' in o.split(chr(10)), 'magazzino: frase modificata')
    check('• Mag. Lamiere: 2 cassoni pieni' in o, 'magazzino: plurale cassoni + stato')
    p.click('#back'); p.wait_for_selector('#v-home', state='visible')

    # ---- Controllo lamiere ----
    p.click('[data-go=lam]'); p.wait_for_selector('#v-lam', state='visible')
    check(p.locator('#la-src').count() == 0 and p.locator('#la-toggle').count() == 0, 'lamiere: niente casella incolla, niente Modifica')
    check(p.locator('#la-lots .group').count() == 1 and out('#la-out') == '', 'lamiere: parte con 1 lotto vuoto')
    p.fill('#la-num-0', '19223')
    for k, vals in [('testa', ['25.7', '25.9', '25.3']), ('coda', ['25.3', '25.5', '25.4']), ('lung', ['12285', '12280']), ('larg', ['2064', '2064'])]:
        for i, v in enumerate(vals):
            p.fill(f'#la-{k}-0-{i}', v)
    check(out('#la-out') == LAM1, 'lamiere: messaggio nel formato proposto')
    p.click('#la-add')
    p.fill('#la-num-1', '19224'); p.fill('#la-testa-1-0', '25.1')
    o = out('#la-out')
    check(o == LAM1 + chr(10) * 2 + 'Lotto 19224' + chr(10) + 'Spessori testa: 25.1','lamiere: secondo lotto, righe vuote non escono')
    p.click('#la-rm-1')
    check(out('#la-out') == LAM1, 'lamiere: Togli lotto')
    p.click('#la-copy'); p.wait_for_selector('#la-status', state='visible', timeout=3000)
    check(p.inner_text('#la-status') in ('Copiato', 'Tieni premuto e scegli Copia'), 'lamiere: Copia risponde')
    check(p.get_attribute('#la-wa', 'href').startswith('https://wa.me/?text=*Controllo%20lamiere'), 'lamiere: Apri in WhatsApp ha il testo')

    b.close()
srv.shutdown()
sys.exit(0 if ok else 1)
