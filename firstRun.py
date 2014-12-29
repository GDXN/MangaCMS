

'''
Do the initial database setup, so a functional system can be bootstrapped from an empty database.
'''

import ScrapePlugins.BuMonitor.MonitorRun
import ScrapePlugins.BuMonitor.ChangeMonitor
import ScrapePlugins.DjMoeLoader.djMoeDbLoader

import ScrapePlugins.BtSeriesFetcher.btSeriesEnqueuer
import ScrapePlugins.BtLoader.btFeedLoader

import ScrapePlugins.CxLoader.cxFeedLoader

'''
We need one instance of each type of plugin (series, manga, hentai), plus some extra for no particular reason (safety!)

Each plugin is instantiated, and then the plugin database setup method is called.

'''
toInit = [
	ScrapePlugins.BuMonitor.MonitorRun.BuWatchMonitor,
	ScrapePlugins.BuMonitor.ChangeMonitor.BuDateUpdater,
	ScrapePlugins.DjMoeLoader.djMoeDbLoader.DjMoeDbLoader,
	ScrapePlugins.BtSeriesFetcher.btSeriesEnqueuer.BtSeriesEnqueuer,
	ScrapePlugins.BtLoader.btFeedLoader.BtFeedLoader,
	ScrapePlugins.CxLoader.cxFeedLoader.CxFeedLoader,
]


def firstRun():
	for plg in toInit:
		print(plg)
		tmp = plg()
		tmp.checkInitPrimaryDb()

if __name__ == "__main__":
	firstRun()
