from pathlib import Path
import json, hashlib, importlib.util
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'data/raw/online_retail_II.xlsx'
engine = 'calamine' if importlib.util.find_spec('python_calamine') else 'openpyxl'
book = pd.ExcelFile(source, engine=engine)
frames=[]
summary={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sheets':{}}
for sheet in book.sheet_names:
    f=pd.read_excel(book, sheet_name=sheet)
    f.columns=f.columns.str.strip()
    f=f.rename(columns={'Invoice':'InvoiceNo','Price':'UnitPrice','Customer ID':'CustomerID'})
    summary['sheets'][sheet]={'rows':len(f),'columns':list(f.columns),'start':str(f.InvoiceDate.min()),'end':str(f.InvoiceDate.max()),'missing':{k:int(v) for k,v in f.isna().sum().items()}}
    f['SourceSheet']=sheet
    f['SourceRow']=range(2,len(f)+2)
    frames.append(f)
    print(sheet, len(f), flush=True)
raw=pd.concat(frames,ignore_index=True)
cols=['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country']
summary['raw_rows']=len(raw)
summary['exact_duplicates']=int(raw.duplicated(subset=cols).sum())
summary['negative_price']=int((raw.UnitPrice<0).sum())
summary['zero_price']=int((raw.UnitPrice==0).sum())
summary['negative_quantity']=int((raw.Quantity<0).sum())
summary['non_numeric_stock_codes']=raw.loc[~raw.StockCode.astype(str).str.match(r'^\d{5}[A-Za-z]*$'),['StockCode','Description']].value_counts().head(50).to_string()
summary['nonstandard_invoices']=raw.loc[~raw.InvoiceNo.astype(str).str.match(r'^(C)?\d{6}$'),'InvoiceNo'].astype(str).value_counts().head(20).to_dict()
raw.to_pickle(ROOT/'data/raw/source_snapshot.pkl')
(ROOT/'qa/source_profile.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2),flush=True)
