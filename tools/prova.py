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
    LV = "try{localStorage.setItem('reportistica.v1.loginvisto','1')}catch(e){}"   # le prove vecchie: la schermata Accedi non si propone da sola
    p0 = b.new_context(viewport={'width': 400, 'height': 900}); p0.add_init_script(LV)
    p = p0.new_page()
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
    check(p.is_visible('#share') and sh.startswith('https://wa.me/?text=') and 'https://lucacavo92-wq.github.io/reportistica-fil/' in tx and tx.startswith('*Reportistica FIL*') and 'Come si usa' not in tx and tx.endswith('arriveranno più avanti.'), 'home: tasto Condividi apre wa.me col testo (link del sito, senza "Come si usa")')

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
    check(len(cbs) == 16 and all(cbs), 'magazzino: 16 caselle (una per campo), tutte attive di partenza')
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
    LS = "() => Object.keys(localStorage).filter(k => k.startsWith('reportistica.') && k !== 'reportistica.v1.loginvisto').sort()"
    def nuovo(ora=datetime(2026, 9, 29, 22, 40), init=None):
        c = b.new_context(viewport={'width': 400, 'height': 900})
        c.add_init_script(LV)
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

    # ======================= ARCHIVIO messaggi =======================
    import zipfile, io, json, re, tempfile, os
    from datetime import timezone
    UTC = lambda *a: datetime(*a, tzinfo=timezone.utc)
    AK = "() => JSON.parse(localStorage.getItem('reportistica.v1.archivio') || '{\"d\":[]}').d"
    NOWA = "() => ['wa','mg-wa','la-wa','arc-wa'].forEach(i => document.getElementById(i).addEventListener('click', e => e.preventDefault()))"
    ISO = re.compile(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$')
    OKCOPIA = ('Copiato', 'Tieni premuto e scegli Copia')
    errs.clear()
    ca, q = nuovo(UTC(2026, 10, 6, 20, 40)); q.evaluate(NOWA)
    ag = lambda: q.evaluate(AK)
    check(ag() == [], 'archivio: a memoria vuota non salva niente')
    # Copia salva una voce (Report turno)
    q.click('[data-go=turno]'); q.fill('#in-prod', '401'); t1 = q.eval_on_selector('#out', 'e => e.value')
    q.click('#copy'); q.wait_for_selector('#status', state='visible', timeout=3000)
    a = ag()
    check(len(a) == 1 and a[0]['r'] == 'turno' and a[0]['x'] == t1 and ISO.match(a[0]['t']) and a[0]['t'].startswith('2026-10-06T22:40:') and a[0]['t'].endswith('+02:00') and a[0]['l'] == '06/10/2026 22:40', 'archivio: Copia salva una voce (tipo turno, testo completo, ora Europe/Rome ISO + leggibile)')
    check(q.inner_text('#status') in OKCOPIA, 'archivio: Copia funziona uguale')
    # niente doppione: Copia poi WhatsApp con testo identico, aggiorna solo l'ora
    q.clock.set_fixed_time(UTC(2026, 10, 6, 20, 55)); q.click('#wa')
    a = ag()
    check(len(a) == 1 and a[0]['l'] == '06/10/2026 22:55' and a[0]['x'] == t1, "archivio: WhatsApp col testo identico non crea doppione, aggiorna l'ora")
    check(q.get_attribute('#wa', 'href').startswith('https://wa.me/?text='), 'archivio: WhatsApp ha ancora il suo link')
    # testo diverso -> nuova voce; poi tornando al primo testo -> altra voce (il confronto e' con la piu' recente)
    q.fill('#in-prod', '402'); t2 = q.eval_on_selector('#out', 'e => e.value'); q.click('#wa')
    check([e['x'] for e in ag()] == [t1, t2], 'archivio: testo diverso -> nuova voce')
    q.fill('#in-prod', '401'); q.click('#copy')
    check([e['x'] for e in ag()] == [t1, t2, t1], 'archivio: confronto solo con la voce piu recente dello stesso report')
    # magazzino
    q.click('#back'); q.click('[data-go=mag]'); q.fill('#mg-in-tot', '21')
    tm = q.eval_on_selector('#mg-out', 'e => e.value'); q.click('#mg-copy'); q.wait_for_selector('#mg-status', state='visible', timeout=3000)
    # lamiere: vuoto non salva, compilato si
    q.click('#back'); q.click('[data-go=lam]'); n0 = len(ag()); q.click('#la-copy'); q.click('#la-wa')
    check(len(ag()) == n0, 'archivio: report lamiere vuoto -> niente da salvare')
    q.fill('#la-num-0', '19223'); q.fill('#la-testa-0-0', '25.7'); tl = q.eval_on_selector('#la-out', 'e => e.value'); q.click('#la-wa')
    a = ag()
    check([e['r'] for e in a] == ['turno', 'turno', 'turno', 'magazzino', 'lamiere'] and a[3]['x'] == tm and a[4]['x'] == tl, 'archivio: tipo giusto per Report turno, Controllo magazzino, Controllo lamiere (Copia e WhatsApp)')
    # pagina Archivio
    q.click('#back'); q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible')
    check(q.text_content('#hTitle') == 'Archivio' and q.is_visible('#back') and q.is_visible('#arc-zip') and q.is_enabled('#arc-zip'), 'archivio: pagina con titolo, freccia indietro e tasto Salva file (zip)')
    items = q.eval_on_selector_all('.arcitem', 'els => els.map(e => e.innerText)')
    check(len(items) == 5 and 'Lamiere' in items[0] and 'Magazzino' in items[1] and 'Turno' in items[2] and items[0].count('\n') >= 1, 'archivio: elenco dal piu recente con data/ora, tipo e prime righe')
    check('06/10/2026' in items[0] and '*' not in items[0], 'archivio: elenco con data e senza asterischi')
    def fl(k):
        q.click(f'#arc-flt [data-f={k}]'); return q.locator('.arcitem').count()
    check([fl('turno'), fl('magazzino'), fl('lamiere'), fl('tutti')] == [3, 1, 1, 5], 'archivio: filtri Turno / Magazzino / Lamiere / Tutti')
    check(q.get_attribute('#arc-flt [data-f=tutti]', 'aria-pressed') == 'true', 'archivio: filtro attivo evidenziato')
    # apri una voce
    q.locator('.arcitem').nth(1).click()
    check(q.is_visible('#arc-det') and not q.is_visible('#arc-list') and q.eval_on_selector('#arc-view-out', 'e => e.value') == tm, 'archivio: toccando una voce si apre il testo intero')
    check(q.is_visible('#arc-copy') and q.is_visible('#arc-wa') and q.inner_text('#arc-del') == 'Elimina' and q.get_attribute('#arc-wa', 'href').startswith('https://wa.me/?text='), 'archivio: tasti Copia, Apri in WhatsApp, Elimina')
    n1 = len(ag()); q.click('#arc-copy'); q.wait_for_selector('#arc-status', state='visible', timeout=3000); q.click('#arc-wa')
    check(len(ag()) == n1, "archivio: Copia/WhatsApp dall'archivio non aggiungono voci")
    q.click('#back')
    check(q.is_visible('#arc-list') and not q.is_visible('#arc-det') and q.is_visible('#v-arc'), 'archivio: freccia dal dettaglio torna all elenco')
    q.locator('.arcitem').nth(1).click()
    q.click('#arc-del')
    check(q.inner_text('#arc-del') == 'Confermi?' and len(ag()) == 5, 'archivio: Elimina primo tocco chiede conferma e non cancella')
    q.click('#arc-del'); q.wait_for_timeout(100)
    a = ag()
    check(len(a) == 4 and all(e['r'] != 'magazzino' for e in a) and q.is_visible('#arc-list') and q.locator('.arcitem').count() == 4, 'archivio: Elimina al secondo tocco toglie la voce e torna all elenco')
    # Azzera dei report non tocca l'archivio
    q.click('#back'); q.click('[data-go=turno]'); q.click('#azz-turno'); q.click('#azz-turno')
    q.click('#back'); q.click('[data-go=mag]'); q.click('#azz-mag'); q.click('#azz-mag')
    q.click('#back'); q.click('[data-go=lam]'); q.click('#azz-lam'); q.click('#azz-lam'); q.wait_for_timeout(100)
    check(len(ag()) == 4, "archivio: Azzera dei tre report non cancella l'archivio")
    check('reportistica.v1.archivio' in q.evaluate(LS), 'archivio: chiave reportistica.v1.archivio')
    # sopravvive al ricaricamento
    q.wait_for_timeout(500); q.reload(); q.wait_for_selector('#v-home', state='visible'); q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible')
    check(q.locator('.arcitem').count() == 4, 'archivio: dopo il ricaricamento le voci ci sono ancora ' + str(q.locator('.arcitem').count()) + str(ag()) + q.url)
    # limite 200
    q.evaluate("() => localStorage.setItem('reportistica.v1.archivio', JSON.stringify({v:1, d:Array.from({length:200}, (_, i) => ({t:'2026-10-0'+(1+i%5)+'T10:'+String(i%60).padStart(2,'0')+':00+02:00', l:'x', r:'turno', x:'msg'+i}))}))")
    q.click('#back'); q.click('[data-go=mag]'); q.fill('#mg-in-tot', '99'); q.click('#mg-copy')
    a = ag()
    check(len(a) == 200 and a[0]['x'] == 'msg1' and a[-1]['r'] == 'magazzino', 'archivio: limite 200 (il piu vecchio sparisce da solo)')
    ca.close()
    # ---- archivio vuoto ----
    cb, q = nuovo(); q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible')
    check(q.is_visible('#arc-empty') and q.inner_text('#arc-empty') == 'Nessun messaggio salvato' and q.is_disabled('#arc-zip') and q.locator('.arcitem').count() == 0, 'archivio vuoto: "Nessun messaggio salvato" e tasto zip disabilitato')
    cb.close()
    # ---- zip: download ----
    NOSHARE = "Object.defineProperty(navigator, 'share', { value: undefined, configurable: true });"
    SEED = [('2026-10-06T14:05:30+02:00', 'turno', '*Report turno 6-14 del 06/10*\nProduzione 398 ton\nCassone: 2 (pieno, metà)'),
            ('2026-10-06T14:05:50+02:00', 'turno', '*Report turno 6-14 del 06/10*\nProduzione 400 ton'),
            ('2026-10-06T17:30:00+02:00', 'magazzino', 'Buongiorno,\n*Controllo magazzino*\n• Totale pacchi in magazzino: 21'),
            ('2026-12-01T09:00:00+01:00', 'lamiere', '*Controllo lamiere*\nLotto 19223\nSpessori testa: 25.7 25.9 25.3')]
    SEEDJS = "() => localStorage.setItem('reportistica.v1.archivio', JSON.stringify({v:1, d:%s.map(([t, r, x]) => ({t, l:'l', r, x}))}))" % json.dumps(SEED)
    errs.clear()
    cz, q = nuovo(UTC(2026, 10, 6, 22, 30), NOSHARE)      # 22:30 UTC = 00:30 del 07/10 a Roma
    q.evaluate(SEEDJS); q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible')
    check(q.is_enabled('#arc-zip'), 'zip: tasto abilitato con archivio pieno')
    with q.expect_download() as dl: q.click('#arc-zip')
    d = dl.value; zp = os.path.join(tempfile.gettempdir(), 'prova_archivio.zip'); d.save_as(zp)
    check(d.suggested_filename == 'report 2026-10-06 2026-12-01.zip', 'zip: nome report <data primo> <data ultimo>.zip')
    zf = zipfile.ZipFile(zp)
    check(zf.testzip() is None, 'zip: testzip OK (CRC di tutti i file corretti)')
    names = zf.namelist()
    check(names == ['2026-10-06_14-05_turno.txt', '2026-10-06_14-05_turno_2.txt', '2026-10-06_17-30_magazzino.txt', '2026-12-01_09-00_lamiere.txt', 'indice.csv'], 'zip: un .txt per messaggio AAAA-MM-GG_HH-MM_tipo.txt (nome doppio -> _2) + indice.csv: ' + str(names))
    ok_c = all(zf.read(n).startswith(b'\xef\xbb\xbf') and zf.read(n)[3:].decode('utf-8') == SEED[i][2] for i, n in enumerate(names[:4]))
    check(ok_c, 'zip: contenuti uguali ai messaggi, UTF-8 con BOM')
    check(all(i.compress_type == zipfile.ZIP_STORED and i.flag_bits & 0x800 for i in zf.infolist()), 'zip: formato stored, nomi UTF-8 (flag 0x0800)')
    check(zf.getinfo(names[0]).date_time == (2026, 10, 6, 14, 5, 30) and zf.getinfo(names[3]).date_time == (2026, 12, 1, 9, 0, 0), 'zip: data/ora DOS dei file = ora del messaggio')
    csv = zf.read('indice.csv'); cs = csv.decode('utf-8-sig')
    check(csv.startswith(b'\xef\xbb\xbf') and cs.split('\r\n') == ['data,ora,tipo,file', '2026-10-06,14:05,turno,2026-10-06_14-05_turno.txt', '2026-10-06,14:05,turno,2026-10-06_14-05_turno_2.txt', '2026-10-06,17:30,magazzino,2026-10-06_17-30_magazzino.txt', '2026-12-01,09:00,lamiere,2026-12-01_09-00_lamiere.txt', ''], 'zip: indice.csv (data, ora, tipo, nome file)')
    # test su 200 messaggi lunghi e accentati
    q.evaluate("() => localStorage.setItem('reportistica.v1.archivio', JSON.stringify({v:1, d:Array.from({length:200}, (_, i) => ({t:'2026-10-06T10:'+String(i%60).padStart(2,'0')+':'+String(Math.floor(i/60)).padStart(2,'0')+'+02:00', l:'x', r:['turno','magazzino','lamiere'][i%3], x:'Voce '+i+' àèìòù €\\n'+'riga lunga '.repeat(50)}))}))")
    q.click('#back'); q.click('#arc-open')
    with q.expect_download() as dl: q.click('#arc-zip')
    dl.value.save_as(zp); zf = zipfile.ZipFile(zp)
    check(zf.testzip() is None and len(zf.namelist()) == 201 and zf.read(zf.namelist()[7])[3:].decode('utf-8').startswith('Voce 7 àèìòù €'), 'zip: 200 messaggi -> 201 file, testzip OK')
    check(not errs, 'zip: nessun errore JS')
    cz.close()
    # share: usato per primo se disponibile
    SHARE_OK = "navigator.canShare = () => true; navigator.share = d => { window.__sh = d.files.map(f => f.name + ':' + f.type + ':' + f.size); return Promise.resolve(); };"
    SHARE_KO = "navigator.canShare = () => true; navigator.share = d => Promise.reject(new Error('non riuscito'));"
    SHARE_AB = "navigator.canShare = () => true; navigator.share = d => Promise.reject(new DOMException('annullato', 'AbortError'));"
    for nome, scr, atteso in [('riuscito', SHARE_OK, 0), ('fallito', SHARE_KO, 1), ('annullato', SHARE_AB, 0)]:
        csh, q = nuovo(UTC(2026, 10, 6, 20, 40), scr); q.evaluate(SEEDJS); n_dl = []
        q.on('download', lambda d_: n_dl.append(d_)); q.click('#arc-open'); q.click('#arc-share'); q.wait_for_timeout(600)
        if nome == 'riuscito':
            sh = q.evaluate('window.__sh')
            check(sh and len(sh) == 1 and sh[0].startswith('report 2026-10-06 2026-12-01.txt:text/plain:'), 'condividi: navigator.share({files}) provato e riceve il file TXT unico')
        check(len(n_dl) == atteso, 'condividi: share ' + nome + ' -> ' + ('ricade sul download' if atteso else 'nessun download'))
        csh.close()

    # ---- Zip: "Salva file" resta solo download anche se share esiste ----
    errs.clear()
    cs2, q = nuovo(UTC(2026, 10, 6, 20, 40), SHARE_OK); q.evaluate(SEEDJS); n_dl = []
    q.on('download', lambda d_: n_dl.append(d_)); q.click('#arc-open'); q.click('#arc-zip'); q.wait_for_timeout(600)
    check(len(n_dl) == 1 and not q.evaluate('window.__sh'), 'zip: "Salva file (zip)" scarica sempre (non usa la condivisione)')
    cs2.close()
    # ---- avviso archivio quasi pieno (180/200) e archivio pieno ----
    def riempi(qq, n):
        qq.evaluate("n => localStorage.setItem('reportistica.v1.archivio', JSON.stringify({v:1, d:Array.from({length:n}, (_, i) => ({t:'2026-10-0'+(1+i%5)+'T10:'+String(i%60).padStart(2,'0')+':00+02:00', l:'x', r:'turno', x:'msg'+i}))}))", n)
    errs.clear()
    cw, q = nuovo(UTC(2026, 10, 6, 20, 40)); q.evaluate(NOWA)
    check(q.is_hidden('#arc-badge'), 'avviso: home senza badge con archivio vuoto')
    riempi(q, 179); q.reload(); q.wait_for_selector('#v-home', state='visible')
    check(q.is_hidden('#arc-badge'), 'avviso: 179 messaggi -> nessun badge in home')
    q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible')
    check(q.is_hidden('#arc-warn'), 'avviso: 179 messaggi -> nessun banner')
    q.click('#back'); q.click('[data-go=lam]'); q.fill('#la-num-0', '1'); q.fill('#la-testa-0-0', '25.1'); q.click('#la-copy')   # il 180esimo
    q.click('#back')
    check(q.is_visible('#arc-badge') and q.inner_text('#arc-badge') == '180/200', 'avviso: al 180esimo messaggio compare il badge 180/200 sul tasto Archivio in home')
    q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible')
    check(q.is_visible('#arc-warn') and q.inner_text('#arc-warn-t') == 'Archivio quasi pieno: 180/200. Salva il file zip' and q.is_visible('#arc-w-zip') and q.is_visible('#arc-w-share'), 'avviso: banner "Archivio quasi pieno: 180/200. Salva il file zip" con scorciatoie Salva/Condividi')
    with q.expect_download() as dl: q.click('#arc-w-zip')
    check(dl.value.suggested_filename.endswith('.zip'), 'avviso: scorciatoia Salva del banner scarica lo zip')
    riempi(q, 200); q.click('#back'); q.click('[data-go=lam]'); q.fill('#la-testa-0-0', '25.2'); q.click('#la-copy'); q.click('#back')
    check(len(q.evaluate(AK)) == 200 and q.inner_text('#arc-badge') == '200/200' and 'full' in q.get_attribute('#arc-badge', 'class'), 'avviso: a 200 il badge e rosso (200/200), le voci restano 200')
    q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible')
    check(q.inner_text('#arc-warn-t') == 'Archivio pieno: i messaggi più vecchi vengono cancellati', 'avviso: a 200 il banner diventa "Archivio pieno: ..."')
    # ---- Cancella archivio (3 tocchi) ----
    check(q.is_visible('#arc-clear') and q.is_enabled('#arc-clear') and q.inner_text('#arc-clear') == 'Cancella archivio' and q.get_attribute('#arc-clear', 'class') == 'danger', 'cancella: tasto rosso in fondo, abilitato')
    q.click('#arc-clear')
    check(q.inner_text('#arc-clear') == 'Sei sicuro? Cancella tutto' and len(q.evaluate(AK)) == 200, 'cancella: un solo tocco chiede e non cancella')
    q.screenshot(path=os.path.join(tempfile.gettempdir(), 'x.png'))
    q.click('#arc-clear')
    check(q.inner_text('#arc-clear') == 'Confermi? Non si può annullare' and len(q.evaluate(AK)) == 200, 'cancella: secondo tocco = conferma finale, ancora niente cancellato')
    q.wait_for_timeout(4400)
    check(q.inner_text('#arc-clear') == 'Cancella archivio' and len(q.evaluate(AK)) == 200, 'cancella: aspettando si torna indietro e non si cancella')
    q.click('#arc-clear'); q.click('#arc-clear'); q.click('#arc-clear'); q.wait_for_timeout(100)
    check(q.evaluate("() => localStorage.getItem('reportistica.v1.archivio')") is None and q.is_visible('#arc-empty') and q.inner_text('#arc-empty') == 'Nessun messaggio salvato' and q.is_hidden('#arc-warn') and q.is_disabled('#arc-clear') and q.is_disabled('#arc-zip') and q.is_disabled('#arc-share'), 'cancella: al terzo tocco cancella tutto; pagina vuota, banner via, tasti disabilitati')
    q.click('#back')
    check(q.is_hidden('#arc-badge'), 'cancella: il badge in home sparisce')
    check(not errs, 'avviso/cancella: nessun errore JS')
    cw.close()
    # ---- archivio rovinato / localStorage bloccato: nessun errore, Copia e WhatsApp funzionano ----
    for nome, val in [('testo non JSON', '{{{non json'), ('versione diversa', '{"v":99,"d":[]}'), ('d non lista', '{"v":1,"d":"abc"}'), ('voci sbagliate', '{"v":1,"d":[null,5,{"t":1},{"t":"2026-10-06T10:00:00+02:00","l":"x","r":"boh","x":"y"}]}')]:
        errs.clear()
        cc, q = nuovo(UTC(2026, 10, 6, 20, 40), "try{ if(!sessionStorage.getItem('g')){ localStorage.setItem('reportistica.v1.archivio', %r); sessionStorage.setItem('g','1'); } }catch(e){}" % val); q.evaluate(NOWA)
        q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible'); vuoto = q.is_visible('#arc-empty') and q.is_disabled('#arc-zip')
        q.click('#back'); q.click('[data-go=turno]'); q.fill('#in-prod', '5'); q.click('#copy'); q.wait_for_selector('#status', state='visible', timeout=3000)
        q.click('#back'); q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible')
        check(vuoto and q.locator('.arcitem').count() == 1 and not errs, 'archivio rovinato (' + nome + str((vuoto, q.locator('.arcitem').count(), errs)) + '): pagina vuota, poi Copia salva comunque, nessun errore JS')
        cc.close()
    errs.clear()
    cl_, q = nuovo(UTC(2026, 10, 6, 20, 40), "Object.defineProperty(window, 'localStorage', { get(){ throw new Error('bloccato'); } });")
    q.evaluate(NOWA); q.click('[data-go=turno]'); q.fill('#in-prod', '9'); q.click('#copy'); q.wait_for_selector('#status', state='visible', timeout=3000)
    st_ok = q.inner_text('#status') in OKCOPIA
    q.click('#wa'); q.click('#back'); q.click('[data-go=mag]'); q.fill('#mg-in-tot', '1'); q.click('#mg-copy'); q.click('#mg-wa'); q.click('#back'); q.click('#arc-open'); q.wait_for_selector('#v-arc', state='visible')
    check(st_ok and q.is_visible('#arc-empty') and q.is_disabled('#arc-zip') and not errs, 'archivio: localStorage bloccato -> Copia/WhatsApp funzionano, archivio vuoto, nessun errore JS')
    cl_.close()
    # archivio pieno (quota): Copia funziona lo stesso
    errs.clear()
    cq, q = nuovo(UTC(2026, 10, 6, 20, 40), "const _s = Storage.prototype.setItem; Storage.prototype.setItem = function(k, v){ if (k === 'reportistica.v1.archivio') throw new DOMException('piena', 'QuotaExceededError'); return _s.call(this, k, v); };")
    q.click('[data-go=turno]'); q.fill('#in-prod', '9'); q.click('#copy'); q.wait_for_selector('#status', state='visible', timeout=3000)
    check(q.inner_text('#status') in OKCOPIA and not errs, 'archivio: memoria piena -> Copia funziona lo stesso, nessun errore')
    cq.close()

    # ======================= PIATTINE e VIROLE (come Bat) =======================
    errs.clear()
    cm, q = nuovo(UTC(2026, 10, 8, 10, 0)); q.evaluate(NOWA)
    q.click('[data-go=mag]'); q.wait_for_selector('#v-mag', state='visible')
    mo = lambda: q.eval_on_selector('#mg-out', 'e => e.value').split(chr(10))
    ATTR = "e => [e.tagName, e.type, e.inputMode, e.className, e.closest('.group').querySelector('h3').textContent, e.closest('li').querySelectorAll('input').length, e.closest('li').querySelector('label.name').textContent]"
    ab, ap, av = [q.locator('#mg-in-' + i).evaluate(ATTR) for i in ['bat', 'piattine', 'virole']]
    check(ab[:4] == ap[:4] == av[:4] and ab[5] == ap[5] == av[5] and ap[4] == 'Piattine' and av[4] == 'Virole' and ap[6] == 'Piattine (numero)' and av[6] == 'Virole (numero)', 'piattine/virole: stesso tipo di campo, layout e casella di Bat ' + str((ab, ap, av)))
    keys = q.eval_on_selector_all('#mg-groups input.cb', 'els => els.map(e => e.id)')
    check(keys.index('mg-ck-bat') + 1 == keys.index('mg-ck-piattine') and keys.index('mg-ck-piattine') + 1 == keys.index('mg-ck-virole'), "piattine/virole: nell'ordine Bat, Piattine, Virole")
    q.fill('#mg-in-bat', '3'); q.fill('#mg-in-piattine', '4'); q.fill('#mg-in-virole', '5')
    L = mo()
    check(L.count('• 3 bat') == 1 and L.count('• 4 piattine') == 1 and L.count('• 5 virole') == 1 and L.index('• 3 bat') + 1 == L.index('• 4 piattine') and L.index('• 4 piattine') + 1 == L.index('• 5 virole'), 'piattine/virole: compaiono nel messaggio dopo Bat ' + str(L))
    q.click('#mg-ck-piattine')
    check('• 4 piattine' not in mo() and '• 5 virole' in mo() and not q.is_visible('#mg-in-piattine'), 'piattine: casella spenta toglie la riga (virole resta)')
    q.click('#mg-ck-virole')
    check('• 5 virole' not in mo() and '• 3 bat' in mo(), 'virole: casella spenta toglie la riga')
    q.click('#mg-ck-piattine'); q.click('#mg-ck-virole')
    check('• 4 piattine' in mo() and '• 5 virole' in mo(), 'piattine/virole: caselle riaccese -> righe di nuovo')
    q.click('#mg-ck-virole')
    q.wait_for_timeout(500); q.reload(); q.wait_for_selector('#v-home', state='visible')
    q.click('[data-go=mag]'); q.wait_for_selector('#v-mag', state='visible')
    check(q.input_value('#mg-in-piattine') == '4' and q.input_value('#mg-in-virole') == '5' and q.input_value('#mg-in-bat') == '3' and not q.is_checked('#mg-ck-virole') and q.is_checked('#mg-ck-piattine') and '• 4 piattine' in mo() and '• 5 virole' not in mo(), 'piattine/virole: memoria dopo ricarica (valori e casella spenta)')
    q.click('#azz-mag'); q.click('#azz-mag'); q.wait_for_timeout(500)
    check(q.input_value('#mg-in-piattine') == '' and q.input_value('#mg-in-virole') == '' and q.is_checked('#mg-ck-virole') and not any(w in q.eval_on_selector('#mg-out', 'e => e.value') for w in ['piattine', 'virole']) and q.evaluate("() => localStorage.getItem('reportistica.v1.magazzino')") is None, 'piattine/virole: Azzera svuota campi, caselle e memoria')
    pr = q.evaluate("() => { const f = MG.parse('*Controllo magazzino*\\n• 2 piattine\\n• 7 virole\\n• 1 bat'); return [f.piattine, f.virole, f.bat, f.xm.length]; }")
    check(pr == ['2', '7', '1', 0], 'piattine/virole: lettura di un messaggio salvato ' + str(pr))
    check(not errs, 'piattine/virole: nessun errore JS')
    cm.close()

    # ======================= ACCESSO e INVIO ONLINE (rete finta: nessuna chiamata vera) =======================
    SBH = 'https://tzevatahoxxtkesyqssh.supabase.co'
    PUBKEY = 'sb_publishable_87KOPApbv0LGUPA8Tx2fBA_REqKz-ni'
    COLS = ['body', 'kind', 'name', 'report_date', 'shift']
    def finto():
        return {'log': [], 'off': False, 'valid': set(), 'rt': 'RT1', 'refresh_ok': True, 'post_status': None, 'posted': []}
    def sb_handler(st):
        def h(route, req):
            st['log'].append((req.method, req.url, dict(req.headers), req.post_data))
            if st['off']: route.abort(); return
            u = req.url
            js = lambda code, o: route.fulfill(status=code, content_type='application/json', body=json.dumps(o))
            if '/auth/v1/token?grant_type=password' in u:
                d = json.loads(req.post_data or '{}')
                if req.headers.get('apikey') == PUBKEY and d.get('email') == 'l.cavo@reportistica-fil.it' and d.get('password') == 'giusta':
                    st['valid'] = {'AT1'}; st['rt'] = 'RT1'
                    js(200, {'access_token': 'AT1', 'refresh_token': 'RT1', 'expires_in': 3600, 'user': {'id': 'x'}})
                else: js(400, {'error': 'invalid_grant', 'error_description': 'Invalid login credentials'})
            elif '/auth/v1/token?grant_type=refresh_token' in u:
                d = json.loads(req.post_data or '{}')
                if st['refresh_ok'] and d.get('refresh_token') == st['rt']:
                    st['valid'] = {'AT2'}; st['rt'] = 'RT2'
                    js(200, {'access_token': 'AT2', 'refresh_token': 'RT2', 'expires_in': 3600, 'user': {'id': 'x'}})
                else: js(400, {'error': 'invalid_grant'})
            elif u.endswith('/rest/v1/reports'):
                tok = (req.headers.get('authorization') or '').replace('Bearer ', '')
                if st['post_status']: js(st['post_status'], {'message': 'no'}); return
                if tok not in st['valid'] or req.headers.get('apikey') != PUBKEY: js(401, {'message': 'JWT expired'}); return
                st['posted'].append(json.loads(req.post_data)); route.fulfill(status=201, body='')
            else: route.fulfill(status=404, body='')
        return h
    def sb_nuovo(st, ora=UTC(2026, 10, 8, 10, 0), init=None, vp=None, lv=True):
        c = b.new_context(viewport=vp or {'width': 400, 'height': 900})
        if lv: c.add_init_script(LV)
        if init: c.add_init_script(init)
        c.route(SBH + '/**', sb_handler(st))
        q = c.new_page(); q.on('pageerror', lambda e: errs.append(str(e)))
        q.clock.set_fixed_time(ora); q.goto(URL); q.wait_for_selector('#v-home', state='attached'); return c, q
    onl = lambda: q.text_content('#onl-t')
    attendi = lambda txt: q.wait_for_function("t => document.getElementById('onl-t').textContent.includes(t)", arg=txt, timeout=5000)
    coda = lambda: q.evaluate("() => { const r = localStorage.getItem('reportistica.v1.coda'); return r ? JSON.parse(r).d : []; }")
    SESS = "() => localStorage.getItem('reportistica.v1.sessione')"
    def entra(user='l.cavo', pw='giusta'):
        q.click('#onl-btn'); q.wait_for_selector('#v-login', state='visible')
        q.fill('#lg-user', user); q.fill('#lg-pass', pw); q.click('#lg-go')
    errs.clear()
    st = finto(); cs, q = sb_nuovo(st); q.evaluate(NOWA)
    check(q.is_visible('#v-home') and 'Non collegato: i report non vengono salvati online' in onl() and q.is_visible('#onl-btn') and q.text_content('#onl-btn') == 'Accedi' and not q.is_visible('#onl-exit'), 'online: non loggato -> home con riga "Non collegato" e tasto Accedi')
    q.click('[data-go=turno]'); q.fill('#in-prod', '5'); q.click('#copy'); q.wait_for_selector('#status', state='visible', timeout=3000)
    check(q.inner_text('#status') in OKCOPIA and len(coda()) == 1 and st['log'] == [], 'online: non loggato -> Copia funziona, 1 voce in coda, nessuna chiamata online')
    q.click('#copy'); q.click('#wa')
    check(len(coda()) == 1, "online: stesso testo copiato/WhatsApp piu' volte -> una sola voce (come l'archivio)")
    q.click('#back')
    check("1 da inviare dopo l'accesso" in onl(), 'online: la riga non collegato mostra le voci in coda')
    entra('l.cavo', 'sbagliata')
    q.wait_for_selector('#lg-err', state='visible', timeout=3000)
    check(q.inner_text('#lg-err') == 'Nome utente o password sbagliati' and q.is_visible('#v-login') and q.evaluate(SESS) is None and q.get_attribute('#lg-pass', 'type') == 'password', 'accesso: password sbagliata -> messaggio chiaro, resta sulla schermata, niente sessione')
    q.click('#lg-eye'); check(q.get_attribute('#lg-pass', 'type') == 'text', 'accesso: occhio mostra la password'); q.click('#lg-eye')
    lg = [x for x in st['log'] if 'grant_type=password' in x[1]][0]
    check(lg[0] == 'POST' and lg[2].get('apikey') == PUBKEY and json.loads(lg[3]) == {'email': 'l.cavo@reportistica-fil.it', 'password': 'sbagliata'} and 'sbagliata' not in lg[1], "accesso: chiamata giusta (apikey, email con dominio aggiunto, password nel corpo e non nell'URL)")
    q.fill('#lg-user', ' L.Cavo '); q.fill('#lg-pass', 'giusta'); q.click('#lg-go')
    q.wait_for_selector('#v-home', state='visible', timeout=5000); attendi('Online: tutto salvato')
    ses = json.loads(q.evaluate(SESS))
    check(ses['u'] == 'l.cavo' and ses['at'] == 'AT1' and ses['rt'] == 'RT1', 'accesso: sessione salvata (nome, token)')
    check(len(st['posted']) == 1 and coda() == [] and q.is_visible('#onl-exit') and q.text_content('#onl-exit') == 'Esci (l.cavo)' and not q.is_visible('#onl-btn'), 'accesso ok: parte la coda, "Online: tutto salvato", tasto Esci (l.cavo)')
    P = st['posted'][0]; rq = [x for x in st['log'] if x[1].endswith('/rest/v1/reports')][-1]
    sel = q.evaluate("() => [document.querySelector('#shiftRow [aria-pressed=true]').textContent, document.getElementById('date').value]")
    check(sorted(P) == COLS and P['kind'] == 'turno' and P['shift'] == sel[0] and P['report_date'] == sel[1] and P['name'] == f'Report turno {sel[0]} {sel[1]}' and 'Produzione 5 ton' in P['body'], 'invio turno: solo le 5 colonne, kind/shift/report_date/name giusti ' + str(P)[:150])
    check(rq[2].get('apikey') == PUBKEY and rq[2].get('authorization') == 'Bearer AT1' and rq[2].get('prefer') == 'return=minimal' and 'AT1' not in rq[1], "invio: intestazioni giuste (apikey, Bearer, return=minimal), token non nell'URL")
    q.click('[data-go=mag]'); q.fill('#mg-in-tot', '21'); q.click('#mg-copy'); q.click('#back'); attendi('Online: tutto salvato')
    q.click('[data-go=lam]'); q.fill('#la-num-0', '19223'); q.click('#la-copy'); q.click('#back'); attendi('Online: tutto salvato'); q.wait_for_timeout(300)
    M, Lm = st['posted'][1], st['posted'][2]
    check(sorted(M) == COLS and M['kind'] == 'magazzino' and M['shift'] is None and M['report_date'] is None and M['name'] == 'Controllo magazzino 2026-10-08 12-00' and 'Totale pacchi in magazzino: 21' in M['body'], 'invio magazzino: payload e nome giusti ' + str(M)[:150])
    check(sorted(Lm) == COLS and Lm['kind'] == 'lamiere' and Lm['shift'] is None and Lm['report_date'] is None and Lm['name'] == 'Controllo lamiere 2026-10-08 12-00' and 'Lotto 19223' in Lm['body'], 'invio lamiere: payload e nome giusti ' + str(Lm)[:150])
    check(len(st['posted']) == 3, 'invio: un solo invio per ogni Copia (nessun doppione)')
    # 401 -> rinnovo -> riprova
    st['valid'].clear(); n0 = len(st['posted'])
    q.click('[data-go=mag]'); q.fill('#mg-in-sped', '7'); q.click('#mg-copy'); q.click('#back'); attendi('Online: tutto salvato')
    sess2 = json.loads(q.evaluate(SESS))
    check(len(st['posted']) == n0 + 1 and sess2['at'] == 'AT2' and sess2['rt'] == 'RT2' and any('grant_type=refresh_token' in x[1] for x in st['log']), '401: rinnovo del token una volta e poi riprova (inviato, nuova sessione salvata)')
    # rete assente -> resta in coda -> evento online -> si svuota
    st['off'] = True; n0 = len(st['posted'])
    q.click('[data-go=lam]'); q.fill('#la-num-0', '19224'); q.click('#la-copy'); q.click('#back'); q.wait_for_timeout(300)
    check(len(coda()) == 1 and 'In coda: 1 report da inviare' in onl() and len(st['posted']) == n0 and not q.is_visible('#onl-btn'), 'rete assente: il report resta in coda, riga "In coda: 1 report da inviare"')
    st['off'] = False; q.evaluate("() => window.dispatchEvent(new Event('online'))"); attendi('Online: tutto salvato')
    check(coda() == [] and len(st['posted']) == n0 + 1 and st['posted'][-1]['kind'] == 'lamiere', 'torna la rete (evento online): la coda si svuota in ordine')
    # dato rifiutato (422): scartato dalla coda, segnalato
    st['post_status'] = 422; n0 = len(st['posted'])
    q.click('[data-go=mag]'); q.fill('#mg-in-intest', '3'); q.click('#mg-copy'); q.click('#back'); q.wait_for_selector('#onl-note', state='visible', timeout=5000)
    check(coda() == [] and len(st['posted']) == n0 and 'rifiutato' in q.text_content('#onl-note'), 'errore 422: voce scartata dalla coda e segnalata')
    st['post_status'] = None
    # 401 che resta -> in coda, "Accedi di nuovo"
    st['valid'].clear(); st['refresh_ok'] = False; n0 = len(st['posted'])
    q.click('[data-go=mag]'); q.fill('#mg-in-intest', '4'); q.click('#mg-copy'); q.click('#back'); attendi('Accesso scaduto')
    check(len(coda()) == 1 and q.text_content('#onl-btn') == 'Accedi di nuovo' and q.is_visible('#onl-btn') and len(st['posted']) == n0, '401 che resta: report in coda, riga "Accesso scaduto" e tasto "Accedi di nuovo"')
    st['refresh_ok'] = True; entra(); q.wait_for_selector('#v-home', state='visible', timeout=5000); attendi('Online: tutto salvato')
    check(coda() == [] and len(st['posted']) == n0 + 1, 'accedi di nuovo: la coda parte')
    # Esci: doppio tocco
    q.click('#onl-exit'); check(q.text_content('#onl-exit') == 'Confermi?' and q.evaluate(SESS) is not None, 'esci: primo tocco chiede conferma')
    q.click('#onl-exit'); q.wait_for_timeout(100)
    check(q.evaluate(SESS) is None and 'Non collegato' in onl() and not q.is_visible('#onl-exit'), 'esci: secondo tocco -> sessione tolta, "Non collegato"')
    q.click('[data-go=mag]'); q.fill('#mg-in-intest', '9'); q.click('#mg-copy'); q.click('#back'); q.wait_for_timeout(300)
    check(len(coda()) == 1, "dopo Esci: l'app si usa lo stesso, il report va in coda")
    check(not errs, 'online: nessun errore JS')
    cs.close()
    # all'apertura, con sessione salvata e coda: parte da sola
    sess_js = "try{localStorage.setItem('reportistica.v1.sessione', JSON.stringify({v:1,u:'l.cavo',at:'AT1',rt:'RT1',exp:9999999999999}));localStorage.setItem('reportistica.v1.coda', JSON.stringify({v:1,d:[{id:'a1',p:{kind:'lamiere',shift:null,report_date:null,name:'Controllo lamiere 2026-10-07 09-00',body:'*Controllo lamiere*\\nLotto 1'}}]}))}catch(e){}"
    st2 = finto(); st2['valid'] = {'AT1'}
    c2, q = sb_nuovo(st2, init="if(!sessionStorage.getItem('g')){ " + sess_js + " sessionStorage.setItem('g','1'); }")
    attendi('Online: tutto salvato')
    check(len(st2['posted']) == 1 and st2['posted'][0]['name'] == 'Controllo lamiere 2026-10-07 09-00' and not q.is_visible('#v-login'), 'apertura app con sessione e coda: la coda parte da sola, nessuna schermata di accesso')
    c2.close()
    # prima volta in assoluto: la schermata Accedi si propone, una volta sola
    errs.clear()
    st3 = finto(); c3_, q = sb_nuovo(st3, lv=False)
    check(q.is_visible('#v-login') and q.is_visible('#lg-skip'), 'prima apertura: compare la schermata Accedi')
    q.click('#lg-skip'); q.wait_for_selector('#v-home', state='visible', timeout=3000)
    check(q.is_visible('#v-home') and 'Non collegato' in onl(), 'prima apertura: "Continua senza accedere" porta alla home, app usabile')
    q.reload(); q.wait_for_selector('#v-home', state='visible')
    check(not q.is_visible('#v-login') and not errs, 'seconda apertura: la schermata Accedi non si ripropone da sola')
    c3_.close()
    # localStorage bloccato: nessun errore JS, app usabile, accesso e invio funzionano in memoria
    errs.clear()
    BLK = "Object.defineProperty(window, 'localStorage', { get(){ throw new Error('bloccato'); } });"
    st4 = finto(); c4, q = sb_nuovo(st4, init=BLK, lv=False); q.evaluate(NOWA)
    check(q.is_visible('#v-home') and 'Non collegato' in onl(), 'localStorage bloccato: home normale, "Non collegato", nessuna schermata Accedi da sola')
    q.click('[data-go=lam]'); q.fill('#la-num-0', '5'); q.click('#la-copy'); q.click('#back')
    q.click('#onl-btn'); q.fill('#lg-user', 'l.cavo'); q.fill('#lg-pass', 'giusta'); q.click('#lg-go'); q.wait_for_selector('#v-home', state='visible', timeout=5000); attendi('Online: tutto salvato')
    check(len(st4['posted']) == 1 and not errs, 'localStorage bloccato: accesso e invio funzionano in memoria, nessun errore JS')
    c4.close()
    # schermate 390px per Luca
    errs.clear()
    anteprime = R.parent / 'anteprime'; anteprime.mkdir(exist_ok=True)
    st5 = finto(); c5, q = sb_nuovo(st5, vp={'width': 390, 'height': 844}); q.evaluate(NOWA)
    q.screenshot(path=str(anteprime / 'online_1_home_non_collegato.png'))
    q.click('#onl-btn'); q.wait_for_selector('#v-login', state='visible'); q.fill('#lg-user', 'l.cavo'); q.screenshot(path=str(anteprime / 'online_2_accedi.png'))
    q.fill('#lg-pass', 'giusta'); q.click('#lg-go'); q.wait_for_selector('#v-home', state='visible', timeout=5000); attendi('Online: tutto salvato')
    q.screenshot(path=str(anteprime / 'online_3_home_collegato.png'))
    st5['off'] = True; q.click('[data-go=mag]'); q.fill('#mg-in-bat', '3'); q.fill('#mg-in-piattine', '4'); q.fill('#mg-in-virole', '5')
    q.click('#mg-copy'); q.wait_for_timeout(300); q.evaluate("() => window.scrollTo(0, document.getElementById('mg-groups').offsetTop + 380)")
    q.screenshot(path=str(anteprime / 'online_4_magazzino_piattine_virole.png'))
    q.click('#back'); q.screenshot(path=str(anteprime / 'online_5_home_in_coda.png'))
    check(not errs and (anteprime / 'online_4_magazzino_piattine_virole.png').exists(), 'anteprime 390px salvate in Report_Turni\\anteprime')
    c5.close()

    b.close()
srv.shutdown()
sys.exit(0 if ok else 1)


