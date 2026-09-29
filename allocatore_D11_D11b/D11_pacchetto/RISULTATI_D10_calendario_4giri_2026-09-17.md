# Risultati — D10: calendario a quattro giri, otto mondi

**Ramo 2: IL LIMITE È LA BASELINE.** Raddoppiare l'esperimento — da due giri a quattro, da 16
a 32 settimane spente per canale — non sposta l'errore sul totale. Nessun disegno costruito
sui media supera quel muro, e va scritto nei limiti del capitolo 7.

Lo si dichiara qui, in prima riga, perché è il §8.5 della pre-registrazione a chiederlo.

**17 settembre 2026.** Si legge accanto a `preregistrazioni/PREREGISTRAZIONE_D10_calendario_4giri.md`,
versione 1 del 17 settembre 2026, committata al `f43fc3f` **prima del primo fit** e qui non
modificata. Il file della pre-registrazione che è girato su Colab è byte per byte quello
committato (sha256 `d780a89e…4ef464`): la regola eseguita è la regola registrata.

---

## 1. Il ramo, calcolato

Il §5 è una tabella deterministica: si prende la prima riga che corrisponde.

| # | Condizione | Verifica | Esito |
|---|---|---|---|
| 1 | `C_tot >= 6` | `C_tot = 2` | no |
| 2 | `C_tot <= 4` **e** `E >= 6,0` | `C_tot = 2`, `E = 8,28` | **SÌ** |
| 3 | tutto il resto | — | non si arriva |

`N = 8`, tutti gli otto mondi con `esito = ok`, tutti e otto ammissibili. Le due cifre
coincidono sui due insiemi, quindi il ramo non dipende da quale si guarda.

## 2. Le tre grandezze, accanto a D2

| Grandezza | D2, due giri | D10, quattro giri | Direzione |
|---|---:|---:|---|
| `C_tot` (mondi con 0,05 ≤ PIT ≤ 0,95) | 4 su 8 | **2 su 8** | peggiora |
| `E` mediano (punti di eccesso di quota media) | 7,18 | **8,28** | peggiora |
| `rapporto_mediana` mediano | 1,3838 | **1,4387** | peggiora |
| `N_ok` (canali identificati, `C_k ≥ 6`) | 7 su 7 | 7 su 7 | tiene |

Come chiede il §4, fra D2 e D10 si confrontano rapporti stima/vero, mai livelli: la verità dei
due disegni non coincide (0,61% di scarto sul mondo 42, dichiarato in pre-registrazione).

La scala di `E` su tutta la griglia, per collocare l'8,28:

| disegno | `E` |
|---|---:|
| osservativo | 22,9 |
| geo su 3 regioni | 19,4 |
| geo canonico | 15,5 |
| **D2, calendario a 2 giri** | **7,2** |
| **D10, calendario a 4 giri** | **8,3** |

Il salto grande è dall'osservativo al calendario. Da due giri a quattro non c'è salto.

## 3. La tabella per mondo

Ogni mondo è misurato contro la propria verità. `E` è `quota_media_stimata_pct` meno
`quota_media_vera_pct`, letta dal file del runner.

| mondo | rot. | `rapporto_mediana` | forbice 5%–95% (mln) | vero (mln) | PIT | copre | `E` | canali dentro |
|---|---|---:|---|---:|---:|:---:|---:|:---:|
| 42  | 0 | 1,4588 | 7,20 – 11,56 | 6,33 | 0,011250 | no | +8,65 | 5 su 7 |
| 101 | 1 | 1,3608 | 6,34 – 11,23 | 6,33 | 0,049875 | no | +6,83 | 7 su 7 |
| 102 | 2 | 1,3406 | 6,32 – 11,05 | 6,33 | 0,050500 | **sì** | +6,53 | 7 su 7 |
| 103 | 3 | 1,4741 | 7,04 – 11,93 | 6,33 | 0,013125 | no | +8,94 | 6 su 7 |
| 104 | 4 | 1,5174 | 7,28 – 12,25 | 6,33 | 0,008625 | no | +9,78 | 7 su 7 |
| 105 | 5 | 1,2235 | 5,60 – 10,14 | 6,33 | 0,149500 | **sì** | +4,24 | 7 su 7 |
| 106 | 6 | 1,4824 | 6,99 – 12,07 | 6,33 | 0,015000 | no | +9,12 | 6 su 7 |
| 107 | 0 | 1,4186 | 6,55 – 11,71 | 6,33 | 0,034500 | no | +7,91 | 6 su 7 |

**Due mondi vanno dichiarati per onestà, e nessuno dei due sposta il ramo.**

Il **101** ha PIT `0,049875`: manca la soglia dello 0,05 per **125 milionesimi**. Contandolo,
`C_tot` salirebbe a 3 — resta `≤ 4`, e con `E = 8,28` il ramo è lo stesso. La soglia era fissata
prima; il mondo resta fuori e lo si scrive.

Il **102** — uno dei due che coprono — è il mondo con più divergenze, 196 su 8.000, il 2,45%.
Il §7 dice che le divergenze si riportano sempre e non squalificano da sole, e il mondo è
ammissibile sui due cancelli veri (R-hat 1,001 e 1,002, ESS 3.239 e 2.048). Resta dentro. Ma
va notato che i mondi che coprono sono anche quelli in cui il campionatore ha faticato di più:
102 con 196 divergenze e 105 con 49, contro le 2–12 degli altri sei.

## 4. Il confronto mondo per mondo con D2 — dove sta la vera notizia

| mondo | `E` D2 | `E` D10 | Δ | copre D2 | copre D10 |
|---|---:|---:|---:|:---:|:---:|
| 42  | 12,05 | 8,65 | **−3,40** | no | no |
| 101 |  7,89 | 6,83 | **−1,06** | no | no |
| 102 |  6,47 | 6,53 | +0,06 | sì | sì |
| 103 | 11,02 | 8,94 | **−2,08** | no | no |
| 104 | 13,24 | 9,78 | **−3,46** | no | no |
| 105 |  5,55 | 4,24 | **−1,31** | sì | sì |
| 106 |  6,11 | 9,12 | +3,01 | sì | **no** |
| 107 |  3,54 | 7,91 | +4,37 | sì | **no** |

**Cinque mondi su otto migliorano, e la mediana peggiora lo stesso.** Non è un paradosso: è
quello che succede quando una distribuzione si stringe intorno a un valore che non si muove.

| | D2 | D10 |
|---|---:|---:|
| `E` mediano | 7,18 | 8,28 |
| `E` medio | 8,23 | **7,75** |
| `E` minimo | 3,54 | 4,24 |
| `E` massimo | 13,24 | 9,78 |
| escursione | 9,70 | **5,54** |
| deviazione standard | 3,47 | **1,81** |
| dev. st. del `rapporto_mediana` | 0,189 | **0,097** |

Quattro giri **dimezzano la dispersione fra i mondi** e lasciano il centro dov'era, intorno agli
8 punti: la mediana sale di 1,1, la media scende di 0,5, e l'escursione si accorcia di 4,2.

Questa è la lettura forte del ramo 2, più forte del solo `C_tot`. La parte di errore che
**varia da mondo a mondo** è la parte che l'esperimento identifica, e raddoppiando i giri si
dimezza. Quello che resta è un **fondo comune di circa 8 punti** che tutti gli otto mondi
condividono e che nessun giro in più tocca. Un errore che non dipende dal mondo e non risponde
alla dose dell'esperimento non è nei media: è nella domanda organica.

I mondi 106 e 107 lo dicono nel modo più chiaro. In D2 coprivano, con `E` 6,11 e 3,54 — i due
valori più bassi degli otto. D10 li ha riportati al livello comune, 9,12 e 7,91, e hanno perso
la copertura. **Due delle quattro coperture di D2 erano dispersione favorevole, non disegno.**
Toglierla è un guadagno di conoscenza che si paga con due mondi in meno nel conteggio.

## 5. Canale per canale: tutte e sette le forbici si stringono

| canale | dose mediana | `C_k` D2 → D10 | `larghezza_relativa` mediana D2 → D10 | var. |
|---|---:|:---:|---|---:|
| Meta Ads | 13,91% | 7 → **8** | 1,6522 → 1,3101 | **−20,7%** |
| Indeed | 13,65% | 7 → **6** | 1,6168 → 1,3264 | **−18,0%** |
| LinkedIn Ads | 13,65% | 6 → **7** | 2,3907 → 2,1921 | −8,3% |
| Altre job board | 13,86% | 8 → 8 | 3,9668 → 3,6436 | −8,1% |
| Google Ads | 13,91% | 6 → 6 | 1,0387 → 0,9697 | −6,6% |
| Subito Lavoro | 13,65% | 8 → 8 | 3,4573 → 3,3245 | −3,8% |
| Jooble | 13,91% | 8 → 8 | 4,3889 → 4,2307 | −3,6% |

**Sette canali su sette hanno l'intervallo più stretto**, riduzione mediana −8,1%. La
somma dei `C_k` passa da 50 a 51 e `N_ok` resta 7 su 7: sui canali il disegno continua a funzionare, e
funziona un po' meglio.

Ed è qui il meccanismo della copertura persa, in una riga: **gli intervalli si sono stretti,
la distorsione no.** Un intervallo più corto attorno a una stima che resta 1,44 volte il vero
copre meno spesso di uno più lungo attorno alla stessa stima. Niente di misterioso: il modello
è diventato più sicuro senza diventare più giusto.

È la quarta volta che questo schema compare nella griglia — *largo copre, stretto sbaglia* —
ma le prime tre volte era **osservato** (D8, D3 parte A, Meta in D1). Qui è **provocato**:
abbiamo cambiato una cosa sola, il numero di giri, e abbiamo guardato cosa succede. È la sola
istanza causale delle quattro, ed è quella che vale per il capitolo 6.4.

## 6. La previsione dichiarata, e come è andata

Il §5 chiudeva così, e la frase era lì apposta:

> Se il vincolo fosse la dose nel tempo, raddoppiare i giri dovrebbe portare `E` verso i 4
> punti. Se il vincolo è la baseline, `E` resta intorno a 7. È una previsione, ed è lì per
> poter essere smentita.

`E` mediano è **8,28**. La previsione "verso i 4 punti" è **smentita**; la previsione
alternativa — "resta intorno a 7" — è quella che si avvicina, e nemmeno quella prende il
numero: `E` non è rimasto a 7, è salito a 8,3, mentre la media è scesa a 7,75.

Il commit `f43fc3f`, scritto prima del run, contava cinque previsioni smentite su sei
dichiarate in tutta la griglia. Con questa **fanno sei su sette**. Vanno scritte tutte, e
questa con la sua data: registrata la sera del 16 settembre, misurata la mattina del 17,
senza che nel mezzo si sia toccato niente.

È il punto su cui la pre-registrazione si giustifica da sola. Una previsione su sette ha
tenuto: se le attese fossero state scelte dopo, avrebbero tenuto tutte.

## 7. Ammissibilità e diagnostica (cap. 4.7)

Otto mondi su otto passano i due cancelli, con margine largo.

| mondo | R-hat `roi_m` | R-hat `beta_m` | ESS `roi_m` | ESS `beta_m` | divergenze | durata |
|---|---:|---:|---:|---:|---:|---:|
| 42  | 1,001 | 1,001 | 4.378 | 5.328 | 2 (0,03%) | 9,8 min |
| 101 | 1,002 | 1,002 | 2.892 | 3.000 | 2 (0,03%) | 11,3 min |
| 102 | 1,001 | 1,002 | 3.239 | 2.048 | 196 (2,45%) | 9,9 min |
| 103 | 1,001 | 1,001 | 2.554 | 2.571 | 3 (0,04%) | 9,8 min |
| 104 | 1,005 | 1,005 | 1.758 | 1.062 | 4 (0,05%) | 11,1 min |
| 105 | 1,001 | 1,002 | 2.943 | 2.323 | 49 (0,61%) | 9,5 min |
| 106 | 1,002 | 1,001 | 3.114 | 1.967 | 12 (0,15%) | 9,4 min |
| 107 | 1,003 | 1,005 | 1.160 | 475 | 11 (0,14%) | 9,6 min |

Soglie: R-hat ≤ 1,1 (massimo osservato 1,005) ed ESS ≥ 100 (minimo osservato 475). Nessun
mondo rilanciato, nessun seme sostituito, nessuna esclusione. Somma delle durate 80,4 minuti,
con gli otto mondi chiusi fra le 00:47:44 e le 02:02:36 del 17 settembre.

## 8. Configurazione e provenienza

Identica al §3 della pre-registrazione, verificata riga per riga sul file dei risultati: 96
nodi, `keep` 2000, 4 catene, 500 adapt, 500 burnin, seme MCMC 42 su tutti i mondi,
`revenue_per_kpi` 40,0, prior `riferimento` (mu 0,2 · sigma 0,9), `decimali_stagionalita` 4,
`disegno = calendario`, `parametri_disegno = rotazione=i;giri=4`.

Le dosi di popolazione per canale confermano il §2: Google 21,08% nel mondo che lo tratta per
primo, gli altri fra 11,75% e 14,06%, identiche a D2. Cambia il numero di giri, non la dose.

Impronte dei dati in ingresso, una per mondo, dal file `impronte_griglia.csv`:

| mondo | 42 | 101 | 102 | 103 | 104 | 105 | 106 | 107 |
|---|---|---|---|---|---|---|---|---|
| impronta | `6459d038cd2c` | `cf848ea3cd3c` | `46908f2a3aab` | `4884cbf15842` | `a9af9024bee6` | `6aefa980a83c` | `b4398643d904` | `af81ef8701c9` |

Generatore con patch G4, impronta `c57be0b1e94c0bbd`; runner con R7; notebook
`colab_griglia_D10.ipynb`, separato da `colab_griglia.ipynb`, che resta come committato.

**Controllo di integrità dei draw, rifatto qui sui file scaricati.** Per tutti e otto i mondi,
8.000 draw a testa, il PIT e il `rapporto_mediana` sono stati **ricalcolati dai draw** e
coincidono con quelli del runner alla cifra; `ci05` e `ci95` coincidono a meno
dell'arrotondamento al decimo con cui il runner li scrive. Il `totale` è sommato **dentro ogni
draw**, che è il formato che rende impossibile l'errore dei quantili sommati.

## 9. Cosa va dove, nella tesi

| Risultato | Numero | Destinazione |
|---|---|---|
| Raddoppiare l'esperimento non riduce l'errore sul totale | `C_tot` 4 → 2, `E` 7,2 → 8,3 | **7.3 limiti** |
| Il residuo è un fondo comune, non una coda | dev. st. di `E` 3,47 → 1,81 a centro fermo | **7.3**, e 6.4 |
| Più esperimento stringe gli intervalli senza spostare le stime | 7 canali su 7, fino a −20,7% | **6.4** |
| Il calendario a due giri resta la raccomandazione | quattro giri non aggiungono, e costano il doppio | **7.2** |
| Quattro giri identificano i canali quanto due | `N_ok` 7 su 7, somma `C_k` 50 → 51 | 5.10 |
| Due delle quattro coperture di D2 erano dispersione | 106 e 107, `E` 6,11 e 3,54 → 9,12 e 7,91 | 6.4 |

La frase per il 7.3, già pronta:

> Raddoppiare l'esperimento — da due giri a quattro, da 16 a 32 settimane spente per canale —
> non riduce l'errore sul totale. Dimezza la dispersione fra i mondi, lascia il centro a otto
> punti e fa scendere la copertura da quattro mondi su otto a due, perché stringe gli
> intervalli senza spostare le stime. Il residuo non è identificabile da un esperimento sui
> media, perché non è nei media: è nella domanda organica, che nessuna campagna spenta rivela.

E la raccomandazione operativa del 7.2 ne esce **rafforzata, non indebolita**: il calendario a
rotazione va fatto a due giri. Quattro costano il doppio di media spenta e non comprano niente
sul totale.

---

*Documento di risultati. La regola con cui sono stati letti sta in
`preregistrazioni/PREREGISTRAZIONE_D10_calendario_4giri.md`, committata prima del primo fit e
mai modificata dopo.*
