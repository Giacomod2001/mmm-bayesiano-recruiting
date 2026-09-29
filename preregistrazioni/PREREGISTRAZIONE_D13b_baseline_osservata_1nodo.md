# Pre-registrazione — D13b: la domanda organica osservata, con la baseline a 1 nodo per trimestre

**23 settembre 2026.** Scritta e committata **prima di qualunque fit**, insieme al notebook che la
contiene: al momento in cui entra in git non esiste nessun numero di D13b. Qualunque risultato va in
un file separato, `RISULTATI_D13b_baseline_1nodo_<data>.md`.

---

## 0. Perché esiste, e il caveat di D13 che vale anche qui

**Perché esiste.** La pre-registrazione di N1 (§8) aveva fissato una condizione: se N1 avesse
trovato che la baseline conta, cioè ramo 2 sul livello oppure ramo A sull'ordine, una prova in stile
D13 con la baseline a 1 nodo per trimestre avrebbe potuto avere senso. N1 ha dato il **ramo 2 sul
livello** (`RISULTATI_N1_nodi_2026-09-23.md`, commit `1f7102a`). Giacomo ha deciso di farla il 23
settembre.

Il nulla di D13 è stato misurato con la baseline a 96 nodi. A f = 0,30 l'`E` mediano era +23,29,
contro +22,92 di D0. Può darsi che il controllo organico non servisse proprio perché i 96 nodi si
erano già presi la stessa informazione. D13b toglie quella possibilità: nodi al minimo provato e
controllo presente.

**Il caveat di D13 (§0 della sua pre-registrazione) vale per intero**, e va in prima pagina dei
risultati:
1. il controllo è costruito dalla baseline vera, quindi misura il **caso più favorevole possibile**:
   è un limite superiore, non una stima di ciò che darebbe un dato reale;
2. nel simulatore la baseline è indipendente dalla spesa, quindi qui il controllo è legittimo. Nel
   mondo reale una parte della domanda spontanea è causata dai media: un controllo del genere
   assorbirebbe parte dell'effetto e sottostimerebbe i media.

## 1. Domanda

Con la baseline a **1 nodo per trimestre**, dare al modello la domanda organica osservata riduce la
sovrastima dei media?

## 2. Disegno

- **Mondi:** gli otto di D0 (42, 101–107). **Dati di D0 identici al byte**: impronta attesa di ogni
  run = quella di D0 dello stesso mondo, che è anche quella di N1 e di D13.
- **Controllo:** `domanda_organica_osservata`, costruito come in D13 dal runner R8
  (`--controllo-baseline`): `c = f · organico · exp(ε)`, con ε ~ N(0; 0,15) e rng `seme + 31`.
  **Un solo livello, f = 0,30.** Dopo la standardizzazione che Meridian applica ai controlli, i tre
  livelli di D13 sono lo stesso dato: correlazione 1,000000000, differenza massima 5,7·10⁻⁶. Fra i
  tre si prende 0,30 perché è l'unico già eseguito su tutti gli otto mondi a 96 nodi: il confronto
  con D13 è appaiato mondo per mondo.
- **Baseline:** `knots_per_quarter` = **1**, cioè 8 nodi, passato dalla riga del run come in N1.
- **Tutto il resto come la griglia:** 2.000 campioni tenuti per catena, 4 catene, adattamento 500,
  burn-in 500, seme MCMC 42 su tutti i mondi, `revenue_per_kpi` 40, prior LogNormale(0,2; 0,9)
  uguale per tutti i canali, gli stessi tre controlli di D0 più quello organico.
- **Un fit di replica come cancello, per primo:** D13 a f = 0,30 sul **mondo 101** a 12 nodi per
  trimestre. Deve riprodurre la riga di D13: `rapporto_mediana` 2,4593, impronta `7eaa88ed1323`,
  96 nodi. Si usa il 101 e non il 42 perché il run di D13 sul mondo 42 a f = 0,30 non era ammissibile
  (R-hat 1,17 e 1,20, ESS 18 e 14), e replicare un run non ammissibile è un controllo debole. **Se
  la replica non riproduce la riga di D13, nessun altro fit parte**, nemmeno al rilancio.
- **Totale: 9 fit**, circa un'ora e mezza di GPU T4 (i fit di N1 e D13 sono durati fra 9,2 e 15,2
  minuti). Ordine: replica, poi il mondo 42, poi 101–107.

## 3. Metriche

Le stesse della griglia: `E` = quota stimata − quota vera in punti, `rapporto_mediana`, PIT,
`C_tot`, e per canale `C_k`, larghezza relativa e `rho` di Spearman.

**Il riferimento è N1 a 1 nodo per trimestre, mondo per mondo**: stessi nodi, stessi dati, senza il
controllo organico. Per ogni mondo ammissibile `w`:

**`ΔE_w = E_w(D13b) − E_w(N1, 1 nodo/trim.)`**

con `E_w(N1)` letto da `griglia_N1/griglia_N1_k01.csv`: 42 +16,14 · 101 +13,88 · 102 +13,87 ·
103 +17,36 · 104 +20,02 · 105 +16,87 · 106 +15,03 · 107 +9,42 (mediana +15,585; tutti e otto
ammissibili).

**Ammissibilità**, criterio della Sezione 4.7: R-hat ≤ 1,1 ed ESS ≥ 100 su `roi_m` e `beta_m`. Le
divergenze si riportano e da sole non squalificano. Un run non ammissibile si riporta col suo numero
**e non si rifà**. I mondi ammissibili sono `N`; soglia di conteggio 6 per `N` = 8, altrimenti
`int(6/8 · N + 0,5)`, come in N1. Un `ΔE_w` esattamente zero non conta né fra i positivi né fra i
negativi.

## 4. Regole di decisione — esaustive, prima riga che corrisponde

### 4.1 Livello

| # | Condizione | Ramo |
|---|---|---|
| 0 | `N` < 5 | **NON LEGGIBILE**: si riportano le cifre, nessuna conclusione |
| 1 | `E` mediano di D13b ≤ **4,0** | **IL CONTROLLO ORGANICO RECUPERA LA BASELINE, SE I NODI NON SE LA PRENDONO**: il nulla di D13 era un effetto dei 96 nodi |
| 2 | mediana di `ΔE` ≤ **−5,0** **e** `ΔE` < 0 in almeno **6 mondi su 8** (o la soglia) | **IL CONTROLLO AIUTA, MA NON BASTA** |
| 3 | mediana di `ΔE` ≥ **+5,0** **e** `ΔE` > 0 in almeno **6 mondi su 8** (o la soglia) | **IL CONTROLLO PEGGIORA LA SOVRASTIMA** |
| 4 | altrimenti | **ANCHE A 1 NODO IL CONTROLLO ORGANICO NON SPOSTA IL LIVELLO IN MODO NETTO** |

La soglia 4,0 è quella di D12 e D13. Le soglie ±5,0 e 6 su 8 sono quelle di N1.

### 4.2 Ordine

`rho` mediano sugli `N` mondi ammissibili, con i riferimenti di N1:

| # | Condizione | Ramo |
|---|---|---|
| 0 | `N` < 5 | **NON LEGGIBILE** |
| A | mediana ≥ **+0,6071** (17/28, «spesa inversa») | **CON BASELINE RIGIDA E CONTROLLO ORGANICO MERIDIAN ORDINA ALMENO COME LA REGOLA EMPIRICA** |
| B | mediana > **+0,2321** (13/56, il caso) | **MEGLIO DEL CASO, NON MEGLIO DELLA REGOLA EMPIRICA** |
| C | altrimenti | **L'ORDINE NON SI DISTINGUE DAL CASO** |

I rami li stampa uno script, `analisi_D13b.py`, committato con questa pre-registrazione. Nessun ramo
si dichiara prima che lo stampi.

## 5. Si riportano sempre, senza che selezionino i rami

- `E`, `rho`, `C_tot` mondo per mondo e in mediana, accanto a N1 a 1 nodo, a D13 a f = 0,30 (96
  nodi) e a D0.
- **L'effetto del controllo ai due numeri di nodi**, mondo per mondo: `ΔE_w` qui, e
  `E_w(D13, f = 0,30) − E_w(D0)` a 96 nodi. Sul mondo 42 il run di D13 non era ammissibile, e lo si
  scrive accanto.
- Il rapporto stimato/vero per canale, per vedere se l'eccesso che a 1 nodo si era spostato su
  Indeed resta lì.
- Ammissibili sul totale; R-hat, ESS e divergenze; ogni run non ammissibile col suo numero.
- Le ore dei run (colonna `quando`) e l'ora del commit di questa pre-registrazione.

## 6. Previsione dichiarata

**Confermata da Giacomo il 23 settembre 2026, prima del commit e prima di qualunque fit:**

- **Livello: ramo 4.** A 96 nodi il controllo, correlato circa 0,975 con la verità (fra 0,972 e
  0,979 negli otto mondi), non ha spostato niente
  (+23,29 contro +22,92). A 1 nodo la sovrastima è già scesa senza nessuna informazione organica in
  più (+15,6). Il residuo quindi non sembra dovuto all'informazione organica mancante, ma a come i
  canali grandi e sempre accesi si dividono l'effetto: il meccanismo per canale di N1 lo suggerisce
  (Google scende, Indeed sale).
- **Ordine: ramo C**, per la stessa ragione di N1: il controllo non tocca i canali piccoli, fermi
  vicino al prior.

**Cosa la smentirebbe:** sul livello il ramo 1 o il ramo 2, che direbbero che il nulla di D13 era
un effetto dei 96 nodi. Sull'ordine il ramo A o B.

## 7. Cosa NON è ammesso dopo aver visto i risultati

1. Spostare le soglie (4,0 · ±5,0 · 6 su 8 e la formula · +0,6071 · +0,2321 · `N` < 5) o i confini
   dei rami.
2. Aggiungere livelli di `f` o di nodi, aggiungere mondi, rifare un run non ammissibile.
3. Cambiare il riferimento (N1 a 1 nodo, mondo per mondo) con D0 o con D13 dopo aver visto quale
   conviene.
4. Far partire gli 8 fit dopo un cancello di replica fallito, o rilanciare la replica sperando che
   torni.
5. Far entrare D13b nella corsa fra le due diagnosi del §4-bis di D12 e §4-ter di D13: quella regola
   era registrata per D12 e D13, non per D13b. D13b si riporta accanto, e la corsa non si ridecide
   con un disegno aggiunto dopo.
6. Omettere o spostare in fondo il caveat del §0.
7. Leggere un ramo 1 o 2 come «basta osservare la domanda organica»: è un limite superiore (§0).

## 8. Controlli di fedeltà — eseguiti prima del commit

Eseguiti il 23 settembre 2026, prima del commit e prima di qualunque fit.

| # | Controllo | Esito |
|---|---|---|
| 1 | il notebook è generato da uno script committato, a partire da un notebook committato di cui si verifica l'impronta | **passato**: `controlli_fedelta_D13b/fai_notebook_D13b.py` parte da `colab_griglia_D13.ipynb` e si ferma se il suo sha256 LF non è `3f17879db07d22f8…`. Verifica anche che runner e generatore nel blob siano quelli committati (R8, G6 `8f86eb032d0113c0`) |
| 2 | la tabella dei run nel blob | **passato**: 9 righe. Run 1 = replica, mondo 101, 12 nodi per trimestre (96), f = 0,30, regola `identico_osservativo` con gli attesi presi dalla riga di D13 (2,4593; pit 0,0; forbice 1,8321–3,1253; dentro 0). Run 2–9 = mondi 42, 101–107 a 1 nodo per trimestre (8 nodi), f = 0,30. Impronta attesa = D0 del mondo in 9 run su 9 |
| 3 | nodi dalla riga del run e controllo di `n_knots` sulla riga (trappole 1 e 2 di N1) | **passato**: stesse sostituzioni del notebook di N1. Provato con righe finte: una riga a 96 nodi per un run a 1 nodo dà anomalia |
| 4 | la pre-registrazione nel blob è questa, identica al byte | **passato**. Il pre-volo la scrive su Drive prima del primo fit: è lo stesso codice che l'ha fatto per D12, D13 e N1 |
| 5 | collaudo locale del pre-volo, controlli 5 e 6, con il generatore ricostruito e il runner veri | **passato**: generatore = main + A + G1..G4 + G6, sha `8f86eb032d0113c0`; autotest del runner; i 5 dataset del mondo 42 identici ai committati; cancello del controllo organico (12 file su 12 identici, rapporto 0,6088 a f = 0,60, correlazione col vero 0,9755, niente scritto a f = 0); cancello dei nodi (1 → 8, 12 → 96, impronta D0 e f = 0,30 in 9 run su 9) |
| 6 | la logica del cancello di replica, con righe finte | **passato, 12 prove su 12**. La replica identica alla riga di D13 passa. Rapporto 2,4594, forbice diversa o f = 0,60 danno anomalia; impronta diversa, colonna di controllo assente o 96 nodi danno anomalia sui run a 1 nodo. Nella sequenza della cella 2: nessuna riga → attesa; riga identica → partono gli 8; riga diversa → fermo, con `ANOMALIA_CANCELLO_REPLICA.txt` |
| 7 | `analisi_D13b.py` su casi sintetici | **passato, 21 casi su 21** (`controlli_fedelta_D13b/collaudo_analisi_D13b.py`): i cinque rami del livello e i quattro dell'ordine, i confini esatti (E 4,00; ΔE −5,00 e +5,00; rho 17/28 e mediana 13/56), `N` = 7 con soglia 5, `N` = 4, replica diversa o assente |

**Che cosa non è stato collaudato qui:** il fit vero (GPU, Meridian) e il montaggio di Drive.
Restano quelli del notebook di N1, che su Colab ha girato 25 fit su 25 con la stessa impostazione.

## 9. Cosa viene consegnato

1. Questa pre-registrazione, **con la sua data, committata prima del primo fit**, insieme a
   `analisi_D13b.py` e al notebook `colab_griglia_D13b_1nodo.ipynb` (cartella Drive `MMM_griglia_D13b_1nodo`) con lo script che lo genera. Il
   notebook caricato su Colab deve avere la stessa impronta di quello committato.
2. Dopo il run: `RISULTATI_D13b_baseline_1nodo_<data>.md`, con i rami in prima riga, il caveat del
   §0 subito sotto, le tabelle del §5 e le righe per l'Appendice A.

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
