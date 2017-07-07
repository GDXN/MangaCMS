
import runStatus
from .FeedLoader import FeedLoader
from .ContentLoader import ContentLoader

import ScrapePlugins.RunBase

import time


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Wr.Run"

	pluginName = "WrLoader"

	sourceName = "WebtoonsReader"
	feedLoader = FeedLoader
	contentLoader = ContentLoader


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()

