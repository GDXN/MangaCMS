
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.SqlBase

import readability.readability
import bs4
import webFunctions


class TsukiScrape(TextScrape.SqlBase.TextScraper):
	tableKey = 'tsuki'
	loggerPath = 'Main.Tsuki'
	pluginName = 'TsukiScrape'

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
				"viewforum.php",
				"viewtopic.php",
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
		self.updateDbEntry(url=url, title=pgTitle, contents=pgBody, mimetype=mimeType, dlstate=2)


	# Retreive remote content at `url`, call the appropriate handler for the
	# transferred content (e.g. is it an image/html page/binary file)
	def retreiveItemFromUrl(self, url):
		self.log.info("Fetching page '%s'", url)
		content, fName, mimeType = self.getItem(url)

		links = []

		if mimeType == 'text/html':
			self.log.info("Processing '%s' as HTML.", url)
			self.processPage(url, content, mimeType)
		elif mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
			self.log.info("Processing '%s' as an image file.", url)
			self.saveFile(url, mimeType, fName, content)
		elif mimeType in ["application/octet-stream"]:
			self.log.info("Processing '%s' as an binary file.", url)
			self.saveFile(url, mimeType, fName, content)
		else:
			self.log.warn("Unknown MIME Type? '%s', Url: '%s'", mimeType, url)


		return links
