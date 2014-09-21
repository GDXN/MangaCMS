
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()
import logging

import TextScrape.SqlBase

import traceback
import readability.readability
import webFunctions
import bs4
import threading
import urllib.parse

import runStatus

import queue
import time
from concurrent.futures import ThreadPoolExecutor

# Double inheritance funkyness to allow subclass to override __tablename__ properly
# If we have TextScrape.SqlBase.PageRow inherit from TextScrape.SqlBase.Base, the
# Base funkyness captures the parent-class tablename and bind to it or something,
# so when it's overridden, the linkage fails.
class TsukiRow(TextScrape.SqlBase.Base):
	_source_key = 'tsuki'


	# Set the default value of `src`. Somehow, despite the fact that `self.src` is being set
	# to a string, it still works.
	def __init__(self, *args, **kwds):
		self.src = self._source_key
		super().__init__(*args, **kwds)

class TsukiScrape(TextScrape.SqlBase.TextScraper):
	rowClass = TsukiRow
	loggerPath = 'Main.Tsuki'
	pluginName = 'TsukiScrape'

	log = logging.getLogger(loggerPath)
	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1


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


	def cleanBtPage(self, inPage):

		doc = readability.readability.Document(inPage, negative_keywords=['mw-normal-catlinks', "printfooter", "mw-panel", 'portal'])
		doc.parse()
		content = doc.content()
		soup = bs4.BeautifulSoup(content)

		# Permute page tree, extract (and therefore remove) all nav tags.
		for tag in soup.find_all(role="navigation"):
			tag.decompose()
		contents = ''


		for aTag in soup.find_all("a"):
			try:
				aTag["href"] = self.convertToReaderUrl(aTag["href"])
			except KeyError:
				continue

		for imtag in soup.find_all("img"):
			try:
				imtag["src"] = self.convertToReaderUrl(imtag["src"])
			except KeyError:
				continue




		for item in soup.body.contents:
			if type(item) is bs4.Tag:
				contents += item.prettify()
			elif type(item) is bs4.NavigableString:
				contents += item
			else:
				print("Wat", item)

		title = doc.title()
		title = title.replace(" - Baka-Tsuki", "")

		return title, contents



	def processPage(self, url, content, mimeType):


		pgTitle, pgBody = self.cleanBtPage(content)
		self.extractLinks(content)
		self.updatePage(url, title=pgTitle, contents=pgBody, mimetype=mimeType, dlstate=2)


	# Retreive remote content at `url`, call the appropriate handler for the
	# transferred content (e.g. is it an image/html page/binary file)
	def retreiveItemFromUrl(self, url):
		self.log.info("Fetching page '%s'", url)
		gotPage = self.wg.getpage(url)
		content, fName, mimeType = self.getItem(url)

		links = []

		if mimeType == 'text/html':
			self.log.info("Processing '%s' as HTML.", url)
			self.processPage(url, content, mimeType)
		elif mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
			self.log.info("Processing '%s' as an image file.", url)
			self.saveFile(url, mimeType, fName, content)
		else:
			self.log.warn("Unknown MIME Type? '%s', Url: '%s'", mimeType, url)


		return links



	def queueLoop(self, outQueue):
		self.log.info("Fetch thread starting")
		try:
			# Timeouts is used to track when queues are empty
			# Since I have multiple threads, and there are known
			# situations where we can be certain that there will be
			# only one request (such as at startup), we need to
			# have a mechanism for retrying fetches from a queue a few
			# times before concluding there is nothing left to do
			timeouts = 0
			while runStatus.run:

				url = self.getToDo()
				if url:

					fetchUrl = url.url

					self.retreiveItemFromUrl(fetchUrl)
					outQueue.put(fetchUrl)
				else:
					timeouts += 1
					time.sleep(1)

				if timeouts > 5:
					break

			self.log.info("Fetch thread exiting!")
		except Exception:
			traceback.print_exc()

	def crawl(self):

		haveUrls = set([self.baseUrl])



		scannedQueue = queue.Queue()

		startUrl = 'http://www.baka-tsuki.org/'
		self.upsert(startUrl)
		self.updatePage(startUrl, dlstate=0)

		scanned = []

		with ThreadPoolExecutor(max_workers=self.threads) as executor:

			processes = []
			for dummy_x in range(self.threads):
				self.log.info("Starting child-thread!")
				processes.append(executor.submit(self.queueLoop, scannedQueue))


			while runStatus.run:



				time.sleep(0.01)

				try:
					got = scannedQueue.get_nowait()
					if got in scanned:
						runStatus.run = False
						self.log.error("Repeated scan of item at URL '%s'", got)
						raise ValueError("Double-scanned item '%s' !" % got)

					scanned.append(got)
				except queue.Empty:
					pass




				if not any([proc.running() for proc in processes]):
					self.log.info("All threads stopped. Main thread exiting.")
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
