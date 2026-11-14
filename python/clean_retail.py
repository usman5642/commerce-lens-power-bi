"""Reproducible cleaning and analytical controls for UCI Online Retail II.

Amounts are invoice-line values in GBP, not accounting revenue or profit.
Duplicates are identified on all eight original business columns before
normalisation. Every original row receives one mutually exclusive disposition.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/model'
OUT.mkdir(exist_ok=True)
f=pd.read_pickle(ROOT/'data/raw/source_snapshot.pkl')
COLS=['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country']
f['RowID']=np.arange(1,len(f)+1)
within=f.duplicated(COLS+['SourceSheet'])
all_dups=f.duplicated(COLS)
f['Disposition']=np.where(within,'Duplicate within sheet',np.where(all_dups,'Duplicate across sheets','Pending'))
f['RawLineValue']=f.Quantity*f.UnitPrice
f['Date']=pd.to_datetime(f.InvoiceDate).dt.normalize()
f['Month']=f.Date.dt.to_period('M').dt.to_timestamp()
for col in ['InvoiceNo','StockCode','Country']:
    f[col]=f[col].astype(str).str.strip()
f['InvoiceNo']=f.InvoiceNo.str.upper()
f['StockCode']=f.StockCode.str.upper()
f['DescriptionClean']=f.Description.fillna('').astype(str).str.replace(r'\s+',' ',regex=True).str.strip().str.upper()
f['CustomerKey']=f.CustomerID.map(lambda x: 'Unknown' if pd.isna(x) else str(int(x)))
f['Country']=f.Country.replace({'EIRE':'Ireland','USA':'United States','RSA':'South Africa'})
NON_MERCH={'POST','DOT','M','C2','D','S','BANK CHARGES','AMAZONFEE','ADJUST','ADJUST2','B','CRUK','TEST001','TEST002'}
def classify(mask,reason):
    f.loc[f.Disposition.eq('Pending') & mask,'Disposition']=reason
classify(f.UnitPrice.le(0),'Zero or negative unit price')
classify(f.StockCode.isin(NON_MERCH)|f.StockCode.str.startswith('GIFT_'),'Non-merchandise or test line')
classify(~f.InvoiceNo.str.match(r'^(C)?\d{6}$'),'Non-standard invoice')
credit=f.InvoiceNo.str.startswith('C') & f.Quantity.lt(0)
sale=~f.InvoiceNo.str.startswith('C') & f.Quantity.gt(0)
classify(~(credit|sale),'Invoice and quantity mismatch')
classify(sale,'Included sale')
classify(credit,'Included credit')
assert not f.Disposition.eq('Pending').any()
included=f.Disposition.str.startswith('Included')
g=f.loc[included].copy()
g['TransactionType']=np.where(g.Disposition.eq('Included sale'),'Sale','Credit')
g['LineValue']=g.RawLineValue.round(4)
g['GrossSales']=np.where(g.TransactionType.eq('Sale'),g.LineValue,0.0)
g['CreditValue']=np.where(g.TransactionType.eq('Credit'),-g.LineValue,0.0)
g['SaleUnits']=np.where(g.TransactionType.eq('Sale'),g.Quantity,0)
g['CreditUnits']=np.where(g.TransactionType.eq('Credit'),-g.Quantity,0)

# Stable product labels: most frequent non-empty description, alphabetical tie-break.
labels=(g.loc[g.DescriptionClean.ne('')].groupby(['StockCode','DescriptionClean']).size()
        .reset_index(name='LabelFrequency').sort_values(['StockCode','LabelFrequency','DescriptionClean'],ascending=[True,False,True]))
products=labels.drop_duplicates('StockCode')[['StockCode','DescriptionClean']].rename(columns={'DescriptionClean':'Product'})
variants=labels.groupby('StockCode').size().rename('DescriptionVariants')
products=products.merge(variants,on='StockCode',validate='one_to_one')
products['Product']=products.Product.str.title()
products['ProductLabel']=products.StockCode+' · '+products.Product
assert set(g.StockCode)<=set(products.StockCode)
countries=pd.DataFrame({'Country':sorted(g.Country.unique())})
countries['Market']=np.where(countries.Country.eq('United Kingdom'),'United Kingdom','International / unspecified')
customers=pd.DataFrame({'CustomerKey':sorted(g.CustomerKey.unique())})
customers['Identified']=np.where(customers.CustomerKey.eq('Unknown'),'Unidentified','Identified')
dates=pd.DataFrame({'Date':pd.date_range(f.Date.min().replace(month=1,day=1),f.Date.max().replace(month=12,day=31))})
dates['Year']=dates.Date.dt.year
dates['MonthNumber']=dates.Date.dt.month
dates['MonthName']=dates.Date.dt.strftime('%b')
dates['YearMonth']=dates.Date.dt.strftime('%Y-%m')
dates['YearMonthSort']=dates.Year*100+dates.MonthNumber
dates['MonthStart']=dates.Date.dt.to_period('M').dt.to_timestamp()
dates['CompleteMonth']=np.where((dates.MonthStart>=f.Date.min()) & ((dates.MonthStart+pd.offsets.MonthEnd(0))<=f.Date.max()),'Complete','Partial / outside source')

fact_cols=['RowID','InvoiceNo','Date','StockCode','CustomerKey','Country','TransactionType','Quantity','UnitPrice','LineValue','GrossSales','CreditValue','SaleUnits','CreditUnits']
facts=g[fact_cols].sort_values('RowID')
audit=f.groupby(['Month','Disposition'],as_index=False).agg(Rows=('RowID','size'),SignedLineValue=('RawLineValue','sum'))
sorts={'Duplicate within sheet':1,'Duplicate across sheets':2,'Zero or negative unit price':3,'Non-merchandise or test line':4,'Non-standard invoice':5,'Invoice and quantity mismatch':6,'Included sale':7,'Included credit':8}
audit['DispositionOrder']=audit.Disposition.map(sorts)
quality=f.groupby('Month',as_index=False).agg(RawRows=('RowID','size'),MissingCustomerRows=('CustomerID',lambda x:x.isna().sum()),MissingDescriptionRows=('Description',lambda x:x.isna().sum()))
quality=quality.merge(g.groupby('Month',as_index=False).agg(IncludedRows=('RowID','size'),UnidentifiedGrossSales=('GrossSales',lambda x:x[g.loc[x.index,'CustomerKey'].eq('Unknown')].sum())),on='Month',how='left')
for name,frame in {'Sales':facts,'Date':dates,'Product':products,'Country':countries,'Customer':customers,'RowAudit':audit,'QualityMonthly':quality}.items():
    frame.to_csv(OUT/f'{name}.csv',index=False,date_format='%Y-%m-%d',float_format='%.4f')
g.to_pickle(ROOT/'qa/cleaned_snapshot.pkl')
f.loc[~included,['RowID','SourceSheet','SourceRow']+COLS+['Disposition','RawLineValue']].to_csv(ROOT/'qa/excluded_rows.csv',index=False)
products[products.DescriptionVariants.gt(1)].to_csv(ROOT/'qa/product_label_variants.csv',index=False)

def metrics(h):
    s=h[h.TransactionType.eq('Sale')]
    known=s[s.CustomerKey.ne('Unknown')]
    orders=known.groupby('CustomerKey').InvoiceNo.nunique()
    return {'rows':len(h),'gross_sales':float(h.GrossSales.sum()),'credits':float(h.CreditValue.sum()),'net_sales':float(h.LineValue.sum()),'sales_orders':int(s.InvoiceNo.nunique()),'known_buyers':int(known.CustomerKey.nunique()),'repeat_buyers':int(orders.ge(2).sum()),'repeat_buyer_share':float(orders.ge(2).mean()),'credit_rate':float(h.CreditValue.sum()/h.GrossSales.sum()),'unknown_gross_share':float(s.loc[s.CustomerKey.eq('Unknown'),'GrossSales'].sum()/s.GrossSales.sum()),'gross_aov':float(s.GrossSales.sum()/s.InvoiceNo.nunique())}
summary={'all_history':metrics(g),'2011_jan_nov':metrics(g[g.Date.between('2011-01-01','2011-11-30')]),'2010_jan_nov':metrics(g[g.Date.between('2010-01-01','2010-11-30')]),'row_dispositions':f.Disposition.value_counts().to_dict(),'product_description_variants':int(products.DescriptionVariants.gt(1).sum()),'missing_customer_rows':int(f.CustomerID.isna().sum()),'missing_description_rows':int(f.Description.isna().sum()),'source_rows':len(f),'included_rows':len(g)}
summary['2011_net_yoy']=summary['2011_jan_nov']['net_sales']/summary['2010_jan_nov']['net_sales']-1
focus=g[g.Date.between('2011-01-01','2011-11-30')]
summary['top_countries_2011']=focus.groupby('Country').LineValue.sum().sort_values(ascending=False).head(8).to_dict()
summary['monthly_2011']=focus.groupby(focus.Date.dt.strftime('%Y-%m')).agg(NetSales=('LineValue','sum'),GrossSales=('GrossSales','sum'),Credits=('CreditValue','sum')).round(4).reset_index().to_dict('records')
summary['top_products_2011']=focus.merge(products,on='StockCode',validate='many_to_one').groupby(['StockCode','Product']).agg(NetSales=('LineValue','sum'),Credits=('CreditValue','sum')).sort_values('NetSales',ascending=False).head(10).reset_index().to_dict('records')
known=focus[(focus.TransactionType=='Sale') & (focus.CustomerKey!='Unknown')]
buyer_sales=known.groupby('CustomerKey').GrossSales.sum().sort_values(ascending=False)
summary['top10_buyer_gross_share']=float(buyer_sales.head(10).sum()/buyer_sales.sum())
summary['2011_uk_net_share']=float(focus.loc[focus.Country.eq('United Kingdom'),'LineValue'].sum()/focus.LineValue.sum())
tests={
 'source_row_count':len(f)==1067371,
 'row_reconciliation':int(audit.Rows.sum())==len(f),
 'raw_value_reconciliation':bool(np.isclose(audit.SignedLineValue.sum(),f.RawLineValue.sum(),atol=.0001,rtol=0)),
 'net_equals_gross_less_credits':bool(np.isclose(g.LineValue.sum(),g.GrossSales.sum()-g.CreditValue.sum(),atol=.0001,rtol=0)),
 'no_exact_original_duplicates_remaining':not g.duplicated(COLS).any(),
 'positive_prices':bool(g.UnitPrice.gt(0).all()),
 'sale_and_credit_signs':bool((g.loc[g.TransactionType=='Sale','Quantity'].gt(0).all()) and (g.loc[g.TransactionType=='Credit','Quantity'].lt(0).all())),
 'dates_unique':dates.Date.is_unique,
 'product_key_unique':products.StockCode.is_unique,
 'customer_key_unique':customers.CustomerKey.is_unique,
 'country_key_unique':countries.Country.is_unique,
 'no_orphan_product':set(g.StockCode)<=set(products.StockCode),
 'no_orphan_customer':set(g.CustomerKey)<=set(customers.CustomerKey),
 'no_orphan_country':set(g.Country)<=set(countries.Country),
 'no_orphan_date':set(g.Date)<=set(dates.Date),
 'no_silently_deleted_unknown_customers':bool(g.CustomerKey.eq('Unknown').any()),
 'december_2011_marked_partial':bool(dates.loc[dates.YearMonth.eq('2011-12'),'CompleteMonth'].eq('Partial / outside source').all()),
}
(ROOT/'qa/analysis_summary.json').write_text(json.dumps(summary,indent=2))
(ROOT/'qa/data_checks.json').write_text(json.dumps(tests,indent=2))
assert all(tests.values()),tests
print(json.dumps(summary,indent=2))
print('PASS',len(tests),'data checks')
