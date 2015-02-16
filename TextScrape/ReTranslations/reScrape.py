
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import webFunctions

# import TextScrape.ReTranslations.gDocParse as gdp

class ReScrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'retrans'
	loggerPath = 'Main.ReTrans.Scrape'
	pluginName = 'ReTransScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1


	startUrl = [
		"https://docs.google.com/document/d/1ljoXDy-ti5N7ZYPbzDsj5kvYFl3lEWaJ1l3Lzv1cuuM/preview",
		"https://docs.google.com/document/d/1t4_7X1QuhiH9m3M8sHUlblKsHDAGpEOwymLPTyCfHH0/preview"
		]
	baseUrl = "https://docs.google.com/document/"

	badwords = []



def test():
	scrp = ReScrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

