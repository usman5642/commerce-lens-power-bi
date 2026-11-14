# Power BI files

## What is here

| Folder | Contents | Status |
|---|---|---|
| `report-definition/` | The report layout exported from the final PBIX: one page, 13 visuals, the custom theme and resources | Read-only reference. **Not a complete PBIP project.** It has no `.pbip` file, no `definition.pbir` and no semantic model folder, so Power BI Desktop cannot open it on its own. |
| `power-query/` | The eight queries used by the published model | Byte-for-byte equal, ignoring whitespace, to the queries inside the final PBIX |
| `power-query/local-csv-variant/` | An earlier set of queries that load the CSVs from a `DataFolder` parameter | Documentation only. Not tested. |
| `model/base-measures.tmdl` | The 36 base measures (sales, customers, ranking, data quality, labels) | Matches the PBIX |
| `model/commerce-lens-measures.tmdl` | 41 measures and three calculated columns added for this report | Applied in the PBIX |
| `model/commerce-lens-fix-*.tmdl` | Two later corrections that replace the matching measures in the file above | Applied in the PBIX |
| `model/partitions-and-relationships.tmdl` | Table partitions (Power Query) and the four relationships | Matches the PBIX |
| `model/sales-table.tmdl` | Column definitions for the Sales table | Reference |

The PBIX also contains 14 measures in a `Diagnostics` folder, which another report on the same model uses. They are not used on this page and are not published here.

## Opening the report

The PBIX is attached to a GitHub Release, not committed to Git. It was exported from Power BI Service. Opening it in Power BI Desktop on Windows **has not been tested**.

The data is imported, so viewing does not need a refresh. A refresh would download the workbook from UCI's legacy URL in `power-query/Sales.pq`, and that has not been tested either.

## Do not reapply the TMDL scripts to the PBIX

The `createOrReplace` scripts are already applied. They are kept so the logic can be read and compared.
