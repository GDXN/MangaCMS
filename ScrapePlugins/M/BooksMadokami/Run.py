

from .DbLoader      import DbLoader
from .ContentLoader import ContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Books.Mk.Run"

	pluginName = "MkBookLoader"


	sourceName = "MadokamiBooks"
	feedLoader = DbLoader
	contentLoader = ContentLoader

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()
