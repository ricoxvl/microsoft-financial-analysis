# Model and evaluation method

See the complete README for equations, assumptions and limitations. All values are USD millions unless explicitly displayed as billions.

The 18-driver register is `assumptions_register.csv`. Each selected original annual fact is in `data/processed/source_facts.csv`; original HTML and API bytes are preserved in `data/raw/`. `results/filing_reconciliation.csv` holds 165 API-to-10-K checks.

Forecast horizon: FY2027–2029, aggregate annual Microsoft statements. Other assets and liabilities fixed. Cash and funding follow explicit cash flows; no unrecognized balancing adjustments. Forecast depreciation includes all reported depreciation; finance lease asset amortization is not added again. Finite-lived intangible amortization is separate.

Backtest origins are the FY2022–2025 annual filing dates. One-year targets are FY2023–2026. Only original annual inputs with filing dates no later than each origin are used. Three-year averages require warmup data. The baseline extrapolates each target metric's latest annual growth. The protocol is specified in code before computing errors; retrospective research is still susceptible to hindsight. Four samples per metric do not establish statistical superiority.

Signed error = forecast − actual. MAE = mean absolute error. MAPE = mean(abs(error)/abs(actual)), undefined for zero actuals and often unsuitable near zero or for negative series. WAPE = sum(abs(error))/sum(abs(actual)). Bias = mean signed error. Baseline gap = baseline MAE − model MAE. Positive gap favors the model. All evaluated actuals are nonzero and positive. Holdout outputs are frozen; Excel edits do not regenerate historical evaluation.

Results: revenue MAPE 4.6%, EBIT 8.0%, FCF 18.4%. Revenue and FCF have lower MAE than baseline; EBIT has higher MAE. All FCF holdouts overforecast. The evaluation does not imply actual future earnings or cash changes caused by this work.
