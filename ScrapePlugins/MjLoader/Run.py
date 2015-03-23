

from ScrapePlugins.MjLoader.mjFeedLoader import MjFeedLoader
from ScrapePlugins.MjLoader.mjContentLoader import MjContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Mj.Run"

	pluginName = "MjLoader"


	sourceName = "MangaJoy"
	feedLoader = MjFeedLoader
	contentLoader = MjContentLoader


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=True):
		mon = Runner()
		mon.go()
