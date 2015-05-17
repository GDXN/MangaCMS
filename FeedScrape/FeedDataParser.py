
#!/usr/bin/python
# from profilehooks import profile
import urllib.parse
import re
import json
import logging
from FeedScrape.feedNameLut import getNiceName
# pylint: disable=W0201


skip_filter = [
	"www.baka-tsuki.org",
	"re-monster.wikia.com",
]

def buildReleaseMessage(raw_item, series, vol, chap, postfix=''):
	'''
	Special case behaviour:
		If vol or chapter is None, the
		item in question will sort to the end of
		the relevant sort segment.
	'''
	return {
		'srcname'   : raw_item['srcname'],
		'series'    : series,
		'vol'       : vol,
		'chp'       : chap,
		'published' : raw_item['published'],
		'itemurl'   : raw_item['linkUrl'],
		'postfix'   : postfix,
	}

def packChapterFragments(chapStr, fragStr):
	chap = float(chapStr)
	frag = float(fragStr)
	return '%0.2f' % (chap + (frag / 100.0))


class DataParser():

	amqpint = None

	def __init__(self):
		logPath = 'Main.Feeds.Parser'
		self.log = logging.getLogger(logPath)

	####################################################################################################################################################
	# Sousetsuka
	####################################################################################################################################################


	def extractSousetsuka(self, item):

		# check that 'Desumachi' is in the tags? It seems to work well enough now....

		desumachi_norm  = re.search(r'^(Death March kara Hajimaru Isekai Kyusoukyoku) (\d+)\W(\d+)$', item['title'])
		desumachi_extra = re.search(r'^(Death March kara Hajimaru Isekai Kyusoukyoku) (\d+)\W(Intermission.*?)$', item['title'])
		if desumachi_norm:
			series = desumachi_norm.group(1)
			vol    = desumachi_norm.group(2)
			chp    = desumachi_norm.group(3)
			return buildReleaseMessage(item, series, vol, chp)
		elif desumachi_extra:
			series  = desumachi_extra.group(1)
			vol     = desumachi_extra.group(2)
			postfix = desumachi_extra.group(3)
			return buildReleaseMessage(item, series, vol, None, postfix=postfix)

		# else:
		# 	self.log.warning("Cannot decode item:")
		# 	self.log.warning("%s", item)
		return False

	####################################################################################################################################################
	# お兄ちゃん、やめてぇ！ / Onii-chan Yamete
	####################################################################################################################################################

	def extractOniichanyamete(self, item):
		# print('"{}" "{}"'.format(item['title'], item['tags']))

		tilea_norm       = re.search(r'^(Tilea’s Worries) – Chapter (\d+)$',               item['title'])
		tilea_extra      = re.search(r'^(Tilea’s Worries) – ([^0-9]*?)$',                  item['title'])
		other_world_norm = re.search(r'^(I’m Back in the Other World\?) – Chapter (\d+)$', item['title'])
		jashin_norm      = re.search(r'^(Jashin Average) – (\d+)$',                        item['title'])


		if tilea_norm:
			series  = tilea_norm.group(1)
			vol     = None
			chp     = tilea_norm.group(2)
			return buildReleaseMessage(item, series, vol, chp)
		elif tilea_extra:
			series  = tilea_extra.group(1)
			vol     = None
			chp     = None
			postfix = tilea_extra.group(2)
			return buildReleaseMessage(item, series, vol, chp, postfix=postfix)
		elif other_world_norm:
			series  = other_world_norm.group(1)
			vol     = None
			chp     = other_world_norm.group(2)
			return buildReleaseMessage(item, series, vol, chp)
		elif jashin_norm:
			series  = jashin_norm.group(1)
			vol     = None
			chp     = jashin_norm.group(2)
			return buildReleaseMessage(item, series, vol, chp)
		elif 'otoburi' in item['tags']:
			# Arrrgh, the volume/chapter structure for this series is a disaster!
			pass
		# else:
		# 	# self.log.warning("Cannot decode item:")
		# 	# self.log.warning("%s", item['title'])
		# 	# self.log.warning("Cannot decode item: '%s'", item['title'])
		# 	# print(item['tags'])
		return False


	####################################################################################################################################################
	# Natsu TL
	####################################################################################################################################################


	def extractNatsuTl(self, item):
		meister  = re.search(r'^(Magi Craft Meister) Volume (\d+) Chapter (\d+)$', item['title'])
		if meister:
			series = meister.group(1)
			vol    = meister.group(2)
			chp    = meister.group(3)
			return buildReleaseMessage(item, series, vol, chp)
		return False



	####################################################################################################################################################
	# TheLazy9
	####################################################################################################################################################


	def extractTheLazy9(self, item):
		kansutoppu  = re.search(r'^(Kansutoppu!) Chapter (\d+)$', item['title'])
		garudeina  = re.search(r'^(Garudeina Oukoku Koukoku Ki) Chapter (\d+): Part (\d+)$', item['title'])
		# meister  = re.search(r'^(Magi Craft Meister) Volume (\d+) Chapter (\d+)$', item['title'])

		if kansutoppu:
			series = kansutoppu.group(1)
			vol    = None
			chp    = kansutoppu.group(2)
			return buildReleaseMessage(item, series, vol, chp)
		if garudeina:
			series = garudeina.group(1)
			vol    = None
			chp    = packChapterFragments(garudeina.group(2), garudeina.group(3))

			return buildReleaseMessage(item, series, vol, chp)

		# print(item['title'])
		return False


	####################################################################################################################################################
	####################################################################################################################################################
	##
	##  Dispatcher
	##
	####################################################################################################################################################
	####################################################################################################################################################


	def dispatchRelease(self, item):

		if item['srcname'] == 'Sousetsuka':
			return self.extractSousetsuka(item)
		if item['srcname'] == 'お兄ちゃん、やめてぇ！':
			return self.extractOniichanyamete(item)
		if item['srcname'] == 'Natsu TL':
			return self.extractNatsuTl(item)
		if item['srcname'] == 'TheLazy9':
			return self.extractTheLazy9(item)
		# else:
		# 	print(item)

		return False


	def getProcessedReleaseInfo(self, feedDat):

		if any([item in feedDat['linkUrl'] for item in skip_filter]):
			return

		release = self.dispatchRelease(feedDat)
		if release:
			ret = {
				'type' : 'release-feed',
				'data' : feedDat
			}
			return json.dumps(ret)
		return False


	def getRawFeedMessage(self, feedDat):

		ret = {
			'type' : 'raw-feed',
			'data' : feedDat
		}
		return json.dumps(ret)

	def processFeedData(self, feedDat):

		if any([item in feedDat['linkUrl'] for item in skip_filter]):
			return

		nicename = getNiceName(feedDat['linkUrl'])
		if not nicename:
			nicename = urllib.parse.urlparse(feedDat['linkUrl']).netloc
		feedDat['srcname'] = nicename


		raw = self.getRawFeedMessage(feedDat)
		if raw:
			self.amqpint.put_item(raw)

		new = self.getProcessedReleaseInfo(feedDat)
		if new:
			self.amqpint.put_item(new)

