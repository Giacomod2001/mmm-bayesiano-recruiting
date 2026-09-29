# D11 — risultati: seguire la regola 90/10 non fa guadagnare

**17 settembre 2026.** Eseguito secondo `PREREGISTRAZIONE_D11_riparto_controfattuale.md` (v2), scritta
e chiusa prima di calcolare queste cifre. Soglie e rami non sono stati toccati dopo.

---

## In prima riga, come richiesto dalla pre-registrazione

**La regola non batte il controllo nullo. In nessuno degli otto casi.** Il ramo calcolato è il **4 —
LA REGOLA NON GUADAGNA**: `S = 0` (mai sopra il 90° percentile del nullo) e `V = 3` (guadagna in tre
casi su otto). Sui sette casi non visti: `V = 2`, `S = 0`.

**E la mia previsione è smentita.** Avevo dichiarato il ramo 3: `V >= 6` e `S <= 2`. La seconda metà
regge (`S = 0`), la prima no: prevedevo che quasi tutti i casi guadagnassero qualcosa, e invece cinque
su otto **perdono**. Avevo sottovalutato che il canale tagliato non è sempre quello a marginale basso.

---

## 1. I numeri

Contributo incrementale vero dei media, in candidature. `beta` fisso al mondo non modificato: si
valuta la superficie di risposta implicita nei parametri veri del mondo, non un mondo nuovo (§0 della
pre-registrazione).

| caso | (a) attuale | (b) 90/10 | (c) allocatore vecchio | (d) nullo, mediana | (e) oracolo |
|---|---:|---:|---:|---:|---:|
| D1/101 | 158.329,5 | 158.092,8 | 156.693,7 | 157.946,6 | 159.402,1 |
| D1/103 | 158.329,8 | 158.140,1 | 156.333,6 | 158.109,8 | 159.368,9 |
| D1/105 | 158.330,8 | **158.895,0** | 156.274,9 | 157.843,2 | 159.622,6 |
| D1/107 | 158.329,7 | 156.986,3 | 156.464,7 | 156.986,3 | 160.102,2 |
| D2/102 | 158.329,1 | **158.906,3** | 156.650,1 | 157.611,9 | 159.576,4 |
| D2/103 | 158.329,8 | 158.199,6 | 156.333,6 | 158.109,8 | 159.368,9 |
| D10/42 *(già visto)* | 158.330,7 | **158.605,3** | 156.317,7 | 157.839,8 | 159.538,9 |
| D10/103 | 158.329,8 | 158.199,6 | 156.333,6 | 158.109,8 | 159.368,9 |

In percentuale del non far niente, con il percentile nel nullo e la frazione catturata:

| caso | `g_b` | `g_b` % | `g_c` % | nullo, 90° perc. | `p_b` | `f_b` | EUR mossi (b) / (c) |
|---|---:|---:|---:|---:|---:|---:|---:|
| D1/101 | −236,7 | −0,149% | −1,033% | +770,6 | 0,565 | −0,221 | 75.590 / 123.173 |
| D1/103 | −189,7 | −0,120% | −1,261% | +512,2 | 0,500 | −0,183 | 79.301 / 125.451 |
| D1/105 | **+564,2** | +0,356% | −1,298% | +564,2 | 0,890 | 0,437 | 77.081 / 117.643 |
| D1/107 | **−1.343,4** | −0,848% | −1,178% | +679,6 | 0,470 | −0,758 | 145.079 / 123.074 |
| D2/102 | **+577,2** | +0,365% | −1,060% | +601,9 | 0,880 | 0,463 | 74.737 / 116.788 |
| D2/103 | −130,2 | −0,082% | −1,261% | +512,2 | 0,560 | −0,125 | 79.301 / 125.451 |
| D10/42 | **+274,6** | +0,173% | −1,271% | +753,4 | 0,690 | 0,227 | 76.726 / 112.945 |
| D10/103 | −130,2 | −0,082% | −1,261% | +512,2 | 0,530 | −0,125 | 79.301 / 125.451 |
| **mediana** | | **−0,082%** | **−1,261%** | | **0,563** | **−0,125** | |

Conteggi pre-registrati: `V = 3`, `S = 0`, `W = 8` su otto casi; `V = 2`, `S = 0`, `W = 7` sui sette
non visti. Soglia di identificazione 6 su 8 (5 su 7).

## 2. La cifra che chiude la questione

**Muovere budget a caso guadagna nel 35% delle estrazioni** (mediana sugli otto casi delle 200
ripartizioni casuali: fra il 27% e il 42,5%). **La regola guadagna in 3 casi su 8, cioè il 37,5%.**

Sono lo stesso numero. E il percentile mediano della regola dentro il proprio nullo è **0,563**: la
regola batte poco più della metà delle mosse casuali. È una monetina.

Va detto per intero, perché è meno banale di così: **nemmeno muovere a caso è neutro.** Il nullo ha
mediana negativa in tutti e otto i casi (da −220 a −1.343 candidature): due canali presi a sorte
peggiorano più spesso di quanto migliorino, perché la spesa attuale non è lontana da un ottimo locale.
La regola non fa peggio del caso. Non fa nemmeno meglio.

## 3. Perché: la regola sceglie sul livello del ROI, e conta il marginale

Rendimento marginale vero, nel mondo e al passo effettivi della mossa, in euro di contributo per euro
di spesa. Il lato tagliato è pesato per gli euro.

| caso | alzato | marg. | tagliato | marg. | netto per EUR | saturazione dell'alzato |
|---|---|---:|---|---:|---:|---:|
| D1/101 | Indeed | 1,12 | Google + LinkedIn | 1,25 | **−0,13** | 71% |
| D1/103 | Indeed | 1,07 | LinkedIn + Google | 1,17 | **−0,10** | 72% |
| D1/105 | Indeed | 1,09 | LinkedIn | 0,80 | **+0,29** | 71% |
| D1/107 | Meta Ads | 1,02 | Google Ads | 1,39 | **−0,37** | 38% |
| D2/102 | Indeed | 1,11 | LinkedIn | 0,81 | **+0,31** | 71% |
| D2/103 | Indeed | 1,07 | Meta Ads | 1,14 | **−0,07** | 72% |
| D10/42 | Indeed | 1,02 | LinkedIn | 0,88 | **+0,14** | 71% |
| D10/103 | Indeed | 1,07 | Meta Ads | 1,14 | **−0,07** | 72% |

Il netto è positivo **esattamente quando** il marginale del canale alzato supera quello del canale
tagliato, e mai altrimenti. Nessuna sorpresa: è aritmetica. La sorpresa è dove cade.

**Indeed, che la regola alza in sette casi su otto, sta al 71–72% di saturazione in ogni mondo.** Il
suo ROI medio è il più alto o quasi (2,52 contro 1,73 di portafoglio), quindi il cancello 90/10 lo
promuove; il suo euro marginale rende **1,02–1,12**, cioè meno di quanto rendano gli euri che si
tolgono a Google (1,17–1,39) o a Meta (1,14). La previsione del §8 di `ALLOCATOR_cosa_fare` era
giusta, ed è questa: **la correzione marginale colpisce proprio il verdetto più frequente del
cancello.**

**E c'è un dettaglio più netto ancora.** L'oracolo, in tutti e otto i casi, prende i soldi da
**LinkedIn Ads**. I tre casi in cui la regola guadagna sono esattamente i tre in cui **anche lei**
taglia LinkedIn. I cinque in cui perde sono i cinque in cui taglia Google o Meta.

> Il guadagno della regola, quando c'è, viene interamente dal lato del taglio, e solo quando il taglio
> cade sul canale giusto. Il lato dell'alzata — il verdetto che la regola pronuncia con il 90% dei
> draw d'accordo — non contribuisce mai positivamente al saldo.

## 4. L'allocatore vecchio è peggio, e di molto

`W = 8`: la regola 90/10 batte l'allocatore della §6.2 in **tutti e otto** i casi, per euro spostato.
L'allocatore vecchio perde in tutti e otto, fra **−1,03% e −1,30%** del contributo vero, cioè fra
−0,53 e −0,71 euro per euro spostato. Porta Google al massimo e taglia i tre job board al minimo: al
margine sono fra i canali che rendono di più. Muove anche il 50% di budget in più della regola
(≈120.000 EUR contro ≈78.000).

Questo non riabilita la regola: dice che il confronto giusto per lei non è l'allocatore vecchio ma il
non far niente, e con quello pareggia.

## 5. Quanto guadagno c'era da prendere

L'oracolo — la migliore fra le 42 coppie ordinate, stessa cifra spostata — guadagna una mediana di
**+0,72%** (fra +0,66% e +1,12%), cioè circa 1.140 candidature. La regola ne cattura una frazione
mediana **negativa** (`f_b` = −0,125).

L'oracolo è un tetto che nessuno può raggiungere: conosce le curve vere. Serve solo a dare la scala.
E la scala dice che il guadagno disponibile spostando il 2% del budget è **sotto l'1%** del contributo
dei media: anche l'allocazione perfetta, su questo mondo e con questa ampiezza di mossa, vale poco.

## 6. Che cosa questo risultato NON dice

1. **Non smentisce il cancello 90/10 come rilevatore di direzione.** Le 25 direzioni giuste su 27
   restano giuste *nel senso in cui erano state misurate*: il canale alzato ha davvero un ROI **medio**
   sopra la media di portafoglio. D11 misura un'altra cosa — se spostare denaro lì faccia guadagnare —
   e la risposta è no. Le due affermazioni convivono, e in tesi vanno scritte insieme: altrimenti la
   prima si legge come una promessa che la seconda smentisce.
2. **Non smentisce la precondizione sperimentale.** D11 non tocca il confronto fra regime osservativo
   e regime sperimentale: quello resta.
3. **Non dice che il passo del 15% sia sbagliato in sé.** Dice che un passo uniforme applicato a un
   canale saturo distrugge il margine: al passo pieno Indeed rende 1,02–1,12, contro il 2,52 del suo
   ROI medio.
4. **Non è un mondo che il generatore produrrebbe.** Con `beta` fisso si valuta la superficie di
   risposta implicita nei parametri veri di quel mondo (§0 della pre-registrazione). È l'unica strada
   possibile, ed è un'altra cosa.

## 7. La conseguenza pratica, in una riga

La §7 di `ALLOCATOR_cosa_fare` dichiarava che il cancello valida il verso e non la taglia, e che la
taglia giusta la potrà dare solo la macchina marginale. **D11 misura quanto costa quella lacuna: tutto
il guadagno.** Finché la taglia non viene dai marginali, la regola è difendibile come *rilevatore di
direzione* e non è difendibile come *procedura di riallocazione*.

## 8. I controlli di fedeltà

| # | Controllo | Esito |
|---|---|---|
| 1 | generatore ricostruito: 8 sostituzioni A cumulative, poi G1…G4 a fuzz 0 | impronta **`c57be0b1e94c0bbd`** = attesa |
| 2 | G5 senza `--riparto` è un no-op | 17 file su 17 bit-identici (mondo 42 base e mondo 103 calendario a 4 giri) |
| 3 | somma non zero in euro → errore | rifiutato, con il dettaglio per canale e la tolleranza |
| 4 | forma del percorso preservata | moltiplicatore settimanale costante entro 3,4·10⁻⁵ |
| 5 | gli otto riparti si riproducono da `proposta_budget.py` | 8 su 8 |
| 6 | doppia strada: generatore G5 contro calcolo analitico | scarto relativo massimo **3,8·10⁻⁷** |
| 7 | costanza di `K = beta × pop × mg` dai file | variazione relativa 3,3·10⁻⁴ … 6,3·10⁻³; scarto contro il `beta × pop × mg` esatto del generatore ≤ 2,1·10⁻⁴ |
| + | canali non toccati invariati | contributo vero identico a `+0,0` candidature |
| + | riparti applicati al mondo base | somma in euro entro ±0,03 EUR in tutti e otto i casi |

## 9. Come si rifanno questi conti

```
python studio_D11.py          # 8 casi x 5 ripartizioni, scrive D11_risultati.csv
python controlli_6_7.py       # controlli 6 e 7
```

Servono: il generatore ricostruito con la catena A + G1…G4 + **G5**
(`patch_G5_generatore_riparto.diff`), il pacchetto `D11_pacchetto` con i draw e
`proposta_budget.py`. Nessuna GPU, nessun fit: il generatore è numpy, ogni mondo è circa un secondo e
mezzo, l'intero studio meno di un minuto.

Il controllo nullo è riproducibile: `numpy.random.default_rng(20260917 + seme_mondo)`, 200 coppie
ordinate uniformi fra le 42, stessa cifra in euro della mossa (b). Le 1.600 differenze sono in
`D11_controllo_nullo.json`.

---

*Risultati. La pre-registrazione che li governa è in un file separato, datato prima.*
