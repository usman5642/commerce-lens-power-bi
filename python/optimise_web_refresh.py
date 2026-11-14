import csv,json,zlib,base64
from pathlib import Path
p=Path(__file__).resolve().parent.parent;w=p/'web-build'
b=json.loads((p/'Retail Performance/Retail Performance.SemanticModel/model.bim').read_text())
m=(w/'RetailSource.pq').read_text()
start=m[:m.index('    WithinFirst =')]
# The fact query does one exact deduplication, without constructing million-row audit joins.
body='''    Unique = Table.Distinct(Original, Keys),
    Codes = Table.TransformColumns(Unique,{{"InvoiceNo",each Text.Upper(Text.Trim(Text.From(_))),type text},{"StockCode",each Text.Upper(Text.Trim(Text.From(_))),type text},{"Country",each Text.Trim(_),type text}}),
    Countries = Table.TransformColumns(Codes,{{"Country",each if _="EIRE" then "Ireland" else if _="USA" then "United States" else if _="RSA" then "South Africa" else _,type text}}),
    NonMerchandise = {"POST","DOT","M","C2","D","S","BANK CHARGES","AMAZONFEE","ADJUST","ADJUST2","B","CRUK","TEST001","TEST002"},
    Valid = Table.SelectRows(Countries,each
        let Credit = Text.StartsWith([InvoiceNo],"C"), Digits = if Credit then Text.Range([InvoiceNo],1) else [InvoiceNo]
        in [UnitPrice]>0 and not List.Contains(NonMerchandise,[StockCode]) and not Text.StartsWith([StockCode],"GIFT_") and Text.Length(Digits)=6 and Text.Select(Digits,{"0".."9"})=Digits and ((Credit and [Quantity]<0) or (not Credit and [Quantity]>0))),
    CustomerKey = Table.AddColumn(Valid,"CustomerKey",each if [CustomerID]=null then "Unknown" else Number.ToText([CustomerID],"0","en-GB"),type text),
    AddDate = Table.AddColumn(CustomerKey,"Date",each Date.From([InvoiceDate]),type date),
    TransactionType = Table.AddColumn(AddDate,"TransactionType",each if [Quantity]>0 then "Sale" else "Credit",type text),
    LineValue = Table.AddColumn(TransactionType,"LineValue",each Number.Round([Quantity]*[UnitPrice],4),Currency.Type),
    GrossSales = Table.AddColumn(LineValue,"GrossSales",each if [TransactionType]="Sale" then [LineValue] else 0,Currency.Type),
    CreditValue = Table.AddColumn(GrossSales,"CreditValue",each if [TransactionType]="Credit" then -[LineValue] else 0,Currency.Type),
    SaleUnits = Table.AddColumn(CreditValue,"SaleUnits",each if [TransactionType]="Sale" then [Quantity] else 0,Int64.Type),
    CreditUnits = Table.AddColumn(SaleUnits,"CreditUnits",each if [TransactionType]="Credit" then -[Quantity] else 0,Int64.Type),
    Sales = Table.TransformColumnTypes(Table.SelectColumns(CreditUnits,{"RowID","InvoiceNo","Date","StockCode","CustomerKey","Country","TransactionType","Quantity","UnitPrice","LineValue","GrossSales","CreditValue","SaleUnits","CreditUnits"}),{{"UnitPrice",Currency.Type}})
in
    Sales
'''
queries={'Sales':start+body}
for t in b['model']['tables']:
 name=t['name']
 if name not in ['Product','Country','Customer','RowAudit','QualityMonthly']:continue
 with (p/f'data/model/{name}.csv').open(newline='') as f:
  r=csv.reader(f);header=next(r);rows=list(r)
 raw=json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode();comp=zlib.compress(raw)[2:-4];enc=base64.b64encode(comp).decode()
 assert json.loads(zlib.decompress(base64.b64decode(enc),-15))==rows
 types={'string':'type text','int64':'Int64.Type','decimal':'Currency.Type','dateTime':'type date'}
 pairs=','.join('{'+json.dumps(c['name'])+','+types[c['dataType']]+'}' for c in t['columns'])
 code='// Verified snapshot derived from UCI Online Retail II by build/clean_retail.py.\n// Fixed historical dataset; regenerate alongside Sales if the source snapshot changes.\nlet\n    Rows = Json.Document(Binary.Decompress(Binary.FromText("'+enc+'",BinaryEncoding.Base64),Compression.Deflate)),\n    Source = Table.FromRows(Rows,'+json.dumps(header).replace('[','{').replace(']','}')+'),\n    Typed = Table.TransformColumnTypes(Source,{'+pairs+'},"en-GB")\nin\n    Typed\n'
 queries[name]=code
parts=['createOrReplace\n']
for name,code in queries.items():
 (w/(name+'-optimised.pq')).write_text(code)
 parts.append('    ref table '+name+'\n        partition '+name+' = m\n            mode: import\n            source =\n'+''.join('                '+line+'\n' for line in code.splitlines())+'\n')
for target,col in [('Date','Date'),('Product','StockCode'),('Country','Country'),('Customer','CustomerKey')]:
 parts.append(f'    relationship Sales_{target}\n        fromColumn: Sales.{col}\n        toColumn: {target}.{col}\n        crossFilteringBehavior: oneDirection\n\n')
(w/'Optimised refresh and relationships.tmdl').write_text(''.join(parts))
print({k:len(v) for k,v in queries.items()});print('TMDL bytes',sum(map(len,parts)))
