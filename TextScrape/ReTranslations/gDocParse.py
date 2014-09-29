


import re
import json

TYPE_KEY  = 'ty'

# Chunk types
CONTENTS  = 'is'
MARKUP    = 'as'
UNKNOWN_1 = 'ae'
UNKNOWN_2 = 'te'

# Content keys
TEXT_KEY = 's'

# Markup Keys
MARKUP_KEY = 'st'

MARKUP_START = 'si'
MARKUP_END   = 'ei'


IGNORE_MARKUP = ['doco_anchor', 'comment', 'import_warnings']

MARKUP_TYPE_LINK = 'link'
MARKUP_TYPE_LIST = 'list'
MARKUP_TYPE_PARA = 'paragraph'
MARKUP_TYPE_CELL = 'cell'

class GDocParser(object):

	def __init__(self, inPageContents):
		self.contents = inPageContents

		self.document = ''

		self.currentChunk = ''


	def parseChunk(self, chunk):

		if chunk[TYPE_KEY] == CONTENTS:
			self.currentChunk += chunk[TEXT_KEY]
		elif chunk[TYPE_KEY] == MARKUP:
			if chunk[MARKUP_START] == chunk[MARKUP_END]:
				return

			if chunk[MARKUP_KEY] in IGNORE_MARKUP:
				return
			print("Markup", chunk[MARKUP_KEY], chunk[MARKUP_START], chunk[MARKUP_END])

			if chunk[MARKUP_KEY] == MARKUP_TYPE_LINK:
				if not chunk['sm']['lnks_link']:  # Empty link
					return

				print(chunk['sm'])



			# print(self.currentChunk[chunk[MARKUP_START]-1:chunk[MARKUP_END]])

		elif chunk[TYPE_KEY] == UNKNOWN_1:
			pass
		elif chunk[TYPE_KEY] == UNKNOWN_2:
			pass
		else:
			print("Wat?", chunk[TYPE_KEY])
			print(chunk)

	def parse(self):

		extr = re.compile(r'DOCS_modelChunk = (\[{.+?}\]);.*?DOCS_modelChunkLoadStart')
		ret = extr.findall(self.contents)
		for item in ret:
			loaded = json.loads(item)
			for chunk in loaded:
				self.parseChunk(chunk)







def test():
	import webFunctions
	wg = webFunctions.WebGetRobust()

	# pg = wg.getpage('https://docs.google.com/document/d/1ljoXDy-ti5N7ZYPbzDsj5kvYFl3lEWaJ1l3Lzv1cuuM/preview')
	# pg = wg.getpage('https://docs.google.com/document/d/17__cAhkFCT2rjOrJN1fK2lBdpQDSO0XtZBEvCzN5jH8/preview')
	pg = wg.getpage('https://docs.google.com/document/d/1t4_7X1QuhiH9m3M8sHUlblKsHDAGpEOwymLPTyCfHH0/preview')
	print(len(pg))


	parse = GDocParser(pg)
	parse.parse()

if __name__ == "__main__":
	import logSetup
	if __name__ == "__main__":
		print("Initializing logging")
		logSetup.initLogging()

	test()
