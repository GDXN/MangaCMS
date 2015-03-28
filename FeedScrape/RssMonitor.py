
#!/usr/bin/python
from profilehooks import profile

import abc
import feedparser
import FeedScrape.RssMonitorDbBase
import time
import json
import bs4
import TextScrape.RelinkLookup
# import TextScrape.RELINKABLE as RELINKABLE

# pylint: disable=W0201

class RssMonitor(FeedScrape.RssMonitorDbBase.RssDbBase, metaclass=abc.ABCMeta):
	__metaclass__ = abc.ABCMeta

	loggerPath = 'Main.Rss'

	def __init__(self):
		super().__init__()
		relink = TextScrape.RelinkLookup.getRelinkable()
		# print(relink)

	@abc.abstractproperty
	def feedUrls(self):
		pass


	@profile
	def parseFeed(self, rawFeed):
		return feedparser.parse(rawFeed)

	def loadFeeds(self):

		rawRet = []

		if not hasattr(self, 'wg'):
			import webFunctions
			self.wg = webFunctions.WebGetRobust(logPath='Main.Text.Feed.Web')

		for feedUrl in self.feedUrls:
			# So.... Feedparser shits itself on the feed content,
			# because it's character detection mechanism is apparently
			# total crap.
			# Therefore, use webGet instead, because it can handle
			# encoding properly
			rawFeed = self.wg.getpage(feedUrl)
			feed = self.parseFeed(rawFeed)

			rawRet.append(self.processFeed(feed))

		ret = self.consolidateReturn(rawRet)
		print(ret)

	def consolidateReturn(self, returnData):
		print(returnData)

	def extractContents(self, contentDat):
		# TODO: Add more content type parsing!
		if len(contentDat) != 1:
			raise ValueError("How can one post have multiple contents?")

		contentDat = contentDat[0]
		assert contentDat['type'] == 'text/html'

		content = contentDat['value']
		soup = bs4.BeautifulSoup(content)

		links = []
		for link in soup.find_all('a'):
			try:
				links.append(link['href'])
			except KeyError:
				pass

		return content, links

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

	def processFeed(self, feed):


		meta = feed['feed']
		entries = feed['entries']
		print(meta['title'])
		print(meta['subtitle'])
		print(meta['subtitle'])
		print(len(entries))

		ret = []

		for entry in entries:

			item = {}

			item['title'] = entry['title']

			if 'tags' in entry:
				tags = []
				for tag in entry['tags']:
					tags.append(tag['term'])

				item['tags'] = json.dumps(tags)

			item['linkUrl'] = entry['link']


			if 'content' in entry:
				item['contents'], links = self.extractContents(entry['content'])
			elif 'summary' in entry:
				item['contents'], links = self.extractSummary(entry['summary'])
			else:
				raise ValueError("No contents in item?")


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

				if not 'updated' in item or ('updated' in item and item['updated'] < item['published']):
					item['updated'] = item['published']

			ret.append(item)


		print()


class RssTest(RssMonitor):

	tableKey = 'test'

	feedUrls = [
		'http://krytykal.org/feed/',
		'https://oniichanyamete.wordpress.com/feed/',
		'http://skythewood.blogspot.com/feeds/posts/default',
		'http://www.baka-tsuki.org/project/index.php?title=Special:RecentChanges&feed=atom',
		'http://www.taptaptaptaptap.net/feed/',
		'http://guhehe.net/feed/',
		'http://japtem.com/feed/',
		'http://giraffecorps.liamak.net/feed/',
	]




def test():
	fetch = RssTest()
	# fetch.loadFeeds()


if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	test()

