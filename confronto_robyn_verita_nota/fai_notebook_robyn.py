"""Costruisce confronto_robyn_verita_nota/colab_robyn_mondo42.ipynb dal demo
collaudato (confronto_robyn_meridian/colab_robyn_demo.ipynb): le celle di setup
restano identiche, cambiano dati, specifica, iperparametri, selezione e metriche.
La verita' del mondo 42 si legge qui dal CSV di D0 e si scrive nel notebook."""
import csv, json, os, sys
REPO = sys.argv[1]
DEMO = os.path.join(REPO, "confronto_robyn_meridian", "colab_robyn_demo.ipynb")
FUORI = os.path.join(REPO, "confronto_robyn_verita_nota", "colab_robyn_mondo42.ipynb")
demo = json.load(open(DEMO, encoding="utf-8"))
setup = "".join(demo["cells"][2]["source"])
assert setup.startswith('install.packages("Robyn")'), setup[:60]

NOMI = {"Google Ads": "google_ads", "Meta Ads": "meta_ads", "LinkedIn Ads": "linkedin_ads",
        "Indeed": "indeed", "Subito Lavoro": "subito_lavoro", "Jooble": "jooble",
        "Altre job board": "altre_job_board"}
ORDINE = ["google_ads", "meta_ads", "linkedin_ads", "indeed", "subito_lavoro", "jooble", "altre_job_board"]
with open(os.path.join(REPO, "griglia", "griglia_D0_osservativo_canali.csv"), newline="", encoding="utf-8") as f:
    v = {NOMI[r["canale"]]: r for r in csv.DictReader(f) if r["seed_mondo"] == "42"}
assert sorted(v) == sorted(ORDINE)
vec = lambda campo: "c(" + ", ".join(v[c][campo] for c in ORDINE) + ")"

MD0 = """# Robyn a verita' nota - mondo 42 nazionale

**Domanda, una sola.** La sovrastima e' una proprieta' del regime osservativo, oppure anche del modo in cui Meridian lo tratta? Robyn, sullo **stesso mondo** e con la **stessa verita'**, sbaglia allo stesso modo? Pre-registrazione: `preregistrazioni/PREREGISTRAZIONE_ROBYN_verita_nota.md`, committata prima del run.

**Prima di iniziare:**
1. Runtime -> Cambia tipo di runtime -> **R** (CPU va bene).
2. Carica `mondo42_nazionale.csv` (cartella `confronto_robyn_verita_nota/` del repository) dal **pannello file a sinistra**. La cella 2 ne verifica l'impronta e si ferma se non e' quello committato.

**Tempo:** ~15-20 min di installazione, ~40-60 min di run.

**Le quattro avvertenze, accanto a ogni cifra:** (1) Robyn e' nazionale: l'aggregazione toglie la dimensione geografica, e il confronto e' fra due impianti diversi, non fra due stimatori sulla stessa informazione; (2) Robyn restituisce stime puntuali: niente copertura, si confrontano solo livello e ordinamento; (3) la selezione fra i candidati di Pareto e' un grado di liberta' dell'analista, ed e' parte del confronto; (4) un mondo solo: non si generalizza.

**Uscite** (nello zip finale): `robyn_riepilogo.csv` (il ramo e le metriche), `robyn_roas.csv` (decomposizione e ROI per canale del modello scelto), `robyn_metrics.csv` (vincitori dei cluster), `robyn_pareto_candidati.csv` (tutti i candidati di Pareto), `robyn_iperparametri_scelto.csv`, `robyn_iperparametri_range.csv`, e la cartella `robyn_output/` con l'onepager.
"""

C_DATI = r'''library(Robyn)
cat("Robyn", as.character(packageVersion("Robyn")), "| inizio", format(Sys.time(), tz = "Europe/Rome", usetz = TRUE), "\n")

# --- il CSV: deve essere quello committato (0f9a40e), impronta sul contenuto a fine riga LF
F_DATI <- "mondo42_nazionale.csv"
SHA_ATTESO <- "75b74de70f57c027f2a83a42a5da1018ea513f1c7b56f66f2e9ba181df54b68d"
if (!file.exists(F_DATI)) stop("Manca ", F_DATI, ": caricalo dal pannello file a sinistra ",
                               "(confronto_robyn_verita_nota/ del repository) e riesegui da questa cella.")
sha <- substr(trimws(system(paste0("tr -d '\\r' < ", F_DATI, " | sha256sum"), intern = TRUE)), 1, 64)
cat("sha256 del CSV (fine riga LF):", sha, "\n")
if (sha != SHA_ATTESO) stop("mondo42_nazionale.csv NON e' quello committato: ", sha, " invece di ", SHA_ATTESO)
dt <- read.csv(F_DATI, stringsAsFactors = FALSE)
dt$DATE <- as.Date(dt$DATE)
CANALI <- c("google_ads", "meta_ads", "linkedin_ads", "indeed", "subito_lavoro", "jooble", "altre_job_board")
CONTESTO <- c("stagionalita", "domanda_clienti", "ricerche_candidati")
stopifnot(identical(names(dt), c("DATE", "candidature", CANALI, CONTESTO)))
stopifnot(nrow(dt) == 104, sum(dt$candidature) == 855534)
data("dt_prophet_holidays")

# --- la verita' del mondo 42: griglia/griglia_D0_osservativo_canali.csv, seed_mondo = 42
VERITA <- data.frame(
  canale = CANALI,
  spesa = @SPESA@,
  roi_vero = @ROIVERO@,
  roi_meridian_D0 = @ROIMER@)
stopifnot(all(abs(colSums(dt[, CANALI]) - VERITA$spesa) < 0.01))   # stessa spesa al centesimo
QUOTA_VERA <- 18.5066   # quota di TOTALI: controllo (e) di prepara_mondo42_nazionale.py
VALORE_KPI <- 40        # EUR per candidatura
cat("104 settimane,", format(min(dt$DATE)), "->", format(max(dt$DATE)), "| candidature 855534 | spesa",
    format(sum(VERITA$spesa), nsmall = 2), "EUR | quota vera 18,5066%\n")
'''.replace("@SPESA@", vec("spesa")).replace("@ROIVERO@", vec("roi_vero")).replace("@ROIMER@", vec("roi_stimato"))

C_SPEC = r'''InputCollect <- robyn_inputs(
  dt_input = dt,
  dt_holidays = dt_prophet_holidays,
  date_var = "DATE",
  dep_var = "candidature",
  dep_var_type = "conversion",
  prophet_vars = c("trend", "season"),
  prophet_country = "IT",          # senza "holiday" Robyn lo ignora con un avviso (pre-reg., par. 3)
  context_vars = CONTESTO,         # TRE controlli, come Meridian: la stagionalita' entra due volte
  paid_media_spends = CANALI,
  paid_media_vars = CANALI,        # solo spesa, nessuna variabile di esposizione
  window_start = min(dt$DATE),
  window_end = max(dt$DATE),
  adstock = "geometric"
)

# Gli iperparametri si RIGENERANO dai canali nuovi: copiare i nomi del demo fa fallire il run.
# Range fissati nella pre-registrazione: quelli del demo per i canali digitali, uguali per tutti.
nomi <- hyper_names(adstock = InputCollect$adstock, all_media = InputCollect$all_media)
print(nomi)
RANGE <- list(alphas = c(0.5, 3), gammas = c(0.3, 1), thetas = c(0, 0.3))
hyperparameters <- list()
for (n in nomi) hyperparameters[[n]] <- RANGE[[sub(".*_", "", n)]]
# intervallo strettissimo (estremi identici scatenano un bug noto di hyper_collector):
# test = ultimo ~10%, validazione = penultimo ~10%
hyperparameters$train_size <- c(0.79, 0.81)
stopifnot(length(nomi) == 3 * length(CANALI), !any(sapply(hyperparameters, is.null)))
write.csv(data.frame(iperparametro = names(hyperparameters),
                     min = sapply(hyperparameters, `[`, 1), max = sapply(hyperparameters, `[`, 2)),
          "robyn_iperparametri_range.csv", row.names = FALSE)
InputCollect <- robyn_inputs(InputCollect = InputCollect, hyperparameters = hyperparameters)
'''

C_RUN = r'''T_INIZIO_RUN <- Sys.time()
OutputModels <- robyn_run(
  InputCollect = InputCollect,
  iterations = 2000,
  trials = 5,
  ts_validation = TRUE,
  add_penalty_factor = FALSE,
  cores = max(1, parallel::detectCores() - 1),
  seed = 42
)

OutputCollect <- robyn_outputs(
  InputCollect, OutputModels,
  pareto_fronts = "auto",
  csv_out = "pareto",
  clusters = TRUE,
  export = TRUE,
  plot_folder = "robyn_output",
  plot_pareto = TRUE
)
T_FINE_RUN <- Sys.time()
cat("run: inizio", format(T_INIZIO_RUN, tz = "Europe/Rome", usetz = TRUE),
    "- fine", format(T_FINE_RUN, tz = "Europe/Rome", usetz = TRUE), "\n")
'''

C_SEL = r'''# La selezione si fa PRIMA di calcolare qualunque quota, e non guarda la quota (pre-reg., par. 4).
rh <- as.data.frame(OutputCollect$resultHypParam)      # Robyn lo filtra gia' sulle soluzioni di Pareto
write.csv(rh, "robyn_pareto_candidati.csv", row.names = FALSE)
vincitori <- OutputCollect$clusters$models$solID
if (is.null(vincitori) || length(vincitori) == 0) {
  cat("ATTENZIONE: il clustering non ha prodotto vincitori: si sceglie fra tutte le soluzioni di Pareto\n")
  vincitori <- rh$solID
}
cand <- rh[rh$solID %in% vincitori, ]
stopifnot(nrow(cand) > 0)
cand <- cand[order(cand$nrmse_test, cand$decomp.rssd, cand$solID), ]
sel <- cand$solID[1]
cat("Candidati di Pareto:", nrow(rh), "| vincitori dei cluster:", nrow(cand),
    "| selezionato:", sel, "(nrmse_test minimo)\n")
cols_m <- intersect(c("solID", "rsq_train", "rsq_val", "rsq_test", "nrmse_train", "nrmse_val",
                      "nrmse_test", "decomp.rssd", "mape", "train_size"), names(cand))
metriche <- cand[, cols_m]
write.csv(metriche, "robyn_metrics.csv", row.names = FALSE)
write.csv(rh[rh$solID == sel, ], "robyn_iperparametri_scelto.csv", row.names = FALSE)
metriche
'''

C_RAMO = r'''# ============================================================================
# IL RAMO (pre-registrazione, par. 6), stampato in prima riga da questo script
# ============================================================================
xd <- as.data.frame(OutputCollect$xDecompAgg)
xs <- xd[xd$solID == sel, ]
write.csv(xs, "robyn_roas.csv", row.names = FALSE)
paid <- xs[match(CANALI, xs$rn), ]
stopifnot(nrow(paid) == 7, !anyNA(paid$xDecompAgg))
finestra <- dt$DATE >= as.Date(InputCollect$window_start) & dt$DATE <= as.Date(InputCollect$window_end)
den <- sum(dt$candidature[finestra])
stopifnot(den == 855534)
quota_A <- 100 * sum(paid$xDecompAgg) / den          # definizione A: quella della regola
quota_F <- 100 * sum(paid$xDecompPerc)               # definizione F: sul dipendente fittato
somma_es <- 100 * sum(paid$effect_share)             # 100% per costruzione (R/model.R)
rapporto <- quota_A / QUOTA_VERA
ramo <- if (rapporto >= 1.8 && rapporto <= 2.6) "1" else if (rapporto < 1.5) "2" else
  if (rapporto > 2.6) "3" else "4"
TESTI <- c("1" = "E' IL REGIME: i due framework sbagliano nello stesso modo",
           "2" = "ANCHE IL MODELLO CONTA",
           "3" = "ROBYN SBAGLIA DI PIU'",
           "4" = "NON CONCLUSIVO")
esito_prev <- if (ramo == "1") "CONFERMATA" else if (ramo == "2") "SMENTITA" else "NON CONFERMATA"
it <- function(x, d = 2) gsub(".", ",", formatC(x, format = "f", digits = d), fixed = TRUE)

canali <- data.frame(canale = CANALI, spesa = VERITA$spesa, spesa_robyn = paid$total_spend,
                     contributo_candidature = paid$xDecompAgg, roi_vero = VERITA$roi_vero)
canali$roi_stimato <- canali$contributo_candidature * VALORE_KPI / canali$spesa
canali$rapporto_stima_vero <- canali$roi_stimato / canali$roi_vero
canali$roi_meridian_D0 <- VERITA$roi_meridian_D0
rho_robyn <- cor(canali$roi_stimato, canali$roi_vero, method = "spearman")
rho_spesa_inversa <- cor(-canali$spesa, canali$roi_vero, method = "spearman")
rho_meridian <- cor(canali$roi_meridian_D0, canali$roi_vero, method = "spearman")
m <- metriche[metriche$solID == sel, ]

cat("ROBYN - ramo ", ramo, " (", TESTI[[ramo]], ") | rapporto ", it(rapporto), " = quota ",
    it(quota_A, 4), "% / 18,5066% | previsione dichiarata (ramo 1): ", esito_prev, "\n", sep = "")
cat("\nmodello scelto:", sel, "| Robyn", as.character(packageVersion("Robyn")), "\n")
cat("quota attribuita ai media: A (xDecompAgg / 855.534 osservate) ", it(quota_A, 4),
    "% | F (somma xDecompPerc, sul fittato) ", it(quota_F, 4),
    "% | somma effect_share ", it(somma_es, 2), "% (100% per costruzione)\n", sep = "")
cat("rapporto contro 18,5066%: A ", it(rapporto, 4), " | F ", it(quota_F / QUOTA_VERA, 4),
    " | Meridian sullo stesso mondo 2,26\n", sep = "")
cat("rho Spearman ROI stimato vs vero: Robyn ", it(rho_robyn, 4), " | regola spesa inversa ",
    it(rho_spesa_inversa, 4), " | Meridian D0 ", it(rho_meridian, 4), "\n", sep = "")
for (k in intersect(c("nrmse_train", "nrmse_val", "nrmse_test", "rsq_train", "rsq_val", "rsq_test",
                      "decomp.rssd", "train_size"), names(m)))
  cat(k, it(m[[k]], 4), " ")
cat("\n\n")
print(transform(canali, roi_stimato = round(roi_stimato, 4), rapporto_stima_vero = round(rapporto_stima_vero, 3),
                contributo_candidature = round(contributo_candidature, 1)), row.names = FALSE)
cat("\nAVVERTENZE: (1) Robyn e' nazionale, impianti diversi; (2) stime puntuali, niente copertura;",
    "(3) la selezione fra i candidati di Pareto e' un grado di liberta' dell'analista; (4) un mondo solo.\n")

riep <- data.frame(ramo = ramo, testo_ramo = TESTI[[ramo]], previsione = "ramo 1", esito_previsione = esito_prev,
                   rapporto_A = rapporto, quota_A_pct = quota_A, quota_F_pct = quota_F,
                   somma_effect_share_pct = somma_es, quota_vera_pct = QUOTA_VERA, denominatore = den,
                   rho_robyn = rho_robyn, rho_spesa_inversa = rho_spesa_inversa, rho_meridian_D0 = rho_meridian,
                   modello = sel, robyn = as.character(packageVersion("Robyn")),
                   inizio_run = format(T_INIZIO_RUN, tz = "Europe/Rome", usetz = TRUE),
                   fine_run = format(T_FINE_RUN, tz = "Europe/Rome", usetz = TRUE))
riep <- cbind(riep, m[, setdiff(names(m), "solID"), drop = FALSE])
write.csv(riep, "robyn_riepilogo.csv", row.names = FALSE)
write.csv(canali, "robyn_canali_verita.csv", row.names = FALSE)

# onepager del modello selezionato
invisible(robyn_onepagers(InputCollect, OutputCollect, select_model = sel, export = TRUE))
'''

C_ZIP = r'''file_out <- c("robyn_riepilogo.csv", "robyn_canali_verita.csv", "robyn_roas.csv", "robyn_metrics.csv",
              "robyn_pareto_candidati.csv", "robyn_iperparametri_scelto.csv", "robyn_iperparametri_range.csv",
              list.files("robyn_output", recursive = TRUE, full.names = TRUE))
zip("robyn_verita_nota_risultati.zip", files = file_out)
cat("Creato robyn_verita_nota_risultati.zip (", length(file_out), " file): scaricalo dal pannello file a sinistra.\n",
    "Fine: ", format(Sys.time(), tz = "Europe/Rome", usetz = TRUE), "\n", sep = "")
'''

def md(t): return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}
def code(t): return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
                     "source": t.splitlines(keepends=True)}
nb = {"nbformat": demo["nbformat"], "nbformat_minor": demo["nbformat_minor"],
      "metadata": {"colab": {"name": "colab_robyn_mondo42.ipynb"},
                   "kernelspec": {"name": "ir", "display_name": "R"}, "language_info": {"name": "R"}},
      "cells": [md(MD0),
                md("## 1. Setup (~15-20 min): Robyn da CRAN + nevergrad (invariato dal demo)\n"), code(setup),
                md("## 2. Il mondo 42 nazionale, verificato, e la sua verita'\n"), code(C_DATI),
                md("## 3. Specifica del modello (pre-registrazione, par. 3)\n"), code(C_SPEC),
                md("## 4. Run (~40-60 min su CPU)\n"), code(C_RUN),
                md("## 5. Selezione: vincitori dei cluster, nrmse_test minimo, senza guardare la quota\n"), code(C_SEL),
                md("## 6. Metriche e RAMO (stampato in prima riga)\n"), code(C_RAMO),
                md("## 7. Scarica i risultati\n\nIl runtime R di Colab non ha `files.download`: scarica lo zip dal **pannello file a sinistra** (tasto destro -> Download).\n"),
                code(C_ZIP)]}
with open(FUORI, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("scritto", FUORI, os.path.getsize(FUORI), "byte")
