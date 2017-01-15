

'''
Do the initial database setup, so a functional system can be bootstrapped from an empty database.
'''

import ScrapePlugins.M.BuMonitor.MonitorRun
import ScrapePlugins.M.BuMonitor.ChangeMonitor
import ScrapePlugins.H.DjMoeLoader.djMoeDbLoader

import ScrapePlugins.M.BtSeriesFetcher.btSeriesEnqueuer
import ScrapePlugins.M.BtLoader.btFeedLoader


'''
We need one instance of each type of plugin (series, manga, hentai), plus some extra for no particular reason (safety!)

Each plugin is instantiated, and then the plugin database setup method is called.

'''
toInit = [
	ScrapePlugins.M.BuMonitor.MonitorRun.BuWatchMonitor,
	ScrapePlugins.M.BuMonitor.ChangeMonitor.BuDateUpdater,
	ScrapePlugins.H.DjMoeLoader.djMoeDbLoader.DjMoeDbLoader,
	ScrapePlugins.M.BtSeriesFetcher.btSeriesEnqueuer.BtSeriesEnqueuer,
	ScrapePlugins.M.BtLoader.btFeedLoader.BtFeedLoader,
	]


def firstRun():
	for plg in toInit:
		print(plg)
		tmp = plg()
		tmp.checkInitPrimaryDb()

if __name__ == "__main__":
	firstRun()
