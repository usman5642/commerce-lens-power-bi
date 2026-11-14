// Verified snapshot derived from UCI Online Retail II by build/clean_retail.py.
// Fixed historical dataset; regenerate alongside Sales if the source snapshot changes.
let
    Rows = Json.Document(Binary.Decompress(Binary.FromText("XZRZchghDETv4m+H0r6cxeX7XyOomYlNvqih5qFWq+Hr60OI+g/LH+KPzw9zkdorq8Ws58tMSWaXu8sXNdHH9+egTJs7qLK777WZA+QQStlzQpaXLbMLfGpKa80/bjWIM81mKQRod8piukB9xLLzrKWdg/jgRpoDtqfKUr5Ae6Qa+RAhYmhrKqqKDhgsrMvviv6Avn8ajck9tTJwGud8OaXn6huMB9zGDViks3COU1p9KmamrrxdzQdUBeiho7jAyflwdoqlcXH1j6MRFxpo0Rug1azZW/lyv8B+TBVqhihyBMHhNOOYfVrXf6YiAqOmCaMuhziGw56BtaRiz78u8AlOFjFKhQva45ljep8cpabsQV7uvHGN3cLoElVHlFSeXMxBwmRaq35NhH/i6mzQuSeK6myYpdeEgSmjc20Tf6NvYDNp0FSDKaiVjPSHz0ykLu7Jq0YaHGqJ0y90tJ2KEdUr4iLtvSLHjEg+txLO9PZmNqk1F/MFvoFN0jm9GNeRkTcNaWxSMi2/wTewUTnNNQHps3eCXiZti26lb17bIZH3Lpr0k/SCyR3BfgWPfxLrUlMxA1LxFqgl7ltV0n4F5OKewDodO7aNEIyL2YbHoNojV1713rwGpcGTHSEEAfiexhnOfhUrV/SFPtkpSzw8vN86RVYhODHIeQeLV18ReAMr7jg+67mW2JsJTMndiKzCI/n9Fw==",BinaryEncoding.Base64),Compression.Deflate)),
    Source = Table.FromRows(Rows,{"Month", "RawRows", "MissingCustomerRows", "MissingDescriptionRows", "IncludedRows", "UnidentifiedGrossSales"}),
    Typed = Table.TransformColumnTypes(Source,{{"Month",type date},{"RawRows",Int64.Type},{"MissingCustomerRows",Int64.Type},{"MissingDescriptionRows",Int64.Type},{"IncludedRows",Int64.Type},{"UnidentifiedGrossSales",Currency.Type}},"en-GB")
in
    Typed
