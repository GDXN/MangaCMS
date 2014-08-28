
def setupTableCountersPostgre(conn):
	doTableCount(conn, "MangaItems")
	doTableCount(conn, "HentaiItems")

def doTableCount(conn, table):

	cur = conn.cursor()

	print("Ensuring commit hooks for table-size tracking exist.")

	cur.execute("BEGIN;")
	cur.execute('''CREATE TABLE IF NOT EXISTS MangaItemCounts (
										sourceSite    TEXT    NOT NULL,
										dlState       INT     NOT NULL,
										quantity      BIGINT  NOT NULL,
										id            SERIAL  PRIMARY KEY
										);''')



	print("Ensuring commit hooks for table-size tracking exist.")


	cur.execute('''

CREATE OR REPLACE FUNCTION update_row_counts() RETURNS trigger AS $$
	BEGIN
		IF (TG_OP = 'DELETE') THEN
			INSERT INTO MangaItemCounts(sourceSite, dlState, quantity) VALUES (OLD.sourceSite, OLD.dlState,-1);

		ELSIF (TG_OP = 'UPDATE') THEN
			INSERT INTO MangaItemCounts(sourceSite, dlState, quantity) VALUES (OLD.sourceSite, OLD.dlState,-1);
			INSERT INTO MangaItemCounts(sourceSite, dlState, quantity) VALUES (NEW.sourceSite, NEW.dlState,1);

		ELSIF (TG_OP = 'INSERT') THEN
			INSERT INTO MangaItemCounts(sourceSite, dlState, quantity) VALUES (NEW.sourceSite, NEW.dlState,1);

		END IF;
		RETURN NEW;
	END;

$$ LANGUAGE plpgsql;
	''')



	cur.execute('''DROP TRIGGER IF EXISTS update_row_count_trigger ON {tableName};'''.format(tableName=table))
	cur.execute('''CREATE TRIGGER update_row_count_trigger
						AFTER INSERT OR UPDATE OR DELETE ON {tableName}
						FOR EACH ROW EXECUTE PROCEDURE update_row_counts();'''.format(tableName=table))


	print("Pre-Counting table items in table %s." % table)

	cur.execute("SELECT DISTINCT(dlState) FROM {tableName};".format(tableName=table))
	rets = cur.fetchall()
	values = [val[0] for val in rets]
	values = set(values)


	values.add(-1)
	values.add(0)
	values.add(1)
	values.add(2)

	cur.execute("SELECT DISTINCT(sourceSite) FROM {tableName};".format(tableName=table))
	rets = cur.fetchall()
	sources = [val[0] for val in rets]


	print("Hooks created. Doing initial table item count")


	# We need to zero the existing data.


	for source in sources:
		cur.execute("UPDATE MangaItemCounts SET quantity=0 WHERE sourceSite=%s;", (source, ))
		for val in values:
			cur.execute("""SELECT COUNT(*) FROM {tableName} WHERE sourceSite=%s AND dlState=%s;""".format(tableName=table), (source, val))
			count = cur.fetchall().pop()[0]
			print("Row", source, val, count)
			cur.execute("INSERT INTO MangaItemCounts (sourceSite, dlState, quantity) VALUES (%s, %s, %s);", (source, val, count))

	print("Items counted. Good to go!")

	cur.execute('COMMIT;')

	cur.close()