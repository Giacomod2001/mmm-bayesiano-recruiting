# esperimenti/

Varianti di `genera_dati_simulati.py` per i dataset di controllo. Ognuna cambia una
cosa sola: seed 42, quota target 18,5%, prior e resto identici. Ogni script scrive in
`dati_simulati/` accanto a se stesso (le cartelle seguono `os.path.dirname(__file__)`).

**`genera_casuale.py`** (`--suffisso _casuale`) - `CORR_SPESA_STAGIONALITA_TARGET` da
0.50 a 0.0: la spesa non segue piu' la stagione (kappa da 1,0-2,2 a ~0). Risponde a:
quanto dell'identificazione dipende dalla correlazione fra budget e stagionalita'?
Cambia anche `CORR_BANDA`, ma e' costante morta, mai usata. Residuo: la griglia di
kappa e' unilaterale e non cancella la correlazione del rumore AR(1), restano 0,157 su
Google Ads (media 0,071 sui sette canali, contro 0,50 nell'originale).

**`genera_casuale2.py`** (`--suffisso _casuale2`) - come sopra piu' la griglia di kappa
bilaterale, `linspace(-5.0, 5.0, 239)` invece di `linspace(0.0, 5.0, 120)` (stesso passo,
0,042). Cinque canali su sette scelgono kappa negativo e cancellano la correlazione del
rumore: max |corr| 0,006 contro 0,157. E' la versione da usare quando serve correlazione
realizzata nulla e non solo assenza di accoppiamento strutturale; `_casuale` resta per
confronto. Spesa 3.629.777 EUR contro 3.630.786 di `_casuale`, quota invariata.

**`genera_pause.py`** (`--suffisso _pause`) - `settimane_spente` nel dict `CANALI`: 11
settimane spente su 104 per canale, estratte indipendentemente con un rng dedicato
(`SEED + 99`, non consuma lo stream principale). La spesa segue la stagione come
nell'originale. Risponde a: le pause sfalsate bastano a separare canali altrimenti
collineari fra loro? Spesa totale -7,1%, quota vera invariata a 0,185.

**`genera_geo.py`** (`--suffisso _geo`) - geo-experiment: su Google Ads e LinkedIn Ads la quota
regionale va a 0 in 6 regioni su 20 per due blocchi da 8 settimane (rng `seed + 77`, regioni e
blocchi indipendenti fra i due canali), con le superstiti rinormalizzate: il totale nazionale
settimanale non cambia. Risponde a: basta il contrasto geo x tempo a identificare i canali?

Ingestion: i CSV di canale omettono le settimane in pausa invece di scriverle a 0 (93
su 104). Reindicizzare sul calendario di `stagionalita.csv` prima di allineare i canali.
`_geo`: nei cinque canali di controllo spesa, impressioni e clic sono bit-identici all'originale,
`conversioni_piattaforma` no (la Poisson dell'outcome sposta lo stream rng; scarto sotto lo 0,7%).
