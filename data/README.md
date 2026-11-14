# Data

## Source and licence

Chen, D. (2012). *Online Retail II* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D

Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/

The source describes all transactions of a UK-based, non-store online retailer between 1 December 2009 and 9 December 2011, in pounds sterling. Customer IDs are the numeric identifiers supplied in the source; there are no names or contact details.

## Changes made to the source

These tables are derived from the source and are not the original file. The changes were:

- **Exact duplicates removed.** Duplicates were matched on all eight original columns, within and across the two source sheets, before any normalisation.
- **Codes cleaned.** Invoice and stock codes were trimmed and upper-cased.
- **Country names standardised.** EIRE, USA and RSA were renamed Ireland, United States and South Africa.
- **Excluded rows:**
  - zero or negative unit prices;
  - non-merchandise and test stock codes, such as postage, bank charges, manual adjustments and gift vouchers;
  - invoice numbers that are not six digits with an optional leading C;
  - rows where the invoice type and the sign of the quantity disagree.
- **Sales and credits split.** Sale lines are positive quantities on ordinary invoices. Credit lines are negative quantities on C-prefixed invoices.
- **Missing customer IDs kept.** They are labelled `Unknown` rather than deleted.
- **Product labels.** Each stock code is labelled with its most frequent cleaned description.
- **Audit tables added.** A row-disposition audit and monthly data-quality counts were added.

Every one of the 1,067,371 source rows gets exactly one disposition in `RowAudit.csv`.

## Files

| File | Rows | Kept in Git? |
|---|---|---|
| `Sales.csv` | 1,021,272 | **No.** It is 90.4 MiB. Download `commerce-lens-cleaned-data.zip` from the Releases page and extract it here. |
| `Product.csv` | 4,739 | Yes |
| `Customer.csv` | 5,876 (5,875 IDs plus `Unknown`) | Yes |
| `Country.csv` | 43 | Yes |
| `Date.csv` | 1,095 (2009 to 2011) | Yes |
| `PurchaseBand.csv` | 4 | Yes |
| `RowAudit.csv` | 126 | Yes |
| `QualityMonthly.csv` | 25 | Yes |
