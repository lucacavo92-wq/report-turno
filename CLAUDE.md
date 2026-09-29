# Report turno FIL — guida per Claude Code

Progetto di Luca, separato da Magazzino Bidoni ed Enduro Crono. Scrivere sempre in **italiano**, frasi semplici. Luca risponde spesso con "y" = sì/fatto.

## A cosa serve
Ogni turno si manda sul gruppo WhatsApp "FIL A.S.Q" un report quasi sempre uguale. L'app legge il report precedente
(copiato da WhatsApp), lo divide in campi, aggiorna turno e data e fa cambiare solo i campi spuntati.

## File
- `index.html`: tutta l'app in un solo file (HTML + CSS + JS), con logo e foto incorporati.
- App installabile (PWA) su GitHub Pages: https://lucacavo92-wq.github.io/report-turno/
  `manifest.webmanifest`, `sw.js` (funziona anche offline, prima prova la rete), logo `logo.svg`, icone `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`.
  Se cambi i file salvati offline, aumenta la versione `CACHE` in `sw.js`.
- Pubblicata anche come pagina Claude (senza logo vero): https://claude.ai/artifact/2kxs19zG365LzmRw4w3SV5

## Decisioni prese (29/09/2026)
- Turni: **6-14, 14-22, 22-6**. Il report è del turno appena finito, scelto dall'ora del telefono:
  10:00–17:59 → 6-14; 18:00–01:59 → 14-22 (dopo mezzanotte data del giorno prima); 02:00–09:59 → 22-6 con la **data della mattina**.
- Campi: Produzione (ton), Ritardi, Copertura schede (si sceglie l'ora → "Copertura schede fino alle 7.30");
  Controllo magazzino (dal foglio di Luca del 29/09): Pacchi in magazzino, Pacchi spedibili, Intestature a terra (numeri),
  Cassone Montalbetti, Cassone Risaliti, Cassone scoria (box "N° cassoni" + per ogni cassone tasti pieno/metà/vuoto → "2 (pieno, metà)"), Bancali talloni (n° + stato scritto),
  Talloni da tagliare, Lamiere bloccate nel pulpito (numeri);
  Reparto taglio bramme: Bramme tagliate (numero), Cassone scoria (come sopra). Righe vuote non escono nel messaggio.
  Sicurezza: DPI e procedure, Pulizia, Violenza, Near miss;
  Qualità: Estetica, Planarità, Larghezze/lunghezze/spessori (ognuno **Conforme / Non conforme**) + Note qualità (testo libero;
  es. "Planarità sul 25 mm accettabile" va nelle note); Ambiente: Scrubber, Emissioni convogliate, Emissioni diffuse; Segnalazioni.
- Tasto grosso **Modifica** → elenco campi con il valore attuale; con ✎ si apre un **box vuoto** con il testo fisso intorno.
  Box vuoto: Ritardi / Copertura / Note qualità spariscono, Segnalazioni diventa "Nessuna", gli altri restano come prima.
- Home: solo casella per incollare (piccola), tasto **Modifica**, messaggio pronto. Turno e data stanno dentro Modifica.
- Ogni campo ha **un solo quadratino a 3 stati** (si tocca il quadratino o il nome): vuoto = resta com'era,
  **✎ blu** = da modificare (si apre il box vuoto), **✕** = tolto dal messaggio. Le voci fisse che mancano nel report
  incollato partono già su ✕; un gruppo con tutto su ✕ sparisce anche come titolo.
- Se non è incollato niente compare il tasto **Genera messaggio** (messaggio da zero con i valori standard + le modifiche).
- Righe prima di "Report turno" (saluti tipo "Buongiorno") si ignorano.
- App **pulita**: niente esempi, descrizioni o numeri dei passi (la usano persone esperte).
- Intestazione: logo in alto a sinistra, "FIL", "Report turno". Titolo del messaggio in grassetto: `*Report turno 14-22 del 28/09*`.

## Da fare
- Grafica stile sito FIL (blu #2884ff, Open Sans, schede bianche con bordo blu in alto). Intestazione: barra bianca con logo FIL
  a sinistra e accanto "REPORT TURNO" + turno/data. Logo `logo.svg` ridisegnato dalla foto della carta intestata del 29/09
  (blu #3a7fc1 con "FI", nero con "L", lettere bianche strette). La pagina Claude pubblicata ha un quadrato "FIL" al posto del logo.
- Luca deve ancora provare Copia e Apri in WhatsApp.
- Serve repository pubblico + Pages acceso (Settings → Pages → main / root) per l'indirizzo github.io.
