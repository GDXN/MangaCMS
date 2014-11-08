
import webFunctions
import settings
import os.path

import ScrapePlugins.RetreivalBase

from concurrent.futures import ThreadPoolExecutor

import processDownload

import ScrapePlugins.FoolSlide.FoolSlideDownloadBase

class ContentLoader(ScrapePlugins.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):



	loggerPath = "Main.Rh.Cl"
	pluginName = "RedHawk Scans Content Retreiver"
	tableKey = "rh"
	dbName = settings.dbName
	tableName = "MangaItems"
	groupName = "RedHawk"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 2

	contentSelector = ('div', 'page')


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = ContentLoader()

		fl.go()
