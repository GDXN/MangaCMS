

from .DbLoader import DbLoader
from .ContentLoader import ContentLoader

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Manga.NHentai.Run"
	pluginName = "NHentai"


	sourceName = "NHentai"
	feedLoader = DbLoader
	contentLoader = ContentLoader


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		run = Runner()
		run.go()
