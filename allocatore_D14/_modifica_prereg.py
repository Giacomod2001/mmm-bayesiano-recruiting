"""Applica alla pre-registrazione D14 le risposte al §13 e le aggiunte (a) e (b) approvate da Giacomo il 24/9."""
import os
import sys

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preregistrazioni",
                 "PREREGISTRAZIONE_D14_allocatore_ROAS_benchmark.md")
s = open(P, encoding="utf-8").read()


def R(a, b):
    global s
    if s.count(a) != 1:
        sys.exit("NON TROVATO UNA VOLTA SOLA: " + a[:70])
    s = s.replace(a, b)


R("""**24 settembre 2026. BOZZA per la verifica di Giacomo.** Nessun calcolo di D14 parte prima del suo
OK esplicito su questo documento. I risultati andranno in un file separato, scritto dopo il run.""",
  """**24 settembre 2026. APPROVATA da Giacomo il 24/9**, con le risposte al §13 e le aggiunte (a) al §5
e (b) al §8. La bozza verificata aveva sha256
`18f6498e4cd6cbba7298520460cb58b3c2398cba4197dfacd1c04a5f9987c9b0`. Questa versione si congela
prima del run: nessun calcolo di D14 è stato fatto prima del congelamento. I risultati andranno in un
file separato, scritto dopo il run.""")

R("""- (e′) la migliore delle 5.040 graduatorie.
""", """- (e′) la migliore delle 5.040 graduatorie.

**Aggiunta (a), approvata il 24/9.** A questa cifra il nullo di R1 **favorisce la regola**: una mossa
concentrata del 12% del budget su una sola coppia di canali perde spesso. Un eventuale A1 va quindi
letto insieme al controllo nella banda (d′). Quel controllo l'ho già visto nel run preliminare (§0),
e per questo non può diventare il criterio.
""")

R("""- Il livello zero di B1 e quello di B2 coincidono: sono i ROAS perfetti.
""", """- Il livello zero di B1 e quello di B2 coincidono: sono i ROAS perfetti.

**Aggiunta (b), approvata il 24/9.** Se il livello zero fallisce, i risultati di B1 e di B2 riportano
comunque **in prima riga l'elenco completo dei livelli che soddisfano il criterio**, e non solo la
frase «nemmeno con ROAS esatti».
""")

R("""   prima riga, previsioni confermate o smentite una per una, i limiti del §10 in prima pagina.""",
  """   prima riga, previsioni confermate o smentite una per una, i limiti del §10 in prima pagina, e il
   run preliminare citato con la sua impronta, i quattro punti di differenza e le cifre del §0. La
   cartella `D14_preliminare_ANNULLATO` resta archiviata e non si cancella.""")

R("""## 13. Punti da verificare prima dell'OK
""", """## 13. Punti da verificare prima dell'OK — risposte di Giacomo del 24/9

1. **Casi**: gli 8 casi di D11/R1, come nella bozza, con accanto il conteggio sui 6 mondi distinti.
2. **Nullo**: come nella bozza. Criterio = nullo di R1; (d′) ed (e′) solo come descrizione.
3. **Gruppi di B2**: come nella bozza.
4. **Run preliminare**: citato anche nel file dei risultati (impronta, quattro punti di differenza,
   cifre del §0); la cartella resta archiviata e non si cancella.

Testo della bozza, lasciato com'era:
""")

open(P, "w", encoding="utf-8").write(s)
print("modificata")
