# ============================================================================
# DIAGNOSTICA D12 - perche' l'impronta del mondo blackout non torna
# ============================================================================
# Da incollare in una cella NUOVA del notebook D12 gia' aperto su Colab, DOPO
# che la cella 1 e' stata eseguita (serve solo che il generatore sia stato
# scritto in /content/mmm-bayesiano-recruiting/). Non fitta niente, non tocca
# niente su Drive, ci mette una ventina di secondi.
#
# Risponde a tre domande:
#   1. quale dei sette file media differisce, e di quanto
#   2. se a differire sono le colonne che il modello VEDE (spesa, impressioni)
#      oppure quelle che non vede (conversioni_piattaforma)
#   3. se i numeri sostanziali del disegno - quota vera, spesa tolta, costo -
#      sono gli stessi calcolati in locale
import hashlib, json, os, subprocess, sys

REPO = '/content/mmm-bayesiano-recruiting'
GEN = os.path.join(REPO, 'genera_dati_simulati.py')
FM = ['google_ads_settimanale.csv', 'meta_ads_settimanale.csv',
      'linkedin_ads_settimanale.csv', 'indeed_settimanale.csv',
      'subito_lavoro_settimanale.csv', 'jooble_settimanale.csv',
      'altre_job_board_settimanale.csv']

# le impronte per file calcolate in locale il 21/9/2026 (numpy 2.4.1)
LOCALI = {
    'google_ads_settimanale.csv': ('ca2feca8ee8d9550', 744913),
    'meta_ads_settimanale.csv': ('60f3cfdf7a880588', 694113),
    'linkedin_ads_settimanale.csv': ('6124ed2aa15970a4', 634718),
    'indeed_settimanale.csv': ('830209bbce483c15', 505612),
    'subito_lavoro_settimanale.csv': ('41591cd2cf0c33dd', 491451),
    'jooble_settimanale.csv': ('91c2d51f59969afb', 433038),
    'altre_job_board_settimanale.csv': ('1b2520c373e141f3', 522282),
}
ATTESA_COMPLESSIVA = 'b7a2b625ffc9a013'

import numpy as np
import pandas as pd
print('numpy  :', np.__version__)
print('pandas :', pd.__version__)
print('python :', sys.version.split()[0])
print()

for flag, cart in (([], 'mondo_0042'), (['--blackout'], 'mondo_0042_blackout')):
    r = subprocess.run([sys.executable, GEN, '--seed-mondo', '42'] + flag, cwd=REPO,
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise SystemExit('generatore fallito: ' + (r.stderr or r.stdout)[-400:])
base = os.path.join(REPO, 'dati_simulati_mondi', 'mondo_0042', 'modello')
bk = os.path.join(REPO, 'dati_simulati_mondi', 'mondo_0042_blackout', 'modello')

print('=' * 78)
print('1. IMPRONTE PER FILE, mondo 42 blackout')
print('=' * 78)
h = hashlib.sha256()
diversi = []
for f in FM:
    b = open(os.path.join(bk, f), 'rb').read()
    h.update(b)
    mio = hashlib.sha256(b).hexdigest()[:16]
    atteso, byte_attesi = LOCALI[f]
    uguale = (mio == atteso)
    if not uguale:
        diversi.append(f)
    print('  %-32s %s  %7d byte   %s' %
          (f, mio, len(b), 'uguale' if uguale else
           'DIVERSO (locale %s, %d byte)' % (atteso, byte_attesi)))
print('  %-32s %s   (attesa %s)' % ('=> complessiva', h.hexdigest()[:16], ATTESA_COMPLESSIVA))
print()
print('  file diversi: %d su 7 -> %s' % (len(diversi), ', '.join(diversi) or 'nessuno'))

print()
print('=' * 78)
print('2. QUALI COLONNE DIFFERISCONO fra il mondo base e il mondo blackout')
print('=' * 78)
print('   (il modello riceve spesa e impressioni; conversioni_piattaforma NON')
print('    entra nel fit: e\' il benchmark attribuito, e il KPI viene dal file')
print('    candidature_settimanali.csv)')
print()
for f in FM:
    a = pd.read_csv(os.path.join(base, f))
    b = pd.read_csv(os.path.join(bk, f))
    chiavi = ['settimana', 'regione', 'campagna']
    m = a.merge(b, on=chiavi, suffixes=('_base', '_bk'), how='inner')
    riga = ['%-32s righe comuni %5d' % (f, len(m))]
    for col in ('spesa', 'impressioni', 'clic', 'conversioni_piattaforma'):
        d = (m[col + '_base'] != m[col + '_bk']).sum()
        riga.append('%s %d' % (col[:5], int(d)))
    print('  ' + '  '.join(riga))

print()
print('=' * 78)
print('3. I NUMERI SOSTANZIALI DEL DISEGNO')
print('=' * 78)
j = json.load(open(os.path.join(REPO, 'dati_simulati_mondi', 'mondo_0042_blackout',
                                'verita', 'parametri_generazione.json'), encoding='utf-8'))
sc = j['scenario_blackout']
c = sc['costo_del_disegno']
ATTESI = [('quota vera di questo mondo (%)', sc['quota_media_vera_di_questo_mondo_pct'], 17.9884),
          ('quota vera del mondo base (%)', sc['quota_media_vera_mondo_base_pct'], 18.5),
          ('spesa tolta totale (EUR)', sc['spesa_tolta_totale_eur'], 125463.37),
          ('candidature vere perse', c['candidature_vere_perse'], 5339.0),
          ('contributo vero, mondo base', c['contributo_vero_totale_mondo_base'], 158330.7),
          ('contributo vero, blackout', c['contributo_vero_totale'], 152991.7),
          ('candidature osservate', c['candidature_osservate'], 850576)]
for nome, qui, locale in ATTESI:
    ok = abs(float(qui) - float(locale)) <= max(0.05, abs(float(locale)) * 1e-6)
    print('  %-34s %14s   locale %14s   %s' % (nome, qui, locale, 'uguale' if ok else 'DIVERSO'))
print('  regioni trattate:', ', '.join(sc['regioni_trattate']))
print('  blocchi 1-based :', sc['blocchi_1based_inclusivi'])
print()
print('Incolla TUTTO questo in chat.')
