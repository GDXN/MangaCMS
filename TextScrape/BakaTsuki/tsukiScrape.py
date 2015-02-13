
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class TsukiScrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'tsuki'
	loggerPath = 'Main.Tsuki.Scrape'
	pluginName = 'TsukiScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 4


	baseUrl = "http://www.baka-tsuki.org/"
	startUrl = baseUrl

	badwords = ["/blog/",
				"/forums/",

				# Yes, I only speak&read english. Leave me to my filtering shame.
				"Category:Brazilian",
				"Category:Brazilian_Portuguese",
				"Category:Czech",
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
				"?title=User_talk:",
				"&oldid=",
				"title=Baka-Tsuki:",
				"title=Special:Book"]

	stripTitle = ' - Baka-Tsuki'


	decomposeBefore = [
		{'id'      :'mw-head'},
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
	scrp = TsukiScrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()




