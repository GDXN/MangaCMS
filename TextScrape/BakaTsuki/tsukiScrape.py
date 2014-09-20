
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
		print("Setting self.src", self.src)
		super().__init__(*args, **kwds)

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




	def getItem(self, itemUrl):

		content, handle = self.wg.getpage(itemUrl, returnMultiple=True)
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % itemUrl)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		mType = handle.info()['Content-Type']

		# If there is an encoding in the content-type (or any other info), strip it out.
		# We don't care about the encoding, since WebFunctions will already have handled that,
		# and returned a decoded unicode object.
		if ";" in mType:
			mType = mType.split(";")[0].strip()

		self.log.info("Retreived file of type '%s', name of '%s' with a size of %0.3f K", mType, fileN, len(content)/1000.0)
		return content, fileN, mType


	def convertToReaderUrl(self, inUrl):
		url = urllib.parse.urljoin(self.baseUrl, inUrl)
		url = '/books/render?url=%s' % urllib.parse.quote(url)
		return url

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

			# the fact that retLinks is a set takes care of preventing duplicates.
			retLinks.add(url)



		for imtag in soup.find_all("img"):
						# Skip empty anchor tags
			try:
				turl = imtag["src"]
			except KeyError:
				continue

			# Skip tags with `img src=""`.
			# No idea why they're there, but they are
			if not url:
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


			retLinks.add(url)

		return retLinks




	def addPage(self, pgUrl, pgTitle, pgBody, mimeType):
		# TODO: Update logic!

		haveRow = self.session.query(self.rowClass).filter_by(url=pgUrl).first()
		if not haveRow:
			print(self.rowClass)
			newRow = self.rowClass(url=pgUrl, title=pgTitle, series=None, contents=pgBody, istext=True, mimetype=mimeType)
			self.session.add(newRow)
		self.session.commit()


	def processPage(self, url, content, mimeType):


		pgTitle, pgBody = self.cleanBtPage(content)
		links = self.extractLinks(content)
		self.addPage(url, pgTitle, pgBody, mimeType)

		return links


	# Retreive remote content at `url`, call the appropriate handler for the
	# transferred content (e.g. is it an image/html page/binary file)
	def retreiveItemFromUrl(self, url):
		self.log.info("Fetching page '%s'", url)
		gotPage = self.wg.getpage(url)
		content, fName, mimeType = self.getItem(url)

		links = []

		if mimeType == 'text/html':
			self.log.info("Processing '%s' as HTML.", url)
			links = self.processPage(url, content, mimeType)
		elif mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
			self.log.info("Processing '%s' as an image file.", url)
			self.saveFile(url, mimeType, fName, content)
		else:
			self.log.warn("Unknown MIME Type? '%s', Url: '%s'", mimeType, url)
		self.log.info("%s new links" % len(links))

		return links



	def queueLoop(self, inQueue, outQueue):

		try:
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
					ret = self.retreiveItemFromUrl(url)
					for url in ret:
						outQueue.put(url)
					timeouts = 0
				except queue.Empty:
					timeouts += 1
					time.sleep(1)

				if timeouts > 5:
					break

			self.log.info("Fetch thread exiting!")
		except Exception:
			traceback.print_exc()

	def crawl(self):

		haveUrls = set([self.baseUrl])


		toScanQueue = queue.Queue()
		linkReturnQueue = queue.Queue()

		toScanQueue.put('http://www.baka-tsuki.org/project/index.php?title=Main_Page')


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
