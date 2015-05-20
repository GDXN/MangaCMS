
#!/usr/bin/python
# from profilehooks import profile
import urllib.parse
import re
import json
import logging
from FeedScrape.feedNameLut import getNiceName
import settings
import FeedScrape.AmqpInterface
# pylint: disable=W0201


skip_filter = [
	"www.baka-tsuki.org",
	"re-monster.wikia.com",
]




def extractChapterVol(inStr):

	# Becuase some series have numbers in their title, we need to preferrentially
	# chose numbers preceeded by known "chapter" strings when we're looking for chapter numbers
	# and only fall back to any numbers (chpRe2) if the search-by-prefix has failed.
	chpRe1 = re.compile(r"(?<!volume)(?<!vol)(?<!v)(?<!of)(?<!season) ?(?:chapter |ch|c)(?: |_|\.)?((?:\d+)|(?:\d+\.)|(?:\.\d+)|(?:\d+\.\d+))", re.IGNORECASE)
	chpRe2 = re.compile(r"(?<!volume)(?<!vol)(?<!v)(?<!of)(?<!season) ?(?: |_)(?: |_|\.)?((?:\d+)|(?:\d+\.)|(?:\.\d+)|(?:\d+\.\d+))", re.IGNORECASE)
	volRe  = re.compile(r"(?: |_|\-)(?:volume|vol|v|season)(?: |_|\.)?((?:\d+)|(?:\d+\.)|(?:\.\d+)|(?:\d+\.\d+))", re.IGNORECASE)

	chap = None
	for chRe in [chpRe1, chpRe2]:
		chapF = chRe.findall(inStr)
		if chapF:
			chap  = float(chapF.pop(0)) if chapF else None
		if chap != None:
			break

	volKey = volRe.findall(inStr)
	vol    = float(volKey.pop(0))  if volKey    else None

	chap   = chap if chap != None else 0.0
	vol    = vol  if vol  != None else 0.0

	if vol == 0:
		vol = None
	return chap, vol


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
		amqp_settings = {}
		amqp_settings["RABBIT_CLIENT_NAME"] = settings.RABBIT_CLIENT_NAME
		amqp_settings["RABBIT_LOGIN"]       = settings.RABBIT_LOGIN
		amqp_settings["RABBIT_PASWD"]       = settings.RABBIT_PASWD
		amqp_settings["RABBIT_SRVER"]       = settings.RABBIT_SRVER
		amqp_settings["RABBIT_VHOST"]       = settings.RABBIT_VHOST
		self.amqpint = FeedScrape.AmqpInterface.RabbitQueueHandler(settings=amqp_settings)

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

		return False

	####################################################################################################################################################
	# Yoraikun
	####################################################################################################################################################


	def extractYoraikun(self, item):

		if 'The Rise of the Shield Hero' in item['tags']:
			chp, vol = extractChapterVol(item['title'])
			if vol == 0:
				vol = None

			return buildReleaseMessage(item, 'The Rise of the Shield Hero', vol, chp)

		elif 'Konjiki no Wordmaster' in item['tags']:
			chp, vol = extractChapterVol(item['title'])
			if vol == 0:
				vol = None

			return buildReleaseMessage(item, 'Konjiki no Wordmaster', vol, chp)

		return False

	####################################################################################################################################################
	# FlowerBridgeToo
	####################################################################################################################################################


	def extractFlowerBridgeToo(self, item):
		# Seriously, you were too lazy to type out the *tags*?
		# You only have to do it ONCE!
		if 'MGA Translation' in item['tags']:
			chp, vol = extractChapterVol(item['title'])
			# Also called "Martial God Asura"
			return buildReleaseMessage(item, 'Xiuluo Wushen', vol, chp)
		elif 'Xian Ni' in item['tags']:
			chp, vol = extractChapterVol(item['title'])
			return buildReleaseMessage(item, 'Xian Ni', vol, chp)

		return False


	####################################################################################################################################################
	# Gravity Translation
	####################################################################################################################################################


	def extractGravityTranslation(self, item):

		chp, vol = extractChapterVol(item['title'])
		if 'Zhan Long' in item['tags']:
			return buildReleaseMessage(item, 'Zhan Long', vol, chp)
		elif 'Battle Through the Heavens' in item['tags']:
			return buildReleaseMessage(item, 'Battle Through the Heavens', vol, chp)
		elif "Ascension of the Alchemist God" in item['title'] or "TAG Chapter" in item['title']:
			return buildReleaseMessage(item, 'Ascension of the Alchemist God', vol, chp)

		return False


	####################################################################################################################################################
	# Pika Translations
	####################################################################################################################################################


	def extractPikaTranslations(self, item):
		chp, vol = extractChapterVol(item['title'])
		if 'Close Combat Mage' in item['tags']:
			return buildReleaseMessage(item, 'Close Combat Mage', vol, chp)

		return False



	####################################################################################################################################################
	# Blue Silver Translations
	####################################################################################################################################################


	def extractBlueSilverTranslations(self, item):

		if 'Douluo Dalu' in item['tags']:

			# All the releases start with the chapter number.
			# This check is only needed because there are a few releases of
			# related things that are annoyingly tagged in as well.
			if not all([val in '0123456789' for val in item['title'].split()[0]]):
				return False

			proc_str = "%s %s" % (item['tags'], item['title'])
			proc_str = proc_str.replace("'", " ")
			chp, vol = extractChapterVol(proc_str)

			return buildReleaseMessage(item, 'Douluo Dalu', vol, chp)
		return False



	####################################################################################################################################################
	# Alyschu & Co
	####################################################################################################################################################


	def extractAlyschuCo(self, item):
		# Whyyyy would you do these bullshit preview things!
		if "PREVIEW" in item['title'] or "preview" in item['title']:
			return False

		chp, vol = extractChapterVol(item['title'])

		if 'Against the Gods' in item['tags'] or 'Ni Tian Xie Shen (Against the Gods)' in item['title']:
			return buildReleaseMessage(item, 'Against the Gods', vol, chp)
		elif 'The Simple Life of Killing Demons' in item['tags']:
			return buildReleaseMessage(item, 'The Simple Life of Killing Demons', vol, chp)
		elif 'Magic, Mechanics, Shuraba' in item['title']:
			return buildReleaseMessage(item, 'Magic, Mechanics, Shuraba', vol, chp)
		elif 'The Flower Offering' in item['tags']:
			return buildReleaseMessage(item, 'The Flower Offering', vol, chp)

		return False



	####################################################################################################################################################
	# Henouji Translation
	####################################################################################################################################################


	def extractHenoujiTranslation(self, item):
		# fffuuuu "last part" is not a helpful title!
		chp, vol = extractChapterVol(item['title'])
		# print(item['title'], item['tags'])

		# if 'Against the Gods' in item['tags'] or 'Ni Tian Xie Shen (Against the Gods)' in item['title']:
		# 	return buildReleaseMessage(item, 'Against the Gods', vol, chp)

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
			# return None
			return self.extractSousetsuka(item)
		if item['srcname'] == 'お兄ちゃん、やめてぇ！':
			# return None
			return self.extractOniichanyamete(item)
		if item['srcname'] == 'Natsu TL':
			# return None
			return self.extractNatsuTl(item)
		if item['srcname'] == 'TheLazy9':
			# return None
			return self.extractTheLazy9(item)
		if item['srcname'] == 'Yoraikun Translation':
			# return None
			return self.extractYoraikun(item)
		if item['srcname'] == 'Flower Bridge Too':
			# return None
			return self.extractFlowerBridgeToo(item)
		if item['srcname'] == 'Gravity Translation':
			# return None
			return self.extractGravityTranslation(item)
		if item['srcname'] == 'Pika Translations':
			# return None
			return self.extractPikaTranslations(item)
		if item['srcname'] == 'Blue Silver Translations':
			# return None
			return self.extractBlueSilverTranslations(item)
		if item['srcname'] == 'Alyschu & Co':
			# return None
			return self.extractAlyschuCo(item)
		if item['srcname'] == 'Henouji Translation':
			return self.extractHenoujiTranslation(item)
			# return None

		# if item['srcname'] == 'Flower Bridge Too':
		# 	return self.extractYoraikun(item)
		# else:
		# print("'%s' '%s' '%s'" % (item['srcname'], item['title'], item['tags']))

		return False


	def getProcessedReleaseInfo(self, feedDat):

		if any([item in feedDat['linkUrl'] for item in skip_filter]):
			return

		release = self.dispatchRelease(feedDat)
		if release:
			ret = {
				'type' : 'parsed-release',
				'data' : release
			}
			return json.dumps(ret)
		return False


	def getRawFeedMessage(self, feedDat):

		ret = {
			'type' : 'raw-feed',
			'data' : feedDat
		}
		return json.dumps(ret)

	def processFeedData(self, feedDat, tx_raw=True, tx_parse=True):

		if any([item in feedDat['linkUrl'] for item in skip_filter]):
			return

		nicename = getNiceName(feedDat['linkUrl'])
		if not nicename:
			nicename = urllib.parse.urlparse(feedDat['linkUrl']).netloc
		feedDat['srcname'] = nicename


		raw = self.getRawFeedMessage(feedDat)
		if raw and tx_raw:
			self.amqpint.put_item(raw)

		new = self.getProcessedReleaseInfo(feedDat)
		if new and tx_parse:
			self.amqpint.put_item(new)


