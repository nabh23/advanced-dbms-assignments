# Project Milestone: Initial Setup and Data Load

## Submission Details:
- *create_script.sql* - .sql file with the set of CREATE TABLE statements, with primary keys
- *insert_script.sql* - script used to insert data (pre-loaded database); we're working on creating the self-contained python script to insert synthetic data for upcoming milestones
- *test_queries.sql* - .sql file with the test queries
    - 3a) SEL: A selection query on a large table, involving a predicate on something other than the primary key
    - 3b) JOIN: A join of the result of 3a) with a small table
    - 3c) GRP: A group-by query over the result of 3b) that includes one categorical attribute with <20 unique values from the small table and the average of a numeric attribute from the large table
