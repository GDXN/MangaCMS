
from FeedScrape.FeedDataParser import extractChapterVol
from FeedScrape.FeedDataParser import extractVolChapterFragmentPostfix
from tests.title_test_data import data as test_data


VOLUME_KEYS   = ['volume', 'season', 'book', 'vol', 'volume', 'season', 'book', 'vol', 'vol.', 'v']
FRAGMENT_KEYS = ['part', 'episode', 'of', 'pt',  'part', 'p']
CHAPTER_KEYS  = ['chapter', 'episode', 'ch', 'c']


class Token(object):
	def __init__(self, text, position, parent):
		self.text     = text
		self.position = position
		self.parent   = parent

	def isNumeric(self):
		if not self.text:
			return False
		# Handle strings with multiple decimal points, e.g. '01.05.15'
		if self.text.count(".") > 1:
			return False
		return all([char in '0123456789.' for char in self.text])

	def getNumber(self):
		return float(self.text)

	def __repr__(self):
		ret = "<{:14} at: {:2} contents: '{}' number: {}>".format(self.__class__.__name__, self.position, self.text, self.isNumeric())
		return ret

	def string(self):
		return self.text

	def lastData(self):
		all_before = self.parent._preceeding(self.position)
		ret = [item for item in all_before if isinstance(item, DataToken)]
		if not len(ret):
			return NullToken()
		return ret[-1]

	def nextData(self):
		all_before = self.parent._following(self.position)
		ret = [item for item in all_before if isinstance(item, DataToken)]
		if not len(ret):
			return NullToken()
		return ret[0]

class DataToken(Token):
	pass

class DelimiterToken(Token):
	pass

class NullToken(Token):
	def __init__(self):
		pass

	def isNumeric(self):
		return False

	def getNumber(self):
		raise ValueError("NullToken cannot be converted to a number!")

	def __repr__(self):
		ret = "<{:14}>".format(self.__class__.__name__)
		return ret

	def string(self):
		return ''

class TitleParser(object):
	DELIMITERS = [' ', '_', ',', ':', '-']
	def __init__(self, title):
		self.raw = title

		self.chunks = []
		last_split = 0
		indice = 0

		# Consume the string in [data, delimiter] 2-tuples.
		while indice < len(self.raw):
			for delimiter in self.DELIMITERS:
				if self.raw[indice:].startswith(delimiter):
					data = DataToken(
							text     = self.raw[last_split:indice],
							position = len(self.chunks),
							parent   = self)
					self.chunks.append(data)
					tok  = DelimiterToken(
							text     = self.raw[indice:indice+len(delimiter)],
							position = len(self.chunks),
							parent   = self)
					self.chunks.append(tok)
					indice = indice+len(delimiter)
					last_split = indice
					continue
			indice += 1

		# Finally, tack on any trailing data tokens (if they're present)
		if last_split < indice:
			data = DataToken(
				text     = self.raw[last_split:indice],
				position = len(self.chunks),
				parent   = self)
			self.chunks.append(data)


	def _preceeding(self, offset):
		return self.chunks[:offset]
	def _following(self, offset):
		return self.chunks[offset+1:]


	def getNumbers(self):
		return [item for item in self.chunks if item.isNumeric()]

	def getVolume(self):
		for item in self.getNumbers():
			if item.lastData().string().lower() in VOLUME_KEYS:
				return item.getNumber()
		return None
	def getFragment(self):
		for item in self.getNumbers():
			if item.lastData().string().lower() in FRAGMENT_KEYS:
				return item.getNumber()
		return None

	def getChapter(self):
		numbers = self.getNumbers()
		# Try for any explicit chapters first
		for item in numbers:
			if item.lastData().string().lower() in CHAPTER_KEYS:
				return item.getNumber()

		# Then any numbers that are just not associated with known
		# volume/fragment values
		for item in numbers:
			if item.lastData().string().lower() not in VOLUME_KEYS+FRAGMENT_KEYS:
				return item.getNumber()
		return None

	def __repr__(self):
		ret = "<Parsed title: '{}'\n".format(self.raw)
		for item in self.chunks:
			ret += "	{}\n".format(item)
		ret += ">"
		ret = ret.strip()
		return ret

def test():
	count = 0
	mismatch = 0
	for key, value in test_data.items():

		if any(value):
			# print(key, value)
			p = TitleParser(key)
			vol, chp, frag = p.getVolume(), p.getChapter(), p.getFragment()


			if len(value) == 2:
				e_chp, e_vol = value
			elif len(value) == 4:
				e_vol, e_chp, e_frag, e_post = value
			if vol != e_vol or chp != e_chp:
				print(p)
				print("Parsed: {}, {}, {}".format(vol, chp, frag))
				print("Expect:", e_vol, e_chp, e_frag, e_post)
				print()
				mismatch += 1

			# for number in p.getNumbers():
			# 	print(number)
			# 	print("Preceeded by:", number.lastData())
			count += 1

		if len(value) == 2:
			assert value == extractChapterVol(key)
		elif len(value) == 4:
			assert value == extractVolChapterFragmentPostfix(key)
		else:
			print("Wat?")
			print(key, value)
	# print("All matches passed!")
	print("{} Items with parsed output".format(count))
	print("{} Items mismatch in new parser".format(mismatch))

if __name__ == "__main__":

	test()

