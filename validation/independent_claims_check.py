"""Independent re-computation of every figure used in the Commerce Lens publication drafts.

Written separately from verify_final.py (pandas instead of Decimal loops) so the two
checks do not share code. Reads only the eight cleaned CSVs.
Usage: python3 -I independent_claims_check.py <path to 03_Cleaned_Data> <output.json>
"""
import sys, json
from pathlib import Path
import pandas as pd

D = Path(sys.argv[1]); OUT = Path(sys.argv[2])
s = pd.read_csv(D / 'Sales.csv', dtype={'InvoiceNo': str, 'StockCode': str, 'CustomerKey': str},
                parse_dates=['Date'])
dates = pd.read_csv(D / 'Date.csv', parse_dates=['Date', 'MonthStart'])
prod = pd.read_csv(D / 'Product.csv', dtype={'StockCode': str})
country = pd.read_csv(D / 'Country.csv')
cust = pd.read_csv(D / 'Customer.csv', dtype={'CustomerKey': str})
audit = pd.read_csv(D / 'RowAudit.csv')
qual = pd.read_csv(D / 'QualityMonthly.csv')
band = pd.read_csv(D / 'PurchaseBand.csv')

R = {}; checks = []
def check(name, cond, detail=''):
    checks.append({'check': name, 'pass': bool(cond), 'detail': detail})

# ---------- data-shape invariants (what the cleaned CSVs actually show) ----------
check('net = gross - credits on every row',
      ((s.GrossSales - s.CreditValue - s.LineValue).abs() < 1e-6).all())
check('sales rows positive qty, credits negative qty, never both',
      (s.loc[s.TransactionType.eq('Sale'), 'Quantity'] > 0).all()
      and (s.loc[s.TransactionType.eq('Credit'), 'Quantity'] < 0).all()
      and set(s.TransactionType) == {'Sale', 'Credit'})
check('credit rows are C-prefixed invoices, sale rows are not',
      s.loc[s.TransactionType.eq('Credit'), 'InvoiceNo'].str.startswith('C').all()
      and not s.loc[s.TransactionType.eq('Sale'), 'InvoiceNo'].str.startswith('C').any())
check('all unit prices > 0', (s.UnitPrice > 0).all())
nonmerch = {'POST','DOT','M','C2','D','S','BANK CHARGES','AMAZONFEE','ADJUST','ADJUST2','B','CRUK','TEST001','TEST002'}
check('no non-merchandise or GIFT_ stock codes', not (s.StockCode.isin(nonmerch) | s.StockCode.str.startswith('GIFT_')).any())
check('invoice numbers match ^C?\\d{6}$', s.InvoiceNo.str.match(r'^C?\d{6}$').all())
check('dimension keys unique', prod.StockCode.is_unique and country.Country.is_unique
      and cust.CustomerKey.is_unique and dates.Date.is_unique)
check('no orphan keys in Sales', set(s.StockCode) <= set(prod.StockCode) and set(s.Country) <= set(country.Country)
      and set(s.CustomerKey) <= set(cust.CustomerKey) and set(s.Date) <= set(dates.Date))
check('unknown customers retained, not deleted', (s.CustomerKey == 'Unknown').any())
R['sales_rows'] = len(s)
R['source_rows_in_audit'] = int(audit.Rows.sum())
inc = int(audit.loc[audit.Disposition.str.startswith('Included'), 'Rows'].sum())
check('RowAudit included rows = Sales rows', inc == len(s), f'{inc} vs {len(s)}')
check('RowAudit accounts for 1,067,371 source rows', R['source_rows_in_audit'] == 1067371)
R['audit_by_disposition'] = audit.groupby('Disposition').Rows.sum().sort_values(ascending=False).to_dict()
R['source_first_date'] = str(s.Date.min().date()); R['source_last_date'] = str(s.Date.max().date())
R['countries'] = len(country); R['products'] = len(prod); R['identified_customers'] = int((cust.CustomerKey != 'Unknown').sum())
R['purchase_bands'] = band.to_dict('records')

# ---------- metric engine mirroring the DAX definitions ----------
unmapped = {'Channel Islands', 'European Community', 'Unspecified', 'West Indies', 'Korea'}
def metrics(h):
    gross = h.GrossSales.sum(); credits = h.CreditValue.sum(); net = gross - credits
    sales = h[h.TransactionType.eq('Sale')]
    orders = sales.InvoiceNo.nunique()
    known = sales[sales.CustomerKey.ne('Unknown')]
    per_buyer = known.groupby('CustomerKey').InvoiceNo.nunique()
    bands = {b.Band: int(((per_buyer >= b.MinOrders) & (per_buyer <= b.MaxOrders)).sum()) for b in band.itertuples()}
    unid = h.loc[h.CustomerKey.eq('Unknown'), 'GrossSales'].sum()
    unm = h.loc[h.Country.isin(unmapped)]
    unm_net = unm.GrossSales.sum() - unm.CreditValue.sum()
    return dict(net=round(net, 4), gross=round(gross, 4), credits=round(credits, 4), orders=int(orders),
                buyers=int(per_buyer.size), gross_order_value=round(gross / orders, 2) if orders else None,
                credit_rate_pct=round(100 * credits / gross, 3) if gross else None,
                id_coverage_pct=round(100 * (1 - unid / gross), 2) if gross else None,
                unidentified_pct=round(100 * unid / gross, 2) if gross else None,
                repeat_share_pct=round(100 * (per_buyer >= 2).mean(), 2) if per_buyer.size else None,
                bands=bands, map_coverage_pct=round(100 * (net - unm_net) / net, 2) if net else None,
                unmapped_net=round(unm_net, 2))

def window(a, b, market=None, country_name=None, stock=None):
    h = s[(s.Date >= a) & (s.Date <= b)]
    if market == 'UK': h = h[h.Country.eq('United Kingdom')]
    if market == 'International': h = h[h.Country.ne('United Kingdom')]
    if country_name: h = h[h.Country.eq(country_name)]
    if stock: h = h[h.StockCode.eq(stock)]
    return h

def scenario(name, cur, prior, **kw):
    c = metrics(window(*cur, **kw)); out = {'current_window': cur, 'filters': kw, **c}
    if prior:
        p = metrics(window(*prior, **kw)); out['prior_window'] = prior; out['prior_net'] = p['net']
        out['net_yoy_pct'] = round(100 * (c['net'] - p['net']) / p['net'], 4)
        out['orders_yoy_pct'] = round(100 * (c['orders'] - p['orders']) / p['orders'], 2)
        out['buyers_yoy_pct'] = round(100 * (c['buyers'] - p['buyers']) / p['buyers'], 2)
        out['gov_yoy_pct'] = round(100 * (c['gross_order_value'] - p['gross_order_value']) / p['gross_order_value'], 2)
        out['credit_rate_change_pp'] = round(c['credit_rate_pct'] - p['credit_rate_pct'], 2)
    else:
        out['prior_net'] = None
    R[name] = out
    return out

J11 = ('2011-01-01', '2011-11-30'); J10 = ('2010-01-01', '2010-11-30')
scenario('default_2011_complete_all', J11, J10)
scenario('partial_2011_1to9_dec', ('2011-12-01', '2011-12-09'), ('2010-12-01', '2010-12-09'))
scenario('full_2010_complete', ('2010-01-01', '2010-12-31'), None)
scenario('uk_2011_complete', J11, J10, market='UK')
scenario('international_2011_complete', J11, J10, market='International')
scenario('netherlands_2011_complete', J11, J10, country_name='Netherlands')
scenario('regency_cakestand_2011_complete', J11, J10, stock='22423')

# ---------- the specific checks behind the drafts ----------
d = R['default_2011_complete_all']
check('default net £8,572,828.10', abs(d['net'] - 8572828.103) < 0.01, d['net'])
check('default orders 17,407 / buyers 4,168', d['orders'] == 17407 and d['buyers'] == 4168)
check('default like-for-like +2.3%', round(d['net_yoy_pct'], 1) == 2.3, d['net_yoy_pct'])
check('default gross order value shows as £509', round(d['gross_order_value']) == 509, d['gross_order_value'])
check('default credit/gross 3.2%', round(d['credit_rate_pct'], 1) == 3.2, d['credit_rate_pct'])
check('default customer-ID coverage 86.5% of gross', round(d['id_coverage_pct'], 1) == 86.5, d['id_coverage_pct'])
check('default repeat share 62.6%', round(d['repeat_share_pct'], 1) == 62.6, d['repeat_share_pct'])
check('default bands 1,559 / 1,273 / 1,026 / 310', list(d['bands'].values()) == [1559, 1273, 1026, 310], d['bands'])
check('default map coverage 99.7%', round(d['map_coverage_pct'], 1) == 99.7, d['map_coverage_pct'])
p = R['partial_2011_1to9_dec']
check('partial +9.8%, £440,399.56 vs £401,141.88', round(p['net_yoy_pct'], 1) == 9.8 and abs(p['net'] - 440399.56) < .01)
check('partial credit rate 28.3%, ID gap 16.6%, GOV £753',
      round(p['credit_rate_pct'], 1) == 28.3 and round(p['unidentified_pct'], 1) == 16.6 and round(p['gross_order_value']) == 753,
      (p['credit_rate_pct'], p['unidentified_pct'], p['gross_order_value']))
f = R['full_2010_complete']
check('2010: £9.14M, 19,627 orders, 4,205 buyers, no PY', round(f['net'] / 1e6, 2) == 9.14 and f['orders'] == 19627 and f['buyers'] == 4205)
u = R['uk_2011_complete']; i = R['international_2011_complete']
check('UK £7.19M, +0.2%', round(u['net'] / 1e6, 2) == 7.19 and round(u['net_yoy_pct'], 1) == 0.2, u['net_yoy_pct'])
check('International £1.38M, 1,690 orders, 399 buyers, +15.1%',
      round(i['net'] / 1e6, 2) == 1.38 and i['orders'] == 1690 and i['buyers'] == 399 and round(i['net_yoy_pct'], 1) == 15.1, i['net_yoy_pct'])
n = R['netherlands_2011_complete']
check('Netherlands £262,997.04, 87 orders, 8 buyers, +6.2%',
      abs(n['net'] - 262997.04) < .01 and n['orders'] == 87 and n['buyers'] == 8 and round(n['net_yoy_pct'], 1) == 6.2, n['net_yoy_pct'])
rc = R['regency_cakestand_2011_complete']
check('Regency Cakestand £131.85K, 1,757 orders', round(rc['net'] / 1e3, 2) == 131.85 and rc['orders'] == 1757, (rc['net'], rc['orders']))

# heatmap (top 10 products by net, 2011 complete) and international top 8
f11 = window(*J11).assign(Net=lambda x: x.GrossSales - x.CreditValue)
top = f11.groupby('StockCode').Net.sum().sort_values(ascending=False).head(10)
R['top10_products_2011'] = [{'stock': k, 'product': prod.set_index('StockCode').Product[k], 'net': round(v, 2)} for k, v in top.items()]
R['top10_total'] = round(top.sum(), 2)
check('top-10 product total £695.3K', round(top.sum() / 1e3, 1) == 695.3, R['top10_total'])
check('top-10 share of default net rounds to 8.1%', round(100 * top.sum() / d['net'], 1) == 8.1, round(100 * top.sum() / d['net'], 2))
R['top10_share_of_net_pct'] = round(100 * top.sum() / d['net'], 2)
heat = f11[f11.StockCode.isin(top.index)].groupby(['StockCode', f11.Date.dt.month]).Net.sum().unstack()
R['heatmap_blank_cells'] = {k: [int(m) for m in range(1, 12) if m not in heat.columns or pd.isna(heat.loc[k, m])] for k in top.index}
R['heatmap_negative_cells'] = {k: [int(m) for m in heat.columns if heat.loc[k, m] < 0] for k in top.index if (heat.loc[k] < 0).any()}
intl = f11[f11.Country.ne('United Kingdom')].groupby('Country').Net.sum().sort_values(ascending=False)
R['international_top8_2011'] = {k: round(v, 2) for k, v in intl.head(8).items()}
check('international top 8 order', list(intl.head(8).index) == ['Netherlands', 'Ireland', 'Germany', 'France', 'Australia', 'Switzerland', 'Spain', 'Belgium'], list(intl.head(8).index))
R['uk_share_of_default_net_pct'] = round(100 * u['net'] / d['net'], 2)
mon = f11.groupby(f11.Date.dt.strftime('%Y-%m')).Net.sum()
R['peak_month_2011_complete'] = mon.idxmax(); R['peak_month_net'] = round(mon.max(), 2)
R['monthly_net_2011'] = {k: round(v, 2) for k, v in mon.items()}

# unidentified bias by market (context for the coverage card)
for nm, h in [('uk', window(*J11, market='UK')), ('international', window(*J11, market='International'))]:
    sales = h[h.TransactionType.eq('Sale')]
    unk = sales[sales.CustomerKey.eq('Unknown')]; kn = sales[sales.CustomerKey.ne('Unknown')]
    R[f'unidentified_{nm}_pct_of_gross'] = round(100 * unk.GrossSales.sum() / sales.GrossSales.sum(), 2)
    R[f'gov_unknown_{nm}'] = round(unk.GrossSales.sum() / max(unk.InvoiceNo.nunique(), 1), 2)
    R[f'gov_known_{nm}'] = round(kn.GrossSales.sum() / kn.InvoiceNo.nunique(), 2)

# credit posting-date context: largest credit invoices in each window
cr = s[s.TransactionType.eq('Credit')]
def big_credits(a, b, k=3):
    g = cr[(cr.Date >= a) & (cr.Date <= b)].groupby(['InvoiceNo', 'Date']).CreditValue.sum().sort_values(ascending=False).head(k)
    return [{'invoice': i, 'date': str(dt.date()), 'credit': round(v, 2)} for (i, dt), v in g.items()]
R['largest_credits_2011_complete'] = big_credits(*J11)
R['largest_credits_partial_dec_2011'] = big_credits('2011-12-01', '2011-12-09')
pc = cr[(cr.Date >= '2011-12-01') & (cr.Date <= '2011-12-09')]
R['partial_credit_share_of_largest_invoice_pct'] = round(100 * R['largest_credits_partial_dec_2011'][0]['credit'] / pc.CreditValue.sum(), 1)
# same-day match: does the biggest Dec-2011 credit mirror a same-day sale of the same item and qty?
top_inv = R['largest_credits_partial_dec_2011'][0]['invoice']
row = cr[cr.InvoiceNo.eq(top_inv)].iloc[0]
twin = s[(s.TransactionType.eq('Sale')) & (s.StockCode.eq(row.StockCode)) & (s.Quantity.eq(-row.Quantity)) & (s.CustomerKey.eq(row.CustomerKey))]
R['largest_partial_credit_detail'] = {'stock': row.StockCode, 'qty': int(row.Quantity), 'date': str(row.Date.date()),
                                      'matching_sales': twin[['InvoiceNo', 'Date']].astype(str).to_dict('records')}
ex = p['credits'] - R['largest_credits_partial_dec_2011'][0]['credit']
R['partial_credit_rate_without_largest_pct'] = round(100 * ex / p['gross'], 2)

# same-day sale/credit pairs: effect on ratios (context for interview notes)
def pair_effect(window_, sale_inv, credit_inv):
    h = window(*window_); sales = h[h.TransactionType.eq('Sale')]
    sale_val = sales.loc[sales.InvoiceNo.eq(sale_inv), 'GrossSales'].sum()
    cred_val = h.loc[h.InvoiceNo.eq(credit_inv), 'CreditValue'].sum()
    g, c, o = h.GrossSales.sum(), h.CreditValue.sum(), sales.InvoiceNo.nunique()
    return {'sale_invoice': sale_inv, 'credit_invoice': credit_inv, 'sale_value': round(sale_val, 2), 'credit_value': round(cred_val, 2),
            'credit_rate_with_pair_pct': round(100 * c / g, 2), 'credit_rate_without_pair_pct': round(100 * (c - cred_val) / (g - sale_val), 2),
            'gov_with_pair': round(g / o, 2), 'gov_without_pair': round((g - sale_val) / (o - 1), 2)}
R['pair_jan_2011_in_default'] = pair_effect(J11, '541431', 'C541433')
R['pair_dec_2011_in_partial'] = pair_effect(('2011-12-01', '2011-12-09'), '581483', 'C581484')
R['pair_jan_2011_share_of_default_credits_pct'] = round(100 * 77183.6 / d['credits'], 1)
unm = f11[f11.Country.isin(unmapped)].groupby('Country').Net.sum().sort_values(ascending=False)
R['unmapped_net_by_country_2011_complete'] = {k: round(v, 2) for k, v in unm.items()}
R['unknown_customer_sales_rows_all_history'] = int(s.CustomerKey.eq('Unknown').sum())

# what the model's ORIGINAL [Net Sales Previous Year] would return (it shifts every selected Date row,
# including Date-table rows after the source ends): partial Dec 2011 -> all of Dec 2010; 2010 -> all of 2009
def net(a, b):
    h = window(a, b); return h.GrossSales.sum() - h.CreditValue.sum()
dec10_full = net('2010-12-01', '2010-12-31'); y2009 = net('2009-01-01', '2009-12-31')
R['original_measure_partial_dec_2011_yoy_pct'] = round(100 * (p['net'] - dec10_full) / dec10_full, 1)
R['original_measure_2010_yoy_pct'] = round(100 * (f['net'] - y2009) / y2009, 1)
R['dec_2010_full_month_net'] = round(dec10_full, 2); R['calendar_2009_net_dec_only'] = round(y2009, 2)
check('original measure: partial Dec 2011 = -41.9%', R['original_measure_partial_dec_2011_yoy_pct'] == -41.9, R['original_measure_partial_dec_2011_yoy_pct'])
check('original measure: 2010 = +1,073.8%', R['original_measure_2010_yoy_pct'] == 1073.8, R['original_measure_2010_yoy_pct'])
R['unidentified_share_default_pct'] = d['unidentified_pct']

R['checks'] = checks
R['summary'] = f"{sum(c['pass'] for c in checks)}/{len(checks)} checks passed"
OUT.write_text(json.dumps(R, indent=2, default=str))
for c in checks: print(('PASS ' if c['pass'] else 'FAIL ') + c['check'] + (f"  [{c['detail']}]" if c['detail'] != '' else ''))
print(R['summary'])

# A failed check must be visible to shell scripts and CI as well as in the JSON.
if not all(c['pass'] for c in checks):
    raise SystemExit(1)
