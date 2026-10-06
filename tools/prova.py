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

    # ---- tasto Condividi in home ----
    sh = p.get_attribute('#share', 'href')
    import urllib.parse
    tx = urllib.parse.unquote(sh.split('text=', 1)[1]) if 'text=' in sh else ''
    check(p.is_visible('#share') and sh.startswith('https://wa.me/?text=') and 'https://lucacavo92-wq.github.io/report-turno/' in tx and tx.startswith('*Reportistica FIL*') and 'Come si usa' not in tx and tx.endswith('arriveranno più avanti.'), 'home: tasto Condividi apre wa.me col testo (link del sito, senza "Come si usa")')

    # ---- Report turno: campi visibili subito, niente casella di incolla ----
    p.click('[data-go=turno]'); p.wait_for_selector('#v-turno', state='visible')
    check(p.locator('#src').count() == 0 and p.locator('#gen').count() == 0 and p.locator('#toggle').count() == 0, 'turno: niente casella incolla, niente Genera, niente Modifica')
    check(p.is_visible('#in-prod') and p.is_visible('#in-dpi') and p.is_visible('#date'), 'turno: campi visibili subito')
    o = out()
    check(o == ZERO, 'turno: messaggio da zero identico a esempio 4 (turno/data da ora 22:40)')
    ids = p.eval_on_selector_all('#groups input.cb', 'els => els.map(e => e.checked)')
    check(len(ids) == 27 and all(ids), 'turno: 27 caselle (una per campo), tutte attive di partenza')
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
    # ---- Cassone Nostro nel Report turno ----
    check(p.is_visible('#in-nostro') and p.locator('#in-nostro').evaluate("e => e.closest('li').querySelector('label.name').textContent") == 'Cassone Nostro' and p.is_checked('#ck-nostro'), 'turno: Cassone Nostro presente, casella attiva')
    check(p.locator('#in-nostro').evaluate("e => e.closest('li').previousElementSibling.querySelector('label.name').textContent") == 'Cassone Risaliti', 'turno: Cassone Nostro subito dopo Cassone Risaliti')
    check('Nostro' not in out(), 'turno: Nostro vuoto -> non esce')
    p.fill('#in-nostro', '1')
    li_n = p.locator('li', has=p.locator('#in-nostro'))
    li_n.locator('.cas .fix').nth(0).get_by_role('button', name='vuoto').click()
    o_n = out()
    check('• Cassone Nostro: 1 (vuoto)' in o_n, 'turno: messaggio con "• Cassone Nostro: 1 (vuoto)"')
    check(o_n.index('Cassone Montalbetti') < o_n.index('Cassone Nostro') < o_n.index('Bancali') if 'Bancali' in o_n else o_n.index('Cassone Montalbetti') < o_n.index('Cassone Nostro'), 'turno: Nostro dopo Montalbetti/Risaliti nel messaggio')
    rl = p.evaluate("t => { const f = parse(t); return f.nostro.n + '|' + f.nostro.s.join(',') }", o_n)
    check(rl == '1|vuoto', 'turno: la lettura riconosce la riga Cassone Nostro')
    p.click('#ck-nostro')
    check('Nostro' not in out(), 'turno: casella spenta toglie la riga Nostro')
    p.click('#ck-nostro')
    check('• Cassone Nostro: 1 (vuoto)' in out(), 'turno: casella riaccesa rimette la riga Nostro')
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

    # ---- Memoria delle ultime impostazioni (localStorage, stesso contesto, ricarico la pagina) ----
    errs = []
    LS = "() => Object.keys(localStorage).filter(k => k.startsWith('reportistica.')).sort()"
    def nuovo(ora=datetime(2026, 9, 29, 22, 40), init=None):
        c = b.new_context(viewport={'width': 400, 'height': 900})
        if init: c.add_init_script(init)
        q = c.new_page(); q.on('pageerror', lambda e: errs.append(str(e)))
        q.clock.set_fixed_time(ora); q.goto(URL); return c, q
    def dopo(q):                      # aspetta il salvataggio ritardato (300 ms) e ricarica la pagina
        q.wait_for_timeout(500); q.reload(); q.wait_for_selector('#v-home', state='visible')
    c1, q = nuovo()
    o1 = lambda i: q.eval_on_selector(i, 'e => e.value')
    check(q.evaluate(LS) == [], 'memoria: a memoria vuota non salva niente')
    # Report turno
    q.click('[data-go=turno]')
    q.fill('#in-prod', '777'); q.fill('#in-ritardi', 'Ritardo 15 min'); q.fill('#in-copertura', '07:30')
    q.fill('#in-montalbetti', '2')
    lit = q.locator('li', has=q.locator('#in-montalbetti'))
    lit.locator('.cas .fix').nth(0).get_by_role('button', name='pieno').click()
    lit.locator('.cas .fix').nth(1).get_by_role('button', name='metà').click()
    q.fill('#in-bancali', '4'); q.fill('#st-bancali', 'pronti')
    q.click('#ck-nearmiss'); q.click('#shiftRow [data-i="2"]')
    q.locator('li', has=q.locator('#ck-planarita')).get_by_role('button', name='non conforme').click()
    q.fill('#in-noteq', 'Nota di prova')
    ot = o1('#out')
    dopo(q)
    check(q.evaluate(LS) == ['reportistica.v1.turno'], 'memoria: dopo modifiche del turno esiste solo la chiave reportistica.v1.turno')
    q.click('[data-go=turno]'); q.wait_for_selector('#v-turno', state='visible')
    check(q.input_value('#in-prod') == '777' and q.input_value('#in-ritardi') == 'Ritardo 15 min' and q.input_value('#in-copertura') == '07:30', 'memoria turno: numero, testo e orario copertura tornano dopo il ricaricamento')
    check(q.input_value('#in-montalbetti') == '2' and q.input_value('#in-bancali') == '4' and q.input_value('#st-bancali') == 'pronti', 'memoria turno: cassoni (numero) e bancali tornano')
    check(q.is_checked('#ck-nearmiss') is False and q.is_checked('#ck-dpi') is True, 'memoria turno: caselle abilita/disabilita tornano')
    check(q.input_value('#in-noteq') == 'Nota di prova', 'memoria turno: note tornano')
    ot2 = o1('#out')
    check(ot2.split('\n', 1)[1] == ot.split('\n', 1)[1], "memoria turno: il messaggio (tolta la riga turno/data) e' identico a prima")
    check('Cassone Montalbetti: 2 (pieno, metà)' in ot2 and 'planarità non conforme' in ot2, 'memoria turno: stati dei cassoni e scelta non conforme tornano')
    check(ot2.startswith('*Report turno 14-22 del 29/09*') and q.get_attribute('#shiftRow [data-i="2"]', 'aria-pressed') == 'false', "memoria turno: turno e data NON si memorizzano (tornano dall'ora, 22:40 -> 14-22)")
    # Magazzino (memoria separata)
    q.click('#back'); q.click('[data-go=mag]'); q.wait_for_selector('#v-mag', state='visible')
    check(q.input_value('#mg-in-tot') == '' and q.input_value('#mg-in-risaliti') == '', 'memoria: il magazzino non prende i valori del turno (separate)')
    q.fill('#mg-in-tot', '55'); q.fill('#mg-in-risaliti', '1'); q.click('#mg-st-risaliti-0-metà'); q.fill('#mg-note-risaliti', 'nuovo')
    q.fill('#mg-in-scM', '3'); q.click('#mg-st-scM-2-pieno'); q.click('#mg-ck-q3'); q.fill('#mg-in-q5', 'Frase mia')
    om = o1('#mg-out')
    dopo(q)
    check(q.evaluate(LS) == ['reportistica.v1.magazzino', 'reportistica.v1.turno'], 'memoria: due chiavi separate (turno e magazzino)')
    q.click('[data-go=mag]'); q.wait_for_selector('#v-mag', state='visible')
    check(q.input_value('#mg-in-tot') == '55' and q.input_value('#mg-in-risaliti') == '1' and q.input_value('#mg-note-risaliti') == 'nuovo' and q.input_value('#mg-in-scM') == '3', 'memoria magazzino: numeri, cassoni, nota tornano')
    check(q.is_checked('#mg-ck-q3') is False and q.input_value('#mg-in-q5') == 'Frase mia', 'memoria magazzino: caselle e frasi tornano')
    check(o1('#mg-out') == om and '• 1 cassone Risaliti metà nuovo' in om, 'memoria magazzino: messaggio identico a prima (stati cassoni compresi)')
    q.click('#back'); q.click('[data-go=turno]')
    check(q.input_value('#in-prod') == '777', "memoria: il turno non e' cambiato quando si lavora sul magazzino")
    # Lamiere
    q.click('#back'); q.click('[data-go=lam]'); q.wait_for_selector('#v-lam', state='visible')
    q.fill('#la-num-0', '19223'); q.fill('#la-testa-0-0', '25.7'); q.fill('#la-larg-0-1', '2064')
    q.click('#la-add'); q.fill('#la-num-1', '19224'); q.fill('#la-lung-1-0', '12285')
    ol = o1('#la-out')
    dopo(q)
    q.click('[data-go=lam]'); q.wait_for_selector('#v-lam', state='visible')
    check(q.locator('#la-lots .group').count() == 2 and q.input_value('#la-num-1') == '19224' and q.input_value('#la-testa-0-0') == '25.7' and q.input_value('#la-larg-0-1') == '2064', 'memoria lamiere: lotti aggiunti e misure tornano')
    check(o1('#la-out') == ol and 'Lotto 19224' in ol, 'memoria lamiere: messaggio identico a prima')
    check(q.evaluate(LS) == ['reportistica.v1.lamiere', 'reportistica.v1.magazzino', 'reportistica.v1.turno'], 'memoria: tre chiavi separate')
    # Azzera: lamiere
    check(q.is_visible('#azz-lam') and q.inner_text('#azz-lam') == 'Azzera', 'azzera: tasto presente nelle lamiere')
    q.click('#azz-lam')
    check(q.inner_text('#azz-lam') == 'Confermi?' and q.locator('#la-lots .group').count() == 2, 'azzera: primo tocco chiede conferma e non cancella')
    q.click('#azz-lam'); q.wait_for_timeout(100)
    check(q.locator('#la-lots .group').count() == 1 and o1('#la-out') == '' and q.evaluate("() => localStorage.getItem('reportistica.v1.lamiere')") is None, 'azzera lamiere: valori standard e memoria cancellata')
    # Azzera: magazzino
    q.click('#back'); q.click('[data-go=mag]')
    q.click('#azz-mag'); q.click('#azz-mag'); q.wait_for_timeout(100)
    check(o1('#mg-out') == MAG_ZERO and q.input_value('#mg-in-tot') == '' and q.evaluate("() => localStorage.getItem('reportistica.v1.magazzino')") is None, 'azzera magazzino: valori standard e memoria cancellata')
    # Azzera: turno (il turno scelto a mano resta)
    q.click('#back'); q.click('[data-go=turno]')
    q.click('#shiftRow [data-i="0"]')
    q.click('#azz-turno'); q.click('#azz-turno'); q.wait_for_timeout(100)
    ot3 = o1('#out')
    check(ot3.startswith('*Report turno 6-14 ') and ot3.split('\n', 1)[1] == ZERO.split('\n', 1)[1] and q.is_checked('#ck-nearmiss') and q.input_value('#in-prod') == '' and q.evaluate("() => localStorage.getItem('reportistica.v1.turno')") is None, 'azzera turno: valori standard, turno scelto resta, memoria cancellata')
    dopo(q)
    q.click('[data-go=turno]'); q.wait_for_selector('#v-turno', state='visible')
    check(o1('#out') == ZERO and q.evaluate(LS) == [], 'azzera: dopo il ricaricamento riparte da zero, niente salvato')
    # turno e data seguono l'ora anche con la memoria piena
    q.fill('#in-prod', '5'); q.wait_for_timeout(500)
    q.clock.set_fixed_time(datetime(2026, 10, 1, 8, 5)); q.reload(); q.click('[data-go=turno]')
    check(q.input_value('#in-prod') == '5' and o1('#out').startswith('*Report turno 22-6 del 01/10*'), "memoria: valori tornano ma turno/data seguono l'ora nuova (08:05 -> 22-6 del 01/10)")
    c1.close()
    # storage corrotto o incompatibile: si parte da zero senza errori
    for nome, val in [('testo non JSON', '{{{non json'), ('versione diversa', '{"v":99,"d":{"values":{"prod":"1"}}}'), ('tipi sbagliati', '{"v":1,"d":{"values":{"prod":{"x":1},"montalbetti":"zz","planarita":"q","dpi":5},"excluded":"abc"}}'), ('lotti sbagliati', '{"v":1,"d":[{"num":5},null]}')]:
        init = "try{localStorage.setItem('reportistica.v1.turno', %r); localStorage.setItem('reportistica.v1.magazzino', %r); localStorage.setItem('reportistica.v1.lamiere', %r)}catch(e){}" % (val, val, val)
        errs.clear()
        c2, q = nuovo(init=init)
        q.click('[data-go=turno]'); a = q.eval_on_selector('#out', 'e => e.value')
        q.click('#back'); q.click('[data-go=mag]'); bm = q.eval_on_selector('#mg-out', 'e => e.value')
        q.click('#back'); q.click('[data-go=lam]'); cl = q.eval_on_selector('#la-out', 'e => e.value')
        check(a == ZERO and bm == MAG_ZERO and cl == '' and not errs, 'memoria corrotta (' + nome + '): parte da zero, nessun errore JS')
        c2.close()
    # localStorage non disponibile (finestra privata ecc.): l'app funziona lo stesso
    errs.clear()
    c3, q = nuovo(init="Object.defineProperty(window, 'localStorage', { get(){ throw new Error('bloccato'); } });")
    q.click('[data-go=turno]'); q.fill('#in-prod', '9'); q.wait_for_timeout(500)
    check('Produzione 9 ton' in q.eval_on_selector('#out', 'e => e.value') and not errs, "memoria: localStorage bloccato -> l'app funziona lo stesso, nessun errore")
    c3.close()

    b.close()
srv.shutdown()
sys.exit(0 if ok else 1)
