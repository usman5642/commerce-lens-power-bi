"""Independent standard-library reconciliation of the public retail snapshot."""
import csv, json
from decimal import Decimal
from pathlib import Path

# Public-repository layout: this script lives in validation/, the CSVs in data/.
# Sales.csv is distributed as a Release asset; extract it into data/ first.
ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / 'data'
if not (DATA / 'Sales.csv').exists():
    raise SystemExit('data/Sales.csv not found: download the cleaned-data ZIP from the Releases page and extract it into data/')
scenarios = {
    'default_2011': ('2011-01-01', '2011-11-30', None),
    'prior_default': ('2010-01-01', '2010-11-30', None),
    'partial_2011': ('2011-12-01', '2011-12-09', None),
    'prior_partial': ('2010-12-01', '2010-12-09', None),
    'full_2010': ('2010-01-01', '2010-12-31', None),
    'uk_2011': ('2011-01-01', '2011-11-30', 'UK'),
    'international_2011': ('2011-01-01', '2011-11-30', 'International'),
    'netherlands_2011': ('2011-01-01', '2011-11-30', 'Netherlands'),
}
agg = {k: dict(gross=Decimal(0), credits=Decimal(0), orders=set(), buyers=set()) for k in scenarios}
products = {}
for row in csv.DictReader((DATA / 'Sales.csv').open()):
    d, country = row['Date'], row['Country']
    for name, (start, end, market) in scenarios.items():
        if not start <= d <= end:
            continue
        if market == 'UK' and country != 'United Kingdom':
            continue
        if market == 'International' and country == 'United Kingdom':
            continue
        if market == 'Netherlands' and country != market:
            continue
        a = agg[name]
        a['gross'] += Decimal(row['GrossSales'])
        a['credits'] += Decimal(row['CreditValue'])
        if row['TransactionType'] == 'Sale':
            a['orders'].add(row['InvoiceNo'])
            if row['CustomerKey'] != 'Unknown':
                a['buyers'].add(row['CustomerKey'])
    if '2011-01-01' <= d <= '2011-11-30':
        code = row['StockCode']
        products[code] = products.get(code, Decimal(0)) + Decimal(row['GrossSales']) - Decimal(row['CreditValue'])
out = {}
for k, a in agg.items():
    out[k] = dict(net=str(a['gross']-a['credits']), gross=str(a['gross']),
                  credits=str(a['credits']), orders=len(a['orders']), buyers=len(a['buyers']))
assert abs(Decimal(out['default_2011']['net']) - Decimal('8572828.103')) < Decimal('.01')
assert out['default_2011']['orders'] == 17407
assert out['default_2011']['buyers'] == 4168
assert abs(Decimal(out['prior_default']['net']) - Decimal('8377737.824')) < Decimal('.01')
assert abs(Decimal(out['partial_2011']['net']) - Decimal('440399.56')) < Decimal('.01')
assert abs(Decimal(out['prior_partial']['net']) - Decimal('401141.88')) < Decimal('.01')
assert abs(Decimal(out['uk_2011']['net']) - Decimal('7192114.073')) < Decimal('.01')
assert abs(Decimal(out['international_2011']['net']) - Decimal('1380714.03')) < Decimal('.01')
out['top10_product_total'] = str(sum(sorted(products.values(), reverse=True)[:10]))
assert abs(Decimal(out['top10_product_total']) - Decimal('695321.33')) < Decimal('.01')
out['regency_cakestand_net'] = str(products['22423'])
out['status'] = 'PASS: 9 reconciliation assertions'
(ROOT / 'independent_reconciliation.json').write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
