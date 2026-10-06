import sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
from playwright.sync_api import sync_playwright
A = pathlib.Path(r'C:\Users\Luca\Desktop\FIL\Report_Turni\anteprime')
save = len(sys.argv) > 1 and sys.argv[1] == 'save'
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2)
    p = ctx.new_page()
    p.clock.set_fixed_time(datetime(2026,9,29,22,40))
    p.goto('http://127.0.0.1:8765/index.html'); p.wait_for_selector('.tile')
    H = lambda: p.evaluate('document.documentElement.scrollHeight')
    res = {}
    res['home'] = H()
    if save: p.screenshot(path=str(A/'1_home.png'), full_page=True)
    for key, name, shot in [('mag','magazzino','2_magazzino.png'),('lam','lamiere','3_lamiere.png'),('turno','report_turno','4_report_turno.png')]:
        p.click(f'[data-go={key}]'); p.wait_for_timeout(300)
        res[name] = H()
        if save: p.screenshot(path=str(A/shot), full_page=True)
        p.click('#back'); p.wait_for_timeout(200)
    print(res)
    if save:
        p2 = b.new_context(viewport={'width':390,'height':420}, device_scale_factor=2).new_page()
        p2.clock.set_fixed_time(datetime(2026,9,29,22,40))
        p2.goto('http://127.0.0.1:8765/index.html'); p2.click('[data-go=turno]'); p2.wait_for_timeout(300)
        p2.focus('#in-prod'); p2.wait_for_timeout(200)
        p2.screenshot(path=str(A/'5_tastiera.png'))
        print('focus visibile', p2.evaluate("(()=>{const r=document.activeElement.getBoundingClientRect();return [r.top,r.bottom,innerHeight]})()"))
    b.close()
