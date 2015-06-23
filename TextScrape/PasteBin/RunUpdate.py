


from .Scrape import Scrape
from .Run import Runner as RunnerBase



class Runner(RunnerBase):

	pluginName = "PasteBinScrapeUpdate"
	def _go(self):

		self.log.info("Doing update scan.")
		scraper = Scrape()
		scraper.crawl(shallow=True, checkOnly=True)


def test():
	import logSetup
	logSetup.initLogging()
	scrp = Runner()
	scrp.go()


if __name__ == "__main__":
	test()

