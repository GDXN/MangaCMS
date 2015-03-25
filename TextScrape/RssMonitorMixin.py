
import abc
import feedparser

class RssFetchMixin(metaclass=abc.ABCMeta):
	__metaclass__ = abc.ABCMeta


	@abc.abstractproperty
	def feedUrls(self):
		pass

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
			feed = feedparser.parse(rawFeed)

			rawRet.append(self.processFeed(feed))

		ret = self.consolidateReturn(rawRet)
		print(ret)

	def consolidateReturn(self, returnData):
		print(returnData)

	def processFeed(self, feed):

		for key, value in feed.items():
			if key == 'entries':
				continue
			print(key, value)

		print()
		print()
		print()
		print()



class RssTest(RssFetchMixin):

	tableKey = 'test'

	feedUrls = [
		'https://trippingoverwn.wordpress.com/feed/',
		'https://oniichanyamete.wordpress.com/feed/',
		'https://manga0205.wordpress.com/feed/',
	]




def test():
	fetch = RssTest()
	fetch.loadFeeds()

if __name__ == "__main__":
	test()

