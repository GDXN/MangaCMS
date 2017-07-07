

from .DbLoader import DbLoader
from .ContentLoader import ContentLoader

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Manga.CrunchyRoll.Run"
	pluginName = "CrunchyRoll"

	sourceName = "CrunchyRoll"
	feedLoader = DbLoader
	contentLoader = ContentLoader



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():
		run = Runner()
		run.go()
