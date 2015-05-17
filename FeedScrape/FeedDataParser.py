
#!/usr/bin/python
# from profilehooks import profile
import urllib.parse
import abc
import json
# pylint: disable=W0201


skip_filter = [
	"www.baka-tsuki.org",
	"re-monster.wikia.com",
]

def getNiceName(srcUrl):
	return False


class DataParser():

	amqpint = None

	def getRawFeedMessage(self, feedDat):

		netloc = getNiceName(feedDat['linkUrl'])
		if not netloc:
			netloc = urllib.parse.urlparse(feedDat['linkUrl']).netloc
		feedDat['srcname'] = netloc

		ret = {
			'type' : 'raw-feed',
			'data' : feedDat
		}
		return json.dumps(ret)

	def processFeedData(self, feedDat):

		if any([item in feedDat['linkUrl'] for item in skip_filter]):
			return

		raw = self.getRawFeedMessage(feedDat)
		self.amqpint.put_item(raw)
