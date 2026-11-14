// Verified snapshot derived from UCI Online Retail II by build/clean_retail.py.
// Fixed historical dataset; regenerate alongside Sales if the source snapshot changes.
let
    Rows = Json.Document(Binary.Decompress(Binary.FromText("jZXBbsIwDIZfJeoZac/AGGMdDKF10w6Ig2lMay11KjcRgqdf2ZA27cJ/qdTq85/Yv+1ut8U0D8koCBWTotTEppQkKgV357IOPddyEPbFbnJlIfKeWiNRhOTQSO4g0rrsodONzhIAcEZKkOKsJVUOrhwCqR+QiFNvGQLPXLfulfu8D1IDAQ+sHdknQM6zxZ5J3Sx2XVZJJyDoUfSSI0Iaac0AuBidI0UOXxgzJPkUtXHL8QGwZc1gRqXB5GDESIuViQKS+TP1hMzLMhojHbviPWlEFFeS2kwKzfULhYRwa04tGzora2kY2yvraEdCyrmJoJGbaCk3hFhZUfbipkZ76K6VaEP9aBfCxpxaNz2Y1JB0jy3X6sieMVDS+ccwgH5rSUD0fdw67L+L5uadGCVGOuIathxL6OPl5/Dvwx+mSrDm7/tt+oOH5Er1clt79wU=",BinaryEncoding.Base64),Compression.Deflate)),
    Source = Table.FromRows(Rows,{"Country", "Market"}),
    Typed = Table.TransformColumnTypes(Source,{{"Country",type text},{"Market",type text}},"en-GB")
in
    Typed
