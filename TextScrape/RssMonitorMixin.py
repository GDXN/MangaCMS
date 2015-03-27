
#!/usr/bin/python
from profilehooks import profile

import abc
import feedparser
import time
import json
import bs4
import sql

# pylint: disable=W0201

class RssFetchMixin(metaclass=abc.ABCMeta):
	__metaclass__ = abc.ABCMeta



	@abc.abstractproperty
	def feedTableName(self):
		pass

	@abc.abstractproperty
	def feedUrls(self):
		pass


	def checkInitRssDb(self):
		with self.conn.cursor() as cur:

			cur.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
												dbid        SERIAL PRIMARY KEY,
												src         TEXT NOT NULL,

												linkUrl     TEXT NOT NULL UNIQUE,
												title       TEXT,
												contents    TEXT,
												contentHash TEXT NOT NULL,
												author      TEXT,

												tags        JSON,

												updated     DOUBLE PRECISION DEFAULT -1,
												published   DOUBLE PRECISION NOT NULL,

												);'''.format(tableName=self.feedTableName))

			# 'entryHash' is going to be the feed URL + entry title hashed?

			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]

			indexes = [
				("%s_source_index"     % self.feedTableName, self.feedTableName, '''CREATE INDEX %s ON %s (src     );'''  ),
				("%s_linkUrl_index"    % self.feedTableName, self.feedTableName, '''CREATE INDEX %s ON %s (linkUrl );'''  ),
				("%s_istext_index"     % self.feedTableName, self.feedTableName, '''CREATE INDEX %s ON %s (istext  );'''  ),
				("%s_linkUrl_index"    % self.feedTableName, self.feedTableName, '''CREATE INDEX %s ON %s (linkUrl );'''  ),
				("%s_title_index"      % self.feedTableName, self.feedTableName, '''CREATE INDEX %s ON %s (title   );'''  ),
				("%s_title_trigram"    % self.feedTableName, self.feedTableName, '''CREATE INDEX %s ON %s USING gin (title gin_trgm_ops);'''  ),
			]

			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))

		self.conn.commit()
		self.log.info("Retreived page database created")

		self.feedTable = sql.Table(self.feedTableName.lower())
		self.feedCols = (
			self.feedTable.dbid,
			self.feedTable.src,
			self.feedTable.guid,
			self.feedTable.title,
			self.feedTable.contents,
			self.feedTable.contentHash,
			self.feedTable.author,
			self.feedTable.linkUrl,
			self.feedTable.tags,
			self.feedTable.updated,
			self.feedTable.published,
		)


		self.validFeedKwargs = ['dbid', 'src', 'guid', 'title', 'contents', 'contentHash', 'author', 'linkUrl', 'tags', 'updated', 'published']


		self.feedColMap = {
			'dbid'        : self.feedTable.dbid,
			'src'         : self.feedTable.src,
			'guid'        : self.feedTable.guid,
			'title'       : self.feedTable.title,
			'contents'    : self.feedTable.contents,
			'contentHash' : self.feedTable.contentHash,
			'author'      : self.feedTable.author,
			'linkUrl'     : self.feedTable.linkUrl,
			'tags'        : self.feedTable.tags,
			'updated'     : self.feedTable.updated,
			'published'   : self.feedTable.published,
		}

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


class RssTest(RssFetchMixin):

	feedTableName = 'book_feed_items'
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
	fetch.loadFeeds()

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	test()

