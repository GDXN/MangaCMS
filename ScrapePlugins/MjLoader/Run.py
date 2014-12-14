

from ScrapePlugins.MjLoader.mjFeedLoader import MjFeedLoader
from ScrapePlugins.MjLoader.mjContentLoader import MjContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Mj.Run"

	pluginName = "MjLoader"


	sourceName = "MangaJoy"
	feedLoader = MjFeedLoader
	contentLoader = MjContentLoader


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		mon = Runner()
		mon.go()
