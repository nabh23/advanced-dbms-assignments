/* Query 3a */
SELECT * 
FROM "Track" 
WHERE "Milliseconds" > 200000;

/* Query 3b */
WITH "T1" AS (
	SELECT * 
	FROM "Track" 
	WHERE "Milliseconds" > 200000
)
SELECT "T1".*, "M1"."Name" as "MediaType"
FROM "T1" JOIN "MediaType" "M1"
ON "T1"."MediaTypeId" = "M1"."MediaTypeId";

/* Query 3c */
WITH "T2" AS (
	WITH "T1" AS (
		SELECT * 
		FROM "Track" 
		WHERE "Milliseconds" > 200000
	)
	SELECT "T1".*, "M1"."Name" as "MediaType"
	FROM "T1" JOIN "MediaType" "M1"
	ON "T1"."MediaTypeId" = "M1"."MediaTypeId"
)
SELECT "MediaType" as "MediaType", round(Avg("UnitPrice"), 2) as "AvgSongPrice"
FROM "T2"
GROUP BY "MediaType"
ORDER BY "AvgSongPrice";


