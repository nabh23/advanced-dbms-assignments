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



-- Index Creation

-- 



--



--



