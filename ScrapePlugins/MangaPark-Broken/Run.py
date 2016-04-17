

from .FeedLoader import FeedLoader
from .ContentLoader import ContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Mp.Run"

	pluginName = "MpLoader"

	sourceName = "MangaPark"
	feedLoader = FeedLoader
	contentLoader = ContentLoader






if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		mon = Runner()
		mon.go()

