

run = True

def getStatus(con, pluginName):
	cur = con.cursor()
	ret = cur.execute("""SELECT running,lastRun,lastRunTime FROM pluginStatus WHERE name=?""", (pluginName, ))
	rets = ret.fetchall()[0]
	return rets
