SELECT SUM(LineValue) AS net_sales, SUM(GrossSales) AS gross_sales,
SUM(CreditValue) AS credits,
COUNT(DISTINCT CASE WHEN TransactionType='Sale' THEN InvoiceNo END) AS sales_orders,
COUNT(DISTINCT CASE WHEN TransactionType='Sale' AND CustomerKey<>'Unknown' THEN CustomerKey END) AS known_buyers
FROM sales WHERE Date BETWEEN '2011-01-01' AND '2011-11-30';