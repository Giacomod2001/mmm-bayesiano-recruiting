# D11 e D11b — il codice di valutazione dell'allocatore, ritrovato

**Ritrovato il 22 settembre 2026.** Questa cartella era sul Desktop di Giacomo, dentro
OneDrive, con il nome `03_D11b/`. I file portano la data del 21 settembre 2026, ore 19:54. Il
giorno prima era stata cercata in tutto il progetto, anche fuori da git, e non era stata trovata:
la pre-registrazione di R1 (commit `08bc420`, §2-bis) registra che il codice di D11 «non esiste» e
che la macchina va ricostruita.

È conservata **esattamente come ritrovata**, 59 file su 59 identici al byte all'originale. Il
`.gitattributes` di questa cartella impedisce a git di normalizzare i fine riga, che cambierebbero i
byte.

## Che cosa contiene

| File | Che cos'è | sha256 (primi 16) |
|---|---|---|
| `studio_D11.py` | il codice che produsse le cifre di D11 citate nel Capitolo 6 | `60f6a8c0b4805cb8` |
| `D11_risultati.csv` | la sua uscita, caso per caso | `409bcf4728836e7b` |
| `g5/genera_dati_simulati.py` | il generatore con la patch **G5** (`--riparto`, `beta` fisso) | `c94aaee9d211d049` |
| `studio_D11b.py`, `colab_D11b.ipynb`, `PROMPT_D11b_allocatore_regole_alternative.md` | lo studio D11b dell'altra sessione (quattro regole alternative) | `84f6fdd9d099393b` |
| `D11_pacchetto/` | il pacchetto di lavoro di D11: `LEGGIMI.md`, un estratto delle Sezioni 6.1-6.2, i parametri di generazione, e copie di file già nel repository | — |

Dei 59 file, **50 sono già nel repository e sono identici** (le pre-registrazioni D0-D10, i CSV e i
draw della griglia, `colab_griglia_D10.ipynb`, `proposta_budget.py`). **Sono nuovi 9**: i quattro
file di D11 e i tre di D11b della tabella, più `D11_pacchetto/LEGGIMI.md`,
`D11_pacchetto/estratto_6.1_6.2_vincoli_allocatore.md` e `D11_pacchetto/parametri_generazione.json`.

Manca `D11_controllo_nullo.json`, che `studio_D11.py` scrive accanto a sé: non era nella cartella
ritrovata.

## Come si riesegue

`studio_D11.py` cerca tutto accanto a sé: `D11_pacchetto/` per i draw e i CSV, `g5/` per il
generatore. Dalla cartella:

```bash
python studio_D11.py
```

Riscrive `D11_risultati.csv` e scrive `D11_controllo_nullo.json` nella stessa cartella. **Per non
sovrascrivere l'originale ritrovato, eseguirlo su una copia.**

## Che cosa ha cambiato, il 22 settembre

1. **Il cancello di R1** (§2-bis della sua pre-registrazione) era stato superato da una ricostruzione
   indipendente, verificata contro la tabella pubblicata di D11: sei colonne su sette esatte su
   tutti e otto i casi. Ora c'è anche il codice originale, e il confronto si può fare sul codice e
   non solo sulle cifre stampate.
2. **Il `p_b` di D11.** Il codice originale calcola `p_b = (gd < gb).mean()`, riga 135: una sola
   convenzione, il minore stretto, la stessa adottata da R1. I casi D2/103 e D10/103 sono lo stesso
   calcolo e differiscono solo alla sesta cifra decimale del riparto (Meta Ads −8,444655 contro
   −8,444656); `D11_risultati.csv` riporta per loro 0,56 e 0,53. Il motivo, verificato nel codice:
   la coppia della 90/10 può essere estratta dal controllo nullo, e allora la mossa casuale dovrebbe
   coincidere con quella della regola. Ma le due mosse usano due fonti diverse della stessa spesa —
   la 90/10 quella del file dei canali, arrotondata al centesimo (`spesa_fit`, riga 81), il nullo
   quella del generatore (`eur_b_mondo`, riga 108) — e quindi differiscono all'ultima cifra. Con il
   minore stretto quei quasi-pareggi cadono sotto o sopra a seconda dell'arrotondamento. Il `p_b`
   di D11 è **instabile per quasi-pareggi**, non incoerente nella convenzione. La mediana calcolata con i pareggi trattati esattamente è 0,547; quella
   pubblicata è 0,563. La sostanza non cambia: la regola batte poco più della metà delle mosse
   casuali.
