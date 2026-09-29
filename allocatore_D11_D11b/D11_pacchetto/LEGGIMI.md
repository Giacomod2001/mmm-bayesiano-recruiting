# D11 — pacchetto di lavoro

Il repo `Tesi-MMM` e' privato e la tua sessione non lo vede: qui dentro c'e' tutto il
necessario per i passi 1, 2 e 3 di D11. Leggi per primo
`ALLOCATOR_cosa_fare_2026-09-17.md`: e' il quadro completo, e la sua ultima sezione ha le
regole di lavoro del progetto, che valgono anche per te.

---

## 1. Via libera alla correzione del §0. Verificata indipendentemente.

**Hai ragione, ed e' un errore nella specifica originale del test.** La prova e' nel codice,
non nei dati: `genera_dati_simulati.py` ricostruito con G4, passo 7 di `genera()`,
righe 1056-1061:

```python
totale_atteso = organico_tot / (1.0 - S)       # non dipende dalla spesa dei media
grezzo = float(risposta_grezza[ch].sum())      # dipende dalla spesa
beta[ch] = quote_ch[ch] * totale_atteso / max(grezzo, 1e-12)
risposta[ch] = beta[ch] * risposta_grezza[ch]  # = quote_ch[ch] * totale_atteso
```

`grezzo` si semplifica. Il contributo di ogni canale e' `quota_kpi x totale_atteso` per
costruzione, qualunque sia il budget. Il passo 3 come era scritto avrebbe prodotto cinque
numeri identici. **La correzione a `beta` fisso e' approvata.**

**Il tuo passo 2 e' corretto, e l'ho verificato.** Le impressioni sono lineari nella spesa:
riga 974, `impr = sp / CAMPAGNE[cp]["cpm"] * 1000.0`, cpm costante per campagna, nessuna
pressione d'asta. Quindi scalare la spesa del canale di `(1+d)` scala davvero impressioni e
adstock di `(1+d)` — purche' il riparto scali TUTTE le campagne del canale dello stesso
fattore, il che tiene costante il cpm miscelato. L'unica non linearita' che resta e' Hill,
che e' esattamente quella che vogliamo misurare.

**Due cose da aggiungere al documento prima di committarlo.**

(a) Con `beta` fisso non stiamo piu' leggendo un mondo che il generatore produrrebbe: stiamo
valutando **la superficie di risposta implicita nei parametri veri di quel mondo**. E'
legittimo ed e' l'unica strada, ma e' un'altra cosa e va dichiarato.

(b) La tua scoperta e' anche **un limite dello strumento** che va nel capitolo 7, e nessuno
l'aveva notato: *il simulatore e' stato costruito per verificare il recupero di una verita'
nota, non per rispondere a domande controfattuali sul budget; la calibrazione di `beta` sulla
quota dichiarata rende il contributo dei media indipendente dalla spesa per costruzione.*
Scrivilo, e' un risultato.

## 2. Il [GAP] dello scenario (c) e' chiuso

`estratto_6.1_6.2_vincoli_allocatore.md` contiene il testo che ti mancava. In sintesi:
limite di variazione **+-30%** su ogni canale, piu' un **pavimento di spesa su LinkedIn Ads**.
L'allocatore attuale porta Google Ads al massimo e taglia al minimo Subito Lavoro, Altre job
board e Jooble.

**Attenzione, e va messo in pre-registrazione: neanche l'allocatore vecchio quadra.** Google
+30% sono 381.384 EUR sul mondo 42; i tre tagli al -30% ne liberano 112.945. Quindi:

- esegui (c) scalando l'alzata di Google a cio' che i tagli liberano, stessa logica di (b),
  cosi' anche (c) e' a spesa totale costante;
- riporta il confronto **per euro spostato**, perche' (b) muove circa il 2% del budget e (c)
  il 3,1%: i valori assoluti non sono comparabili. Il tuo `f_b = g_b/g_e` gia' normalizza (b)
  contro l'oracolo; per (c) serve il guadagno per euro.

## 3. Sulla previsione non cieca

Hai fatto la cosa giusta a dichiararlo, e la soluzione — caso 7 marcato come gia' visto,
conteggi dati due volte su 8 e sui 7 non visti — e' quella corretta.

Una sola cosa: il tuo `+9.471 EUR su 110.022 spostati` non e' stato riprodotto
indipendentemente. Citalo come **"calcolo dell'autore del 17 settembre, non riprodotto"**,
altrimenti entra un numero senza provenienza in un documento che sulla provenienza e'
severissimo.

## 4. Cosa c'e' in questo pacchetto

| file | a cosa serve |
|---|---|
| `ALLOCATOR_cosa_fare_2026-09-17.md` | il quadro completo, da leggere per primo |
| `proposta_budget.py` | la regola 90/10. Rilancialo per verificare di riottenere gli 8 riparti |
| `colab_griglia_D10.ipynb` | nel blob della cella 1: la catena di patch A + G1..G4 |
| `parametri_generazione.json` | i parametri di Hill per la previsione |
| `griglia_D10/` | draw e canali di D10 (casi 7 e 8) |
| `griglia/griglia_D1_*`, `griglia_D2_*` | draw e canali di D1 e D2 (casi 1-6) |
| `griglia/griglia_D0_osservativo_canali.csv` | il regime osservativo, per confronto |
| `preregistrazioni/` | le undici pre-registrazioni: usale come modello di formato |
| `RISULTATI_D10_...md` | la lettura di D10, se ti serve il contesto |
| `TESTO_6.4_7.3_...md` | il testo di tesi gia' scritto su questo materiale |
| `estratto_6.1_6.2_...md` | i vincoli dell'allocatore, per lo scenario (c) |

**Non c'e' il resto del repo**, quindi non committare: consegna patch o file, e al commit ci
pensa Giacomo. Il notebook `colab_griglia_D10.ipynb` e `colab_griglia.ipynb` non si toccano
mai: sono la provenienza che le pre-registrazioni citano.

## 5. Promemoria sulla catena di patch

Le sostituzioni della catena A sono **cumulative** (`_src = _src.replace(...)`). Applicarle
al file originale una per una e' l'errore classico: la numero 4 inserisce un blocco che la 7
e la 8 riscrivono. Il cancello di fedelta': l'impronta del generatore ricostruito con G4 deve
essere **`c57be0b1e94c0bbd`**. Se non torna, fermati.
