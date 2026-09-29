# R1 — sette strategie di riallocazione sugli otto casi di D11: risultati

**NESSUN RAMO.** Nessuna delle tre righe della regola del §5 corrisponde. Le tre condizioni sono
esclusive ma **non esaustive**, e i risultati sono caduti nello spazio che nessuna copre:

- riga 1: nessuna strategia ha `g%` mediano > 0 **e** percentile ≥ 0,90 in almeno 6 casi su 8.
  Le dieci letture hanno 0 casi su 8 con percentile ≥ 0,90;
- riga 2: cinque letture perdono meno dello 0,10% mediano (le tre soglie di S1, S2 e S5), **ma
  nessuna** muove meno di 10.000 EUR mediani;
- riga 3: non tutte perdono più dello 0,10%: quelle stesse cinque no.

**La regola non si sana a posteriori** (§7, punto 1): non si sceglie il ramo «più vicino» e non si
aggiunge una riga. Si riportano le cifre, e nessuna delle tre conclusioni registrate si può scrivere.

**Previsione dichiarata** (ramo 2, con S4 la migliore fra quelle che muovono e S1 a 0,80 che quasi non
muove mai): **smentita in tutte e tre le parti.**
- Il ramo 2 non è selezionato.
- La migliore è S5 (+0,087% mediano); S4 perde lo 0,241%.
- S1 muove in tutti gli otto casi a tutte e tre le soglie, perché `P(A > B)` non scende mai sotto
  0,935.

Il ramo che la pre-registrazione indicava come smentita, il ramo 1, non si è verificato.

**Il ramo stampato dallo script, e una correzione.** Nella prima versione `studio_R1.py` stampava
«RAMO 3» perché il ramo 3 era l'`else` finale, e non ne verificava la condizione. Il 23 settembre lo
script è stato corretto perché applichi la regola come è scritta: verifica anche la riga 3 e, se non
corrisponde nessuna riga, stampa «NESSUN RAMO» con il motivo riga per riga. Nessuna soglia è
cambiata. Rieseguito, lo script riscrive `R1_risultati.csv` **identico al byte** (sha256
`2c7578261626d397…`).

---

## Le sei avvertenze del §9, prima di ogni tabella

1. **ROI medio, non marginale** (§0). Nessuna di queste strategie può correggere l'errore
   diagnosticato in D11: può farlo solo la macchina marginale, cioè M1, mai eseguito.
2. **Otto casi, ma sei mondi distinti**: il 103 compare tre volte. I casi non sono indipendenti, e
   questo vale per ogni mediana che segue.
3. **`beta` fisso**: si valuta la superficie di risposta implicita nei parametri veri del mondo, non
   un mondo nuovo.
4. **Sette strategie, dieci letture sugli stessi otto casi.** La molteplicità è reale, e la soglia
   severa la governa solo in parte. Sono riportate tutte e dieci.
5. **Il codice di valutazione di D11.** Al momento del calcolo non era nel repository, e le cifre di
   D11 sono state riprodotte da una ricostruzione indipendente (§2-bis). Il codice originale è stato
   ritrovato il 22 settembre (`allocatore_D11_D11b/`). Il cancello qui sotto dice su che cosa la
   ricostruzione coincide e su che cosa no.
6. **I draw sono in float32.** Ogni quantità derivata è calcolata in float64.

---

## Il cancello del §2-bis: non superato su una colonna

La macchina ricostruita, applicata ai riparti di D11, doveva riprodurre la tabella di D11 caso per
caso, con le tolleranze fissate prima (`R1_cancello_D11.csv`).

| Colonna | Casi entro la tolleranza |
|---|:---:|
| `g_b` % (90/10), ±0,010 punti | 8/8 |
| `g_c` % (allocatore), ±0,010 punti | 8/8 |
| nullo, 90° percentile, ±1% | 8/8 |
| `f_b`, ±0,010 | 8/8 |
| EUR mossi (90/10), ±1 EUR | 8/8 |
| EUR mossi (allocatore), ±1 EUR | 8/8 |
| **`p_b`, ±0,010** | **5/8** |

Sui conteggi, allocatore in perdita 8 su 8, `V` = 3, `S` = 0 e `W` = 8 tornano. Anche il contributo
del non far niente torna: fra 158.329,1 e 158.330,8.

**I tre casi fuori tolleranza su `p_b`:**

| Caso | `p_b` ricostruito | `p_b` pubblicato | Scarto |
|---|---:|---:|---:|
| D2/102 | 0,835 | 0,880 | −0,045 |
| D2/103 | 0,530 | 0,560 | −0,030 |
| D10/42 | 0,665 | 0,690 | −0,025 |

**Le conseguenze registrate al §2-bis, applicate senza margini:**
1. la ricostruzione non è stata ritoccata;
2. lo scarto è riportato caso per caso qui sopra, con il codice (`riallocazione_R1/cancello_D11.py`);
3. nel testo va dichiarato che il `p_b` di D11 citato nel capitolo 6 **non è stato riprodotto**, con
   lo scarto misurato (fino a 0,045). Il paragrafo dell'Appendice A del 22 settembre lo fa già;
4. R1 è stato eseguito comunque, e ogni confronto con la 90/10 e con l'allocatore porta accanto
   questo scarto. Riguarda solo la colonna `p`: `g%`, `f` ed EUR sono riprodotti.

**La causa è nota dal codice ritrovato** (nota del 22/9 nella pre-registrazione). Nell'originale la
mossa 90/10 e il controllo nullo leggono la stessa spesa da due fonti, una arrotondata al centesimo e
l'altra no, e i quasi-pareggi cadono da una parte o dall'altra per l'ultima cifra. Con i pareggi
trattati esattamente la mediana di `p_b` è **0,547**, contro lo 0,563 pubblicato.

---

## Le mediane sugli otto casi

Tutte e dieci le letture, più i due riferimenti di D11 ricalcolati sulla stessa macchina.

| Strategia | `g%` mediano | Casi > 0 | EUR mossi mediani | `p` mediano | `p` ≥ 0,90 | `f` mediano | Candidature per EUR |
|---|---:|:---:|---:|---:|:---:|---:|---:|
| S1 freno 0,70 | −0,082% | 3/8 | 78.191 | 0,547 | 0/8 | −0,125 | −0,00164 |
| S1 freno 0,80 | −0,082% | 3/8 | 78.191 | 0,547 | 0/8 | −0,125 | −0,00164 |
| S1 freno 0,90 | −0,082% | 3/8 | 78.191 | 0,547 | 0/8 | −0,125 | −0,00164 |
| S2 taglia per certezza | −0,082% | 3/8 | 76.031 | 0,547 | 0/8 | −0,124 | −0,00164 |
| S3 passo 1/2 | −0,485% | 0/8 | 61.562 | 0,450 | 0/8 | −0,746 | −0,01225 |
| S3 passo 1/4 | −0,209% | 0/8 | 30.781 | 0,340 | 0/8 | −0,542 | −0,01056 |
| S4 dentro il draw | −0,241% | 2/8 | 62.900 | 0,522 | 0/8 | −0,364 | −0,00571 |
| **S5 quinto percentile** | **+0,087%** | 4/8 | 76.904 | 0,665 | 0/8 | 0,227 | +0,00358 |
| S6 tetto 5% | −0,132% | 0/8 | 20.521 | 0,318 | 0/8 | −0,487 | −0,01001 |
| S7 mossa diffusa | −0,392% | 0/8 | 78.191 | 0,378 | 0/8 | −0,587 | −0,00802 |
| *90/10 (D11)* | *−0,082%* | *3/8* | *78.191* | *0,547* | *0/8* | *−0,125* | *−0,00164* |
| *allocatore (D11)* | *−1,261%* | *0/8* | *123.123* | *0,343* | *0/8* | *−1,396* | *−0,01591* |

Oracolo di D11 come riferimento: +0,72% mediano. Avvertenze 2 e 4: sei mondi distinti, dieci
letture.

---

## Caso per caso

`g%`, guadagno sul contributo vero in percentuale del non far niente:

| Strategia | D1/101 | D1/103 | D1/105 | D1/107 | D2/102 | D2/103 | D10/42 | D10/103 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 freno 0,70 | −0,149 | −0,120 | +0,356 | −0,849 | +0,364 | −0,082 | +0,173 | −0,082 |
| S1 freno 0,80 | −0,149 | −0,120 | +0,356 | −0,849 | +0,364 | −0,082 | +0,173 | −0,082 |
| S1 freno 0,90 | −0,149 | −0,120 | +0,356 | −0,849 | +0,364 | −0,082 | +0,173 | −0,082 |
| S2 taglia per certezza | −0,148 | −0,107 | +0,355 | −0,717 | +0,356 | −0,082 | +0,173 | −0,082 |
| S3 passo 1/2 | −0,371 | −0,485 | −0,505 | −0,443 | −0,384 | −0,485 | −0,492 | −0,485 |
| S3 passo 1/4 | −0,151 | −0,209 | −0,219 | −0,187 | −0,158 | −0,209 | −0,213 | −0,209 |
| S4 dentro il draw | −0,229 | −0,341 | −0,283 | −0,878 | +0,113 | −0,253 | −0,006 | +0,097 |
| S5 quinto percentile | +0,345 | −0,277 | +0,356 | 0,000 | +0,364 | −0,082 | +0,173 | −0,082 |
| S6 tetto 5% | −0,094 | −0,132 | −0,139 | −0,117 | −0,098 | −0,132 | −0,135 | −0,132 |
| S7 mossa diffusa | −0,398 | −0,310 | −0,537 | −1,430 | −0,189 | −0,386 | −0,740 | −0,126 |
| *90/10 (D11)* | −0,149 | −0,120 | +0,356 | −0,849 | +0,364 | −0,082 | +0,173 | −0,082 |
| *allocatore (D11)* | −1,033 | −1,261 | −1,298 | −1,178 | −1,060 | −1,261 | −1,271 | −1,261 |

`p`, percentile dentro il controllo nullo costruito con la stessa cifra in euro della strategia (n/d =
nessuna mossa):

| Strategia | D1/101 | D1/103 | D1/105 | D1/107 | D2/102 | D2/103 | D10/42 | D10/103 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 freno 0,70 | 0,565 | 0,500 | 0,890 | 0,470 | 0,835 | 0,530 | 0,665 | 0,530 |
| S1 freno 0,80 | 0,565 | 0,500 | 0,890 | 0,470 | 0,835 | 0,530 | 0,665 | 0,530 |
| S1 freno 0,90 | 0,565 | 0,500 | 0,890 | 0,470 | 0,835 | 0,530 | 0,665 | 0,530 |
| S2 taglia per certezza | 0,565 | 0,500 | 0,890 | 0,405 | 0,835 | 0,530 | 0,665 | 0,530 |
| S3 passo 1/2 | 0,465 | 0,450 | 0,455 | 0,425 | 0,550 | 0,450 | 0,425 | 0,450 |
| S3 passo 1/4 | 0,435 | 0,335 | 0,375 | 0,335 | 0,500 | 0,335 | 0,345 | 0,335 |
| S4 dentro il draw | 0,495 | 0,470 | 0,550 | 0,345 | 0,785 | 0,490 | 0,595 | 0,710 |
| S5 quinto percentile | 0,840 | 0,400 | 0,890 | n/d | 0,835 | 0,530 | 0,665 | 0,530 |
| S6 tetto 5% | 0,340 | 0,305 | 0,360 | 0,290 | 0,480 | 0,305 | 0,330 | 0,305 |
| S7 mossa diffusa | 0,435 | 0,385 | 0,370 | 0,315 | 0,600 | 0,370 | 0,340 | 0,500 |
| *90/10 (D11)* | 0,565 | 0,500 | 0,890 | 0,470 | 0,835 | 0,530 | 0,665 | 0,530 |
| *allocatore (D11)* | 0,435 | 0,290 | 0,355 | 0,345 | 0,435 | 0,290 | 0,340 | 0,290 |

Per la 90/10 i `p` di D2/102, D2/103 e D10/42 differiscono da quelli pubblicati in D11: è lo scarto
del cancello.

---

## Che cosa si legge, senza che selezioni un ramo

- **S1 non frena mai.** `P(A > B)` va da 0,935 a 1,000 in tutti gli otto casi, quindi il cancello di
  certezza si apre sempre e S1 coincide con la 90/10 a tutte e tre le soglie. Il posteriore è
  **sicuro** della direzione anche nei casi in cui la direzione perde: la certezza del posteriore non
  separa le mosse buone da quelle cattive.
- **S3 perde in proporzione alla dose.** Un quarto della mossa dell'allocatore perde lo 0,209%, metà
  lo 0,485%, la mossa intera l'1,261%. Ridurre il passo riduce la perdita, ma non la trasforma mai in
  guadagno: è la direzione a essere sbagliata, non solo la dose.
- **S5 è la sola con `g%` mediano positivo** (+0,087%, positiva in 4 casi su 8). Il suo percentile
  non raggiunge mai 0,90 (massimo 0,89). Con dieci letture sugli stessi casi, una mediana positiva di
  questa grandezza è compatibile con il caso (avvertenza 4), e **non si legge come una strategia che
  funziona** (§7, punti 1 e 3).
- **Le strategie che muovono poco perdono comunque.** S6 muove 20.521 EUR mediani e perde lo 0,132%.
  S3 a un quarto muove 30.781 EUR e perde lo 0,209%. Nessuna scende sotto i 10.000 EUR della riga 2.

---

## Ridurre l'errore di attribuzione non mette in ordine i canali (§10, punto 5)

Tutti i valori sono ricalcolati dai CSV della griglia: `E` mediano, e `rho` di Spearman mediano fra
ordine stimato e ordine vero.

| Disegno | `E` mediano | `rho` mediano |
|---|---:|---:|
| D0 osservativo | +22,92 | −0,036 |
| D1 geo canonico | +15,53 | +0,339 |
| D10 calendario a 4 giri | +8,28 | +0,036 |
| D2 calendario a rotazione | +7,18 | +0,107 |
| D12 blackout totale | +5,38 | −0,054 |
| Mondo randomizzato | −4,17 | +0,268 |

L'errore di livello scende da 22,9 punti a meno di 6, e `rho` resta vicino a zero in ogni disegno:
perfino nel mondo randomizzato, dove la copertura è 8 su 8, vale +0,27. È la premessa della
previsione (§6), e i valori ricalcolati coincidono con quelli citati lì alla seconda cifra.

---

## Proposta di righe per il capitolo 7.2 (§10, punto 6), da approvare

> Sugli otto casi di riallocazione valutati contro la verità, nessuna delle sette regole provate
> batte con regolarità le mosse casuali della stessa entità. La migliore guadagna lo 0,09% mediano
> senza mai superare il 90° percentile del controllo nullo, e la versione più prudente dell'allocatore,
> un quarto della sua mossa, perde comunque lo 0,21%. Il criterio fissato prima del calcolo non
> seleziona nessuno dei tre esiti previsti: alcune regole perdono poco, ma solo spostando quanto la
> regola 90/10, e questo lavoro non ha una regola di riallocazione verificata da raccomandare.

---

## File

- `riallocazione_R1/cancello_D11.py` e `R1_cancello_D11.csv`: il cancello del §2-bis;
- `riallocazione_R1/studio_R1.py` (con la correzione del 23/9 alla stampa del ramo) e
  `R1_risultati.csv`: le dieci letture sugli otto casi, 96 righe;
- `riallocazione_R1/controllo_draw_R1.py` e `R1_controllo_draw.csv`: il passo 0 (commit `08bc420`).

Si rieseguono con la cartella del generatore ricostruito **con G6** (impronta `8f86eb032d0113c0`),
che senza flag riproduce il mondo base al bit (controllo 1 di D12):
`python riallocazione_R1/studio_R1.py <cartella con genera_dati_simulati.py G6>`.

*File dei risultati, scritto il 23 settembre 2026 dopo il calcolo. Ogni cifra viene dai CSV di
`riallocazione_R1/` o dai CSV della griglia citati.*
