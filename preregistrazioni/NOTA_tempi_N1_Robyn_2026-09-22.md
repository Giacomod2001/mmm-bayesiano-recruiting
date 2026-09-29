# Nota sui tempi — pre-registrazioni N1 e Robyn a verità nota

**22 settembre 2026.** Questa nota va letta insieme a `PREREGISTRAZIONE_N1_nodi.md` e a
`PREREGISTRAZIONE_ROBYN_verita_nota.md`, ed entra in git con lo stesso commit.

## Che cosa non è andato come previsto

Le due pre-registrazioni dicono «al momento in cui questo documento entra in git non esiste un solo
numero». **Per il commit non è vero.** I fit sono partiti prima:

- **N1** è stato avviato su Colab prima del commit;
- **Robyn** è stato eseguito prima del commit.

La regola 4 del prompt del 22 settembre («i fit partono solo dopo che la pre-registrazione è
committata») **non è stata rispettata**, e lo si scrive qui invece di correggere il testo delle due
pre-registrazioni. Il testo resta com'era, byte per byte, quando è stato fissato.

## Che cosa prova che il testo precede i numeri

- **N1.** Il notebook eseguito su Colab, `colab_griglia_N1_nodi.ipynb` (sha256
  `a3ed95394231d4ec…`, lo stesso di questo commit), contiene nel suo blob il testo di
  `PREREGISTRAZIONE_N1_nodi.md` identico a quello di questo commit. Il controllo 4 del pre-volo lo
  scrive su Drive, in `MMM_griglia_N1/preregistrazioni/`, **prima del primo fit**: la data di quel
  file su Drive e la colonna `quando` di `_verifiche.csv` sono la prova dell'ordine.
- **Robyn.** Il testo di `PREREGISTRAZIONE_ROBYN_verita_nota.md` è stato mostrato per intero in chat
  prima del run, insieme al comando di commit. Qui non c'è una prova su file indipendente dalla chat,
  e lo si dichiara.

## Che cosa si riporta nei risultati

Nei due file di risultati, accanto al ramo, vanno scritte tre ore: l'avvio dei run, la loro fine e
il commit delle pre-registrazioni (l'ora di questo commit in git). Nessuna soglia, nessun ramo e
nessuna previsione cambiano per questo.
