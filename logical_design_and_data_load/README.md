## ER Diagram for Schema

## Three Commonly Accessed Views

### 1. View Involving a JOIN

* Purpose: This view allows the business to analyze the information related to the performance of customer representatives, and understand/manage their respective workloads. We implement a join between the Customer and Employee tables, to see the assigned customer representative for each of the customers.

*Create View Command:*
```
CREATE VIEW customer_relations AS
    SELECT 
        cu."CustomerId" AS "CustomerId",
        cu."FirstName" || ' ' || cu."LastName" AS "FullName",
        cu."Company" AS "Company",
        cu."Address" AS "Address",
        cu."City" AS "City",
        cu."State" || ', ' || cu."Country" AS "Region",
        cu."Phone" AS "Phone",
        cu."Email" AS "Email",
        em."EmployeeId" AS "EmployeeId",
        em."FirstName" || ' ' || em."LastName" AS "Employee",
        em."Title" AS "Title",
        em."City" AS "EmployeeCity",
        em."State" || ', ' || em."Country" AS "EmployeeRegion",
        em."Phone" AS "EmployeePhone",
        em."Email" AS "EmployeeEmail",
        re."ReportsTo" AS "SupervisorId",
        re."FirstName" || ' ' || re."LastName" AS "Supervisor"
    FROM public."Customer" cu
        LEFT JOIN public."Employee" em ON cu."SupportRepId" = em."EmployeeId"
        INNER JOIN public."Employee" re ON em."ReportsTo" = re."EmployeeId";
```

*Representative Query:*
```
-- Display the total number of customers serviced by each employee.
EXPLAIN ANALYZE
SELECT 
	"EmployeeId",
	"Employee",
	COUNT(*) AS "NumberOfCustomersRepresented"	
FROM customer_relations
GROUP BY "EmployeeId", "Employee"
ORDER BY "NumberOfCustomersRepresented" DESC;
```

*Query Plan:*

![Query Plan](./query_plans/view1.PNG "Query Plan for Customer Relations View")

*Operations Dominating the Cost:*  

*Algorithm Used for an Expensive Scenario:*

*Selection Condition in the Query Plan*

### 2. View Involving a GROUP-BY

* Purpose: This view allows the business to analyze the customers who bought maximum worth of items in the digital music store, periodically. To get the result, we implement a join between the Customer, Invoice and InvoiceItem tables to view the customers whose purchase value was highest (weekly/monthly/annually)

*Create View Command:*  
```
CREATE VIEW "TopCustomersBySales" AS
SELECT "c"."CustomerId", SUM("UnitPrice" * "Quantity") AS "TotalAmt"
FROM
(SELECT "Customer"."CustomerId", "FirstName", "LastName", "InvoiceId"
	FROM public."Customer"
	JOIN 
	public."Invoice"
	ON public."Customer"."CustomerId" = public."Invoice"."CustomerId") c
	JOIN public."InvoiceLine"
	ON c."InvoiceId" = "InvoiceLine"."InvoiceId"
	GROUP BY "CustomerId"
	ORDER BY "TotalAmt" DESC;
```

*Representative Query:*  
```
-- Show top 50 Customers (here top signifies customers who bought highest worth of items from the store)
EXPLAIN ANALYZE 
SELECT * FROM "TopCustomersBySales" LIMIT 50;  
```

*Query Plan:*  
![Query Plan](./query_plans/view2.PNG "Query Plan for Top Customers View")

*Operations Dominating the Cost:*  
*Sorting the records in descending order of the TotalAmt:*  

*GROUPBY Operation on CustomerId:*

*Hash Join based on InvoiceId:*




### 3. View of Our Choice

* Purpose: This view would allow business and end users to analyze the top soundtracks in the digital music store at a given point of time, based on the total sales of each track.

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

*Note: 'Exclusive' denotes time taken for execution, for that particular node. 'Inclusive' denotes the total time taken from the bottom of the tree to a node.*

*Operations Dominating the Cost:*   
* As it can be seen from the query plan above, the operations dominating the cost (indicated by the exclusive time column) are:
	1. Aggregation - Grouping by track ID to find the top selling tracks was the most expensive operation, as per the query plan. This operation is depicted in the node with the 'HashAggregate' operator, taking 2.3 ms out of the total ~6.2 ms required for the query.
	2. Join - The join between the Track and InvoiceLine tables is the second most expensive operation. It is denoted by the node with the 'HashJoin' operator. The operation required 1.6 ms.

*Algorithm Used for an Expensive Scenario:*  
	 * Aggregation - The aggregation (GROUP BY) was performed by using the HashAggregate algorithm. This algorithm involves iterating over each row, finding the GROUP-BY key, TrackId in this case, and assigning the row to a bucket corresponding to the TrackId in a hash-table. After processing all rows in this manner, the algorithm scans the hash-table and returns a single row for each key, while performing the required aggregation (sum in this case). Since the algorithm has to scan the entire table before it can return even a single row, this is an expensive operation.

*Selection Condition in the Query Plan:*  
The selection condition was not pushed to the leaves in the query. Rather, it was performed as part of the aggregation operation. This is because in order for the filtering to be done, the aggregated column, 'TrackSales' was required to be computed. Therefore the optimizer, chose to apply this selection as part of the aggregation (HashAggregate) operation.