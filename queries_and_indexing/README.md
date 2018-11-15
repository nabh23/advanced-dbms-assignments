# Performance Experiment: Queries and Indexing

## Abstract

This experiment compares the performance of SELECT queries under different indexing schemes and selectivity criteria (20%, 50%, and 80% of the records returned) against the "Digital Music Store" PostgreSQL database. First, we analyze the performance of SELECT query on a single table. Second, we analyze the performance of SELECT query on two tables JOIN-ed together. We find that there is an increase in query performance when there exists an index on the columns that are being queried. However, we don't observe any significant difference in the performance when the query returns a significant portion of the table.

## Hypothesis

We have written our hypothesis for each of the parts in their respective sections under the *Main Result* section. 

## Assumptions and Setup

In our experiment, we used synthetic data that we generated using the [Log-synth](https://github.com/tdunning/log-synth) (Dunning, 2017) tool based on the data-model of [Chinook](https://github.com/lerocha/chinook-database) database (Rocha, 2017). Log-synth is a utility that allows for random data generation based on a schema. There is support for the generation of addresses, dates, foreign key references, unique id numbers, random integers, realistic person names and street names. It is available as a standalone executable, which can be run from the command line.

Chinook data-model represents a digital media store, including tables for artists, albums, media tracks, invoices and customers. *Track* entity (20000 rows/records) was selected for the experiments, which has nine columns – TrackId, Name, AlbumId, MediaTypeId, GenreId, Composer, Milliseconds, Bytes, and UnitPrice, along with *InvoiceLine* entity (50000 rows/records), which has five columns - InvoiceLineId, InvoiceId, TrackId, UnitPrice, and Quantity.

The database was configured and hosted on cloud as an Amazon RDS (PostgreSQL) instance with [db.t2.micro](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html) (1 virtual CPU, 1 GiB of RAM, not EBS-Optimized, and low network performance as compared to other DB instance classes) class (Amazon Web Services, Inc., 2018).

Timings were measured programmatically using *EXPLAIN ANALYZE*.

## Main Result

### Part A: Selection Query
Our expectation of performance of the SELECT query for different selectivity conditions and different types of indexing strategies are as highlighted below:

```
SELECT "Milliseconds", "Name"
FROM public."Track"
WHERE "Track"."Milliseconds" < 166985;
```

#### Hypothesis

We believe that the case with no indexes will have the lowest query performance. As we add indexes, the query performance is likely to improve; however, the difference will be stark in cases of lower records to be fetched, and not so significant when a larger number of records need to be returned, as the query optimizer then has to run through a large number of records, and indexing does not really benefit it in any way. We also expect that applying two indexes on the table, specifically on the two columns in our SELECT query, may cause the performance to improve, as PostgreSQL could perform an index scan if the query does not need to access any columns that haven’t been indexed. Cover indexes are usually created for the purpose of being used in index-scans. Creation of these indexes in reverse order may lead to differences depending on the column on which we're applying the WHERE clause, i.e. the SELECT_COVER and SELECT_REVERSE may not give similar results w.r.t query performance. We expect the performance to drop in the SELECT_REVERSE as the first column in our cover doesn't remain the column on which we have the WHERE clause.   

#### Results

![Result](./charts/part_a.PNG "Selectivity Criteria versus Time (ms)")

i. **No Index (SELECT_BASELINE)**: We found the performance in this scenario to be the slowest, since the query optimizer had to scan through all the records to select the ones that satisfy the condition in the WHERE clause. We also found the throughput to increase as the number of records selected increases, and the difference between the throughputs for different loads or selectivity %, significantly.

*Query Plan*: For this case, the optimizer chose the Sequential Scan for all the three selection percentages.

ii. **BTREE Index on 1 column (SELECT_BTREE)**: For the index on one column, as expected, we found the query to take lesser time to fetch the records that match the WHERE clause. This is since the query optimizer knew and trudged through only a limited number of records to fetch the rows required, where the efficiency added is due to indexing. However, for increasing selectivity, i.e. as the number of records to be fetched increased, the performance resembled the throughput in the no index case, as the planner preferred a sequential scan as the query had to return a significant portion of the table.

*Query Plan*: For this case, the optimizer chose the Bitmap Heap Scan when running the SELECT query for retrieving 20% of the records, and Sequential Scan for the remaining two selection percentages.

iii. **Indexes on two columns (SELECT_COVER)**: For indexes on two columns, we found that the results were very similar to that of the single btree index, and that it did not contribute to improvements in performance. Again for higher selectivities, the performance dropped and resembled the no-index query performance. Although we expected the performance to improve as we were using SELECT on the two columns on which we had created the cover index, but it didn't. It could be because of the fact that we're trying to return a significant portion of the table, or due to unexplored limitations imposed by Amazon RDS PostgreSQL (like random_page_cost, seq_page_cost settings, or others). 

*Query Plan*: For this case, the optimizer again chose the Bitmap Heap Scan when running the SELECT query for retrieving 20% of the records, and Sequential Scan for the remaining two selection percentages.  

iv. **Indexes on two columns in reverse order (SELECT_REVERSE)**: When we applied the two indexes in reverse order, we found that query performance dropped, especially for the 20% selection case. The performance for the 50% and 80% selectivity remained unchanged. We believe that the performance expectations were not met due to similar reasons as stated for the SELECT_COVER case. Furthermore, the performnace for the 20% selection case would have dropped as the column on which the WHERE clause was applied, wasn't the first in the cover index created. 

*Query Plan*: For this case, the optimizer chose the Sequential Scan for all the three selection percentages.

### Part B: Join Query

```
Select "X"."UnitPrice", "Y"."Milliseconds"
FROM
public."InvoiceLine" "X"
JOIN public."Track" "Y"
ON "X"."TrackId" = "Y"."TrackId"
WHERE "Y"."Milliseconds" < z
```

#### Hypothesis
We expect indexes to be helpful in improving query performance of joins for some, but not all of the performance scenarios. For instance, the first index we create is on X.c, which in our case translates to InvoiceLine.TrackId column. With our join query shown above, we have doubts around whether an index scan would be used in this case, since the SELECT clause has an additional column from the table 'X', and the optimizer might choose to do a sequential scan instead. When creating an index on (Y.c, Y.b), i.e. (Track.TrackId, Track.Milliseconds), the expectation is that the index may still not be picked because the comparison clause would not be efficiently satisfied with the index, the comparison being on Y.b and the index having Y.b as the second columnn. Lastly, if creating an index on the filter column Y.b (Track.Milliseconds), we expect to see a Bitmap Index Scan being used. This is because Bitmap Scans are helpful when we need many rows from the table, but not all, and when the rows that we'll be returning are not in single block on disk (which would be the case with Y.b < z condition).

#### Results

![Result](./charts/part_b.png "Selectivity Criteria versus Time (ms)")

i. **No Index (JOIN_BASELINE)**: The baseline case was the most time consuming, for the 20% and 80% selectivity cases, however the difference was not significant, compared to other cases where we used indexes. For 50% selectivity, the results were better for the baseline case than two of the index cases (B-tree and Cover), although again negligibly.  

*Query Plan*: For all selectivity cases, the optimizer first performed filtering on Y.b (Track.Milliseconds) based on a sequential scan. Thereafter, a hash was created, mapping the filtered rows to different buckets based Y.c (Track.TrackId). The final step involved a sequential scan over the larger of our two tables, X (InvoiceLine), using the hash created in the previous step to perform a Hash Join. The result is in conjunction with our expectations since there were no indexes to leverage in this scenario, and the operation could be performed efficiently by pushing the filter (selectivity condition) to the bottom of the plan.

ii. **B-trees Index on 1 column (JOIN_BTREE)**: With a B-tree index in place on X.c (InvoiceLine.TrackId) table, we observed that there was no significant difference in execution time, compared to the baseline case. Further, the performance degraded when the selectivity was increased to 50% and 80%, much like the baseline.  

*Query Plan*: The optimizer produces the same plan as was produced in our baseline, i.e., pushing the filter condition to the bottom while performing a sequential scan on the table Y (Track), hashing the filtered rows, doing a sequential scan on the table X (InvoiceLine) and performing a Hash Join. Further, this plan was chosen for all selectivity values. This result was expected, because doing a complete scan of the index on InvoiceLine, and then for each index entry, accessing the actual table row for the column X.a (InvoiceLine.UnitPrice) would not have had a performance advantage over a simple sequential scan.

iii. **Indexes on two columns (JOIN_COVER)**:  The time taken to execute the join query in the presence of a composite index on (Y.c, Y.b) also did not seem to have a performance advantage over the baseline or the case with a single index on X.c. Here as well, the time taken to execute the query increased, as the proportion of rows being selected from the table Y (Track) increased. A possible explanation for this behavior follows as part of the query plan.  

*Query Plan*: The optimizer again chose a similar plan as the previous two cases, with the Y (Track) table being sequentially scanned, filtered and hashed based on the selectivity condition. The InvoiceLine table is then sequentially scanned and a Hash Join is performed. The same plan was selected for all values of row selectivity. As we had hypothesized, the index was not utilized by the optimizer, arguably because it would have been difficult to perform a comparison condition Y.b < z using with Y.b as the second column, i.e. (Y.c, Y.b).

iv. **B-tree Index on filter column (JOIN_FILTER)**: With a B-tree index created on the filter column Y.b, we see some improvement in the 20% selectivity case execution time. But the improvement is lost for the 50% and 80% row cases. As in all other cases, the time taken for execution increases with an increase in the number of rows being retained by the filter clause.  

*Query Plan*: For this case, the optimizer chose to do a Bitmap Index Scan on the filter column (Y.b) and build a Bitmap Heap from the filtered rows, for building a hash, but only in the case of 20% selectivity. For 50% and 80% row cases, the optimizer still preferred a sequential scan and Hash join scheme as has been discussed before. A reason could be that performing a Bitmap based scan with a large number of rows present might not offer a performance advantage over filtering those rows using a sequential scan. Once the filtering was determined by the optimizer using the aforementioned two approaches, the join was performed in pretty much the same way, as in all other scenarios.

### Part C: Extensions

#### 1. **Hash indexes**:

```
EXPLAIN ANALYZE SELECT "Milliseconds", "Name"
FROM public."Track"
WHERE "Track"."Milliseconds" = 489733;
```

Hypothesis: We expect the planner to select the Index Scan for this query as we're fetching a single a record from the table, at a specific value in the column on which we have created a hash index, using the WHERE clause.

Result: We observe that it takes 0.01 ms on average for the query execution and the planner uses the Index Scan to perform the query. 

#### 2. **Clustered index for select**:

Hypothesis: We expect that the query performance will be much higher than with a b-tree index. This is because clustering reorders and essentially changes the way the data is stored physically, the query optimizer will perform significantly better with a clustered index.   
The only disadvantage is that clustering is not updated when the table is updated i.e. new records are inserted into the table, hence one would have to periodically run the clustering operation to make sure that the clustered index is available and maintained correctly. 
```
CREATE INDEX "millisec_clustered_idx" ON "Track" ("Milliseconds");
CLUSTER "Track" USING "millisec_clustered_idx";
```
Select Query:  
```
EXPLAIN ANALYZE SELECT "Milliseconds", "Name"
FROM public."Track"
WHERE "Track"."Milliseconds" < x;
(x = 166985, 327320, 489733, for 20%, 50% and 80% records selectivity)

```

 
Result:  

![Result](./charts/part_c2_1.png "Selectivity Criteria versus Time (ms) for Clustered Index")

Thus, we see that clusteredt index performs much better, and takes very little time to execute the SELECT query for all selectivity ratios. Additionally, we observe that the performance improvement is highest for the 50% and 80% selectivity ratios.

![Result](./charts/part_c2.png "Selectivity Criteria versus Time (ms) Comparison Chart")

The above chart shows that among all the indexes, Clustered Index has the best performance and it takes the lowest time for data load for the 20% selectivity. For the selectivity percentages of 50% and 80% however, the time taken by clustered index is  more than the time taken by other indexes, which makes us think that it does not perform well when the number of records to be fetched is higher. It could be that when larger number of records need to be fetched, the optimizer falls back to a Sequential Scan and hence, even if the data is stored in order on the physical disk, it takes longer for it to return the results.  

However, the one caveat is that this will work well only if the WHERE condition includes the column on which the clustering has been done. For other columns, it may not perform well at all.  

*Query Plan*: The EXPLAIN ANALZYE clause shows that after applying a clustered index, the query optimizer uses:
- for 20%: a Bitmap Heap Scan is used, followed by a Bitmap Index Scan
- for 50%: a Sequential Scan is used; this is probably because the records are all stored in a particular order die to clustered   indexing  
- for 80%: Again, a Sequential Scan is used similar to the 50% case

#### 3.

Hypothesis:

Result:

#### 4.

Hypothesis:

Result:

![Result](./charts/part_c_4.png "Index Building versus Time (ms)")
## Conclusions and Discussions



## References

Amazon Web Services, Inc. (2018). *DB Instance Class*. Retrieved from https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html

Dunning, T. (2017). *Log-synth*. Retrieved from https://github.com/tdunning/log-synth

Rocha, L. (2017). *Chinook Database*. Retrieved from https://github.com/lerocha/chinook-database
