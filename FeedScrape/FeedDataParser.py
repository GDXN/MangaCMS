
#!/usr/bin/python
# from profilehooks import profile

import abc
import json
# pylint: disable=W0201

class DataParser():

	amqpint = None

	def getRawFeedMessage(self, feedDat):
		ret = {
			'type' : 'raw-feed',
			'data' : feedDat
		}
		return json.dumps(ret)

	def processFeedData(self, feedDat):

		self.amqpint.put_item(self.getRawFeedMessage(feedDat))
