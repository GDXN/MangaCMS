

import ScrapePlugins.BuMonitor.MonitorRun
import ScrapePlugins.BuMonitor.ChangeMonitor
import ScrapePlugins.DjMoeLoader.djMoeDbLoader

import ScrapePlugins.BtSeriesFetcher.btSeriesEnqueuer
import ScrapePlugins.BtLoader.btFeedLoader

import ScrapePlugins.CxLoader.cxFeedLoader

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
