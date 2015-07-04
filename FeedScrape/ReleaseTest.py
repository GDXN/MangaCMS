
#!/usr/bin/python
# from profilehooks import profile

import FeedScrape.RssMonitorDbBase
import FeedScrape.FeedDataParser
import FeedScrape.AmqpInterface
# import TextScrape.RELINKABLE as RELINKABLE




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
	import sys
	# import logSetup
	# logSetup.initLogging()
	fetch = RssTest()
	print("Loading existing RSS Items")
	items = fetch.getRowsByValue(limitByKey=False)
	print("Loaded %s items. Converting to testing format" % len(items))
	testdat = convertItems(items)
	print("Converted %s items. Processing" % len(testdat))

	debug_print = False
	if "print" in sys.argv:
		debug_print = True

	transmit = True
	if "no_tx" in sys.argv:
		transmit = False


	# parser = FeedScrape.FeedDataParser.DataParser(transfer=False)
	parser = FeedScrape.FeedDataParser.DataParser(debug_print=debug_print)

	print("Processing items")
	for item in testdat:
		ret = parser.processFeedData(item, tx_raw=False, tx_parse=transmit)
		# if ret:
		# 	print(ret)

	print("Complete")

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	test()

