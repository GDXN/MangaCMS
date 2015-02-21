

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
