
#!/usr/bin/python
# from profilehooks import profile

import abc
import feedparser
import FeedScrape.RssMonitorDbBase
import TextScrape.utilities.Proxy
import FeedScrape.FeedDataParser
import calendar
import json
import bs4
import TextScrape.RelinkLookup
import urllib.error
import FeedScrape.AmqpInterface
import readability.readability
# import TextScrape.RELINKABLE as RELINKABLE
import settings
# pylint: disable=W0201
#
import TextScrape.HtmlProcessor
import urllib.parse

class EmptyFeedError(Exception):
	pass

class RssMonitor(FeedScrape.RssMonitorDbBase.RssDbBase, FeedScrape.FeedDataParser.DataParser):
	__metaclass__ = abc.ABCMeta

	loggerPath = 'Main.Rss'

	# Has to be explicitly overridden, or the inheritnace will
	# asplode.
	log = None
	test_override = []
	htmlProcClass = TextScrape.HtmlProcessor.HtmlPageProcessor

	def __init__(self):


		self.relink = TextScrape.RelinkLookup.getRelinkable()
		pdata = TextScrape.RelinkLookup.getPluginData()

		self.scan = []

		for plugin in pdata:
			for feed in plugin['feeds']:
				self.scan.append((feed, plugin['pluginName'], plugin['tableName'], plugin['key'], plugin['badwords']))

		self.scan.sort()
		super().__init__()

		if self.test_override:
			self.log.warning("In testing mode, overriding normal feed list mechanism!")
			for item in self.scan[:]:
				if not any([nonblock in item[0] for nonblock in self.test_override]):
					self.scan.remove(item)

			for item in self.scan:
				self.log.warning("Test target: '%s'", item[0])

	# @profile
	def parseFeed(self, rawFeed):
		return feedparser.parse(rawFeed)

	def loadFeeds(self):

		ret = []

		if not hasattr(self, 'wg'):
			import webFunctions
			self.wg = webFunctions.WebGetRobust(logPath='Main.Text.Feed.Web')

		for feedUrl, pluginName, tableName, tableKey, badwords in self.scan:
			# So.... Feedparser shits itself on the feed content,
			# because it's character detection mechanism is apparently
			# total crap.
			# Therefore, use webGet instead, because it can handle
			# encoding properly

			try:
				self.log.info("Checking feed '%s'.", feedUrl)
				rawFeed = self.wg.getpage(feedUrl)
				feed = self.parseFeed(rawFeed)

				data = self.processFeed(feed, feedUrl)
				self.insertFeed(tableName, tableKey, pluginName, feedUrl, data, badwords)

			except urllib.error.URLError:
				self.log.error('Failure retrieving feed at url "%s"!', feedUrl)


	def extractContents(self, feedUrl, contentDat):
		# TODO: Add more content type parsing!

		# So the complete fruitcakes at http://gravitytales.com/feed/ are apparently
		# embedding their RSS entries in a CDATA field in their feed, somehow.
		# Anyways, I think they probably broke wordpress. However, they're then breaking
		# /my/ stuff, so work around their fucked up feed format.
		if isinstance(contentDat, str):
			contentDat = [{
				'value' : contentDat,
				'type'  : 'text/html'
			}]
		if len(contentDat) != 1:
			print(contentDat)
			raise ValueError("How can one post have multiple contents?")

		contentDat = contentDat[0]

		baseurl = urllib.parse.urlsplit(feedUrl).netloc.lower()
		tld = set([baseurl.split(".")[-1]])

		scraper = self.htmlProcClass(
									baseUrls           = [feedUrl],
									pageUrl            = feedUrl,
									pgContent          = contentDat['value'],
									loggerPath         = self.loggerPath,
									followGLinks       = True,
									tld                = tld,
									relinkable         = self.relink,
									ignoreMissingTitle = True,
								)

		try:
			extracted = scraper.extractContent()
		except readability.readability.Unparseable:
			self.log.error("Parsing error in content!")
			return contentDat, []

		assert contentDat['type'] == 'text/html'
		content = extracted['contents']

		# Use a parser that doesn't try to generate a well-formed output (and therefore doesn't insert
		# <html> or <body> into content that will be only a part of the rendered page)
		soup = bs4.BeautifulSoup(content, "html.parser")



		if soup.html:
			soup.html.unwrap()
		if soup.body:
			soup.body.unwrap()

		try:
			cont = soup.prettify()
		except RuntimeError:
			try:
				cont = str(soup)
			except RuntimeError:
				cont = '<H2>WARNING - Failure when cleaning and extracting content!</H2><br><br>'
				cont += content


		return extracted

	def extractSummary(self, contentDat):
		# TODO: Some stats to try to guess is the content is HTML or not (and then whack it with markdown!)

		soup = bs4.BeautifulSoup(contentDat)

		links = []
		for link in soup.find_all('a'):
			try:
				links.append(link['href'])
			except KeyError:
				pass

		return contentDat, links

	def processFeed(self, feed, feedUrl, feedtype='eastern'):


		meta = feed['feed']
		entries = feed['entries']

		ret = []

		for entry in entries:
			item = {}

			item['title'] = entry['title']
			item['guid'] = entry['guid']

			item['tags'] = []
			if 'tags' in entry:
				for tag in entry['tags']:
					item['tags'].append(tag['term'])


			item['linkUrl'] = entry['link']


			if 'content' in entry:
				item['contents'] = entry['content']
			elif 'summary' in entry:
				item['contents'] = entry['summary']
			else:
				self.log.error('Empty item in feed?')
				self.log.error('Feed url: %s', feedUrl)
				continue

			item['authors'] = entry['authors']
			# guid
			# contents
			# contentHash
			# author
			# linkUrl
			# tags


			if 'updated_parsed' in entry:
				item['updated'] = calendar.timegm(entry['updated_parsed'])

			if 'published_parsed' in entry:
				item['published'] = calendar.timegm(entry['published_parsed'])

			if not 'published' in item or ('updated' in item and item['published'] > item['updated']):
				item['published'] = item['updated']
			if not 'updated' in item:
				item['updated'] = -1

			item['feedtype'] = feedtype


			self.processFeedData(item)

			item['tags'] = json.dumps(item['tags'])

			ret.append(item)
		return ret

	def insertFeed(self, tableName, tableKey, pluginName, feedUrl, feedContent, badwords):
		print("InsertFeed!")
		dbFunc = TextScrape.utilities.Proxy.EmptyProxy(tableKey=tableKey, tableName=tableName, scanned=[feedUrl])

		for item in feedContent:
			if item['title'].startswith('User:') and tableKey == 'tsuki':
				# The tsuki feed includes changes to user pages. Fuck that noise. Ignore that shit.
				continue

			try:
				ret = self.extractContents(feedUrl, item['contents'])
				# print(ret)
				# ret = dbFunc.processHtmlPage(feedUrl, item['contents'])
			except RuntimeError:
				ret = {}
				ret['contents'] = '<H2>WARNING - Failure when cleaning and extracting content!</H2><br><br>'
				ret['contents'] += item['contents']
				ret['rsrcLinks'] = []
				ret['plainLinks'] = []
				self.log.error("Wat? Error when extracting contents!")



			if not self.itemInDB(contentid=item['guid']):

				self.log.info("New article in feed!")


				row = {
					'srcname'    : tableKey,
					'feedurl'    : feedUrl,
					'contenturl' : item['linkUrl'],
					'contentid'  : item['guid'],
					'title'      : item['title'],
					'contents'   : ret['contents'],
					'author'     : '',
					'tags'       : item['tags'],
					'updated'    : item['updated'],
					'published'  : item['published'],
				}

				self.insertIntoDb(**row)

			dbFunc.upsert(item['linkUrl'], dlstate=0, distance=0, walkLimit=1)
			for link in ret['plainLinks']:
				print("Adding link '%s' to the queue" % link)
				if not any([badword in link for badword in badwords]):
					dbFunc.upsert(link, dlstate=0, distance=0, walkLimit=1)
				else:
					print("Filtered link!", link)
			for link in ret['rsrcLinks']:
				if not any([badword in link for badword in badwords]):
					dbFunc.upsert(link, distance=0, walkLimit=1, istext=False)





class RssTest(RssMonitor):

	tableKey = 'wp'

	test_override = [
		# 'https://bluesilvertranslations.wordpress.com/feed/',
		'https://natsutl.wordpress.com/feed/',
	# 	'http://krytykal.org/feed/',
	# 	'https://oniichanyamete.wordpress.com/feed/',
	# 	'http://skythewood.blogspot.com/feeds/posts/default',
	# 	'http://www.baka-tsuki.org/project/index.php?title=Special:RecentChanges&feed=atom',
	# 	'http://www.taptaptaptaptap.net/feed/',
	# 	'http://guhehe.net/feed/',
	# 	'http://japtem.com/feed/',
	# 	'http://giraffecorps.liamak.net/feed/',
	]




def test():
	# import logSetup
	# logSetup.initLogging()
	fetch = RssTest()
	fetch.loadFeeds()


if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	test()

