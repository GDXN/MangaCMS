

import ScrapePlugins.IrcGrabber.ViScans.ViScrape
import ScrapePlugins.IrcGrabber.StupidCommotion.StupidCommotionQueue
import ScrapePlugins.IrcGrabber.IMangaScans.ImsScrape
import ScrapePlugins.IrcGrabber.EgScans.EgScrape
import ScrapePlugins.IrcGrabber.IlluminatiManga.IrcQueue
import ScrapePlugins.IrcGrabber.ATeam.IrcQueue

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.IRC.Q.Run"

	pluginName = "IrcEnueue"

	runClasses = [
		ScrapePlugins.IrcGrabber.ViScans.ViScrape.ViTriggerLoader,
		ScrapePlugins.IrcGrabber.StupidCommotion.StupidCommotionQueue.StupidCommotionTriggerLoader,
		ScrapePlugins.IrcGrabber.IMangaScans.ImsScrape.IMSTriggerLoader,
		ScrapePlugins.IrcGrabber.EgScans.EgScrape.EgTriggerLoader,
		ScrapePlugins.IrcGrabber.ATeam.IrcQueue.TriggerLoader,
		ScrapePlugins.IrcGrabber.IlluminatiManga.IrcQueue.TriggerLoader
	]

	def _go(self):

		self.log.info("Checking IRC feeds for updates")

		for runClass in self.runClasses:

			fl = runClass()
			fl.go()
			fl.closeDB()

			time.sleep(3)

			if not runStatus.run:
				return

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	run = Runner()
	run.go()


