## ER Diagram for Schema

## Three Commonly Accessed Views

### 1. View Involving a join

### 2. View Involving a GROUP-BY

### 3. View of Our Choice

*Purpose: This view would allow business and end users to analyze the top soundtracks in the digital music store at a given point of time, based on the total sales of each track.

*Create View Command:*  
```
CREATE VIEW "TopTracksBySales" AS
SELECT "T"."Name", SUM("I"."UnitPrice" * "I"."Quantity") AS "TrackSales"
FROM public."Track" "T"
JOIN
public."InvoiceLine" "I"
ON "T"."TrackId" = "I"."TrackId"
GROUP BY "T"."TrackId"
ORDER BY "TrackSales" DESC
```

*Representative Query:*  
```
-- Show top tracks by SALES, only when the sales are more than 2 currency units
EXPLAIN ANALYZE 
SELECT * FROM "TopTracksBySales"
WHERE "TrackSales" > 2  
```

*Query Plan:*
![Query Plan](./query_plans/view3.PNG "Query Plan for Top Tracks View")

