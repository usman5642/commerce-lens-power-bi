let
    Days = Table.FromList(List.Dates(#date(2009,1,1),1095,#duration(1,0,0,0)),Splitter.SplitByNothing(),{"Date"}),
    Typed = Table.TransformColumnTypes(Days,{{"Date",type date}}),
    Year = Table.AddColumn(Typed,"Year",each Date.Year([Date]),Int64.Type),
    MonthNumber = Table.AddColumn(Year,"MonthNumber",each Date.Month([Date]),Int64.Type),
    MonthName = Table.AddColumn(MonthNumber,"MonthName",each Date.ToText([Date],"MMM","en-GB"),type text),
    YearMonth = Table.AddColumn(MonthName,"YearMonth",each Date.ToText([Date],"yyyy-MM","en-GB"),type text),
    YearMonthSort = Table.AddColumn(YearMonth,"YearMonthSort",each [Year]*100+[MonthNumber],Int64.Type),
    MonthStart = Table.AddColumn(YearMonthSort,"MonthStart",each Date.StartOfMonth([Date]),type date),
    CompleteMonth = Table.AddColumn(MonthStart,"CompleteMonth",each if [MonthStart]>=#date(2009,12,1) and Date.EndOfMonth([Date])<=#date(2011,12,9) then "Complete" else "Partial / outside source",type text)
in CompleteMonth
