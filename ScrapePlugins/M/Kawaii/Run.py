

from .FeedLoader import FeedLoader
from .ContentLoader import ContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Kw.Run"

	pluginName = "kawaii"

	sourceName = "Kawaii Scans"
	feedLoader = FeedLoader
	contentLoader = ContentLoader



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()
