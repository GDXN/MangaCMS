
# XDCC Plugins

import ScrapePlugins.M.IrcGrabber.IrcOfferLoader.IrcQueue
import ScrapePlugins.M.IrcGrabber.IMangaScans.ImsScrape
import ScrapePlugins.M.IrcGrabber.EgScans.EgScrape
import ScrapePlugins.M.IrcGrabber.IlluminatiManga.IrcQueue
import ScrapePlugins.M.IrcGrabber.SimpleXdccParser.IrcQueue
import ScrapePlugins.M.IrcGrabber.ModernXdccParser.IrcQueue
import ScrapePlugins.M.IrcGrabber.TextPackScraper.IrcQueue

# Trigger loader plugins
import ScrapePlugins.M.IrcGrabber.CatScans.IrcQueue
import ScrapePlugins.M.IrcGrabber.RenzokuseiScans.IrcQueue

# Channel grabber
import ScrapePlugins.M.IrcGrabber.ChannelLister.ChanLister

import ScrapePlugins.RunBase

import time
import traceback
import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.IRC.Q.Run"

	pluginName = "IrcEnqueue"

	runClasses = [
		ScrapePlugins.M.IrcGrabber.SimpleXdccParser.IrcQueue.TriggerLoader,
		ScrapePlugins.M.IrcGrabber.IrcOfferLoader.IrcQueue.TriggerLoader,
		ScrapePlugins.M.IrcGrabber.IMangaScans.ImsScrape.IMSTriggerLoader,
		ScrapePlugins.M.IrcGrabber.EgScans.EgScrape.EgTriggerLoader,
		ScrapePlugins.M.IrcGrabber.ModernXdccParser.IrcQueue.TriggerLoader,
		ScrapePlugins.M.IrcGrabber.TextPackScraper.IrcQueue.TriggerLoader,
		ScrapePlugins.M.IrcGrabber.IlluminatiManga.IrcQueue.TriggerLoader,

		ScrapePlugins.M.IrcGrabber.CatScans.IrcQueue.TriggerLoader,
		ScrapePlugins.M.IrcGrabber.RenzokuseiScans.IrcQueue.TriggerLoader,

		ScrapePlugins.M.IrcGrabber.ChannelLister.ChanLister.ChannelTriggerLoader
	]

	def _go(self):

		self.log.info("Checking IRC feeds for updates")

		for runClass in self.runClasses:

			try:
				fl = runClass()
				fl.go()
				fl.closeDB()
			except Exception as e:
				self.log.critical("Error in IRC enqueue system!")
				self.log.critical(traceback.format_exc())
				self.log.critical("Exception:")
				self.log.critical(e)
				self.log.critical("Continuing with next source")



			time.sleep(3)

			if not runStatus.run:
				return

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	run = Runner()
	run.go()


