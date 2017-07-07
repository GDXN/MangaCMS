

from .SeriesLoader   import SeriesLoader
from .SeriesEnqueuer import SeriesEnqueuer

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.BtS.Run"

	pluginName = "BtEnqueue"

	sourceName = "BatotoSeries"

	feedLoader    = SeriesLoader
	contentLoader = SeriesEnqueuer


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		run = Runner()

		run.go()
		# fl.go()
