# Addendum alla pre-registrazione D1 — denominatore del danno collaterale (§5-bis)

**15 settembre 2026.** Si legge insieme a `PREREGISTRAZIONE_D1_geo_canonico.md`, versione 1
del 15 settembre 2026, che **non viene modificata**. Scritto **prima di qualunque fit** della
griglia.

---

## 1. Motivo

Il §10.4 della pre-registrazione D1 prevede, per il danno collaterale del §5-bis, il file
`copertura_risultati_canali.csv` dello studio osservativo sugli otto mondi, su Drive in
`MMM_copertura`.

**Accertato oggi, prima di qualunque fit: quel file non esiste.** In `MMM_copertura` ci sono
soltanto `copertura_risultati.csv` e i due `_randomizzato`. I draw dello studio osservativo non
sono stati salvati, quindi le righe per canale non sono ricostruibili da quello studio: come
dice il preambolo di `PREREGISTRAZIONE_D0_osservativo_replica.md`, lo studio osservativo del
13 settembre è l'unico eseguito **prima** della patch A4 e non ha né le righe per canale né i
draw.

## 2. Decisione

Il denominatore del danno collaterale del §5-bis — la `larghezza_relativa` dell'osservativo per
**Indeed** e **Jooble**, mondo per mondo — si legge da **`griglia_D0_osservativo_canali.csv`**
(19 colonne), prodotto da **D0** sugli **stessi otto mondi** (`42, 101, 102, 103, 104, 105,
106, 107`) con lo **stesso runner patchato** usato da D1.

Non è un ripiego improvvisato: è esattamente ciò che D0 dichiara di produrre. Il §1 di
`PREREGISTRAZIONE_D0_osservativo_replica.md` elenca fra gli scopi di D0, alla lettera (b),
"fornisce il denominatore del danno collaterale di D1 e D3 su tutti gli otto mondi". D0 gira
per primo, prima di D1, e i suoi attesi sono le otto righe di `copertura_risultati.csv`,
verificate riga per riga dal pre-volo: se D0 non riproduce l'osservativo alla quarta cifra,
non è interpretabile nemmeno D1.

Il numeratore non cambia: resta la `larghezza_relativa` di D1, letta da
`griglia_D1_geo_canali.csv` come già previsto dal §8.

## 3. Perché non altera il disegno

1. **La grandezza non seleziona il ramo.** Lo dice il §5-bis stesso, fin dal titolo: "si
   riportano sempre, non selezionano il ramo". Il §6, punto 4, vieta esplicitamente di usare le
   mediane per selezionare il ramo. Il ramo del §5 si calcola da `C_Google` e `C_LinkedIn`, che
   questo addendum non tocca in nessun modo.
2. **I valori attesi dichiarati restano quelli.** Mediana sugli otto mondi **≥ 1**; mondo 42,
   in multipli del vero, **Indeed 2,09 → 5,16** e **Jooble 3,21 → 4,35**. Nessuna soglia,
   nessun confine di ramo, nessun atteso viene toccato.
3. **Cambia la provenienza del denominatore, non la sua definizione.** Resta la
   `larghezza_relativa` dell'osservativo sullo stesso mondo, alla stessa configurazione di fit
   del §3 (96 nodi, `keep` 2000, seme MCMC 42, prior di riferimento), calcolata dal runner
   dentro i draw e mai a posteriori (§4).
4. **È deciso prima di vedere i numeri.** Questo addendum è datato e committato prima del
   primo fit della griglia, come il §10.3 chiede per la pre-registrazione stessa.

## 4. Condizione

Vale **solo se D0 completa tutti e otto i mondi con `esito = ok`**.

| Caso | Denominatore |
|---|---|
| D0 chiude gli otto mondi con `esito = ok` | `griglia_D0_osservativo_canali.csv`, tutti e otto i mondi |
| D0 chiude su **meno di otto** mondi | gli **N mondi effettivamente arrivati in fondo**, e **N va dichiarato** accanto alla cifra, come il §7 chiede per ogni conteggio |
| D0 **fallisce del tutto** | resta il ripiego del §10.4: la grandezza si calcola **solo sul mondo 42** contro `registro_run_canali.csv` (run `base_96_rif_s42`), e lo si dichiara |

In tutti e tre i casi la grandezza si riporta, non si omette, e si dichiara da dove viene il
denominatore. **Lo studio osservativo non si rifà** (§10.4).

---

*Addendum a una pre-registrazione: non contiene risultati. Il §10.4 di
`PREREGISTRAZIONE_D1_geo_canonico.md` resta scritto com'era; questo documento si legge
accanto, non al suo posto.*
