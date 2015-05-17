
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
# import TextScrape.RELINKABLE as RELINKABLE
import settings



from FeedScrape.RssMonitor import RssMonitor




class RssTest(RssMonitor):

	tableKey = 'rss_monitor'




def convertItems(items):
	ret = []
	for item in items:
		tmp = {}
		tmp['srcname']   = FeedScrape.FeedDataParser.getNiceName(item['contenturl'])
		tmp['linkUrl']   = item['contenturl']
		tmp['title']     = item['title']
		tmp['tags']      = item['tags']
		tmp['published'] = item['published']
		tmp['feedurl']   = item['feedurl']
		tmp['contents']  = item['contents']
		ret.append(tmp)
	return ret

def test():
	# import logSetup
	# logSetup.initLogging()
	fetch = RssTest()
	print("Loading existing RSS Items")
	items = fetch.getRowsByValue(limitByKey=False)
	print("Loaded %s items. Converting to testing format" % len(items))
	testdat = convertItems(items)
	print("Converted %s items. Processing" % len(testdat))

	parser = FeedScrape.FeedDataParser.DataParser()

	for item in testdat:
		ret = parser.processFeedData(item, tx_raw=False)
		# if ret:
		# 	print(ret)

	print("Complete")

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	test()

