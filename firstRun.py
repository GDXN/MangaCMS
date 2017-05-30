

'''
Do the initial database setup, so a functional system can be bootstrapped from an empty database.
'''

import ScrapePlugins.M.BuMonitor.MonitorRun
import ScrapePlugins.M.BuMonitor.ChangeMonitor
import ScrapePlugins.H.DjMoeLoader.DbLoader

import ScrapePlugins.M.BtSeriesFetcher.SeriesEnqueuer
import ScrapePlugins.M.BtLoader.DbLoader


'''
We need one instance of each type of plugin (series, manga, hentai), plus some extra for no particular reason (safety!)

Each plugin is instantiated, and then the plugin database setup method is called.

'''
toInit = [
	ScrapePlugins.M.BuMonitor.MonitorRun.BuWatchMonitor,
	ScrapePlugins.M.BuMonitor.ChangeMonitor.BuDateUpdater,
	ScrapePlugins.H.DjMoeLoader.DbLoader.DbLoader,
	ScrapePlugins.M.BtSeriesFetcher.SeriesEnqueuer.SeriesEnqueuer,
	ScrapePlugins.M.BtLoader.DbLoader.DbLoader,
	]


def checkInitTables():
	for plg in toInit:
		print(plg)
		tmp = plg()
		tmp.checkInitPrimaryDb()
		if hasattr(tmp, "checkInitSeriesDb"):
			tmp.checkInitSeriesDb()

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	checkInitTables()
