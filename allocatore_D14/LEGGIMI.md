# D14 — l'allocatore sui ROAS del benchmark interno

**Entrato nel repository il 29 settembre 2026.** Il run è del 24 settembre (22:46:18-22:46:38 UTC,
13,2 s su CPU) ed è stato fatto in un'altra sessione di lavoro. Il pacchetto consegnato era
`D14_consegna_formale_2026-09-24.zip`. I file sono conservati **come consegnati**, identici al byte.
Una sola eccezione: `PARAGRAFO_6.3_proposto_D14.md` resta fuori, perché è testo della tesi.

## Dove sta cosa

| File | Che cos'è | sha256 (primi 16) |
|---|---|---|
| `../preregistrazioni/PREREGISTRAZIONE_D14_allocatore_ROAS_benchmark.md` | la pre-registrazione approvata e congelata | `43b4cf866856ed7a` |
| `../preregistrazioni/IMPRONTA_PREREGISTRAZIONE_D14.txt` | l'impronta e l'ora del congelamento (2026-09-24T22:44:34Z) | `6943d1bbce329a98` |
| `PREREGISTRAZIONE_D14_bozza_18f6498e.md` | la bozza verificata da Giacomo, prima delle sue risposte | `18f6498e4cd6cbba` |
| `_modifica_prereg.py` | lo script che applica alla bozza le risposte del §13 e le aggiunte (a) e (b) | `235fb12007e70521` |
| `studio_D14.py` | il codice del run | `8401eb4814d6ce2a` |
| `D14_esecuzione.txt` | il registro del run, cancello compreso | `0b93cc59bc9805fc` |
| `D14_risultati.csv` | parte A, caso per caso | `ce9608e492263ef5` |
| `D14_B1_tolleranza.csv`, `D14_B1_estrazioni.csv` | parte B1, errore casuale | `a6bde7b97adfc794`, `205e31d1f67744c5` |
| `D14_B2_sistematico.csv` | parte B2, errore sistematico | `ebe8544da7de8e36` |
| `../RISULTATI_D14_allocatore_ROAS_benchmark_2026-09-24.md` | il file dei risultati, scritto dopo il run | `7517254178958d6d` |

## La catena della pre-registrazione si può verificare

La bozza, passata per `_modifica_prereg.py`, dà esattamente la versione congelata. Verificato il
29/9: sha256 `18f6498e...` in ingresso, `43b4cf86...` in uscita. Lo script scrive con i fine riga
del sistema: su Windows va eseguito con `newline=""` nella `open` di scrittura, altrimenti l'impronta
non torna.

La pre-registrazione **non è cieca**. Il suo §0 dichiara un run preliminare dello stesso studio,
fatto senza approvazione e poi annullato. La cartella `D14_preliminare_ANNULLATO` non era nel
pacchetto consegnato e non è in questo repository.

## Per rieseguirlo

`studio_D14.py` è stato eseguito in una cartella diversa da questa. Si aspetta:

- la pre-registrazione in `./preregistrazioni/`, accanto allo script, e ne controlla l'impronta;
- la macchina di D11 in `../D11/`, cioè `studio_D11.py` e `D11_risultati.csv`, che qui stanno
  in `../allocatore_D11_D11b/`;
- i mondi generati dal generatore G5 in `./mondi/mondo_<seme>/`, con `benchmark/` e `verita/`.

Per rieseguirlo bisogna ricreare questa disposizione. Il codice non è stato adattato, perché il
repository deve contenere il file che ha prodotto le cifre.

## Una svista nel file dei risultati

Nel §6 del RISULTATI si legge che con ROAS esatti la regola «lascia Meta intermedio». Il CSV dice
un'altra cosa: in `D14_B2_sistematico.csv`, al livello δ = 0, Meta Ads va a +28,88% nel mondo 101
e a +30% nel 103. Quindi con ROAS esatti Meta è **alzata al tetto**, non lasciata a un valore
intermedio. La conclusione del paragrafo non cambia: con ROAS esatti la regola perde in 8 casi su 8.
Il testo della tesi (Sezione 6.3) usa la lettura corretta. Il RISULTATI resta come consegnato.
