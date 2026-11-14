// Sales
let
    Source = Csv.Document(File.Contents(DataFolder & "/Sales.csv"), [Delimiter=",", Columns=14, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"RowID", Int64.Type}, {"InvoiceNo", type text}, {"Date", type date}, {"StockCode", type text}, {"CustomerKey", type text}, {"Country", type text}, {"TransactionType", type text}, {"Quantity", Int64.Type}, {"UnitPrice", Currency.Type}, {"LineValue", Currency.Type}, {"GrossSales", Currency.Type}, {"CreditValue", Currency.Type}, {"SaleUnits", Int64.Type}, {"CreditUnits", Int64.Type}}, "en-GB")
in
    Typed

// Date
let
    Source = Csv.Document(File.Contents(DataFolder & "/Date.csv"), [Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Date", type date}, {"Year", Int64.Type}, {"MonthNumber", Int64.Type}, {"MonthName", type text}, {"YearMonth", type text}, {"YearMonthSort", Int64.Type}, {"MonthStart", type date}, {"CompleteMonth", type text}}, "en-GB")
in
    Typed

// Product
let
    Source = Csv.Document(File.Contents(DataFolder & "/Product.csv"), [Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"StockCode", type text}, {"Product", type text}, {"DescriptionVariants", Int64.Type}, {"ProductLabel", type text}}, "en-GB")
in
    Typed

// Country
let
    Source = Csv.Document(File.Contents(DataFolder & "/Country.csv"), [Delimiter=",", Columns=2, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Country", type text}, {"Market", type text}}, "en-GB")
in
    Typed

// Customer
let
    Source = Csv.Document(File.Contents(DataFolder & "/Customer.csv"), [Delimiter=",", Columns=2, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"CustomerKey", type text}, {"Identified", type text}}, "en-GB")
in
    Typed

// RowAudit
let
    Source = Csv.Document(File.Contents(DataFolder & "/RowAudit.csv"), [Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Month", type date}, {"Disposition", type text}, {"Rows", Int64.Type}, {"SignedLineValue", Currency.Type}, {"DispositionOrder", Int64.Type}}, "en-GB")
in
    Typed

// QualityMonthly
let
    Source = Csv.Document(File.Contents(DataFolder & "/QualityMonthly.csv"), [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Month", type date}, {"RawRows", Int64.Type}, {"MissingCustomerRows", Int64.Type}, {"MissingDescriptionRows", Int64.Type}, {"IncludedRows", Int64.Type}, {"UnidentifiedGrossSales", Currency.Type}}, "en-GB")
in
    Typed

// PurchaseBand
let
    Source = Csv.Document(File.Contents(DataFolder & "/PurchaseBand.csv"), [Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Band", type text}, {"MinOrders", Int64.Type}, {"MaxOrders", Int64.Type}, {"BandOrder", Int64.Type}}, "en-GB")
in
    Typed