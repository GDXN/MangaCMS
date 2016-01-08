
import runStatus
from ScrapePlugins.MangaBoxLoader.FeedLoader import FeedLoader
from ScrapePlugins.MangaBoxLoader.ContentLoader import ContentLoader

import ScrapePlugins.RunBase

import time


 # cr
 # mj
 # cs
 # lm
 # th
 # mh
 # mt
 # bt
 # mp
 # sj
 # cx
 # mc
 # s2
 # mb
 # irc-trg
 # irc-irh
 # rs
 # kw
 # mk
 # ki
 # jz
 # se
 # dy
 # wr
 # sk
 # vx
 # ms
 # ze
 # cz
 # sura
 # rh
 # wt



class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Mbx.Run"

	pluginName = "MangaBoxLoader"


	def _go(self):

		self.log.info("Checking MangaBox for updates")
		fl = FeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = ContentLoader()

		if not runStatus.run:
			return

		cl.go()




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=True):

		run = Runner()
		run.go()

