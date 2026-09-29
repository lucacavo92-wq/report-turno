# Report turno FIL — guida per Claude Code

Progetto di Luca, separato da Magazzino Bidoni ed Enduro Crono. Scrivere sempre in **italiano**, frasi semplici.
Luca risponde spesso con "y" = sì/fatto. Usa l'app dal telefono (Android, Chrome): istruzioni passo passo, link già pronti.

**Nome della sessione:** all'inizio di ogni nuova sessione rinominarla (strumento `set_session_title`, senza `session_id`
si usa `get_session` per avere l'id) con il formato **`FIL_GG-MM-AAAA_HH-MM`**, ora italiana
(`TZ=Europe/Rome date +"FIL_%d-%m-%Y_%H-%M"`), es. `FIL_29-09-2026_23-26`.

## A cosa serve
Ogni turno si manda sul gruppo WhatsApp "FIL A.S.Q" un report quasi sempre uguale. L'app legge il report precedente
(copiato da WhatsApp), lo divide in campi, aggiorna turno e data e fa cambiare solo i campi scelti.

## File e come si lavora
- `src/app.html` — **il file da modificare**. È la pagina pubblicata su Claude (senza logo vero: quadrato "FIL").
- `tools/build.py` — crea `index.html` da `src/app.html`: mette il logo `logo.svg`, manifest, icone e service worker.
  Dopo ogni modifica: `python3 tools/build.py`.
- `index.html` — app installabile (PWA) per GitHub Pages: https://lucacavo92-wq.github.io/report-turno/
- `manifest.webmanifest`, `sw.js` (offline; prima prova la rete), `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`, `logo.svg`.
  **Se cambi l'app, aumenta la versione `CACHE` in `sw.js`** (ora `report-turno-v5`).
- `tools/prova.js` — prova automatica: `NODE_PATH=$(npm root -g) node tools/prova.js` (usa Chromium in /opt/pw-browsers).
- Pagina Claude: https://claude.ai/artifact/2kxs19zG365LzmRw4w3SV5 — per aggiornarla da una nuova sessione pubblicare
  `src/app.html` con lo strumento Artifact passando `url` = quel link (prima fare `read` del link). Non mettere il logo vero lì.

Giro completo di una modifica: modifica `src/app.html` → `python3 tools/build.py` → aumenta `CACHE` in `sw.js` →
`tools/prova.js` → pubblica la pagina Claude → commit e push su `main`.

## Com'è fatta l'app (decisioni prese con Luca, 29/09/2026)
- **Home**: intestazione (logo FIL a sinistra, accanto "REPORT TURNO" + "Turno 14-22 del 29/09"), casella piccola per incollare,
  tasto grosso **MODIFICA**, "Messaggio pronto" con **Copia** e **Apri in WhatsApp**. Niente esempi né descrizioni.
- Se non è incollato niente compare **Genera messaggio**: report da zero con le frasi standard + le modifiche.
- **Turni** 6-14, 14-22, 22-6: il report è del turno appena finito, dall'ora del telefono:
  10:00–17:59 → 6-14; 18:00–01:59 → 14-22 (dopo mezzanotte data del giorno prima); 02:00–09:59 → 22-6 con la **data della mattina**.
  Turno e data si possono cambiare dentro Modifica.
- **Dentro Modifica**: in cima Turno e data, poi i campi per gruppo. Ogni campo ha **un solo quadratino a 3 stati**
  (si tocca il quadratino o il nome): vuoto = com'era, **✎ blu** = da modificare (si apre un box vuoto), **✕** = tolto dal messaggio.
  Le voci fisse che mancano nel report incollato partono già su ✕. Un gruppo tutto su ✕ sparisce anche come titolo.
- Box lasciato vuoto con ✎: Ritardi / Copertura / Note qualità spariscono, Segnalazioni diventa "Nessuna", gli altri restano com'erano.
- Righe prima di "Report turno" (saluti) si ignorano. Righe non riconosciute in Sicurezza/Ambiente si ricopiano.

## Campi e formato del messaggio
```
*Report turno 14-22 del 28/09*
Produzione 398 ton                          ← numero
Ritardo 15 min …                            ← Ritardi, testo libero
Copertura schede fino alle 7.30             ← si sceglie l'ora

Controllo magazzino                         ← dal foglio scritto a mano da Luca
• Pacchi in magazzino: 120                  ← numeri: pacchi in magazzino, pacchi spedibili, intestature a terra,
• Cassone Montalbetti: 2 (pieno, metà)         talloni da tagliare, lamiere bloccate nel pulpito
• Cassone Risaliti / Cassone scoria         ← box "N° cassoni" + per ogni cassone pieno / metà / vuoto
• Bancali talloni: 4, pronti                ← numero + stato scritto a mano

Reparto taglio bramme
• Bramme tagliate: 9
• Cassone scoria: 1 (vuoto)

Sicurezza                                   ← DPI e procedure, Pulizia, Violenza, Near miss (frasi)
Qualità                                     ← estetica / planarità / larghezze, lunghezze e spessori: conforme / non conforme
                                              + Note qualità (es. "Planarità sul 25 mm accettabile.")
Ambiente                                    ← Scrubber, Emissioni convogliate, Emissioni diffuse (…): nella norma
Segnalazioni:                               ← testo libero, vuoto = "Nessuna"
```
Voci del magazzino vuote non escono nel messaggio.

## Grafica
Stile del sito FIL (fabbricaitalianalamiere.com): fondo bianco, blu #2884ff, Open Sans, schede bianche con ombra e bordo blu
sottile in alto, titoli dei gruppi blu in maiuscolo. Logo `logo.svg` ridisegnato dalla carta intestata: blu #3a7fc1 con "FI",
nero con "L", lettere bianche strette. Il sito FIL è bloccato dalla rete di questo ambiente.

## Da fare / aperto
- **GitHub Pages non è ancora acceso.** Luca deve farlo da computer:
  1. https://github.com/lucacavo92-wq/report-turno/settings → Danger Zone → Change visibility → public
  2. https://github.com/lucacavo92-wq/report-turno/settings/pages → Deploy from a branch → main / (root) → Save
  Poi controllare https://lucacavo92-wq.github.io/report-turno/ e spiegargli: Chrome → ⋮ → Installa app.
  (Claude non può creare repository né cambiare queste impostazioni: GitHub risponde 403.)
- Luca deve ancora provare bene **Copia** e **Apri in WhatsApp** sul telefono.
- Bancali talloni: se gli stati sono sempre gli stessi, trasformarli in tasti.
