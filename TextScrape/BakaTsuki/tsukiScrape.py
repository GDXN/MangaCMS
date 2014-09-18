
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()
import logging

import TextScrape.SqlBase

import readability.readability
import webFunctions
import bs4
import urllib.parse

import runStatus

import queue
import time
from concurrent.futures import ThreadPoolExecutor

# Double inheritance funkyness to allow subclass to override __tablename__ properly
# If we have TextScrape.SqlBase.PageRow inherit from TextScrape.SqlBase.Base, the
# Base funkyness captures the parent-class tablename and bind to it or something,
# so when it's overridden, the linkage fails.
class TsukiRow(TextScrape.SqlBase.PageRow, TextScrape.SqlBase.Base):
	__tablename__ = 'tsuki_pages'

class TsukiScrape(TextScrape.SqlBase.TextScraper):
	rowClass = TsukiRow
	loggerPath = 'Main.Tsuki'
	pluginName = 'TsukiScrape'

	log = logging.getLogger(loggerPath)
	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 4

	baseUrl = "http://www.baka-tsuki.org/"

	badwords = ["/blog/",
				"/forums/",

				# Yes, I only speak&read english. Leave me to my filtering shame.
				"Category:German",
				"Category:Spanish",
				"Category:French",
				"Category:Vietnamese",
				"Category:Russian",
				"Category:Brazilian_Portuguese",
				"Category:Italian",
				"Category:Polish",
				"Category:Romanian",
				"Category:Hungarian",
				"Category:Norwegian",
				"Category:Korean",
				"Category:Lithuanian",
				"Category:Indonesian",
				"Category:Greek",
				"Category:Turkish",
				"Category:Filipino",
				"Category:Czech",
				"Category:Esperanto",

				# Block user pages
				"title=User:",

				# Links within page
				"http://www.baka-tsuki.org/#",

				# misc
				"printable=yes",
				"title=Special",
				"action=edit",
				"action=history",
				"title=Help:",
				"?title=User_talk:",
				"&oldid=",
				"title=Baka-Tsuki:",
				"title=Special:Book"]



	def cleanBtPage(self, inPage, srcUrl=None):

		doc = readability.readability.Document(inPage, base_url=srcUrl, negative_keywords=['mw-normal-catlinks', "printfooter", "mw-panel", 'portal'])
		doc.parse()
		content = doc.content()
		soup = bs4.BeautifulSoup(content)

		# Permute page tree, extract (and therefore remove) all nav tags.
		for tag in soup.find_all(role="navigation"):
			tag.decompose()

		return doc.title(), soup.prettify()

	def extractLinks(self, pageCtnt):
		soup = bs4.BeautifulSoup(pageCtnt)
		retLinks = set()
		for link in soup.find_all("a"):

			# Skip empty anchor tags
			try:
				turl = link["href"]
			except KeyError:
				continue

			url = urllib.parse.urljoin(self.baseUrl, turl)

			# Filter by domain
			if not self.baseUrl in url:
				continue

			# and by blocked words
			hadbad = False
			for badword in self.badwords:
				if badword in url:
					hadbad = True
			if hadbad:
				continue

			if not url in retLinks:
				retLinks.add(url)

		return retLinks


	def addPage(self, pgUrl, pgTitle, pgBody):
		# TODO: Update logic!

		haveRow = self.session.query(TsukiRow).filter_by(url=pgUrl).first()
		if not haveRow:
			newRow = TsukiRow(url=pgUrl, title=pgTitle, series=None, contents=pgBody)
			self.session.add(newRow)
			self.session.commit()

	def fetchPage(self, url):
		self.log.info("Fetching page '%s'", url)
		gotPage = self.wg.getpage(url)

		pgTitle, pgBody = self.cleanBtPage(gotPage)
		links = self.extractLinks(gotPage)
		self.addPage(url, pgTitle, pgBody)

		return links

	def queueLoop(self, inQueue, outQueue):

		# Timeouts is used to track when queues are empty
		# Since I have multiple threads, and there are known
		# situations where we can be certain that there will be
		# only one request (such as at startup), we need to
		# have a mechanism for retrying fetches from a queue a few
		# times before concluding there is nothing left to do
		timeouts = 0
		while runStatus.run:
			try:
				url = inQueue.get_nowait()
				ret = self.fetchPage(url)
				for url in ret:
					outQueue.put(url)
				timeouts = 0
			except queue.Empty:
				timeouts += 1
				time.sleep(1)

			if timeouts > 5:
				break

		self.log.info("Fetch thread exiting!")

	def crawl(self):

		haveUrls = set([self.baseUrl])


		toScanQueue = queue.Queue()
		linkReturnQueue = queue.Queue()

		toScanQueue.put(self.baseUrl)


		with ThreadPoolExecutor(max_workers=self.threads) as executor:

			processes = []
			for dummy_x in range(self.threads):
				processes.append(executor.submit(self.queueLoop, toScanQueue, linkReturnQueue))


			newUrls = 0
			while runStatus.run:


				try:
					url = linkReturnQueue.get_nowait()

					if not url in haveUrls:
						toScanQueue.put(url)
						haveUrls.add(url)
						newUrls += 1


				except queue.Empty:

					if newUrls:
						self.log.info("%s new URLs to scan", newUrls)
						newUrls = 0

					time.sleep(0.01)

				if not any([proc.running() for proc in processes]):
					break

		self.log.info("Crawler scanned a total of '%s' pages", len(haveUrls))
		self.log.info("Queue Feeder thread exiting!")


if __name__ == '__main__':
	print("Wat")
	row = TsukiRow()
	print(row)
	scrp = TsukiScrape()
	scrp.crawl()
	# scrp.fetchPage("http://www.baka-tsuki.org/project/index.php?title=Category:Light_novel_(English)")
	# scrp.fetchPage("http://www.baka-tsuki.org/project/index.php?title=Chrome_Shelled_Regios")
	# scrp.fetchPage("http://www.baka-tsuki.org/project/index.php?title=Main_Page")
	# print(scrp.session.dirty)

	# t1 = TsukiRow(url='Wat?', title='Wat?', series='Wat?', contents='Wat?')
	# t2 = TsukiRow(url='Lol?', title='Lol?', series='Lol?', contents='Lol?')
	# t3 = TsukiRow(url='er?', title='er?', series='er?', contents='er?')
	# t4 = TsukiRow(url='coas?', title='coas?', series='coas?', contents='coas?')
	# t5 = TsukiRow(url='ter?', title='ter?', series='ter?', contents='ter?')

	# scrp.session.add_all([t1, t2, t3])
	# scrp.session.add(t4)
	# scrp.session.add(t5)
	# scrp.session.commit()

	# print(scrp.session.dirty)
	# print('Columns = ', scrp.columns)
	# print(scrp.session.query(TsukiRow).filter_by(title='Wat?').first())
	# print(scrp.session.dirty)
