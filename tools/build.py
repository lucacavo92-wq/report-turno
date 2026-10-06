# Crea index.html (app installabile, con logo FIL) partendo da src/app.html (pagina Claude, senza logo).
# Uso:  python3 tools/build.py
import base64, pathlib
R = pathlib.Path(__file__).resolve().parent.parent
s = (R / 'src/app.html').read_text(encoding='utf-8')
svg = base64.b64encode((R / 'logo.svg').read_bytes()).decode()
old = '    <div class="logo" id="logo" aria-label="FIL">FIL</div>'
assert old in s, 'segnaposto del logo non trovato in src/app.html'
s = s.replace(old, f'    <img class="logofull" src="data:image/svg+xml;base64,{svg}" alt="FIL">')
head = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<link rel="manifest" href="manifest.webmanifest">\n<meta name="theme-color" content="#12161c">\n'
        '<link rel="icon" href="icon-192.png">\n<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-title" content="Reportistica">\n')
i = s.index('</style>') + len('</style>')
s = head + s[:i].replace('*{box-sizing:border-box}', '*{box-sizing:border-box}\nbody{margin:0}', 1) + '\n</head>\n<body>' + s[i:] + '</body>\n</html>\n'
s = s.replace('</script>\n</body>', "if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});\n</script>\n</body>")
assert 'serviceWorker' in s
(R / 'index.html').write_text(s, encoding='utf-8')
print('index.html aggiornato')
