

from ScrapePlugins.IrcGrabber.ViScans.ViScrape                     import ViTriggerLoader
from ScrapePlugins.IrcGrabber.StupidCommotion.StupidCommotionQueue import StupidCommotionTriggerLoader
from ScrapePlugins.IrcGrabber.IMangaScans.ImsScrape                import IMSTriggerLoader
from ScrapePlugins.IrcGrabber.EgScans.EgScrape                     import EgTriggerLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.IRC.Q.Run"

	pluginName = "IrcEnueue"


	def _go(self):

		self.log.info("Checking IRC feeds for updates")

		fl = ViTriggerLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		fl = StupidCommotionTriggerLoader()
		fl.go()
		fl.closeDB()
		if not runStatus.run:
			return

		fl = IMSTriggerLoader()
		fl.go()
		fl.closeDB()

		if not runStatus.run:
			return


		cl = EgTriggerLoader()
		cl.go()
		cl.closeDB()

