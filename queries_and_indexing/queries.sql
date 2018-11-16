-- Part A: Selection Query

SELECT "Milliseconds", "Name"
FROM public."Track"
WHERE "Track"."Milliseconds" < 166985;

-- Index Creation

-- ii. BTREE

CREATE INDEX IF NOT EXISTS "milliseconds_btree" ON "Track" USING btree ("Milliseconds");

-- iii. COVER

CREATE INDEX IF NOT EXISTS "milliseconds_cover" ON "Track" ("Milliseconds", "Name");

-- iv. REVERSE

CREATE INDEX IF NOT EXISTS "milliseconds_reverse" ON "Track" ("Name", "Milliseconds");

-- Part B: 

Select "X"."UnitPrice", "Y"."Milliseconds"
FROM
public."InvoiceLine" "X"
JOIN public."Track" "Y"
ON "X"."TrackId" = "Y"."TrackId"
WHERE "Y"."Milliseconds" < 166985

-- Index Creation

-- ii. BTREE
CREATE INDEX IF NOT EXISTS "invoiceline_trackid_btree" ON "InvoiceLine" USING btree ("TrackId");

-- iii. COVER
CREATE INDEX IF NOT EXISTS "track_composite_btree" ON "Track" USING btree ("TrackId", "Milliseconds");

-- iV. FILTER
CREATE INDEX IF NOT EXISTS "track_millis_btree" ON "Track" USING btree ("Milliseconds");


-- Part C:

-- 1. Hash indexes

CREATE INDEX IF NOT EXISTS "milliseconds_hash" ON "Track" USING hash ("Milliseconds");

EXPLAIN ANALYZE SELECT "Milliseconds", "Name"
FROM public."Track"
WHERE "Track"."Milliseconds" = 489733;

-- 2. Clustered index for select



-- 3. Clustered indexes for join
CREATE INDEX IF NOT EXISTS "track_trackid_btree" ON "Track" USING btree ("TrackId");	
CLUSTER "Track" USING "track_trackid_btree";

CREATE INDEX IF NOT EXISTS "invoiceline_trackid_btree" ON "InvoiceLine" USING btree ("TrackId");
CLUSTER "InvoiceLine" USING "invoiceline_trackid_btree";

-- 4. Index build timing

-- To record the build time for each of the indexes in main experiment, we have used the CREATE queries mentioned in Part A and B.


