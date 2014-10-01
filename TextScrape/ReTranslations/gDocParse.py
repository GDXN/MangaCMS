

import bs4

import re
import json
import html

# HORRIBLE experimental google doc content extraction system

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

MARKUP_DATA   = 'sm'

# font stuff
FONT_PREFIX   = 'ts_'
FONT_BOLD     = FONT_PREFIX+'bd'
FONT_BOLD_2   = FONT_PREFIX+'bd_i'  # Yeah, I /think/ there are two flags for each modifier?
FONT_ITALIC   = FONT_PREFIX+'it'
FONT_ITALIC_2 = FONT_PREFIX+'it_i'
FONT_FACE     = FONT_PREFIX+'ff'
FONT_COLOUR   = FONT_PREFIX+'fgc'
FONT_SIZE     = FONT_PREFIX+'fs'

# links
LINK_URL  = 'ulnk_url'
LINK_TYPE = 'lnk_type'


# Zero length markup (flags and shit)
# MARKUP_PARA_BREAK =


IGNORE_MARKUP = ['doco_anchor', 'comment', 'import_warnings']

MARKUP_TYPE_LINK = 'link'
MARKUP_TYPE_LIST = 'list'
MARKUP_TYPE_PARA = 'paragraph'
MARKUP_TYPE_CELL = 'cell'
MARKUP_TYPE_TEXT = 'text'

class GDocParser(object):

	def __init__(self, inPageContents):
		self.contents = inPageContents

		self.document = ''

		self.currentChunk = ''

		self.document = RichDocument()

	# There are lots more things in the text markup settings,
	# but I don't really care to parse it all, I mostly just want
	# the basic markup
	def parseTextMarkup(self, chunk):
		fontContents = chunk[MARKUP_DATA]
		if not 'ts_ff' in fontContents:
			print("Wat?")
			print(chunk)

		start, end = chunk[MARKUP_START]-1, chunk[MARKUP_END]
		if fontContents[FONT_BOLD] and not fontContents[FONT_BOLD_2]:
			self.document.bold(start, end)



		if fontContents[FONT_ITALIC] and not fontContents[FONT_ITALIC_2]:
			self.document.italic(start, end)



		face = fontContents[FONT_FACE]
		colour = fontContents[FONT_COLOUR]
		size = fontContents[FONT_SIZE]
		if face and colour and size:
			self.document.setFont(start, end, face, colour, size)


	def parseZeroLengthMarkup(self, chunk):
		cType = chunk[MARKUP_KEY]
		if cType == MARKUP_TYPE_PARA:
			self.document.addParagraphBreak(chunk[MARKUP_START])
		# else:
		# 	print("Unknown zero-length markup", cType)
		# 	print(chunk)

	def parseLink(self, chunk):
		if not chunk['sm']['lnks_link']:  # Empty link
			return
		linkdata = chunk['sm']['lnks_link']
		if not linkdata[LINK_TYPE] == 0:
			raise ValueError("Unknown link type!")

		url = linkdata[LINK_URL]

		start, end = chunk[MARKUP_START]-1, chunk[MARKUP_END]

		self.document.insertLink(start, end, url)

	def parseChunk(self, chunk):

		if chunk[TYPE_KEY] == CONTENTS:
			self.document.addText(chunk[TEXT_KEY])
		elif chunk[TYPE_KEY] == MARKUP:
			if chunk[MARKUP_KEY] in IGNORE_MARKUP:
				return

			elif chunk[MARKUP_START] == chunk[MARKUP_END]:
				self.parseZeroLengthMarkup(chunk)

			elif chunk[MARKUP_KEY] == MARKUP_TYPE_LINK:
				self.parseLink(chunk)

			elif chunk[MARKUP_KEY] == MARKUP_TYPE_TEXT:
				self.parseTextMarkup(chunk)
			else:
				print("Markup", chunk[MARKUP_KEY], chunk[MARKUP_START], chunk[MARKUP_END])

		elif chunk[TYPE_KEY] == UNKNOWN_1:
			print("Image?")
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

		body = self.document.dump()

		doc = "<html><meta charset='UTF-8'><body>"+body+"</body></html>"
		soup = bs4.BeautifulSoup(doc)
		return soup.prettify()

	def getTitle(self):
		titleRe = re.compile("<title>(.*?)</title>")
		titles = titleRe.findall(self.contents)
		title = titles.pop()
		title = title.replace(" - Google Docs", "")
		return title

class RichDocument(object):

	# Basically, google docs stores the text and the markup separately, and
	# refers between the two using char offsets.
	# As a result, if I start permuting the text to insert things like
	# HTML tags, all the char offsets will be invalid.
	# Therefore, we store the text, and a dict of values to inset at `key` char offsets
	# The dump command serializes them all together as it iterates over `text`.
	def __init__(self):

		self.text = ''
		self.metadata = {}

	def addText(self, newText):
		self.text += newText

	def addEnclosingMarkup(self, start, startStr, end, endStr):

		# Do not generate tags for whitespace
		if not self.text[start:end].strip():
			return

		if not start in self.metadata:
			self.metadata[start] = startStr
		else:
			self.metadata[start] += startStr

		if not end in self.metadata:
			self.metadata[end] = endStr
		else:
			self.metadata[end] = endStr + self.metadata[end]

	def addSingleTag(self, offset, tagStr):

		if not offset in self.metadata:
			self.metadata[offset] = tagStr
		else:
			self.metadata[offset] = tagStr + self.metadata[offset]

	# Fuck you, I'm generating simple HTML like it's 1995
	def bold(self, start, end):
		self.addEnclosingMarkup(start, "<b>", end, "</b>")

	def italic(self, start, end):
		self.addEnclosingMarkup(start, "<i>", end, "</i>")

	def setFont(self, start, end, face=None, colour=None, size=None):
		params = []
		if colour and '000000' not in colour:
			param = "color:'{colour}'".format(colour=colour)
			params.append(param)
		if face:
			param = "font-family:'{face}'".format(face=face)
			params.append(param)
		if size:
			param = "font-size: {size}pt".format(size=size)
			params.append(param)
		if params:
			startTag = '<span style="{attrs}">'.format(attrs="; ".join(params))
			self.addEnclosingMarkup(start, startTag, end, "</span>")

	def addEnclosingParagraph(self, start, end):
		self.addEnclosingMarkup(start, "<p>", end, "</p>")

	def addParagraphBreak(self, offset):
		self.addSingleTag(offset, "<p />")

	def insertLink(self, start, end, url):
		openTag = '<a href="{url}">'.format(url=url)
		self.addEnclosingMarkup(start, openTag, end, "</a>")

	def dump(self):
		ret = ''
		for x in range(len(self.text)):
			if x in self.metadata:
				ret += self.metadata[x]
			ret += html.escape(self.text[x])

			# Insert line breaks where they were in the original file
			# Detecting paragraphs in typeset text is /hard/, since all the original information
			# paragraph metadata is stripped out.
			# TL;DR take a look at converting PDFs to HTML. They discard
			# paragraph info as well, and it's messy there as well.
			# if self.text[x] == "\n":
			# 	ret += "<br>"
			# if self.text[x] == "\r":
			# 	pass

		return ret





def test():
	import webFunctions
	wg = webFunctions.WebGetRobust()

	# pg = wg.getpage('https://docs.google.com/document/d/1ljoXDy-ti5N7ZYPbzDsj5kvYFl3lEWaJ1l3Lzv1cuuM/preview')
	# pg = wg.getpage('https://docs.google.com/document/d/17__cAhkFCT2rjOrJN1fK2lBdpQDSO0XtZBEvCzN5jH8/preview')
	pg = wg.getpage('https://docs.google.com/document/d/1t4_7X1QuhiH9m3M8sHUlblKsHDAGpEOwymLPTyCfHH0/preview')
	print(len(pg))


	parse = GDocParser(pg)
	ret = parse.parse()
	parse.getTitle()


	with open("test.html", "wb") as fp:
		fp.write(ret.encode("utf-8"))

if __name__ == "__main__":
	import logSetup
	if __name__ == "__main__":
		print("Initializing logging")
		logSetup.initLogging()

	test()
