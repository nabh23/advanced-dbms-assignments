# Performance Experiment: Queries and Indexing

## Abstract



## Hypothesis



## Assumptions and Setup

In our experiment, we used synthetic data that we generated using the [Log-synth](https://github.com/tdunning/log-synth) (Dunning, 2017) tool based on the data-model of [Chinook](https://github.com/lerocha/chinook-database) database (Rocha, 2017). Log-synth is a utility that allows for random data generation based on a schema. There is support for the generation of addresses, dates, foreign key references, unique id numbers, random integers, realistic person names and street names. It is available as a standalone executable, which can be run from the command line.

Chinook data-model represents a digital media store, including tables for artists, albums, media tracks, invoices and customers. *Track* entity was selected for the experiments, which has nine columns – TrackId, Name, AlbumId, MediaTypeId, GenreId, Composer, Milliseconds, Bytes, and UnitPrice, along with *InvoiceLine* entity, which has five columns - InvoiceLineId, InvoiceId, TrackId, UnitPrice, and Quantity.

The database was configured and hosted on cloud as an Amazon RDS (PostgreSQL) instance with [db.t2.micro](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html) (1 virtual CPU, 1 GiB of RAM, not EBS-Optimized, and low network performance as compared to other DB instance classes) class (Amazon Web Services, Inc., 2018).

Timings were measured programmatically using *EXPLAIN ANALYZE*.

## Main Result

### Part A: Selection Query
Our expectation of performance of the SELECT query for different selectivity conditions and different types of indexing strategies are as highlighted below: 

#### Expectation
We believe that the case with no indexes will have the lowest query performance. As we add indexes, the query performance is likely to improve; however, the difference will be stark in cases of lower records to be fetched, and not so significant when a larger number of records need to be returned, as the query optimizer then has to run through a large number of records, and indexing does not really benefit it in any way. We also expect that applying two indexes on the table, specifically on the two columns in our SELECT query, may cause the performance to improve, and applying the two indexes in reverse order may not be very different, i.e. the SELECT_COVER and SELECT_REVERSE will give very similar results w.r.t query performance.   

#### Results

![Result](./charts/part_a.PNG "Selectivity Criteria versus Time (ms)")

i. **No Index (SELECT_BASELINE)**: We found the performance in this scenario to be the slowest, since the query optimizer had to scan through all the records to select the ones that satisfy the condition in the WHERE clause. We also found the throughput to increase as the number of records selected increases, and the difference between the throughputs for different loads or selectivity %, fairly significant.  
*Query Plan*: For this case, the optimizer chose the Sequential Scan for all the three selection percentages.

ii. **BTREE Index on 1 column (SELECT_BTREE)**: For the index on one column, as expected, we found the query to take lesser time to fetch the records that match the WHERE clause. This is since the query optimizer knew and trudged through only a limited number of records to fetch the rows required, the efficiency added due to indexing. However, for increasing selectivity, i.e. as the number of records to be fetched increased, the performance resembled the throughput in the no index case, as the query optimizer had to sift through almost a similar number of records.  
*Query Plan*: For this case, the optimizer chose the Bitmap Heap Scan when running the SELECT query for retrieving 20% of the records, and Sequential Scan for the remaining two selection percentages.

iii. **Indexes on two columns (SELECT_COVER)**: For indexes on two columns, we found that the results were very similar to that of the single btree index, and that it did not significantly contribute to improvement in performance. Again for higher selectivities, the performance dropped and resembled the no-index query performance.  
*Query Plan*: For this case, the optimizer again chose the Bitmap Heap Scan when running the SELECT query for retrieving 20% of the records, and Sequential Scan for the remaining two selection percentages.  

iv. **Indexes on two columns in reverse order (SELECT_REVERSE)**: When we applied the two indexes in reverse order, surprisingly we found that query performance dropped significantly, especially for the 20% selection case. The performance for the 50% and 80% selectivity improved very slightly, by a factor of 0.001 ms or so.  
*Query Plan*: For this case, the optimizer chose the Sequential Scan for all the three selection percentages.

### Part B: Join Query

![Result](./charts/part_b.png "Selectivity Criteria versus Time (ms)")

## Additional Experiments

### 2. **Clustered index for select**:  
Expectation: We expect that the query performance will be much higher than with a b-tree index. This is because clustering reorders and essentially changes the way the data is stored physically, the query optimizer will perform significantly better with a clustered index.   
The only disadvantage is that clustering is not updated when the table is updated i.e. new records are inserted into the table, hence one would have to periodically run the clustering operation to make sure that the clustered index is available and maintained correctly.  
#### Results:  




## Conclusions and Discussions



## References

Amazon Web Services, Inc. (2018). *DB Instance Class*. Retrieved from https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html

Dunning, T. (2017). *Log-synth*. Retrieved from https://github.com/tdunning/log-synth

Rocha, L. (2017). *Chinook Database*. Retrieved from https://github.com/lerocha/chinook-database
