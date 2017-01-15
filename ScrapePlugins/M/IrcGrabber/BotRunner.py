


import runStatus
import ScrapePlugins.RunBase

from ScrapePlugins.M.IrcGrabber.FetchBot import IrcRetreivalInterface
import time



# The IRC bot run class is slightly special.
# It never returns. The parent class prevents more then one bot from being run.
class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.IRC.Bot"

	pluginName = "IrcBot"


	def _go(self):

		mgr = IrcRetreivalInterface()

		mgr.startBot()

		while 1:
			if not runStatus.run:
				break
			time.sleep(1)


		mgr.stopBot()

