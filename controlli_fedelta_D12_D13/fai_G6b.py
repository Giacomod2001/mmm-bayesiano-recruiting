# Seconda meta' della patch G6: JSON dei parametri e riga di comando.
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
p = "gen_G6.py"
src = open(p, encoding="utf-8").read()


def sub(vecchio, nuovo, etichetta):
    global src
    n = src.count(vecchio)
    if n != 1:
        raise SystemExit("G6b sostituzione '%s': trovata %d volte" % (etichetta, n))
    src = src.replace(vecchio, nuovo)
    print("ok", etichetta)


# --- 9. la descrizione di scenario_geo non puo' mentire sul blackout --------
sub(
'''        **({"scenario_geo": {
            "descrizione": (
                "Esperimento geografico: per ogni canale trattato la spesa "
                "delle regioni trattate, nei blocchi di settimane trattati, e' "
                "moltiplicata per l'intensita' (0 = spenta) e ridistribuita "
                "sulle altre regioni della stessa settimana. La spesa nazionale "
                "settimanale del canale e' quella della base: cambia solo DOVE "
                "viene spesa. I canali non trattati sono bit-identici alla base "
                "dello stesso seme in spesa, impression e clic."),''',
'''        **({"scenario_geo": {
            "descrizione": (
                "Esperimento geografico: per ogni canale trattato la spesa "
                "delle regioni trattate, nei blocchi di settimane trattati, e' "
                "moltiplicata per l'intensita' (0 = spenta) e ridistribuita "
                "sulle altre regioni della stessa settimana. La spesa nazionale "
                "settimanale del canale e' quella della base: cambia solo DOVE "
                "viene spesa. I canali non trattati sono bit-identici alla base "
                "dello stesso seme in spesa, impression e clic."
                if (p["geo_spec"] or {}).get("ridistribuisci", True) else
                "Blackout totale (G6): nelle celle trattate la spesa e' "
                "azzerata e NON ridistribuita. La spesa nazionale settimanale "
                "SCENDE, ed e' il punto del disegno: e' l'unico modo di far "
                "muovere il livello dei media e non solo la loro "
                "distribuzione. Fuori dalle celle trattate la spesa e' quella "
                "del mondo base dello stesso seme, valore per valore. Vedi "
                "scenario_blackout."),''',
    "9 descrizione scenario_geo")

# --- 10. scenario_blackout, accanto a scenario_calendario -------------------
sub(
'''        }} if (p.get("geo_spec") or {}).get("nome") == "calendario" else {}),
        "regole_canali_da_aggiungere_in_CONFIG": [''',
'''        }} if (p.get("geo_spec") or {}).get("nome") == "calendario" else {}),
        **({"scenario_blackout": {
            "descrizione": (
                "Blackout totale geografico (D12): tutti e sette i canali a "
                "spesa esattamente zero nelle stesse " +
                str(p["geo_spec"]["n_regioni"]) + " regioni, per " +
                str(p["geo_spec"]["n_blocchi"]) + " blocchi da " +
                str(p["geo_spec"]["lunghezza_blocco"]) + " settimane. La spesa "
                "tolta NON viene ridistribuita: la spesa nazionale settimanale "
                "scende. Nelle regioni-settimane trattate le candidature "
                "osservate sono la baseline, letta e non inferita."),
            "regioni_trattate": list(p["geo_spec"]["regioni_trattate"]),
            "quota_popolazione_trattata_pct": round(100.0 * sum(
                REGIONI[r] for r in p["geo_spec"]["regioni_trattate"]) /
                sum(REGIONI.values()), 2),
            "strati_di_popolazione": {
                str(i): regs for i, regs in enumerate(p["geo_spec"]["strati"])},
            "costruzione_del_campione": (
                "regioni ordinate per popolazione decrescente e divise in " +
                str(p["geo_spec"]["n_regioni"]) + " strati contigui di pari "
                "numerosita'; da ogni strato si prende quella in posizione " +
                str(p["geo_spec"]["posizione_nello_strato"]) + " (0-based). "
                "Nessuna estrazione casuale: le regioni sono le stesse in tutti "
                "gli otto mondi."),
            "blocchi_1based_inclusivi": [
                [a + 1, b + 1] for a, b in
                p["geo_piano"][list(p["geo_piano"])[0]]["blocchi"]],
            "celle_trattate_per_canale": int(
                len(p["geo_spec"]["regioni_trattate"]) *
                p["geo_spec"]["n_blocchi"] * p["geo_spec"]["lunghezza_blocco"]),
            "spesa_tolta_eur": {
                ch: p["geo_diario"][ch].get("spesa_tolta_eur")
                for ch in p["geo_piano"]},
            "spesa_tolta_totale_eur": round(float(sum(
                p["geo_diario"][ch].get("spesa_tolta_eur") or 0.0
                for ch in p["geo_piano"])), 2),
            "beta_e_ec_del_mondo_base": (
                "beta e la mezza saturazione ec NON sono ricalibrati su questo "
                "mondo: sono quelli del mondo base dello stesso seme, "
                "rigenerato per intero nello stesso processo. Senza questa "
                "scelta la ricalibrazione del passo 7 riporterebbe il "
                "contributo totale di ogni canale al suo valore di sempre "
                "(quota_kpi/S x totale_atteso) qualunque sia la spesa, e il "
                "disegno misurerebbe zero. Conseguenza da dichiarare accanto a "
                "ogni cifra: la verita' di questo mondo e' la superficie di "
                "risposta implicita nei parametri veri del mondo base, non un "
                "mondo che il generatore produrrebbe da solo."),
            "quota_media_vera_di_questo_mondo_pct": round(
                100.0 * p["quota_media_realizzata"], 4),
            "quota_media_vera_mondo_base_pct": round(
                100.0 * p["blackout_base"]["quota_media_realizzata"], 4),
            "costo_del_disegno": {
                "definizione": (
                    "candidature vere che il blackout fa perdere: contributo "
                    "incrementale vero del mondo base meno quello di questo "
                    "mondo, a parita' di tutto il resto. Comprende la coda "
                    "dell'adstock, che continua a pesare nelle settimane "
                    "successive al blocco. E' la cifra che il capitolo 7.2 "
                    "dichiara come non misurata."),
                "candidature_vere_perse": round(
                    p["blackout_base"]["contributo_vero_totale"] -
                    float(sum(v.sum() for v in p["risposta"].values())), 1),
                "candidature_vere_perse_per_canale": {
                    ch: round(p["blackout_base"]["contributo_vero_per_canale"][ch] -
                              float(p["risposta"][ch].sum()), 1)
                    for ch in p["canali"]},
                "contributo_vero_totale_mondo_base": round(
                    p["blackout_base"]["contributo_vero_totale"], 1),
                "contributo_vero_totale": round(
                    float(sum(v.sum() for v in p["risposta"].values())), 1),
                "spesa_totale_mondo_base_eur": round(
                    p["blackout_base"]["spesa_totale"], 2),
                "spesa_totale_eur": round(float(sum(
                    float(v.sum()) for v in p["ch_spesa"].values())), 2),
                "candidature_osservate_mondo_base": int(
                    p["blackout_base"]["candidature_totali"]),
                "candidature_osservate": int(p["candidature"].sum()),
            },
        }} if (p.get("geo_spec") or {}).get("nome") == "blackout" else {}),
        "regole_canali_da_aggiungere_in_CONFIG": [''',
    "10 scenario_blackout")

# --- 11. riga di comando ----------------------------------------------------
sub(
'''    ap.add_argument("--suffisso-mondo", default="",
                    help="con --seed-mondo: etichetta aggiunta al nome della "''',
'''    ap.add_argument("--blackout", action="store_true",
                    help="variante blackout totale (D12): tutti e sette i "
                         "canali a spesa zero in " + str(BLACKOUT_N_REGIONI) +
                         " regioni fisse (una per strato di popolazione) per "
                         "due blocchi da " + str(BLACKOUT_LUNGHEZZA_BLOCCO) +
                         " settimane, spesa NON ridistribuita: la spesa "
                         "nazionale scende. beta e ec restano quelli del mondo "
                         "base dello stesso seme. Richiede --seed-mondo")
    ap.add_argument("--suffisso-mondo", default="",
                    help="con --seed-mondo: etichetta aggiunta al nome della "''',
    "11a flag --blackout")

sub(
'''    varianti = [f for f, on in (("--pause2", args.pause2), ("--sanita", args.sanita),
                                ("--casuale2", args.casuale2), ("--geo", args.geo),
                                ("--calendario", args.calendario)) if on]''',
'''    varianti = [f for f, on in (("--pause2", args.pause2), ("--sanita", args.sanita),
                                ("--casuale2", args.casuale2), ("--geo", args.geo),
                                ("--calendario", args.calendario),
                                ("--blackout", args.blackout)) if on]''',
    "11b mutua esclusione")

sub(
'''    geo_spec = None
    if args.calendario:''',
'''    geo_spec = None
    if args.blackout:
        if args.seed_mondo is None:
            ap.error("--blackout richiede --seed-mondo: non esiste un dataset "
                     "canonico del blackout in dati_simulati/")
        geo_spec = blackout_spec()
    if args.calendario:''',
    "11c costruzione blackout_spec")

sub(
'''        variante = ("_sanita" if args.sanita else "_pause2" if args.pause2
                    else "_casuale2" if args.casuale2 else "_geo" if args.geo
                    else "_calendario" if args.calendario else "")''',
'''        variante = ("_sanita" if args.sanita else "_pause2" if args.pause2
                    else "_casuale2" if args.casuale2 else "_geo" if args.geo
                    else "_calendario" if args.calendario
                    else "_blackout" if args.blackout else "")''',
    "11d suffisso cartella")

open(p, "w", encoding="utf-8", newline="\n").write(src)
print("gen_G6.py aggiornato")
