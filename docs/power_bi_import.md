# Power BI handoff (native .pbix not generated)

Use `data/processed/history.csv`, `results/scenario_summary.csv`, `results/forecast_errors.csv`, `results/backtest_summary.csv` and `docs/assumptions_register.csv`.

Build a Year dimension, FY2019–2029, with June 30 year end; filter the five-year history to FY2022–26 in visuals. Add an Actual/Forecast flag. Unpivot statement columns to Metric / Amount if preferred. For a combined financials fact table, append historical rows with scenario `Actual` to scenario rows (`base`, `upside`, `downside`); **do not duplicate or sum historical actuals across scenarios**. Scenario selection should filter forecast rows and retain Actual rows. All amounts are USD millions.

Suggested DAX for a selector table `Scenario` with no relationships:

```dax
Amount USDm =
VAR SelectedScenario = SELECTEDVALUE(Scenario[scenario], "base")
RETURN
CALCULATE(
    SUM(Financials[Amount]),
    FILTER(
        ALL(Financials[scenario]),
        Financials[scenario] = "Actual" || Financials[scenario] = SelectedScenario
    )
)
```

Restrict any aggregation to one metric. The Amount measure cannot meaningfully sum different statement lines together. Compute margins from revenue/EBIT values, never sum percentages. FCF = CFO − cash capex. Define USD billions as USDm / 1,000. Retain lease principal as a separate financing line and show finance lease additions as noncash capex. Do not recompute historical CFO from the simplified forecast bridge.

Pages: (1) snapshot / annual trends and cash bridge, (2) drivers / margins and working-capital ratios, (3) scenarios / liquidity and FCF, (4) accuracy / holdout model vs actual and baseline. Forecast years require distinct colors or dashed treatment and labels. Show fiscal convention, sources, as-of scope and metric definitions.

The preset forecast CSV updates when Python is rerun. Native interactive what-if parameters would need the model equations ported to Power BI; a slicer alone selects precomputed scenarios. No .pbix has been created or validated.
