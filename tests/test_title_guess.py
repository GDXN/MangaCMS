
from FeedScrape.FeedDataParser import extractChapterVol
from FeedScrape.FeedDataParser import extractVolChapterFragmentPostfix
from tests.title_test_data import data as test_data


# Order matters! Items are checked from left to right.
VOLUME_KEYS   = ['volume', 'season', 'book', 'vol', 'volume', 'season', 'book', 'vol', 'vol.', 'v']
FRAGMENT_KEYS = ['part', 'episode', 'pt',  'part', 'p']
CHAPTER_KEYS  = ['chapter', 'ch', 'c', 'episode']

# Additional split characters
SPLIT_ON = ["!", ")", "(", "[", "]"]


def getDelimiter(instr, delimiters):
	for delimiter in delimiters:
		if instr.startswith(delimiter):
			return delimiter
	return False

def partition(alist, indices):
	return [alist[i:j] for i, j in zip([0]+indices, indices+[None])]

class Token(object):
	def __init__(self, text, position, parent):
		self.text     = text
		self.position = position
		self.parent   = parent

	def splitToken(self, toktype):

		idx = 0
		splits = []
		while idx < len(self.text):
			sp = getDelimiter(self.text[idx:], SPLIT_ON)
			if sp:
				splits.append(idx)
				splits.append(idx+len(sp))
				idx = idx+len(sp)
			else:
				idx += 1

		if 0 in splits:
			splits.remove(0)
		if len(self.text) in splits:
			splits.remove(len(self.text))
		if splits:
			ret = []
			offset = 0
			for chunk in partition(self.text, splits):
				ret.append(toktype(chunk, self.position+offset, self.parent))
				offset += 1
		else:
			ret = [self]

		num_ret = []
		for tok in ret:
			tmp = tok.splitNumeric(toktype)
			for val in tmp:
				num_ret.append(val)


		return num_ret

	def splitNumeric(self, toktype):
		'''
		Given a token containing a string that is partially numeric,
		split the token into sub-tokens that break at the numeric/non-numeric boundaries.
		E.g. 'ch03' becomes ['ch', '03']

		Has some internal protections. Does not split on back/forward slashes unless they are the
		first character.

		Returns a list of tokens in all cases. If no splits were done, the list contains
		only `self`. This allows unconditional use of the return value

		'''
		if not any([char in '0123456789' for char in self.text]):
			return [self]
		if ("/" in self.text and self.text.index("/") > 0) or ("\\" in self.text and self.text.index("\\") > 0):
			return [self]

		nmx = self.text[0] in '0123456789.'
		splits = []
		for idx in range(len(self.text)):
			c_nmx = self.text[idx] in '0123456789.'
			if c_nmx != nmx:
				splits.append(idx)
			nmx = c_nmx

		ret = [self]

		offset = 0
		if splits:
			ret = []
			for chunk in partition(self.text, splits):
				ret.append(toktype(chunk, self.position+offset, self.parent))
				offset += 1

		return ret

	def isNumeric(self):
		if not self.text:
			return False
		# Handle strings with multiple decimal points, e.g. '01.05.15'
		if self.text.count(".") > 1:
			return False
		if not any([char in '0123456789' for char in self.text]):
			return False
		if all([char in '0123456789.' for char in self.text]):
			return True
		return False

	def getNumber(self):
		assert self.isNumeric(), "getNumber() can only be called if the token value is entirely numeric!"
		return float(self.text)

	def __repr__(self):
		ret = "<{:14} at: {:2} contents: '{}' number: {}>".format(self.__class__.__name__, self.position, self.text, self.isNumeric())
		return ret

	def string(self):
		return self.text

	def lastData(self):
		all_before = self.parent._preceeding(self.position)
		# print("LastData: ", self)
		# print("Preceeding:")
		# for item in all_before:
		# 	print("	", item)

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
		indice = 0
		data = ''

		# Consume the string in [data, delimiter] 2-tuples.
		while indice < len(self.raw):
			delimiter = getDelimiter(self.raw[indice:], self.DELIMITERS)
			if delimiter:
				assert self.raw[indice:].startswith(delimiter)
				if data:
					d_toks = DataToken(
							text     = data,
							position = len(self.chunks),
							parent   = self).splitToken(DataToken)
					data = ''
					for tok in d_toks:
						self.chunks.append(tok)
				tok  = DelimiterToken(
						text     = self.raw[indice:indice+len(delimiter)],
						position = len(self.chunks),
						parent   = self)
				self.chunks.append(tok)
				indice = indice+len(delimiter)

			else:
				data += self.raw[indice]
				indice += 1


		# Finally, tack on any trailing data tokens (if they're present)
		if data:
			d_toks = DataToken(
				text     = data,
				position = len(self.chunks),
				parent   = self).splitToken(DataToken)
			for tok in d_toks:
				self.chunks.append(tok)


	def _preceeding(self, offset):
		return self.chunks[:offset]
	def _following(self, offset):
		return self.chunks[offset+1:]


	def getNumbers(self):
		return [item for item in self.chunks if item.isNumeric()]

	def getVolumeItem(self):
		for item in self.getNumbers():
			if item.lastData().string().lower() in VOLUME_KEYS:
				return item
		return None
	def getVolume(self):
		have = self.getVolumeItem()
		if not have:
			return have
		return have.getNumber()

	def getFragment(self):
		vol = self.getVolumeItem()
		chp = self.getChapterItem()
		for item in self.getNumbers():
			if item.lastData().string().lower() in FRAGMENT_KEYS:
				# If the item has already been globbed by the chapter or vol scrape,
				# skip it.
				if chp and item == chp:
					continue
				if vol and item == vol:
					continue
				return item.getNumber()
		return None

	def getChapterItem(self):
		vol = self.getVolumeItem()
		numbers = self.getNumbers()
		# Try for any explicit chapters first
		for item in numbers:
			if item.lastData().string().lower() in CHAPTER_KEYS:
				if vol and item == vol:
					continue
				return item

		# Then any numbers that are just not associated with known
		# volume/fragment values
		for item in numbers:
			if item.lastData().string().lower() not in VOLUME_KEYS+FRAGMENT_KEYS:
				if vol and item == vol:
					continue
				return item
		return None

	def getChapter(self):
		have = self.getChapterItem()
		if not have:
			return have
		return have.getNumber()

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
	for key, value in test_data:
		# if not "  " in key:
		# 	continue
		if any(value):
			# print(key, value)
			p = TitleParser(key)
			vol, chp, frag = p.getVolume(), p.getChapter(), p.getFragment()


			if len(value) == 2:
				e_chp, e_vol = value
				if e_chp == 0.0 and chp == None:
					e_chp = None
				if vol != e_vol or chp != e_chp:
					mismatch += 1
					print(p)
					print("Parsed: v{}, c{}, f{}".format(vol, chp, frag))
					print("Expect: v{}, c{}".format(e_vol, e_chp))
					print()
			elif len(value) == 4:
				e_vol, e_chp, e_frag, e_post = value
				if e_chp == 0.0 and chp == None:
					e_chp = None
				if vol != e_vol or chp != e_chp or frag != e_frag:
					mismatch += 1
					print(p)
					print("Parsed: v{}, c{}, f{}".format(vol, chp, frag))
					print("Expect: v{}, c{}, f{}".format(e_vol, e_chp, e_frag))
					print()
			# for number in p.getNumbers():
			# 	print(number)
			# 	print("Preceeded by:", number.lastData())
			count += 1

		# if len(value) == 2:
		# 	assert value == extractChapterVol(key), "Wat? Values: '{}', '{}', '{}'".format(key, value, extractChapterVol(key))
		# elif len(value) == 4:
		# 	assert value == extractVolChapterFragmentPostfix(key), "Wat? Values: '{}', '{}', '{}'".format(key, value, extractVolChapterFragmentPostfix(key))
		# else:
		# 	print("Wat?")
		# 	print(key, value)
	# print("All matches passed!")
	print("{} Items with parsed output".format(count))
	print("{} Items mismatch in new parser".format(mismatch))

if __name__ == "__main__":

	test()

