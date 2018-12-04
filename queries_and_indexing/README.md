﻿# Performance Experiment: Queries and Indexing

## Abstract

This experiment compares the performance of SELECT queries under different indexing schemes and selectivity criteria (20%, 50%, and 80% of the records returned) against the "Digital Music Store" PostgreSQL database. First, we analyze the performance of SELECT query on a single table. Second, we analyze the performance of SELECT query on two tables JOIN-ed together. We find that there is an increase in query performance in some, but not all cases when an index exists on the columns that are being queried. However, we don't observe any significant difference in the performance when the query returns a significant portion of the table.

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

*Query Plan*: For this case, the optimizer chose the Sequential Scan for all the three selection percentages. Since there was no index to be accessed, the query optimizer performed a sequential scan retrieving the records as dictated in the WHERE clause.

ii. **BTREE Index on 1 column (SELECT_BTREE)**: For the index on one column, as expected, we found the query to take lesser time to fetch the records that match the WHERE clause. This is since the query optimizer knew and trudged through only a limited number of records to fetch the rows required, where the efficiency added is due to indexing. However, for increasing selectivity, i.e. as the number of records to be fetched increased, the performance resembled the throughput in the no index case, as the planner preferred a sequential scan as the query had to return a significant portion of the table.

*Query Plan*: For this case, the optimizer chose the Bitmap Heap Scan when running the SELECT query for retrieving 20% of the records, and Sequential Scan for the remaining two selection percentages. We think the optimizer found the Bitmap Heap Scan more efficient for 20% of the records, since the number of records were fairly large enough to show improved performance with Bitmap Heap Scan. However for selectivities of 50% and 80%, sequential scan turned out to be much efficient, which is why the index was not used.  

iii. **Indexes on two columns (SELECT_COVER)**: For indexes on two columns, we found that the results were very similar to that of the single btree index, and that it did not contribute to improvements in performance. Again for higher selectivities, the performance dropped and resembled the no-index query performance. Although we expected the performance to improve as we were using SELECT on the two columns on which we had created the cover index, but it didn't. It could be because of the fact that we're trying to return a significant portion of the table, or due to unexplored limitations imposed by Amazon RDS PostgreSQL (like random_page_cost, seq_page_cost settings, or others). 

*Query Plan*: For this case, the optimizer again chose the Bitmap Heap Scan when running the SELECT query for retrieving 20% of the records, and Sequential Scan for the remaining two selection percentages. For reasons similar to the one described for BTREE indexes, the Bitmap Heap Scan was the most optimum when selecting 20% (approximately 4000 records), but when selecting 50% or 80%, the sequential scan had a lower cost, which is why the optimizer chose it.  

iv. **Indexes on two columns in reverse order (SELECT_REVERSE)**: When we applied the two indexes in reverse order, we found that query performance dropped, especially for the 20% selection case. The performance for the 50% and 80% selectivity remained unchanged. We believe that the performance expectations were not met due to similar reasons as stated for the SELECT_COVER case. Furthermore, the performnace for the 20% selection case would have dropped as the column on which the WHERE clause was applied, wasn't the first in the cover index created. 

*Query Plan*: For this case, the optimizer chose the Sequential Scan for all the three selection percentages. Here, since we applied the indexes in reverse order, the optimizer really did not find the index useful at all. In addition, the performance was almost similar to the case with no indexes (sometimes worse), which could be because the optimizer had to increase the number of reads due to the reversed indexes.  

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

#### 1. **Hash indexes**: **Prateek Tripathi**

```
EXPLAIN ANALYZE SELECT "Milliseconds", "Name"
FROM public."Track"
WHERE "Track"."Milliseconds" = 489733;
```

Hypothesis: We expect the planner to select the Index Scan for this query as we're fetching a single a record from the table, at a specific value in the column on which we have created a hash index, using the WHERE clause.

Result: We observe that it takes 0.01 ms on average for the query execution and the planner uses the Index Scan to perform the query. 

#### 2. **Clustered index for SELECT**: **Jayashree Raman**  

Hypothesis: We expect that the query performance will be much better than with a multi-column index, however we are unsure if this will essentially perform better than a btree or hash index. This is because clustering reorders and essentially changes the way the data is stored physically, the query optimizer will perform significantly better with a clustered index in some cases, or may not in others.  
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


![Result](./charts/part_c2.png "Selectivity Criteria versus Time (ms) Comparison Chart")

The above chart shows that among all the indexes, Clustered Index takes a small amount of time for data selection for the 20% selectivity. For the selectivity percentages of 50% and 80% however, the time taken by clustered index is  more than the time taken by other indexes, which makes us think that it does not perform well when the number of records to be fetched is higher. It could be that when larger number of records need to be fetched, the optimizer falls back to a Sequential Scan and hence, even if the data is stored in order on the physical disk, it takes longer for it to return the results.  

We found a useful and great explanation of why clustered indexes may sometimes not perform better than non-clustered index at the URL below:
[https://dba.stackexchange.com/questions/137724/difference-between-clustered-index-seek-and-non-clustered-index-seek/137731#137731]
Specifically, the author says that *For any other kind of seek except a singleton, there will be a scanning component as well. The scanning portion will also benefit from the greater density of the nonclustered index (more rows per page). Even if the pages must come in from persistent storage, reading fewer pages is faster.*  


*Query Plan*: The EXPLAIN ANALZYE clause shows that after applying a clustered index, the query optimizer uses:
- for 20%: a Bitmap Heap Scan is used, followed by a Bitmap Index Scan
- for 50%: a Sequential Scan is used; this is probably because the records are all stored in a particular order, and the optimizer scans them sequentially to retrieve all relevant records, which is a fairly large number of records
- for 80%: Again, a Sequential Scan is used similar to the 50% case

#### 3. **Clustered Indexes for Join:** **Harkar Talwar**

Hypothesis:
The expectation here is that creating a clustered index on the join columns would make the optimizer prefer a Merge Join as opposed to a Hash Join. This is because our data would be physically ordered as per the join keys and therefore matching join key values in both the tables should be efficient. Based on this assumption, we expect our join query to perform better, at least for the limited selectivity case.

Result:

![Result](./charts/part_c_3.png "Clustered indexes for join")

The results show that the execution times for the join query after using clustered indexes were slightly lower than other indexing schemes. Also, we observe that the optimizer chose the same plan as it did for most of the other index types, which is:-
1. Push the filter to the bottom, and perform a sequential scan to filter out the rows from table Y (Track)
2. Use the filtered rows to populate a hash table
3. Perform a sequential scan on the table X (InvoiceLine) and perform a Hash Join.

Further, having the rows physically ordered by the join column seems to have yielded a small performance advantage. But it is unclear what caused the improvement, since the operations performed by the optimizer did not seem to be leverage the clustered index.

#### 4. **Index build timing:** **Aakash Agrawal**

Hypothesis:

We hypothesize that the index creation time for the cover indexes and reverse indexes would be more than the indexes built on single columns. Also when we reduce the size of the table by 80%, there should not be any significant difference in the index build time due to the fact that we are left with insignificant amount of records (20 % of 20,000 = 4000).

Result:

![Result](./charts/part_c_4.png "Index Building versus Time (ms)")

From the chart above, we observe that the index creation time is highest for reverse index (where first column is of type varchar and the second column is of type integer) for 20% and 50% scenarios.

Also, we observe that when 80% of the records are deleted from the table, the index creation time is almost same for all the scenarios which follows our hypothesis. The pattern of cover indexes is interesting as the index creation time fluctuates from being greater and lower than normal indexes in different scenarios. We presume that the high build time for reverse index could be because of the order of columns (based on its data type) or the distribution of data in the columns (data pattern). 

## Conclusions and Discussions

We encountered a few interesting results as part of this performance experiment. One important insight from these experiments is that the performance advantage of an index-only scans depends on the number of accessed rows and the index clustering factor. The most efficient results were obtained when the optimizer was able to perform a Bitmap Index Scan based on an index that we created. This however was only done with limited selectivity, i.e. 20% of the rows being fetched. We found that for selection based on a condition, the clustered index does not necessarily perform better. Moreover, our join queries seemed to almost always use a Sequential Scan + Hash Join approach, rather than making use of the created indexes. It was also seen that having clustered indexes, even on the join columns for two tables may not necessarily provide a performance advantage, and the optimizer may still choose to do a Hash Join. Finally, the additional experiment related to analyzing the time for building indexes showed us that not only does the order of the columns in the index matter, but also their data types and the column widths.

A key recommendation to DBAs from this exercise would be that the data access patterns should drive index creation and definitions. Indexes offer a significant advantage only in cases of limited selectivity of rows. If a majority of the table's rows are being fetched, the optimizer might end up doing a sequential scan instead.

In terms of the next steps, we're interested in seeing whether some of the queries defaulting to sequential scans was due to RDS specific PostgreSQL configurations, or was it really the case that the optimizer could not have created more efficient plans for our queries by using the indexes. A step in this direction would be to try playing with the query planner configuration parameters like enable_indexscan, and enable_seqscan (PostgreSQL, 2018) to force the optimizer to pick different scanning methods, and then comparing performance.  


## References

Amazon Web Services, Inc. (2018). *DB Instance Class*. Retrieved from https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html

Dunning, T. (2017). *Log-synth*. Retrieved from https://github.com/tdunning/log-synth

PostgreSQL. (2018). Query Planning. Retrieved from PostgreSQL: https://www.postgresql.org/docs/9.5/runtime-config-query.html

Rocha, L. (2017). *Chinook Database*. Retrieved from https://github.com/lerocha/chinook-database

