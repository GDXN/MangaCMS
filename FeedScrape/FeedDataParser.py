
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
	chpRe1 = re.compile(r"(?<!volume)(?<!vol)(?<!v)(?<!of)(?<!season)(?<!book) ?(?:chapter |chapter\-|\Wch|\Wc)(?: |_|\.)?((?:\d+\.\d+)|(?:\.\d+)|(?:\d+\.)|(?:\d+))", re.IGNORECASE)
	chpRe2 = re.compile(r"(?<!volume)(?<!vol)(?<!v)(?<!of)(?<!season)(?<!book) ?(?: |_)(?: |_|\.)?((?:\d+)|(?:\d+\.)|(?:\.\d+)|(?:\d+\.\d+))", re.IGNORECASE)
	volRe  = re.compile(r"(?: |_|\-|^)(?:book|volume|vol|vol ?\.|vol?\. |v|season)(?: |_|\.)?((?:\d+)|(?:\d+\.)|(?:\.\d+)|(?:\d+\.\d+))", re.IGNORECASE)

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


def extractChapterVolFragment(inStr):
	chp, vol = extractChapterVol(inStr)

	frag = re.compile(r"(?<!book)(?<!volume)(?<!vol)(?<!v)(?<!of)(?<!season)(?<!chapter)(?<!ch)(?<!c) ?(?:part |pt|p)(?: |_|\.)?((?:\d+)|(?:\d+\.)|(?:\.\d+)|(?:\d+\.\d+))", re.IGNORECASE)

	fragKey   = frag.findall(inStr)
	frag_val  = float(fragKey.pop(0))  if fragKey    else None

	return chp, vol, frag_val

def extractVolChapterFragmentPostfix(inStr):
	chp, vol = extractChapterVol(inStr)

	frag = re.compile(r"(?<!book)(?<!volume)(?<!vol)(?<!v)(?<!of)(?<!season)(?<!chapter)(?<!ch)(?<!c) ?(?:episode |part |pt|p)(?: |_|\.)?((?:\d+)|(?:\d+\.)|(?:\.\d+)|(?:\d+\.\d+))", re.IGNORECASE)

	fragKey   = frag.findall(inStr)
	frag_val  = float(fragKey.pop(0))  if fragKey    else None


	postfix = ''
	if 'prologue'  in inStr.lower():
		postfix = 'Prologue'
	if 'afterword' in inStr.lower():
		postfix = 'Afterword'
	if 'epilogue'  in inStr.lower():
		postfix = 'Epilogue'
	if 'interlude' in inStr.lower():
		postfix = 'Interlude'
	if 'foreword' in inStr.lower():
		postfix = 'Foreword'
	if 'appendix' in inStr.lower():
		postfix = 'Appendix'

	return vol, chp, frag_val, postfix


def extractChapterVolEpisode(inStr):
	chp, vol = extractChapterVol(inStr)

	frag = re.compile(r"(?<!book)(?<!volume)(?<!vol)(?<!v)(?<!of)(?<!season)(?<!chapter)(?<!ch)(?<!c) ?(?:episode |pt|p)(?: |_|\.)?((?:\d+)|(?:\d+\.)|(?:\.\d+)|(?:\d+\.\d+))", re.IGNORECASE)

	fragKey   = frag.findall(inStr)
	frag_val  = float(fragKey.pop(0))  if fragKey    else None

	return chp, vol, frag_val


def buildReleaseMessage(raw_item, series, vol, chap=None, frag=None, postfix=''):
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
		'chp'       : packChapterFragments(chap, frag),
		'published' : raw_item['published'],
		'itemurl'   : raw_item['linkUrl'],
		'postfix'   : postfix,
	}

def packChapterFragments(chapStr, fragStr):
	if not chapStr and not fragStr:
		return None
	if not fragStr:
		return chapStr
	chap = float(chapStr)
	frag = float(fragStr)
	return '%0.2f' % (chap + (frag / 100.0))


class DataParser():

	amqpint = None

	def __init__(self):
		super().__init__()

		logPath = 'Main.Feeds.Parser'
		self.log = logging.getLogger(logPath)
		amqp_settings = {}
		amqp_settings["RABBIT_CLIENT_NAME"] = settings.RABBIT_CLIENT_NAME
		amqp_settings["RABBIT_LOGIN"]       = settings.RABBIT_LOGIN
		amqp_settings["RABBIT_PASWD"]       = settings.RABBIT_PASWD
		amqp_settings["RABBIT_SRVER"]       = settings.RABBIT_SRVER
		amqp_settings["RABBIT_VHOST"]       = settings.RABBIT_VHOST
		self.amqpint = FeedScrape.AmqpInterface.RabbitQueueHandler(settings=amqp_settings)

		self.names = set()

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
			return buildReleaseMessage(item, series, vol, postfix=postfix)

		# else:
		# 	self.log.warning("Cannot decode item:")
		# 	self.log.warning("%s", item)
		return False

	####################################################################################################################################################
	# お兄ちゃん、やめてぇ！ / Onii-chan Yamete
	####################################################################################################################################################
	def extractOniichanyamete(self, item):
		other_world_norm = re.search(r'^(I’m Back in the Other World\?) – Chapter (\d+)$', item['title'])
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if       'Jashin Average'   in item['title'] \
				or 'Cthulhu Average'  in item['title'] \
				or 'Evil God Average' in item['tags']  \
				or 'jashin'           in item['tags']:

			if "Side Story" in item['title']:
				return False
			return buildReleaseMessage(item, 'Evil God Average', vol, chp, frag=frag)

		if 'Tilea’s Worries' in item['title']:

			return buildReleaseMessage(item, 'Tilea’s Worries', vol, chp, postfix=postfix)


		if 'I’m Back in the Other World' in item['title']:
			return buildReleaseMessage(item, 'I’m Back in the Other World', vol, chp)

		if 'Kazuha Axeplant’s Third Adventure:' in item['title']:
			return buildReleaseMessage(item, 'Kazuha Axeplant’s Third Adventure', vol, chp)

		elif 'otoburi' in item['tags']:
			# Arrrgh, the volume/chapter structure for this series is a disaster!
			return False
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
		chp, vol, frag = extractChapterVolFragment(item['title'])
		if kansutoppu:
			series = kansutoppu.group(1)
			vol    = None
			chp    = kansutoppu.group(2)
			return buildReleaseMessage(item, series, vol, chp)
		if garudeina:
			series = garudeina.group(1)
			vol    = None
			chp    = garudeina.group(2)
			frag   = garudeina.group(3)

			return buildReleaseMessage(item, series, vol, chp, frag=frag)

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
		elif 'Xian Ni' in item['tags'] or 'Xian Ni Translation' in item['tags']:
			chp, vol = extractChapterVol(item['title'])
			return buildReleaseMessage(item, 'Xian Ni', vol, chp)
		elif 'JMG Translation' in item['tags']:  # Series was dropped, have lots of old releases
			chp, vol = extractChapterVol(item['title'])
			return buildReleaseMessage(item, 'Shaonian Yixian', vol, chp)
		return False

	####################################################################################################################################################
	# Gravity Translation
	####################################################################################################################################################
	def extractGravityTranslation(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'Zhan Long' in item['tags']:
			return buildReleaseMessage(item, 'Zhan Long', vol, chp)
		elif 'Battle Through the Heavens' in item['tags']:
			return buildReleaseMessage(item, 'Battle Through the Heavens', vol, chp)
		elif "Ascension of The Alchemist God" in item['title'] \
			or "TAG Chapter" in item['title']                  \
			or 'The Alchemist God: Chapter' in item['title']:
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
	# Shin Translations
	####################################################################################################################################################
	def extractShinTranslations(self, item):
		chp, vol, frag = extractChapterVolFragment(item['title'])
		if 'THE NEW GATE' in item['tags'] and not 'Status Update' in item['tags']:
			if chp and vol and frag:
				return buildReleaseMessage(item, 'The New Gate', vol, chp, frag=frag)
		return False

	####################################################################################################################################################
	# Scrya Translations
	####################################################################################################################################################
	def extractScryaTranslations(self, item):
		chp, vol, frag = extractChapterVolFragment(item['title'])
		if "So What if It's an RPG World!?" in item['tags']:
			return buildReleaseMessage(item, "So What if It's an RPG World!?", vol, chp, frag=frag)

		return False

	####################################################################################################################################################
	# Japtem
	####################################################################################################################################################
	def extractJaptem(self, item):
		chp, vol, frag = extractChapterVolFragment(item['title'])
		if '[Chinese] Shadow Rogue' in item['tags']:
			return buildReleaseMessage(item, "Shadow Rogue", vol, chp, frag=frag)
		if '[Chinese] Unique Legend' in item['tags']:
			return buildReleaseMessage(item, "Unique Legend", vol, chp, frag=frag)
		if '[Japanese] Magi\'s Grandson' in item['tags']:
			return buildReleaseMessage(item, "Magi's Grandson", vol, chp, frag=frag)
		if '[Japanese / Hosted] Arifureta' in item['tags']:
			return buildReleaseMessage(item, "Arifureta", vol, chp, frag=frag)
		return False

	####################################################################################################################################################
	# Wuxiaworld
	####################################################################################################################################################


	def extractWuxiaworld(self, item):
		chp, vol, frag = extractChapterVolFragment(item['title'])

		if 'CD Chapter Release' in item['tags']:
			return buildReleaseMessage(item, "Coiling Dragon", vol, chp, frag=frag)
		if 'dragon king with seven stars' in item['tags']:
			return buildReleaseMessage(item, "Dragon King with Seven Stars", vol, chp, frag=frag)
		if 'ISSTH Chapter Release' in item['tags']:
			return buildReleaseMessage(item, "I Shall Seal the Heavens", vol, chp, frag=frag)
		if 'BTTH Chapter Release' in item['tags']:
			return buildReleaseMessage(item, "Battle Through the Heavens", vol, chp, frag=frag)
		if 'SL Chapter Release' in item['tags']:
			return buildReleaseMessage(item, "Skyfire Avenue", vol, chp, frag=frag)
		if 'MGA Chapter Release' in item['tags']:
			return buildReleaseMessage(item, "Martial God Asura", vol, chp, frag=frag)

		return False


	####################################################################################################################################################
	# Ziru's Musings | Translations~
	####################################################################################################################################################
	def extractZiruTranslations(self, item):
		if 'Dragon Bloodline' in item['tags'] or 'Dragon’s Bloodline — Chapter ' in item['title']:
			chp, vol, frag = extractChapterVolFragment(item['title'])
			return buildReleaseMessage(item, 'Dragon Bloodline', vol, chp, frag=frag)

		# Wow, the tags must be hand typed. soooo many typos
		if 'Suterareta Yuusha no Eiyuutan' in item['tags'] or \
			'Suterareta Yuusha no Eyuutan' in item['tags'] or \
			'Suterurareta Yuusha no Eiyuutan' in item['tags']:

			extract = re.search(r'Suterareta Yuusha no Ei?yuutan \((\d+)\-(.+?)\)', item['title'])
			if extract:
				vol = int(extract.group(1))
				try:
					chp = int(extract.group(2))
					postfix = ''
				except ValueError:
					chp = None
					postfix = extract.group(2)
				return buildReleaseMessage(item, 'Suterareta Yuusha no Eiyuutan', vol, chp, postfix=postfix)
		return False


	####################################################################################################################################################
	# Void Translations
	####################################################################################################################################################
	def extractVoidTranslations(self, item):
		chp, vol, frag = extractChapterVolFragment(item['title'])
		match = re.search(r'^Xian Ni Chapter \d+ ?[\-–]? ?(.*)$', item['title'])
		if match:
			return buildReleaseMessage(item, 'Xian Ni', vol, chp, postfix=match.group(1))



		return False


	####################################################################################################################################################
	# Calico x Tabby
	####################################################################################################################################################
	def extractCalicoxTabby(self, item):
		chp, vol, frag = extractChapterVolFragment(item['title'])
		if 'Meow Meow Meow' in item['tags']:
			return buildReleaseMessage(item, 'Meow Meow Meow', vol, chp, frag=frag)

		return False


	####################################################################################################################################################
	# Skythewood translations
	####################################################################################################################################################


	def extractSkythewood(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'Altina the Sword Princess' in item['tags']:
			return buildReleaseMessage(item, 'Haken no Kouki Altina', vol, chp, frag=frag)
		if 'Overlord' in item['tags']:
			# Lots of idiot-checking here, because there are a
			# bunch of annoying edge-cases I want to work around.
			# This will PROBABLY BREAK IN THE FUTURE!
			if "Drama CD" in item['title']:
				return False
			if "Track" in item['title']:
				return False
			if not "Volume" in item['title']:
				return False

			return buildReleaseMessage(item, 'Overlord', vol, chp, frag=frag, postfix=postfix)
		if 'Gifting the wonderful world' in item['tags']:
			return buildReleaseMessage(item, 'Gifting the Wonderful World with Blessings!', vol, chp, frag=frag)
		if "Knight's & Magic" in item['tags']:
			return buildReleaseMessage(item, 'Knight\'s & Magic', vol, chp, frag=frag)

		return False

	####################################################################################################################################################
	# Lygar Translations
	####################################################################################################################################################
	def extractLygarTranslations(self, item):
		chp, vol, frag = extractChapterVolFragment(item['title'])

		if 'elf tensei' in item['tags'] and not 'news' in item['tags']:
			return buildReleaseMessage(item, 'Elf Tensei Kara no Cheat Kenkoku-ki', vol, chp, frag=frag)

		return False

	####################################################################################################################################################
	# That Guy Over There
	####################################################################################################################################################
	def extractThatGuyOverThere(self, item):
		chp, vol, frag = extractChapterVolFragment(item['title'])

		if 'wushenkongjian' in item['tags']:
			return buildReleaseMessage(item, 'Wu Shen Kong Jian', vol, chp, frag=frag)

		match = re.search(r'^Le Festin de Vampire – Chapter (\d+)\-(\d+)', item['title'])
		if match:
			chp  = match.group(1)
			frag = match.group(2)
			return buildReleaseMessage(item, 'Le Festin de Vampire', vol, chp, frag=frag)
		return False

	####################################################################################################################################################
	# Otterspace Translation
	####################################################################################################################################################
	def extractOtterspaceTranslation(self, item):
		chp, vol, frag = extractChapterVolFragment(item['title'])
		if 'Elqueeness’' in item['title']:
			return buildReleaseMessage(item, 'Spirit King Elqueeness', vol, chp, frag=frag)
		if '[Dark Mage]' in item['title']:
			return buildReleaseMessage(item, 'Dark Mage', vol, chp, frag=frag)

		return False

	####################################################################################################################################################
	# MadoSpicy TL
	####################################################################################################################################################
	def extractMadoSpicy(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'Kyuuketsu Hime' in item['title']:
			# Hardcode ALL THE THINGS
			postfix = ''
			if "interlude" in postfix.lower():
				postfix = "Interlude {num}".format(num=chp)
				chp = None
			if "prologue" in postfix.lower():
				postfix = "Prologue {num}".format(num=chp)
				chp = None
			return buildReleaseMessage(item, 'Kyuuketsu Hime wa Barairo no Yume o Miru', vol, chp, frag=frag, postfix=postfix)
		return False

	####################################################################################################################################################
	# Tripp Translations
	####################################################################################################################################################
	def extractTrippTl(self, item):
		chp, vol, frag = extractChapterVolEpisode(item['title'])

		if 'Majin Tenseiki' in item['title']:
			return buildReleaseMessage(item, 'Majin Tenseiki', vol, chp, frag=frag)

		return False

	####################################################################################################################################################
	# DarkFish Translations
	####################################################################################################################################################
	def extractDarkFish(self, item):
		chp, vol, frag = extractChapterVolEpisode(item['title'])
		if 'She Professed Herself The Pupil Of The Wise Man'.lower() in item['title'].lower():
			return buildReleaseMessage(item, 'Kenja no Deshi wo Nanoru Kenja', vol, chp, frag=frag)
		# if 'Majin Tenseiki' in item['title']:
		return False

	####################################################################################################################################################
	# Manga0205 Translations
	####################################################################################################################################################
	def extractManga0205Translations(self, item):
		chp, vol, frag = extractChapterVolEpisode(item['title'])
		if 'Sendai Yuusha wa Inkyou Shitai'.lower() in item['title'].lower():
			postfix = ''
			if 'Side Story'.lower() in item['title'].lower():
				postfix = "Side Story {num}".format(num=chp)
				chp = None
			return buildReleaseMessage(item, 'Sendai Yuusha wa Inkyou Shitai', vol, chp, frag=frag, postfix=postfix)

		return False


	####################################################################################################################################################
	# extractAzureSky
	####################################################################################################################################################
	def extractAzureSky(self, item):
		chp, vol, frag = extractChapterVolEpisode(item['title'])
		if 'Shinde Hajimaru'.lower() in item['title'].lower():
			postfix = ''
			if "prologue" in item['title'].lower():
				postfix = 'Prologue'
			return buildReleaseMessage(item, 'Shinde Hajimaru Isekai Tensei', vol, chp, frag=frag, postfix=postfix)
		return False

	####################################################################################################################################################
	# extractRaisingTheDead
	####################################################################################################################################################
	def extractRaisingTheDead(self, item):
		chp, vol, frag = extractChapterVolEpisode(item['title'])


		if 'Isekai meikyuu de dorei harem wo' in item['tags'] \
			or 'Slave harem in the labyrinth of the other world' in item['tags']:
			return buildReleaseMessage(item, 'Isekai Meikyuu De Dorei Harem wo', vol, chp, frag=frag)

		if 'Shinka no Mi' in item['tags']:
			return buildReleaseMessage(item, 'Shinka no Mi', vol, chp, frag=frag)

		return False


	####################################################################################################################################################
	# Tensai Translations
	####################################################################################################################################################
	def extractTensaiTranslations(self, item):
		chp, vol, frag = extractChapterVolEpisode(item['title'])
		if 'Spirit Migration' in item['tags']:
			return buildReleaseMessage(item, 'Spirit Migration', vol, chp, frag=frag)

		if 'Tsuyokute New Saga' in item['tags']:
			return buildReleaseMessage(item, 'Tsuyokute New Saga', vol, chp, frag=frag)

		return False

	####################################################################################################################################################
	# Groups involved in KnW:
	# 	Blazing Translations
	# 	CapsUsingShift Tl
	# 	Insignia Pierce
	# 	Kiriko Translations
	# 	Konjiki no Wordmaster
	# 	Loliquent
	# 	Blazing Translations
	# 	Pummels Translations
	# 	XCrossJ
	# 	Probably another dozen randos per week.
	# Really. Fuck you people. Tag your shit, and start a group blog.
	####################################################################################################################################################
	def extractKnW(self, item):
		chp, vol, frag = extractChapterVolEpisode(item['title'])

		tags = item['tags']
		title = item['title']
		src = item['srcname']

		postfix = ''
		ret = None
		if ('Chapters' in tags and 'Konjiki no Wordmaster' in tags) \
			or 'Konjiki no Wordmaster Web Novel Chapters' in tags   \
			or 'Konjiki' in tags                                    \
			or (src == 'Loliquent' and 'Konjiki no Wordmaster' in title):
			postfix = title.split("–", 1)[-1].strip()
			ret = buildReleaseMessage(item, 'Konjiki no Wordmaster', vol, chp, frag=frag, postfix=postfix)

		elif 'Konjiki no Wordmaster Chapters' in tags                                        \
			or 'Konjiki no Moji Tsukai' in tags                                              \
			or (src == 'Kiriko Translations' and ('KnW' in tags or 'KnW Chapter' in title))  \
			or (src == 'CapsUsingShift Tl' and 'Konjiki no Wordmaster' in title)             \
			or (src == 'Pummels Translations' and 'Konjiki no Word Master Chapter' in title) \
			or (src == 'XCrossJ' and 'Konjiki no Moji Tsukai' in title)                      \
			or (src == 'Insignia Pierce' and 'Konjiki no Word Master Chapter' in title):
			postfix = title.split(":", 1)[-1].strip()
			ret = buildReleaseMessage(item, 'Konjiki no Wordmaster', vol, chp, frag=frag, postfix=postfix)
			# elif 'Konjiki no Moji Tsukai' in tags:

		else:
			pass

		# Only return a value if we've actually found a chapter/vol
		if ret and (ret['vol'] or ret['chp']):
			return ret

		return False


	####################################################################################################################################################
	# Thunder Translations:
	####################################################################################################################################################
	def extractThunder(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'Stellar Transformations' in item['tags'] and (vol or chp):
			return buildReleaseMessage(item, 'Stellar Transformations', vol, chp, frag=frag, postfix=postfix)
		return False


	####################################################################################################################################################
	# Kiri Leaves:
	####################################################################################################################################################
	def extractKiri(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'Tensei Oujo' in item['tags'] and (vol or chp):
			return buildReleaseMessage(item, 'Tensei Oujo wa Kyou mo Hata o Tatakioru', vol, chp, frag=frag, postfix=postfix)

		return False


	####################################################################################################################################################
	# 中翻英圖書館 Translations
	####################################################################################################################################################
	def extractTuShuGuan(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'He Jing Kunlun' in item['tags'] and (vol or chp or postfix):
			return buildReleaseMessage(item, 'The Crane Startles Kunlun', vol, chp, frag=frag, postfix=postfix)

		return False

	####################################################################################################################################################
	# Lingson's Translations
	####################################################################################################################################################
	def extractLingson(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'The Legendary Thief' in item['tags'] and (vol or chp or postfix):
			return buildReleaseMessage(item, 'Virtual World - The Legendary Thief', vol, chp, frag=frag, postfix=postfix)

		return False


	####################################################################################################################################################
	# Sword And Game
	####################################################################################################################################################
	def extractSwordAndGame(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'The Rising of the Shield Hero' in item['tags'] and 'chapter' in item['tags']:
			return buildReleaseMessage(item, 'The Rise of the Shield Hero', vol, chp, frag=frag, postfix=postfix)
		if 'Ark' in item['tags'] and (vol or chp or postfix):
			return buildReleaseMessage(item, 'Ark', vol, chp, frag=frag, postfix=postfix)

		return False


	####################################################################################################################################################
	# Clicky Click Translation
	####################################################################################################################################################
	def extractClicky(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'Legendary Moonlight Sculptor' in item['tags'] and any(['Volume' in tag for tag in item['tags']]):
			return buildReleaseMessage(item, 'Legendary Moonlight Sculptor', vol, chp, frag=frag, postfix=postfix)

		return False


	####################################################################################################################################################
	# Defiring
	####################################################################################################################################################
	def extractDefiring(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'World teacher' in item['title']:
			return buildReleaseMessage(item, 'World teacher', vol, chp, frag=frag, postfix=postfix)
		if 'Shinka no Mi' in item['title']:
			return buildReleaseMessage(item, 'Shinka no Mi', vol, chp, frag=frag, postfix=postfix)

		return False


	####################################################################################################################################################
	# Fanatical Translations
	####################################################################################################################################################
	def extractFanatical(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'One Life One Incarnation Beautiful Bones' in item['tags']:
			return buildReleaseMessage(item, 'One Life, One Incarnation - Beautiful Bones', vol, chp, frag=frag, postfix=postfix)
		if 'Best to Have Met You' in item['tags']:
			return buildReleaseMessage(item, 'Zuimei Yujian Ni', vol, chp, frag=frag, postfix=postfix)
		if 'Blazing Sunlight' in item['tags']:
			return buildReleaseMessage(item, 'Blazing Sunlight', vol, chp, frag=frag, postfix=postfix)
		if 'Wipe Clean After Eating' in item['tags']:
			return buildReleaseMessage(item, 'Chigan Mojing', vol, chp, frag=frag, postfix=postfix)

		return False

	####################################################################################################################################################
	# Giraffe Corps
	####################################################################################################################################################
	def extractGiraffe(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'Ti Shen' in item['tags']:
			return buildReleaseMessage(item, 'Tishen', vol, chp, frag=frag, postfix=postfix)
		if 'True Star' in item['tags']:
			return buildReleaseMessage(item, 'Juxing', vol, chp, frag=frag, postfix=postfix)
		if 'Gong Hua' in item['tags']:
			return buildReleaseMessage(item, 'Gong Hua', vol, chp, frag=frag, postfix=postfix)
		if 'Chen Yue Zhi Yao' in item['tags']:
			return buildReleaseMessage(item, 'Chen Yue Zhi Yao', vol, chp, frag=frag, postfix=postfix)

		return False

	####################################################################################################################################################
	# guhehe.TRANSLATIONS
	####################################################################################################################################################
	def extractGuhehe(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'ShominSample' in item['tags']:
			return buildReleaseMessage(item, 'Ore ga Ojou-sama Gakkou ni "Shomin Sample" Toshite Rachirareta Ken', vol, chp, frag=frag, postfix=postfix)
		if 'OniAi' in item['tags']:
			return buildReleaseMessage(item, 'Onii-chan Dakedo Ai Sae Areba Kankeinai yo ne', vol, chp, frag=frag, postfix=postfix)
		if 'Haganai' in item['tags']:
			return buildReleaseMessage(item, 'Boku wa Tomodachi ga Sukunai', vol, chp, frag=frag, postfix=postfix)

		return False

	####################################################################################################################################################
	# Hajiko translation
	####################################################################################################################################################
	def extractHajiko(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'Ryuugoroshi no Sugosuhibi' in item['title']:
			return buildReleaseMessage(item, 'Ryugoroshi no Sugosuhibi', vol, chp, frag=frag, postfix=postfix)

		return False

	####################################################################################################################################################
	# Imoutolicious
	####################################################################################################################################################
	def extractImoutolicious(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'sekaimo' in item['tags']:
			return buildReleaseMessage(item, 'Sekai Ichi no Imouto-sama', vol, chp, frag=frag, postfix=postfix)
		if 'dawnbringer' in item['tags']:
			return buildReleaseMessage(item, 'Dawnbringer: The Story of the Machine God', vol, chp, frag=frag, postfix=postfix)
		if 'clotaku club' in item['tags']:
			return buildReleaseMessage(item, 'Sumdeokbu!', vol, chp, frag=frag, postfix=postfix)
		if 'four lovers' in item['tags']:
			return buildReleaseMessage(item, 'Shurabara!', vol, chp, frag=frag, postfix=postfix)

		return False

	####################################################################################################################################################
	# Isekai Mahou Translations!
	####################################################################################################################################################
	def extractIsekaiMahou(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
		if 'Isekai Mahou Chapter' in item['title'] and 'Release' in item['title']:
			return buildReleaseMessage(item, 'Isekai Mahou wa Okureteru!', vol, chp, frag=frag, postfix=postfix)

		return False

	####################################################################################################################################################
	# Kerambit's Incisions
	####################################################################################################################################################
	def extractKerambit(self, item):
		vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])

		if 'Yobidasa' in item['tags'] and (vol or chp):
			if not postfix and ":" in item['title']:
				postfix = item['title'].split(":")[-1]

			return buildReleaseMessage(item, 'Yobidasareta Satsuriku-sha', vol, chp, frag=frag, postfix=postfix)
		return False

		# else:
		print(item['title'])
		print(item['tags'])
		print("'{}', '{}', '{}', '{}'".format(vol, chp, frag, postfix))


	####################################################################################################################################################
	# Mahoutsuki Translation
	####################################################################################################################################################
	def extractMahoutsuki(self, item):
		pass

	####################################################################################################################################################
	# Maou the Yuusha
	####################################################################################################################################################
	def extractMaouTheYuusha(self, item):
		pass

	####################################################################################################################################################
	# Nightbreeze Translations
	####################################################################################################################################################
	def extractNightbreeze(self, item):
		pass

	####################################################################################################################################################
	# Ohanashimi
	####################################################################################################################################################
	def extractOhanashimi(self, item):
		pass

	####################################################################################################################################################
	# Omega Harem Translations
	####################################################################################################################################################
	def extractOmegaHarem(self, item):
		pass

	####################################################################################################################################################
	# pandafuqtranslations
	####################################################################################################################################################
	def extractPandaFuq(self, item):
		pass

	####################################################################################################################################################
	# Prince Revolution!
	####################################################################################################################################################
	def extractPrinceRevolution(self, item):
		pass

	####################################################################################################################################################
	# putttytranslations
	####################################################################################################################################################
	def extractPuttty(self, item):
		pass

	####################################################################################################################################################
	# Rising Dragons Translation
	####################################################################################################################################################
	def extractRisingDragons(self, item):
		pass

	####################################################################################################################################################
	# Sword and Game
	####################################################################################################################################################
	def extractSwordandGame(self, item):
		pass

	####################################################################################################################################################
	# Sylver Translations
	####################################################################################################################################################
	def extractSylver(self, item):
		pass

	####################################################################################################################################################
	# Tomorolls
	####################################################################################################################################################
	def extractTomorolls(self, item):
		pass

	####################################################################################################################################################
	# Totokk\'s Translations
	####################################################################################################################################################
	def extractTotokk(self, item):
		pass

	####################################################################################################################################################
	# Translation Nations
	####################################################################################################################################################
	def extractTranslationNations(self, item):
		pass

	####################################################################################################################################################
	# Untuned Translation Blog
	####################################################################################################################################################
	def extractUntunedTranslation(self, item):
		pass

	####################################################################################################################################################
	# Gila Translation Monster
	####################################################################################################################################################
	def extractGilaTranslation(self, item):
		pass




	####################################################################################################################################################
	####################################################################################################################################################
	##
	##  Dispatcher
	##
	####################################################################################################################################################
	####################################################################################################################################################


	def dispatchRelease(self, item):

		ret = False

		if item['srcname'] == 'お兄ちゃん、やめてぇ！':  # I got utf-8 in my code-sauce, bizzickle
			ret = self.extractOniichanyamete(item)
		elif item['srcname'] == 'Sousetsuka':
			ret = self.extractSousetsuka(item)
		elif item['srcname'] == 'Natsu TL':
			ret = self.extractNatsuTl(item)
		elif item['srcname'] == 'TheLazy9':
			ret = self.extractTheLazy9(item)
		elif item['srcname'] == 'Yoraikun Translation':
			ret = self.extractYoraikun(item)
		elif item['srcname'] == 'Flower Bridge Too':
			ret = self.extractFlowerBridgeToo(item)
		elif item['srcname'] == 'Pika Translations':
			ret = self.extractPikaTranslations(item)
		elif item['srcname'] == 'Blue Silver Translations':
			ret = self.extractBlueSilverTranslations(item)
		elif item['srcname'] == 'Alyschu & Co':
			ret = self.extractAlyschuCo(item)
		elif item['srcname'] == 'Henouji Translation':
			ret = self.extractHenoujiTranslation(item)
		elif item['srcname'] == 'Shin Translations':
			ret = self.extractShinTranslations(item)
		elif item['srcname'] == 'Scrya Translations':
			ret = self.extractScryaTranslations(item)
		elif item['srcname'] == 'Japtem':
			ret = self.extractJaptem(item)
		elif item['srcname'] == 'Wuxiaworld':
			ret = self.extractWuxiaworld(item)
		elif item['srcname'] == 'Ziru\'s Musings | Translations~':
			ret = self.extractZiruTranslations(item)
		elif item['srcname'] == 'Void Translations':
			ret = self.extractVoidTranslations(item)
		elif item['srcname'] == 'Calico x Tabby':
			ret = self.extractCalicoxTabby(item)
		elif item['srcname'] == 'Skythewood translations':
			ret = self.extractSkythewood(item)
		elif item['srcname'] == 'LygarTranslations':
			ret = self.extractLygarTranslations(item)
		elif item['srcname'] == 'ThatGuyOverThere':
			ret = self.extractThatGuyOverThere(item)
		elif item['srcname'] == 'otterspacetranslation':
			ret = self.extractOtterspaceTranslation(item)
		elif item['srcname'] == 'MadoSpicy TL':
			ret = self.extractMadoSpicy(item)
		elif item['srcname'] == 'Tripp Translations':
			ret = self.extractTrippTl(item)
		elif item['srcname'] == 'A fish once said this to me':
			ret = self.extractDarkFish(item)
		elif item['srcname'] == 'Manga0205 Translations':
			ret = self.extractManga0205Translations(item)
		elif item['srcname'] == 'Azure Sky Translation':
			ret = self.extractAzureSky(item)
		elif item['srcname'] == 'Raising the Dead':
			ret = self.extractRaisingTheDead(item)
		elif item['srcname'] == 'Tensai Translations':
			ret = self.extractTensaiTranslations(item)

		# The number of people working on Konjiki no Wordmaster
		# is TOO FUCKING HIGH
		elif item['srcname'] == 'Blazing Translations' \
			or item['srcname'] == 'CapsUsingShift Tl' \
			or item['srcname'] == 'Insignia Pierce' \
			or item['srcname'] == 'Kiriko Translations' \
			or item['srcname'] == 'Konjiki no Wordmaster' \
			or item['srcname'] == 'Loliquent' \
			or item['srcname'] == 'Blazing Translations' \
			or item['srcname'] == 'Pummels Translations' \
			or item['srcname'] == 'XCrossJ':
			ret = self.extractKnW(item)

		elif item['srcname'] == 'Thunder Translation':
			ret = self.extractThunder(item)
		elif item['srcname'] == 'Kiri Leaves':
			ret = self.extractKiri(item)
		elif item['srcname'] == 'Gravity Translation' \
			or item['srcname'] == 'Gravity Tales':
			ret = self.extractGravityTranslation(item)
		elif item['srcname'] == '中翻英圖書館 Translations':
			ret = self.extractTuShuGuan(item)
		elif item['srcname'] == 'Lingson\'s Translations':
			ret = self.extractLingson(item)


		elif item['srcname'] == 'Sword and Game':
			ret = self.extractSwordAndGame(item)
		elif item['srcname'] == 'Clicky Click Translation':
			ret = self.extractClicky(item)
		elif item['srcname'] == 'Defiring':
			ret = self.extractDefiring(item)
		elif item['srcname'] == 'Fanatical':
			ret = self.extractFanatical(item)
		elif item['srcname'] == 'Giraffe Corps':
			ret = self.extractGiraffe(item)
		elif item['srcname'] == 'guhehe.TRANSLATIONS':
			ret = self.extractGuhehe(item)
		elif item['srcname'] == 'Hajiko translation':
			ret = self.extractHajiko(item)
		elif item['srcname'] == 'Imoutolicious Light Novel Translations':
			ret = self.extractImoutolicious(item)
		elif item['srcname'] == 'Isekai Mahou Translations!':
			ret = self.extractIsekaiMahou(item)
		elif item['srcname'] == 'izra709 | B Group no Shounen Translations':
			ret = self.extractIzra709(item)

		elif item['srcname'] == 'Kerambit\'s Incisions':
			ret = self.extractKerambit(item)

		# Todo:
		# ret = False
		if False:
			pass
		elif item['srcname'] == 'Mahoutsuki Translation':
			ret = self.extractMahoutsuki(item)
		elif item['srcname'] == 'Maou the Yuusha':
			ret = self.extractMaouTheYuusha(item)
		elif item['srcname'] == 'Nightbreeze Translations':
			ret = self.extractNightbreeze(item)
		elif item['srcname'] == 'Ohanashimi':
			ret = self.extractOhanashimi(item)
		elif item['srcname'] == 'Omega Harem Translations':
			ret = self.extractOmegaHarem(item)
		elif item['srcname'] == 'pandafuqtranslations':
			ret = self.extractPandaFuq(item)
		elif item['srcname'] == 'Prince Revolution!':
			ret = self.extractPrinceRevolution(item)
		elif item['srcname'] == 'putttytranslations':
			ret = self.extractPuttty(item)
		elif item['srcname'] == 'Rising Dragons Translation':
			ret = self.extractRisingDragons(item)
		elif item['srcname'] == 'Sylver Translations':
			ret = self.extractSylver(item)
		elif item['srcname'] == 'Tomorolls':
			ret = self.extractTomorolls(item)
		elif item['srcname'] == 'Totokk\'s Translations':
			ret = self.extractTotokk(item)
		elif item['srcname'] == 'Translation Nations':
			ret = self.extractTranslationNations(item)
		elif item['srcname'] == 'Untuned Translation Blog':
			ret = self.extractUntunedTranslation(item)
		elif item['srcname'] == 'Gila Translation Monster':
			ret = self.extractGilaTranslation(item)



		# else:
		# 	print("'%s', '%s', '%s'" % (item['srcname'], item['title'], item['tags']))

		# OEL Junk
		# 'JawzTranslations'

		# no tags OR title information
		# 'Bad Translation'

		# No parseable content here
		# 'Krytyk\'s Translations'

		# Releases are shit, and it's largely unparseable anyways
		# 'ELYSION Translation'


		ret = False

		# Only return a value if we've actually found a chapter/vol
		if ret and not (ret['vol'] or ret['chp'] or ret['postfix']):
			ret = False

		# Do not trigger if there is "preview" in the title.
		if 'preview' in item['title'].lower():
			ret = False

		return ret

		# DELETE FROM releases WHERE series=2346;
		# DELETE FROM releaseschanges WHERE series=2346;
		# DELETE FROM alternatenames WHERE series=2346;
		# DELETE FROM alternatenameschanges WHERE series=2346;
		# DELETE FROM serieschanges WHERE id=2346;
		# DELETE FROM series WHERE id=2346;

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

		feedDat = feedDat.copy()

		# remove the contents item, since it can be
		# quite large, and is not used.
		feedDat.pop('contents')
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

		# if not nicename in self.names:
		# 	self.names.add(nicename)
		# 	# print(nicename)

		feedDat['srcname'] = nicename


		raw = self.getRawFeedMessage(feedDat)
		if raw and tx_raw:
			self.amqpint.put_item(raw)

		new = self.getProcessedReleaseInfo(feedDat)
		if new and tx_parse:
			self.amqpint.put_item(new)



	####################################################################################################################################################
	# Todo:
	####################################################################################################################################################

	def extractWAT(self, item):
		return False

	def extractAssholeTranslations(self, item):
		return False

	####################################################################################################################################################
	#
	#  ##     ## ##    ## ########     ###    ########   ######  ########    ###    ########  ##       ########
	#  ##     ## ###   ## ##     ##   ## ##   ##     ## ##    ## ##         ## ##   ##     ## ##       ##
	#  ##     ## ####  ## ##     ##  ##   ##  ##     ## ##       ##        ##   ##  ##     ## ##       ##
	#  ##     ## ## ## ## ########  ##     ## ########   ######  ######   ##     ## ########  ##       ######
	#  ##     ## ##  #### ##        ######### ##   ##         ## ##       ######### ##     ## ##       ##
	#  ##     ## ##   ### ##        ##     ## ##    ##  ##    ## ##       ##     ## ##     ## ##       ##
	#   #######  ##    ## ##        ##     ## ##     ##  ######  ######## ##     ## ########  ######## ########
	#
	####################################################################################################################################################

	####################################################################################################################################################
	# Henouji Translation
	####################################################################################################################################################


	def extractHenoujiTranslation(self, item):
		# fffuuuu "last part" is not a helpful title!
		chp, vol = extractChapterVol(item['title'])
		# print(item['title'], item['tags'])


		return False

	####################################################################################################################################################
	# izra709 | B Group no Shounen Translations
	####################################################################################################################################################

	def extractIzra709(self, item):
		# No tags, no parseable stuff in the title. Fuuuuuuuuuu
		return False

