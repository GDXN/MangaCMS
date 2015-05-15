
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.SiteArchiver

import urllib.parse
import webFunctions


class Scrape(TextScrape.SiteArchiver.SiteArchiver):
	tableKey = 'tsuki'
	loggerPath = 'Main.Text.Tsuki.Scrape'
	pluginName = 'TsukiScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 10

	IGNORE_MALFORMED_URLS = True

	baseUrl = "http://www.baka-tsuki.org/"
	startUrl = baseUrl

	feeds = [
		# All changes feed (HIGH VOLUME)
		'http://www.baka-tsuki.org/project/index.php?title=Special:RecentChanges&feed=atom'
	]

	badwords = [
				"/blog/",
				"/forums/",

				# Block loaded resources
				"project/load.php",

				# Yes, I only speak&read english. Leave me to my filtering shame.
				"Category:Brazilian",
				"Category:Brazilian_Portuguese",
				"Category:Czech",
				"Category:Bulgarian",
				"Category:Esperanto",
				"Category:Filipino",
				"Category:French",
				"Category:German",
				"Category:Greek",
				"Category:Hungarian",
				"Category:Indonesian",
				"Category:Italian",
				"Category:Korean",
				"Category:Lithuanian",
				"Category:Norwegian",
				"Category:Polish",
				"Category:Romanian",
				"Category:Russian",
				"Category:Spanish",
				"Category:Turkish",
				"Category:Vietnamese",
				"Special:RecentChangesLinked",
				"Format_guideline",
				"(Bahasa_Indonesia)",

				"(Indonesia)",
				"(German)",
				"(French)",
				"(Russian)",
				"(Italian)",
				"(Romanian)",
				"(Norwegian)",
				"(Lithuanian)",
				"(Greek)",
				"~Brazilian_Portuguese~",
				"(Filipino)",
				"(Esperanto)",
				"(Spanish)",
				"(Vietnamese)",
				"(Brazilian_Portuguese)",
				"(Polish)",
				"(Hungarian)",
				"(Korean)",
				"(Turkish)",
				"(Czech)",

				# Block user pages
				"title=User:",
				"=Talk:",
				"=talk:",


				# Links within page
				"http://www.baka-tsuki.org/#",

				# misc
				"viewforum.php",
				"viewtopic.php",
				"memberlist.php",
				"printable=yes",
				"/forums/",
				"title=Special",
				"action=edit",
				"action=history",
				"action=info",
				"title=Help:",
				"title=User_talk:",
				"&oldid=",
				"oldid=",
				"title=Baka-Tsuki:",
				"title=Special:Book",

				"Special:WhatLinksHere",
				"Special:UserLogin",
				"Special:",
				"action=edit",
				"diff=",
				"oldid=",
				"diff%3D",
				"oldid%3D",
				"feed=atom",
				"action=submit",

				"~Russian_Version~",
				"~Russian",
				"~Brazilian",

				]

	stripTitle = ' - Baka-Tsuki'


	decomposeBefore = [
		{'id'      : 'mw-head'},
		{'rel'     : 'EditURI'},
	]
	decompose = [
		{'role'    :'navigation'},
		{'id'      :'footer'},
		{'id'      :'mw-panel'},
		{'id'      :'mw-head'},
		{'id'      :'mw-navigation'},

	]

	def changeFilter(self, url, title, changePercentage):
		# Skip title cruft on baka-tsuki
		if title.strip().startswith("File:"):
			return True

		if title.strip().startswith("Information for"):
			return True

		return False


def test():
	scrp = Scrape()
	scrp.crawl()

if __name__ == "__main__":
	test()




