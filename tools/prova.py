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
• Mag. Lamiere: 4 cassoni pieno
• Taglio bramme: 1 cassone vuoto

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
    check(p.locator('#mg-cass-add').count() == 0 and p.locator('#mg-cass').count() == 0, 'magazzino: niente Aggiungi cassone')
    check(all(p.is_visible('#mg-in-' + i) for i in ['risaliti', 'montalbetti', 'nostro']) and p.locator('#mg-in-risaliti').evaluate("e => e.closest('.group').querySelector('h3').textContent") == 'Cassoni', 'magazzino: 3 cassoni fissi sempre visibili (Risaliti, Montalbetti, Nostro)')
    check(p.locator('#mg-in-risaliti').evaluate("e => e.closest('li').querySelector('label.name').textContent") == 'Cassone Risaliti' and p.locator('#mg-in-nostro').evaluate("e => e.closest('li').querySelector('label.name').textContent") == 'Cassone Nostro', 'magazzino: nomi Cassone Risaliti / Cassone Nostro')
    cbs = p.eval_on_selector_all('#mg-groups input.cb', 'els => els.map(e => e.checked)')
    check(len(cbs) == 14 and all(cbs), 'magazzino: 14 caselle (una per campo), tutte attive di partenza')
    check(p.locator('#mg-in-bat').count() == 1 and p.locator('#mg-in-bat').evaluate("e => e.closest('.group').querySelector('h3').textContent") == 'Bat', 'magazzino: bat è un campo suo, separato dai cassoni')
    p.fill('#mg-in-bat', '3')
    check('• 3 bat' in out('#mg-out').split(chr(10)) and 'cassone' not in out('#mg-out'), 'magazzino: bat da solo -> riga "• 3 bat", nessun cassone')
    for i, v in [('tot', '21'), ('sped', '13'), ('intest', '8'), ('bat', '1')]:
        p.fill(f'#mg-in-{i}', v)
    p.click('#mg-st-risaliti-0-vuoto')
    p.fill('#mg-note-risaliti', 'appena cambiato')
    p.fill('#mg-in-scM', '4')
    p.click('#mg-st-scM-0-pieno')
    p.fill('#mg-in-scB', '1'); p.click('#mg-st-scB-0-vuoto')
    check(p.locator('#mg-in-scB').evaluate("e => [...e.closest('li').querySelectorAll('.cas .seg button')].map(b => b.textContent).join('|')") == 'vuoto|metà|pieno', 'magazzino: tasti stato in ordine vuoto, metà, pieno')
    check(out('#mg-out') == MAG, "magazzino: campi compilati -> messaggio identico all'esempio")
    p.fill('#mg-in-scB', '2'); p.click('#mg-st-scB-0-pieno'); p.click('#mg-st-scB-1-metà')
    check('• Taglio bramme: 2 cassoni pieno, metà' in out('#mg-out').split(chr(10)), 'magazzino: Taglio bramme 2 cassoni (numero + stato), plurale')
    check('grande' not in out('#mg-out') and 'piccolo' not in out('#mg-out'), 'magazzino: niente piu grande/piccolo')
    p.click('#mg-ck-scB')
    check('Taglio bramme' not in out('#mg-out') and not p.is_visible('#mg-in-scB'), 'magazzino: casella spenta toglie la riga Taglio bramme')
    p.click('#mg-ck-scB')
    p.fill('#mg-in-scB', '1'); p.click('#mg-st-scB-0-pieno'); p.click('#mg-st-scB-0-vuoto')
    check('• Taglio bramme: 1 cassone vuoto' in out('#mg-out').split(chr(10)), 'magazzino: Taglio bramme 1 cassone vuoto')
    # cassoni fissi: Montalbetti (2: pieno, metà), Nostro, plurale, casella spenta
    p.fill('#mg-in-montalbetti', '2')
    check(p.locator('#mg-in-montalbetti').evaluate("e => e.closest('li').querySelectorAll('.cas .fix').length") == 2, 'magazzino: n=2 -> due righe di stato')
    p.click('#mg-st-montalbetti-0-pieno'); p.click('#mg-st-montalbetti-1-metà')
    p.fill('#mg-in-nostro', '1'); p.click('#mg-st-nostro-0-metà')
    o = out('#mg-out').split(chr(10))
    check('• 1 cassone Risaliti vuoto appena cambiato' in o and '• 2 cassoni Montalbetti pieno, metà' in o and '• 1 cassone Nostro metà' in o, 'magazzino: Risaliti / Montalbetti / Nostro nel messaggio, plurale giusto')
    check(o.index('• 1 cassone Risaliti vuoto appena cambiato') < o.index('• 2 cassoni Montalbetti pieno, metà') < o.index('• 1 cassone Nostro metà') < o.index('• 1 bat'), 'magazzino: ordine Risaliti, Montalbetti, Nostro, poi bat')
    p.click('#mg-ck-montalbetti')
    o = out('#mg-out')
    check('Montalbetti' not in o and not p.is_visible('#mg-in-montalbetti') and '1 cassone Risaliti' in o and 'Nostro' in o, 'magazzino: casella spenta toglie la riga Montalbetti e nasconde il campo')
    p.click('#mg-ck-montalbetti')
    check('• 2 cassoni Montalbetti pieno, metà' in out('#mg-out'), 'magazzino: casella riaccesa rimette la riga')
    p.click('#mg-ck-nostro')
    check('Nostro' not in out('#mg-out'), 'magazzino: Nostro spento')
    p.click('#mg-ck-nostro')
    MAG2 = MAG.replace('• 1 bat', '• 2 cassoni Montalbetti pieno, metà' + chr(10) + '• 1 cassone Nostro metà' + chr(10) + '• 1 bat')
    check(out('#mg-out') == MAG2, 'magazzino: messaggio completo con i tre cassoni')
    # caselle su TUTTI i campi del magazzino
    for i in ['tot', 'sped', 'intest', 'risaliti', 'montalbetti', 'nostro', 'bat', 'scM', 'scB', 'q1', 'q2', 'q3', 'q4', 'q5']:
        if not p.is_checked('#mg-ck-' + i): p.click('#mg-ck-' + i)
    for i in ['tot', 'sped', 'intest', 'bat', 'scM', 'scB', 'risaliti']:
        p.click('#mg-ck-' + i)
    o = out('#mg-out')
    check(not any(w in o for w in ['Totale', 'spedibili', 'intestature', 'bat', 'Scoria', 'Mag. Lamiere', 'Taglio bramme', 'Risaliti']), 'magazzino: caselle spente su pacchi, cassoni, bat, scoria -> righe e titolo Scoria spariscono')
    check('*Controllo qualità pacchi*' in o, 'magazzino: gruppo qualità ancora presente')
    for i in ['tot', 'sped', 'intest', 'bat', 'scM', 'scB', 'risaliti']:
        p.click('#mg-ck-' + i)
    check(out('#mg-out') == MAG2, 'magazzino: caselle riaccese -> messaggio atteso')
    p.click('#mg-ck-scM')
    check('Mag. Lamiere' not in out('#mg-out') and 'Taglio bramme' in out('#mg-out') and '*Scoria*' in out('#mg-out') and not p.is_visible('#mg-in-scM'), 'magazzino: casella scoria Mag. Lamiere toglie solo quella riga')
    p.click('#mg-ck-scB')
    check('Scoria' not in out('#mg-out'), 'magazzino: scoria tutta spenta -> sparisce il titolo')
    p.click('#mg-ck-scM'); p.click('#mg-ck-scB')
    check(p.is_checked('#mg-ck-q3') is True, 'magazzino: caselle attive di partenza')
    p.click('#mg-ck-q3')
    p.fill('#mg-in-q5', 'Nessun segno della spianatrice')
    p.fill('#mg-in-scM', '2'); p.click('#mg-st-scM-1-pieno')
    o = out('#mg-out')
    check('tagli' not in o, 'magazzino: casella spenta toglie la frase')
    check('• Nessun segno della spianatrice' in o.split(chr(10)), 'magazzino: frase modificata')
    check(p.is_visible('#mg-note-scM') and p.locator('#mg-in-scM').evaluate("e => [...e.closest('li').querySelectorAll('.cas .seg button')].map(b => b.textContent).join('|')") == 'vuoto|metà|pieno|vuoto|metà|pieno', 'magazzino: Mag. Lamiere ha nota e stati per ogni cassone')
    check('• Mag. Lamiere: 2 cassoni pieno' in o, 'magazzino: Mag. Lamiere plurale cassoni + stato')
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
