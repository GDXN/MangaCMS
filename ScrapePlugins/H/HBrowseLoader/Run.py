

from .DbLoader import DbLoader
from .ContentLoader import ContentLoader

import settings

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Manga.HBrowse.Run"
	pluginName = "H-Browse"


	sourceName = "H-Browse"
	feedLoader = DbLoader
	contentLoader = ContentLoader



if __name__ == "__main__":

	import utilities.testBase as tb

	with tb.testSetup():
		obj = Runner()
		obj.go()
