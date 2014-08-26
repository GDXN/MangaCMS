
import settings
import psycopg2

queries = [
'''
EXPLAIN ANALYZE WITH RECURSIVE cte AS (
   (
   SELECT dbid, seriesName, retreivaltime, 1 AS rn, ARRAY[seriesName] AS arr
   FROM   MangaItems
   ORDER  BY retreivaltime DESC, seriesName DESC
   LIMIT  1
   )
   UNION ALL
   (
   SELECT i.dbid, i.seriesName, i.retreivaltime, c.rn + 1, c.arr || i.seriesName
   FROM   cte c
   JOIN   MangaItems i ON (i.retreivaltime, i.seriesName) < (c.retreivaltime, c.seriesName)
   WHERE  i.seriesName <> ALL(c.arr)
   AND    c.rn < 100
   ORDER  BY i.retreivaltime DESC, i.seriesName DESC
   LIMIT  1
   )
   )
SELECT dbid
FROM   cte
ORDER  BY rn;
''',

'''
EXPLAIN ANALYZE WITH RECURSIVE cte AS (
   (
   SELECT dbid, seriesName, retreivaltime, 1 AS rn, ARRAY[seriesName] AS arr
   FROM   MangaItems
   WHERE  sourceSite = 'jz'
   ORDER  BY retreivaltime DESC, seriesName DESC
   LIMIT  1
   )
   UNION ALL
   (
   SELECT i.dbid, i.seriesName, i.retreivaltime, c.rn + 1, c.arr || i.seriesName
   FROM   cte c
   JOIN   MangaItems i ON (i.retreivaltime, i.seriesName) < (c.retreivaltime, c.seriesName)
   WHERE  i.sourceSite = 'jz'
   AND    i.seriesName <> ALL(c.arr)
   AND    c.rn < 100
   ORDER  BY i.retreivaltime DESC, i.seriesName DESC
   LIMIT  1
   )
   )
SELECT dbid
FROM   cte
ORDER  BY rn;
''',

'''
EXPLAIN ANALYZE WITH RECURSIVE cte AS (
   (
   SELECT dbid, seriesName, retreivaltime, 1 AS rn, ARRAY[seriesName] AS arr
   FROM   MangaItems
   WHERE  sourceSite = 'bt'
   ORDER  BY retreivaltime DESC, seriesName DESC
   LIMIT  1
   )
   UNION ALL
   (
   SELECT i.dbid, i.seriesName, i.retreivaltime, c.rn + 1, c.arr || i.seriesName
   FROM   cte c
   JOIN   MangaItems i ON (i.retreivaltime, i.seriesName) < (c.retreivaltime, c.seriesName)
   WHERE  i.sourceSite = 'bt'
   AND    i.seriesName <> ALL(c.arr)
   AND    c.rn < 100
   ORDER  BY i.retreivaltime DESC, i.seriesName DESC
   LIMIT  1
   )
   )
SELECT dbid
FROM   cte
ORDER  BY rn;
''',

'''
EXPLAIN ANALYZE WITH RECURSIVE cte AS (
   (
   SELECT dbid, seriesName, retreivaltime, 1 AS rn, ARRAY[seriesName] AS arr
   FROM   MangaItems
   WHERE  sourceSite = 'mk'
   ORDER  BY retreivaltime DESC, seriesName DESC
   LIMIT  1
   )
   UNION ALL
   (
   SELECT i.dbid, i.seriesName, i.retreivaltime, c.rn + 1, c.arr || i.seriesName
   FROM   cte c
   JOIN   MangaItems i ON (i.retreivaltime, i.seriesName) < (c.retreivaltime, c.seriesName)
   WHERE  i.sourceSite = 'mk'
   AND    i.seriesName <> ALL(c.arr)
   AND    c.rn < 100
   ORDER  BY i.retreivaltime DESC, i.seriesName DESC
   LIMIT  1
   )
   )
SELECT dbid
FROM   cte
ORDER  BY rn;
'''

'''SELECT COUNT(*) FROM MangaItems WHERE sourceSite='bt';''',
'''SELECT COUNT(*) FROM MangaItems WHERE sourceSite='cz';''',
'''SELECT COUNT(*) FROM MangaItems WHERE sourceSite='irc-irh';''',
'''SELECT COUNT(*) FROM MangaItems WHERE sourceSite='jz';''',
'''SELECT COUNT(*) FROM MangaItems WHERE sourceSite='mb';''',
'''SELECT COUNT(*) FROM MangaItems WHERE sourceSite='mc';''',
'''SELECT COUNT(*) FROM MangaItems WHERE sourceSite='mk';''',
'''SELECT COUNT(*) FROM MangaItems WHERE sourceSite='mt';''',
'''SELECT COUNT(*) FROM MangaItems WHERE sourceSite='sk';''',

'''
SELECT COUNT(*), MAX(sourceSite) FROM MangaItems AS d
	JOIN
	(
		SELECT DISTINCT sourceSite FROM MangaItems AS sn
	) AS di
ON di.sn = d.sourceSite;''',

		]

def test():

	conn = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)

	cur = conn.cursor()

	for query in queries:
		cur.execute(query)
		print("----------------------------------------------------------------------------------------------")
		print(query)
		print("===========================")

		for item in cur.fetchall():

			print(item[0])



if __name__ == "__main__":
	test()
	# updateFsSafeColumn()

