
#!/usr/bin/python
# from profilehooks import profile

import abc
import feedparser
import FeedScrape.RssMonitorDbBase
import TextScrape.utilities.Proxy
import time
import json
import bs4
import TextScrape.RelinkLookup
import urllib.error
import FeedScrape.AmqpInterface
# import TextScrape.RELINKABLE as RELINKABLE
import settings
# pylint: disable=W0201

class EmptyFeedError(Exception):
	pass

class RssMonitor(FeedScrape.RssMonitorDbBase.RssDbBase, metaclass=abc.ABCMeta):
	__metaclass__ = abc.ABCMeta

	loggerPath = 'Main.Rss'

	def __init__(self):
		super().__init__()
		self.relink = TextScrape.RelinkLookup.getRelinkable()
		pdata = TextScrape.RelinkLookup.getPluginData()

		self.scan = []
		for plugin in pdata:
			for feed in plugin['feeds']:
				self.scan.append((feed, plugin['pluginName'], plugin['tableName'], plugin['key'], plugin['badwords']))

		self.scan.sort()
		amqp_settings = {}
		amqp_settings["RABBIT_CLIENT_NAME"] = settings.RABBIT_CLIENT_NAME
		amqp_settings["RABBIT_LOGIN"]       = settings.RABBIT_LOGIN
		amqp_settings["RABBIT_PASWD"]       = settings.RABBIT_PASWD
		amqp_settings["RABBIT_SRVER"]       = settings.RABBIT_SRVER
		amqp_settings["RABBIT_VHOST"]       = settings.RABBIT_VHOST
		self.amqpint = FeedScrape.AmqpInterface.RabbitQueueHandler(settings=amqp_settings)


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


	def extractContents(self, contentDat):
		# TODO: Add more content type parsing!
		if len(contentDat) != 1:
			raise ValueError("How can one post have multiple contents?")

		contentDat = contentDat[0]
		assert contentDat['type'] == 'text/html'

		content = contentDat['value']

		# Use a parser that doesn't try to generate a well-formed output (and therefore doesn't insert
		# <html> or <body> into content that will be only a part of the rendered page)
		soup = bs4.BeautifulSoup(content, "html.parser")

		links = []
		for link in soup.find_all('a'):
			try:
				links.append(link['href'])
			except KeyError:
				pass

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
		return cont, links

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

	def processFeed(self, feed, feedUrl):


		meta = feed['feed']
		entries = feed['entries']

		ret = []

		for entry in entries:
			item = {}

			item['title'] = entry['title']
			item['guid'] = entry['guid']

			tags = []
			if 'tags' in entry:
				for tag in entry['tags']:
					tags.append(tag['term'])

			item['tags'] = json.dumps(tags)


			item['linkUrl'] = entry['link']


			if 'content' in entry:
				item['contents'], links = self.extractContents(entry['content'])
			elif 'summary' in entry:
				item['contents'], links = self.extractSummary(entry['summary'])
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
				item['updated'] = time.mktime(entry['updated_parsed'])

			if 'published_parsed' in entry:
				item['published'] = time.mktime(entry['published_parsed'])

			if not 'published' in item or ('updated' in item and item['published'] > item['updated']):
				item['published'] = item['updated']
			if not 'updated' in item:
				item['updated'] = -1


			self.amqpint.put_item(json.dumps(item))

			ret.append(item)
		return ret

	def insertFeed(self, tableName, tableKey, pluginName, feedUrl, feedContent, badwords):

		dbFunc = TextScrape.utilities.Proxy.EmptyProxy(tableKey=tableKey, tableName=tableName, scanned=[feedUrl])

		for item in feedContent:
			if item['title'].startswith('User:') and tableKey == 'tsuki':
				# The tsuki feed includes changes to user pages. Fuck that noise. Ignore that shit.
				continue

			if not self.itemInDB(contentid=item['guid']):

				self.log.info("New article in feed!")

				try:
					ret = dbFunc.processHtmlPage(feedUrl, item['contents'])
				except RuntimeError:
					ret = {}
					ret['contents'] = '<H2>WARNING - Failure when cleaning and extracting content!</H2><br><br>'
					ret['contents'] += item['contents']

					ret['rsrcLinks'] = []
					ret['plainLinks'] = []

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
					if not any([badword in link for badword in badwords]):
						dbFunc.upsert(link, dlstate=0, distance=0, walkLimit=1)
					else:
						print("Filtered link!", link)
				for link in ret['rsrcLinks']:
					if not any([badword in link for badword in badwords]):
						dbFunc.upsert(link, distance=0, walkLimit=1, istext=False)





class RssTest(RssMonitor):

	tableKey = 'test'

	# feedUrls = [
	# 	'http://krytykal.org/feed/',
	# 	'https://oniichanyamete.wordpress.com/feed/',
	# 	'http://skythewood.blogspot.com/feeds/posts/default',
	# 	'http://www.baka-tsuki.org/project/index.php?title=Special:RecentChanges&feed=atom',
	# 	'http://www.taptaptaptaptap.net/feed/',
	# 	'http://guhehe.net/feed/',
	# 	'http://japtem.com/feed/',
	# 	'http://giraffecorps.liamak.net/feed/',
	# ]




def test():
	# import logSetup
	# logSetup.initLogging()
	fetch = RssTest()
	fetch.loadFeeds()


if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	test()

