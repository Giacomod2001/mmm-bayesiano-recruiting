# Pre-registrazione — D11: il riparto controfattuale. Seguire la regola 90/10 fa guadagnare?

**Versione 2, 17 settembre 2026. Definitiva.** Scritta prima di calcolare le cifre dei confronti.
La v1 poneva due domande all'autore; entrambe hanno avuto risposta ed è recepita qui: la correzione
del §0 è **approvata** e verificata indipendentemente dall'autore sul codice ricostruito (righe
1056-1061), e il buco sullo scenario (c) è **chiuso** (§2). I controlli di fedeltà del §7 sono stati
eseguiti e sono passati: le loro uscite sono in coda, al §10.

---

## 0. Una correzione al disegno, da approvare prima di tutto il resto

**Il confronto come specificato darebbe cinque numeri identici.** Non è un'opinione: è una proprietà
del generatore, verificabile sui file committati.

Al passo 7 di `genera()` (`genera_dati_simulati.py`, "calibrazione di beta sulla quota di contributo
media") il coefficiente di ogni canale è ricalibrato così:

```python
totale_atteso = organico_tot / (1.0 - S)          # non dipende dalla spesa dei media
grezzo  = float(risposta_grezza[ch].sum())        # dipende dalla spesa
beta[ch] = quote_ch[ch] * totale_atteso / max(grezzo, 1e-12)
risposta[ch] = beta[ch] * risposta_grezza[ch]     # = quote_ch[ch] * totale_atteso, SEMPRE
```

`beta` è scelto **proprio per cancellare** l'effetto della spesa: il contributo totale del canale
vale `quota_kpi/S x totale_atteso` qualunque sia la spesa. Verificato sul mondo 42 committato,
confrontando le quote di contributo vero misurate dai file con le costanti `quota_kpi`:

| Canale | quota di contributo misurata | `quota_kpi` / somma | differenza |
|---|---:|---:|---:|
| Google Ads | 30,0546% | 30,0546% | 0,0000 |
| Meta Ads | 24,5902% | 24,5902% | 0,0000 |
| LinkedIn Ads | 7,1038% | 7,1038% | 0,0000 |
| Indeed | 21,8579% | 21,8579% | −0,0000 |
| Subito Lavoro | 7,6503% | 7,6503% | 0,0000 |
| Jooble | 2,7322% | 2,7322% | 0,0000 |
| Altre job board | 6,0109% | 6,0109% | −0,0000 |

Coincidono a tutte le cifre. Quindi: rigenerare il mondo con `--riparto` e rileggere
`verita/contributo_vero.csv` restituirebbe **lo stesso identico totale** per (a), (b), (c), (d) ed (e).
Il test misurerebbe zero, e lo misurerebbe anche se la regola fosse ottima o pessima.

**La correzione, approvata.** Il controfattuale sensato tiene `beta` **fisso** ai valori calibrati
sul mondo non modificato, e lascia che la spesa agisca attraverso le curve di Hill:

```
1. genera il mondo base come sempre  ->  beta[ch] calibrato sulla spesa attuale
2. applica il riparto alla spesa     ->  impressioni x (1+d), adstock x (1+d)  (l'adstock e' lineare)
3. ricalcola la risposta con lo STESSO beta: risposta(t,g) = beta[ch] x pop_g x mg_g x hill((1+d) a)
```

È l'unico modo in cui «spostare budget» cambia il contributo vero, ed è coerente con il resto del
lavoro: il mondo resta lo stesso mondo, con gli stessi parametri veri, e cambia solo dove si spende.
Per lo stesso motivo anche la mezza saturazione `ec` resta quella del mondo non modificato: è una
proprietà del mondo, non della proposta di budget, e lasciarla muovere sposterebbe il metro insieme
alla cosa misurata.

**Che cosa stiamo misurando, detto con precisione.** Con `beta` fisso non stiamo più leggendo un
mondo che il generatore produrrebbe: stiamo valutando **la superficie di risposta implicita nei
parametri veri di quel mondo**. È legittimo, è l'unica strada, ed è un'altra cosa: va dichiarato
accanto a ogni cifra dei risultati, e va scritto nel testo che li commenta.

**E la scoperta è essa stessa un risultato, per il capitolo 7.** Nessuno l'aveva notata prima di
questo test: *il simulatore è stato costruito per verificare il recupero di una verità nota, non per
rispondere a domande controfattuali sul budget; la calibrazione di `beta` sulla quota dichiarata rende
il contributo dei media indipendente dalla spesa per costruzione.* È un limite dello strumento, non
un difetto di questo disegno, e va nel capitolo dei limiti insieme agli altri.
Senza questa correzione D11 non si può fare. Con questa correzione il numero letto non è più
`contributo_vero.csv` del mondo rigenerato, ma il contributo ricalcolato al passo 3; il file del mondo
base resta la fonte di `beta x pop_g x mg_g`, che si ricava dividendo il contributo vero per `hill`.

---

## 1. Domanda

Seguire la regola 90/10 — alzare del 15% i canali che rendono più della media di portafoglio in
almeno il 90% degli 8.000 draw, tagliare quelli che lo fanno in al più il 10%, a spesa totale
costante — fa guadagnare candidature vere rispetto al non far niente? E il guadagno si distingue dal
muovere la stessa cifra fra due canali a caso?

## 2. Disegno

Otto casi, quelli già fissati dalla griglia (mondo BASE, senza esperimento: l'esperimento era la fase
di misura, l'allocazione vale per l'esercizio normale):

| # | Origine | Mondo | Riparto della regola |
|--:|---|--:|---|
| 1 | D1 | 101 | Indeed +15,00; Google Ads −4,19; LinkedIn Ads −4,19 |
| 2 | D1 | 103 | Indeed +15,00; Google Ads −4,13; LinkedIn Ads −4,13 |
| 3 | D1 | 105 | Indeed +15,00; LinkedIn Ads −13,70 |
| 4 | D1 | 107 | Meta Ads +15,00; Google Ads −11,04 |
| 5 | D2 | 102 | Indeed +15,00; LinkedIn Ads −13,43 |
| 6 | D2 | 103 | Indeed +15,00; Meta Ads −8,44 |
| 7 | D10 | 42 | Indeed +13,95; LinkedIn Ads −15,00 |
| 8 | D10 | 103 | Indeed +15,00; Meta Ads −8,44 |

Cinque ripartizioni per caso, tutte sullo stesso mondo base e con `beta` fisso (§0):

- **(a) attuale** — il non far niente. È il riferimento.
- **(b) 90/10** — i riparti della tabella.
- **(c) allocatore vecchio** — dalla §6.2 della tesi: limite di variazione **±30%** per canale,
  Google Ads portato al massimo consentito, Subito Lavoro / Altre job board / Jooble tagliati al
  minimo. **Neanche (c) quadra da solo**: sul mondo 42 il +30% di Google vale 381.384 EUR mentre i tre
  tagli al −30% ne liberano 112.945. Quindi, **decisione presa adesso**: l'alzata di Google si scala a
  ciò che i tagli liberano, esattamente con la logica di (b), così anche (c) è a spesa totale costante
  e i due scenari sono confrontabili sulla stessa regola di bilancio. Poiché (b) muove circa il 2% del
  budget e (c) il 3,1%, **il confronto fra (b) e (c) si riporta per euro spostato**, non in valore
  assoluto.
- **(d) controllo nullo** — 200 ripartizioni casuali che spostano **la stessa cifra in euro** di (b)
  fra due canali estratti a sorte. Estrazione dichiarata adesso: `numpy.random.default_rng(20260917 +
  seme_mondo)`, coppia ordinata uniforme fra le 42 possibili, riestrazione se il taglio eccede la
  spesa del canale che cede. La coppia di (b) non è esclusa: il nullo è su tutte le coppie.
- **(e) oracolo** — fra tutte le 42 coppie ordinate, la migliore sotto le curve vere, stessa cifra.
  È il tetto della stessa classe di mosse, non l'ottimo assoluto.

## 3. Metrica

**Contributo incrementale vero dei media, in candidature**: somma su canali, settimane e regioni della
risposta ricalcolata al passo 3 del §0. Riportata in valore assoluto e come percentuale di (a).
Per ogni caso *i*:

```
g_b(i) = Y_b(i) - Y_a(i)                      candidature guadagnate dalla regola
p_b(i) = frazione delle 200 casuali che guadagnano MENO di (b)      (percentile nel nullo)
f_b(i) = g_b(i) / g_e(i)                      frazione del guadagno disponibile catturata
```

Conteggi sugli N = 8 casi: `V` = casi con `g_b > 0`; `S` = casi con `p_b >= 0,90`; `W` = casi in cui
(b) rende più di (c) **per euro spostato** (riportato, non seleziona il ramo). Se un caso non arriva in fondo, N si dichiara accanto
a ogni cifra e le soglie si riscalano in proporzione, arrotondando 0,5 verso l'alto.

## 4. Regola di decisione — deterministica, prima riga che corrisponde

| # | Condizione | Ramo |
|---|---|---|
| 1 | `S >= 6` | **LA REGOLA GUADAGNA E BATTE IL CASO**: seguirla è meglio del non far niente e meglio di muovere soldi a caso |
| 2 | `3 <= S <= 5` | **NON CONCLUSIVO**: si riportano le cifre e non si scrive nessuna raccomandazione |
| 3 | `S <= 2` e `V >= 6` | **DIREZIONE GIUSTA, GUADAGNO INDISTINGUIBILE DAL CASO**: la regola indovina il verso ma non cattura più di una mossa a caso |
| 4 | `S <= 2` e `V <= 5` | **LA REGOLA NON GUADAGNA**: in una parte dei mondi seguirla peggiora |

Si riportano sempre, senza selezionare il ramo: mediana di `g_b` in % di (a), mediana di `p_b`,
mediana di `f_b`, `W`, e il segno di `g_c` caso per caso.

## 5. Previsione dichiarata — e non è cieca

**Previsione: ramo 3.** `V >= 6` (quasi tutti i casi guadagnano qualcosa) ma `S <= 2` (quasi nessuno
batte il 90° percentile del nullo). Mediana di `f_b` sotto 0,5.

Il motivo è nei parametri di Hill del generatore (`hill_ec_moltiplicatore_esecuzione_media`,
`parametri_generazione.json`), riletti adesso dal file:

| Canale | `ec_mult` | ordine di saturazione |
|---|---:|---|
| Indeed | 0,55 | **satura per primo** |
| Subito Lavoro | 0,90 | |
| Altre job board | 1,20 | |
| Meta Ads | 1,50 | |
| Jooble | 2,00 | |
| Google Ads | 2,20 | penultimo |
| LinkedIn Ads | 2,40 | ultimo |

**La regola alza Indeed in sei casi su otto, ed è il canale che satura per primo.** Sul mondo 42
committato la sua saturazione misurata è 71,0%, la più alta del portafoglio, e l'euro aggiuntivo gli
rende 0,98 contro un ROI medio di 2,52. La regola legge il livello del ROI, che è alto; il livello del
ROI non è il criterio giusto per spostare un euro. I canali tagliati (LinkedIn 0,85 di marginale,
Meta 1,05) rendono poco, quindi lo spostamento resta positivo: di qui `V >= 6`. Ma il guadagno è
piccolo, e una coppia estratta a caso che peschi bene lo supera: di qui `S <= 2`.

**Cosa la smentirebbe:** il ramo 1 (`S >= 6`). Sarebbe la prova che la mia lettura della saturazione è
sbagliata, o che il nullo è più debole di quanto credo perché quasi tutte le coppie casuali
peggiorano. Anche il ramo 2 la indebolisce.

**Previsione secondaria, dichiarata:** `g_c < 0` in almeno 6 casi su 8, e `W >= 6`. L'allocatore
vecchio spinge Google Ads al massimo e taglia Jooble, Subito e Altre job board: al margine sono
esattamente i canali che rendono di più (1,56 · 1,74 · 1,81 sul mondo 42) contro Google a 1,38.

**Dichiarazione di non cecità.** Questa previsione **non è cieca**, e va scritto. Il 17 settembre, su
richiesta dell'autore e prima che D11 fosse definito, ho ricalcolato dai file committati i rendimenti
marginali veri del mondo 42 e ho valutato lì la mossa di D10: spostare 110.022 EUR da LinkedIn a
Indeed rende **+9.471 EUR di contributo vero, +0,09 per EUR mosso**, contro +0,50 della mossa migliore
disponibile — **calcolo del 17 settembre (script `verifica_saturazione.py`), non riprodotto
indipendentemente**, e citato qui come tale. Si noti che quel passo (+20% / −21,5%) è più grande di
quello del caso 7 (+13,95% / −15,00%): per la concavità di Hill il guadagno per euro del caso 7 sarà
diverso, e più alto. Quindi per il **caso 7 (D10, mondo 42)** conosco già segno e ordine di grandezza, su un
passo leggermente diverso (+20% / −21,5% invece di +13,95% / −15,00%), e da lì ho estrapolato agli
altri sette. Conseguenze, decise adesso:

1. il caso 7 si riporta come **già visto**, marcato nella tabella dei risultati;
2. i conteggi `V` e `S` si danno **due volte**: su tutti e 8 i casi e sui soli 7 non visti. Il ramo si
   calcola su tutti e 8; la seconda cifra va accanto, sempre;
3. quello che resta davvero ignoto — e che è il motivo per cui il test vale la pena — è il **controllo
   nullo** e la **frazione catturata**: nessuno dei due è stato calcolato per nessun caso;
4. il collaudo di G5 (§10, controlli 2 e 4) è stato fatto **apposta sul riparto del caso 7**, che era
   già il caso non cieco: nessun altro caso è stato toccato prima di chiudere questo documento.

## 6. Cosa NON è ammesso dopo aver visto i risultati

1. Spostare le soglie (6, 3, 2, 0,90) o i confini dei rami, o aggiungerne.
2. Cambiare la cifra spostata, il passo del 15%, o i canali di un caso.
3. Escludere un caso che non piace; escludere il caso 7 per sanare il ramo, o tenerlo per sanarlo.
4. Leggere il ramo 3 come «la regola funziona», o il ramo 2 come un successo.
5. Cambiare il seme o il numero delle ripartizioni casuali dopo aver visto dove cade `p_b`.
6. Presentare (e) come obiettivo raggiungibile: è un oracolo che conosce le curve vere.

## 7. Controlli di fedeltà, prima di qualunque cifra

1. **Generatore ricostruito**: catena A applicata in ordine e in modo **cumulativo** (la sostituzione 4
   inserisce un blocco che la 7 e la 8 riscrivono: applicarle al file originale una per una è
   l'errore), poi G1…G4. Impronta attesa **`c57be0b1e94c0bbd`**. Se non torna, ci si ferma.
2. **G5 senza flag è un no-op**: `--riparto` assente o vuoto deve dare mondi **bit-identici** a prima,
   confrontati file per file.
3. **Somma zero**: se la somma dei riparti non è zero **in euro** (non in punti percentuali), G5 deve
   dare errore. Il totale non si tocca: è il numero che questo lavoro dimostra inaffidabile.
4. **Forma preservata**: il riparto scala il percorso settimanale del canale con un moltiplicatore
   costante; il rapporto fra due settimane dello stesso canale non cambia.
5. **I riparti si riproducono**: rilanciando `proposta_budget.py` sui draw del repo si devono
   riottenere esattamente gli otto riparti del §2. Se non tornano, non si procede.
6. **Doppia strada**: il contributo controfattuale calcolato dal generatore patchato e quello
   calcolato analiticamente dal mondo base (`beta x pop x mg` ricavato come contributo vero diviso
   `hill`) devono coincidere alla precisione di macchina. È il controllo che smaschera un errore nel
   punto 3 del §0.
7. **Costanza di `K`**: `beta x pop_g x mg_g` ricavato dai file deve essere costante nel tempo,
   escluse le settimane a spesa zero (lì `hill ≈ 0` e l'arrotondamento a 4 decimali del contributo
   esplode nella divisione). Verificato sul mondo 42: variazione relativa fra 3·10⁻⁴ e 6·10⁻³.

## 8. Cosa viene consegnato

1. Questa pre-registrazione, **con la sua data, committata prima** di generare qualunque mondo.
2. La patch G5 con il diff e la prova del controllo 2 (bit-identità senza `--riparto`).
3. Un file di risultati **separato**: gli 8 casi con le cinque cifre ciascuno (assolute e in % di (a)),
   `p_b`, `f_b`, le mediane, i conteggi `V`, `S`, `W` su 8 e su 7, e il ramo calcolato.
4. Se la regola non batte il controllo nullo, **in prima riga della consegna**.

## 9. Precondizioni — cosa manca adesso

Tutto il materiale necessario è arrivato con il pacchetto `D11_pacchetto_2026-09-17.zip`; i controlli
del §7 sono stati eseguiti prima di chiudere questo documento e le loro uscite sono al §10. Restano
due cose da dichiarare, entrambe decise adesso e non modificabili dopo:

1. **I riparti si usano a piena precisione**, non arrotondati a due decimali. Alla precisione piena la
   somma quadra a meno di 10⁻⁴ EUR; con le percentuali scritte a due decimali lo scarto arriva a 65,79
   EUR sul caso D1/103. I valori a due decimali del mandato sono stati verificati come corretti
   (§10, controllo 5), ma i conti si fanno sui numeri che `proposta_budget.py` produce, non sulla loro
   stampa: è la regola 5 delle regole di lavoro.
2. **La tolleranza del controllo «somma zero»** non è una cifra arbitraria: vale l'arrotondamento
   delle percentuali a due decimali, cioè 0,005% della spesa dei canali toccati (53,08 EUR sul mondo
   42), con un pavimento di 1 EUR. Un riparto che sbaglia più di così non è arrotondato: è sbagliato,
   e G5 lo rifiuta con un errore.

## 10. I controlli di fedeltà, eseguiti

Tutti passati, prima di chiudere questo documento e prima di calcolare i sette casi non visti.

| # | Controllo | Esito |
|---|---|---|
| 1 | generatore ricostruito: 8 sostituzioni A **cumulative** in ordine, poi G1…G4 a fuzz 0 | impronta **`c57be0b1e94c0bbd`** = attesa. **Cancello superato** |
| 2 | G5 senza `--riparto` è un no-op | **17 file su 17 bit-identici** sul mondo 42 base, e **17 su 17** sul mondo 103 calendario a 4 giri |
| 3 | somma non zero in euro → errore | rifiutato con il dettaglio per canale: «la somma vale +77.401,34 EUR (tolleranza 53,08)» |
| 4 | forma del percorso preservata | moltiplicatore settimanale costante entro 3,4·10⁻⁵ (arrotondamento al centesimo): Indeed 1,139460–1,139494, LinkedIn 0,849982–0,850018 |
| 5 | gli otto riparti si riproducono da `proposta_budget.py` sui draw | **8 su 8 riprodotti**. Sette identici anche nell'ordine di stampa; su D1/103 Google e LinkedIn hanno lo stesso taglio (−4,13%) e cambia solo quale dei due viene elencato per primo |
| 6 | doppia strada: generatore contro calcolo analitico a `beta` fisso | nel file dei risultati |
| 7 | costanza di `K = beta × pop × mg` | nel file dei risultati |

Controllo aggiuntivo, non previsto dalla v1 ma eseguito: con un riparto attivo **i canali non toccati
devono avere contributo vero invariato**. Sul caso 7: cinque canali su sette invariati a `+0,0`
candidature, spesa totale 3.667.797,24 → 3.667.797,73 EUR (49 centesimi di arrotondamento).

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
