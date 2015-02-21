

import pyparsing as pp

def jsParse(inStr):
	# This disaster is a context-free grammar parser for parsing javascript object literals.
	# It needs to be able to handle a lot of the definitional messes you find in in-the-wild
	# javascript object literals.
	# Unfortunately, Javascript is /way/ more tolerant then JSON when it comes to object literals
	# so we can't just parse objects using python's `json` library.

	TRUE = pp.Keyword("true").setParseAction( pp.replaceWith(True) )
	FALSE = pp.Keyword("false").setParseAction( pp.replaceWith(False) )
	NULL = pp.Keyword("null").setParseAction( pp.replaceWith(None) )

	jsonString = pp.quotedString.setParseAction( pp.removeQuotes )
	jsonNumber = pp.Combine( pp.Optional('-') + ( '0' | pp.Word('123456789',pp.nums) ) +
											pp.Optional( '.' + pp.Word(pp.nums) ) +
											pp.Optional( pp.Word('eE',exact=1) + pp.Word(pp.nums+'+-',pp.nums) ) )

	jsonObject   = pp.Forward()
	jsonValue    = pp.Forward()
	jsonDict     = pp.Forward()
	jsonArray    = pp.Forward()
	jsonElements = pp.Forward()

	commaToNull = pp.Word(',,', exact=1).setParseAction(pp.replaceWith(None))
	jsonElements << pp.ZeroOrMore(commaToNull) + pp.Optional(jsonObject) + pp.ZeroOrMore((pp.Suppress(',') + jsonObject) | commaToNull)

	jsonValue << ( jsonString | jsonNumber | TRUE | FALSE | NULL )


	dictMembers = pp.delimitedList( pp.Group( jsonString + pp.Suppress(':') + jsonValue ) )
	jsonDict << ( pp.Dict( pp.Suppress('{') + pp.Optional(dictMembers) + pp.ZeroOrMore(pp.Suppress(',')) + pp.Suppress('}') ) )
	jsonArray << ( pp.Group(pp.Suppress('[') + pp.Optional(jsonElements) + pp.Suppress(']') ) )
	jsonObject << (jsonValue | jsonDict | jsonArray)

	jsonComment = pp.cppStyleComment
	jsonObject.ignore( jsonComment )

	def convertDict(s, l, toks):
		return dict(toks)

	def convertNumbers(s,l,toks):
		n = toks[0]
		try:
			return int(n)
		except ValueError:
			return float(n)

	jsonNumber.setParseAction(convertNumbers)
	jsonDict.setParseAction(convertDict)

	# jsonObject.setDebug()
	return jsonObject.parseString(inStr).pop()


# Stolen from http://stackoverflow.com/a/12017573/268006
import re
import urllib.parse

import os

# content-disposition = "Content-Disposition" ":"
#                        disposition-type *( ";" disposition-parm )
# disposition-type    = "inline" | "attachment" | disp-ext-type
#                     ; case-insensitive
# disp-ext-type       = token
# disposition-parm    = filename-parm | disp-ext-parm
# filename-parm       = "filename" "=" value
#                     | "filename*" "=" ext-value
# disp-ext-parm       = token "=" value
#                     | ext-token "=" ext-value
# ext-token           = <the characters in token, followed by "*">

def parseContentDispositon(cDispHdr, srcUrl):
	token           = '[-!#-\'*+.\dA-Z^-z|~]+'
	qdtext          = '[]-~\t !#-[]'
	mimeCharset     = '[-!#-&+\dA-Z^-z]+'
	language        = '(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}(?:-[A-Za-z]{3}){,2})?|[A-Za-z]{4,8})(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|\d{3}))(?:-(?:[\dA-Za-z]{5,8}|\d[\dA-Za-z]{3}))*(?:-[\dA-WY-Za-wy-z](?:-[\dA-Za-z]{2,8})+)*(?:-[Xx](?:-[\dA-Za-z]{1,8})+)?|[Xx](?:-[\dA-Za-z]{1,8})+|[Ee][Nn]-[Gg][Bb]-[Oo][Ee][Dd]|[Ii]-[Aa][Mm][Ii]|[Ii]-[Bb][Nn][Nn]|[Ii]-[Dd][Ee][Ff][Aa][Uu][Ll][Tt]|[Ii]-[Ee][Nn][Oo][Cc][Hh][Ii][Aa][Nn]|[Ii]-[Hh][Aa][Kk]|[Ii]-[Kk][Ll][Ii][Nn][Gg][Oo][Nn]|[Ii]-[Ll][Uu][Xx]|[Ii]-[Mm][Ii][Nn][Gg][Oo]|[Ii]-[Nn][Aa][Vv][Aa][Jj][Oo]|[Ii]-[Pp][Ww][Nn]|[Ii]-[Tt][Aa][Oo]|[Ii]-[Tt][Aa][Yy]|[Ii]-[Tt][Ss][Uu]|[Ss][Gg][Nn]-[Bb][Ee]-[Ff][Rr]|[Ss][Gg][Nn]-[Bb][Ee]-[Nn][Ll]|[Ss][Gg][Nn]-[Cc][Hh]-[Dd][Ee]'
	valueChars      = '(?:%[\dA-F][\dA-F]|[-!#$&+.\dA-Z^-z|~])*'
	dispositionParm = '[Ff][Ii][Ll][Ee][Nn][Aa][Mm][Ee]\s*=\s*(?:({token})|"((?:{qdtext}|\\\\[\t !-~])*)")|[Ff][Ii][Ll][Ee][Nn][Aa][Mm][Ee]\*\s*=\s*({mimeCharset})\'(?:{language})?\'({valueChars})|{token}\s*=\s*(?:{token}|"(?:{qdtext}|\\\\[\t !-~])*")|{token}\*\s*=\s*{mimeCharset}\'(?:{language})?\'{valueChars}'.format(**locals())

	# Wat?

	formatArgs = {
		'token'           : token,
		'qdtext'          : qdtext,
		'mimeCharset'     : mimeCharset,
		'language'        : language,
		'valueChars'      : valueChars,
		'dispositionParm' : dispositionParm
	}

	try:
		m = re.match('(?:{token}\s*;\s*)?(?:{dispositionParm})(?:\s*;\s*(?:{dispositionParm}))*|{token}'.format(**formatArgs), cDispHdr)

	except KeyError:
		name = os.path.basename(urllib.parse.unquote(urllib.parse.urlparse(srcUrl).path))

	else:
		if not m:
			name = os.path.basename(urllib.parse.unquote(urllib.parse.urlparse(srcUrl).path))

		# Many user agent implementations predating this specification do not
		# understand the "filename*" parameter.  Therefore, when both "filename"
		# and "filename*" are present in a single header field value, recipients
		# SHOULD pick "filename*" and ignore "filename"

		elif m.group(8) is not None:
			name = urllib.parse.unquote(m.group(8))
			# name = urllib.parse.unquote(m.group(8)).decode(m.group(7)) # Urllib is decoding the headers before I get them, because annoying, apparentlty.

		elif m.group(4) is not None:
			name = urllib.parse.unquote(m.group(4))
			# name = urllib.parse.unquote(m.group(4)).decode(m.group(3))

		elif m.group(6) is not None:
			name = re.sub('\\\\(.)', '\1', m.group(6))

		elif m.group(5) is not None:
			name = m.group(5)

		elif m.group(2) is not None:
			name = re.sub('\\\\(.)', '\1', m.group(2))

		else:
			name = m.group(1)

		# Recipients MUST NOT be able to write into any location other than one to
		# which they are specifically entitled

		if name:
			name = os.path.basename(name)

		else:
			name = os.path.basename(urllib.parse.unquote(urllib.parse.urlparse(srcUrl).path))

	return name

def test():
	tests = (

		'''[{'id': 'thing', }, 'wat']''',      # ok
		'''[{'id': 'thing', }, 'wat',]''',      # ok
		'''"wat", "wat"''',      # ok

		'''
	[{'id': '0B8UYgI2TD_nmNUMzNWJpZnJkRkU', 'title': 'story1-2.txt','enableStandaloneSharing': true,'enableEmbedDialog': true,'projectorFeedbackId': '99950', 'projectorFeedbackBucket': 'viewer-web',},["",1,,1,1,1,1,,,1,1,[0,,0,"AIzaSyDVQw45DwoYh632gvsP5vPDqEKvb-Ywnb8",0,0,1,0,,,0,"/drive/v2internal",0,0,0,[0,0,0]
	]
	,1,5,1,"https://docs.google.com",0,1,"https://docs.google.com",0,1,1,1,1,,1,20,1,0,0,1,1,[[,"0"]
	,6,1,1]
	,1,1,1,,[0,,,,"https://accounts.google.com/ServiceLogin?service\u003dwise\u0026passive\u003d1209600\u0026continue\u003dhttps://docs.google.com/file/d/0B8UYgI2TD_nmNUMzNWJpZnJkRkU/edit?pli%3D1\u0026hl\u003den\u0026followup\u003dhttps://docs.google.com/file/d/0B8UYgI2TD_nmNUMzNWJpZnJkRkU/edit?pli%3D1"]
	,0,1,1,600000,[1]
	,,0,0,[0,0,0]
	,["https://youtube.googleapis.com",1]
	,0,0,,0,1,0]
	,[,"story1-2.txt","https://lh5.googleusercontent.com/0JHRa3LjGQrV7UOhZMcuCj5I81mXlTOnrvtm4HPjQruxNP0SMuGJF-K7HsjDP8b1rM_e\u003ds1600",,,,"0B8UYgI2TD_nmNUMzNWJpZnJkRkU",,,"https://docs.google.com/st/viewurls?id\u003d0B8UYgI2TD_nmNUMzNWJpZnJkRkU\u0026m\u003d1440",,"text/plain",,,6,,"https://docs.google.com/file/d/0B8UYgI2TD_nmNUMzNWJpZnJkRkU/view?pli\u003d1",1,"https://docs.google.com/uc?id\u003d0B8UYgI2TD_nmNUMzNWJpZnJkRkU\u0026export\u003ddownload",,5,,,,,,,,,,,0]]
'''
	)
	for test in tests:
		results = jsParse(test)
		print(results)
		print(results[-1])

if __name__ == "__main__":
	print("wat")
	test()
