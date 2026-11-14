# Python cleaning scripts

These are the original scripts behind the CSVs in `data/`. They are published so the cleaning rules can be read and checked. They were **not re-run** for this repository.

| Script | Purpose |
|---|---|
| `profile_data.py` | Reads the two sheets of `online_retail_II.xlsx`, profiles them and saves a combined snapshot. |
| `clean_retail.py` | Gives every source row one disposition, builds the fact and dimension tables, and asserts 17 data checks. |
| `optimise_web_refresh.py` | A build helper. It generated the Power Query and TMDL files in `powerbi/` from the cleaned tables. |

## Before running

The scripts expect a working folder that this repository does not include:

```
<project>/
  data/raw/online_retail_II.xlsx   # download from the UCI page (see data/README.md)
  data/model/                      # outputs are written here
  qa/                              # must exist before running clean_retail.py
  build/profile_data.py
  build/clean_retail.py
```

`optimise_web_refresh.py` also expects a Power BI project folder and a `web-build` folder. It is kept as a record of how the model files were generated, not as a runnable step.

The scripts need pandas and numpy. `profile_data.py` also needs openpyxl or python-calamine. `validation/verify_final.py` uses the standard library only.
