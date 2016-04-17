

from .mjFeedLoader import MjFeedLoader
from .mjContentLoader import MjContentLoader

import ScrapePlugins.RunBase



class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Mj.Run"

	pluginName = "MjLoader"


	sourceName = "MangaJoy"
	feedLoader = MjFeedLoader
	contentLoader = MjContentLoader


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup( ):
		mon = Runner()
		mon.go()
