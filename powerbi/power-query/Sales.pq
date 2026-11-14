let
    Workbook = Excel.Workbook(Web.Contents("https://archive.ics.uci.edu/ml/machine-learning-databases/00502/online_retail_II.xlsx"), null, true),
    ReadSheet = (sheet as text) as table =>
        let
            Headers = Table.PromoteHeaders(Workbook{[Item=sheet, Kind="Sheet"]}[Data], [PromoteAllScalars=true]),
            Names = Table.RenameColumns(Headers, {{"Invoice","InvoiceNo"},{"Price","UnitPrice"},{"Customer ID","CustomerID"}}),
            Typed = Table.TransformColumnTypes(Names, {{"Description",type text},{"Quantity",Int64.Type},{"InvoiceDate",type datetime},{"UnitPrice",type number},{"CustomerID",Int64.Type},{"Country",type text}}),
            Rows = Table.AddIndexColumn(Typed,"SourceRow",2,1,Int64.Type),
            SheetName = Table.AddColumn(Rows,"SourceSheet",each sheet,type text)
        in SheetName,
    Original = Table.Buffer(Table.AddIndexColumn(Table.Combine({ReadSheet("Year 2009-2010"), ReadSheet("Year 2010-2011")}),"RowID",1,1,Int64.Type)),
    Keys = {"InvoiceNo","StockCode","Description","Quantity","InvoiceDate","UnitPrice","CustomerID","Country"},
    Unique = Table.Distinct(Original, Keys),
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
