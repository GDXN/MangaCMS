
# XDCC Plugins

import ScrapePlugins.IrcGrabber.IrcOfferLoader.IrcQueue
import ScrapePlugins.IrcGrabber.IMangaScans.ImsScrape
import ScrapePlugins.IrcGrabber.EgScans.EgScrape
import ScrapePlugins.IrcGrabber.IlluminatiManga.IrcQueue
import ScrapePlugins.IrcGrabber.SimpleXdccParser.IrcQueue
import ScrapePlugins.IrcGrabber.ModernXdccParser.IrcQueue
import ScrapePlugins.IrcGrabber.TextPackScraper.IrcQueue

# Trigger loader plugins
import ScrapePlugins.IrcGrabber.CatScans.IrcQueue
import ScrapePlugins.IrcGrabber.RenzokuseiScans.IrcQueue

# Channel grabber
import ScrapePlugins.IrcGrabber.ChannelLister.ChanLister

import ScrapePlugins.RunBase

import time
import traceback
import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.IRC.Q.Run"

	pluginName = "IrcEnqueue"

	runClasses = [
		ScrapePlugins.IrcGrabber.SimpleXdccParser.IrcQueue.TriggerLoader,
		ScrapePlugins.IrcGrabber.IrcOfferLoader.IrcQueue.TriggerLoader,
		ScrapePlugins.IrcGrabber.IMangaScans.ImsScrape.IMSTriggerLoader,
		ScrapePlugins.IrcGrabber.EgScans.EgScrape.EgTriggerLoader,
		ScrapePlugins.IrcGrabber.ModernXdccParser.IrcQueue.TriggerLoader,
		ScrapePlugins.IrcGrabber.TextPackScraper.IrcQueue.TriggerLoader,
		ScrapePlugins.IrcGrabber.IlluminatiManga.IrcQueue.TriggerLoader,

		ScrapePlugins.IrcGrabber.CatScans.IrcQueue.TriggerLoader,
		ScrapePlugins.IrcGrabber.RenzokuseiScans.IrcQueue.TriggerLoader,

		ScrapePlugins.IrcGrabber.ChannelLister.ChanLister.ChannelTriggerLoader
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


