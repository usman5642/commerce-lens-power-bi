# Test record

This page separates three kinds of evidence. Please read the labels before relying on a number.

| Label | Meaning |
|---|---|
| **Re-runnable** | A script in `validation/` that anyone can run against the CSVs in `data/`. |
| **Recorded in Power BI Service** | Run on 14 November 2026 in a browser session in Power BI Service, operated by an AI coding agent (Codex) on my behalf. The values below were copied from the saved page snapshots. The raw snapshots stay private because they also show my workspace navigation. These tests have not been re-run for this repository. |
| **Not tested** | Nobody has run this yet. |

## Re-runnable checks (CSV level)

| Script | What it checks | Result when last run |
|---|---|---|
| `validation/verify_final.py` | Standard-library Decimal reconciliation of eight scenarios; nine assertions | PASS: 9 reconciliation assertions (`validation/independent_reconciliation.json`) |
| `validation/independent_claims_check.py` | Separate pandas implementation; 11 data-shape invariants plus every figure quoted in the README | 32/32 checks passed (`validation/independent_claims_check_output.json`) |
| `sql/independent_metric_checks.sql` | One SQL aggregate for January to November 2011 | Run in SQLite against `Sales.csv`: net £8,572,828.10, 17,407 orders, 4,168 identified buyers (`validation/sql_check_output.txt`) |

## Recorded in Power BI Service

All values are as displayed. The default view is Year 2011, Month coverage Complete, Market All.

### Native DAX queries (DAX query view)

| Case | Net | Like-for-like prior | Caption / result |
|---|---|---|---|
| 2011, complete months | 8,572,828.10 | 8,377,737.82 | +2.3% vs same dates a year earlier |
| 2011, partial month (1 to 9 Dec) | 440,399.56 | 401,141.88 | +9.8% (displayed as 0.1 in the raw grid) |
| 2010, complete months | 9,135,828.32 | blank | Full-period prior-year coverage unavailable |
| 2010 with Month coverage = Partial (no such dates exist) | blank | blank | No sales in selection |
| 2010 and 2011 together | 17,708,656.43 | blank | Full-period prior-year coverage unavailable |

The query in `validation/service_native_checks.dax` covers the last four rows. It completed in 2,232 ms in that session. Orders and identified buyers were also returned: 17,407 and 4,168 (2011), 816 and 614 (partial), 19,627 and 4,205 (2010).

### Reading-view interaction tests

| Action | KPI values shown | Comparison caption |
|---|---|---|
| Default view | £8.57M · 17,407 orders · £509 · 3.2% · 4,168 buyers · 86.5% with customer ID | +2.3% vs same dates a year earlier |
| Month coverage = Partial | £440.40K · 816 · £753 · 28.3% · 614 · 83.4% | +9.8% vs same dates a year earlier |
| Year = 2010 | £9.14M · 19,627 · £478 · 2.5% · 4,205 · 87.7% | Full-period prior-year coverage unavailable |
| Market = UK | £7.19M · 15,717 · £474 · 3.4% · 3,769 · 84.3% | +0.2% |
| Market = International | £1.38M · 1,690 · £834 · 2.0% · 399 · 98.1% | +15.1% |
| Click the Netherlands bar | £263.00K · 87 · £3K · 0.2% · 8 · 100.0% | +6.2% |
| Click the Regency Cakestand heatmap row | £131.85K · 1,757 · £80 · 6.1% · 836 · 85.5% | −11.9% |
| Reset to default | Restores 2011 / Complete / All | |
| Save and reload | Implementation and default selection preserved | |

Other recorded results:

- **Performance Analyzer:** one capture recorded visual durations of 108 to 1,342 ms. That is one session's measurement, not a performance guarantee.
- **Layout:** inspected in a 1440 × 900 browser window, where the report rendered at 68% zoom.

**Log order.** Some logs were captured before the last two caption fixes. The earliest 2010 log shows "No comparable prior-year period", and one later 2010 log still shows the earlier map caption ("Mapped countries: 99.7% of net sales ..."). The final wording is in `powerbi/model/commerce-lens-fix-*.tmdl` and in the screenshot.

## Agreement between the two pipelines

The Power BI model builds its Sales table with Power Query (`powerbi/power-query/Sales.pq`) straight from the UCI workbook. The CSVs were produced by a separate pandas script (`python/clean_retail.py`). The recorded Service results above match the CSV recomputation for these aggregates:

- **2011 complete:** net sales, orders and identified buyers.
- **2011 partial:** the same three figures.
- **2010:** net sales and orders.

A row-by-row comparison of the PBIX tables was not possible because the exported PBIX data could not be decoded outside Power BI.

## Not tested

- Opening or refreshing the PBIX in Power BI Desktop.
- A full rebuild on a clean machine.
- Refresh from the UCI URL.
- Re-running the Python cleaning from the raw workbook.
- Mobile layout (none is defined).
- Keyboard and screen-reader use.
- Interactivity in this repository: a screenshot cannot show it.


## Publication finalisation checks — 14 November 2026

The pandas checker now asserts that the top-ten product share rounds to 8.1%, instead of recording an unconditional pass. It exits with status 1 if any check fails. All 32 checks passed after this change.

The nine standard-library assertions were also run from a fresh copy of the repository with the prepared data Release extracted into `data/`. This tests the documented CSV verification route, not a Power BI rebuild.

A disposable copy of the checker was given an intentionally wrong expected net-sales value. It reported 31/32 passes and returned exit status 1. The published script and source data were unchanged by that failure-path test. See `validation/failure_path_test.txt`.
