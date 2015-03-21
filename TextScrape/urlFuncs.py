

import urllib.parse


import TextScrape.gDocParse as gdp


def urlClean(url):
	# Google docs can be accessed with or without the '/preview' postfix
	# We want to remove this if it's present, so we don't duplicate content.
	url = gdp.trimGDocUrl(url)

	while True:
		url2 = urllib.parse.unquote(url)
		url2 = url2.split("#")[0]
		if url2 == url:
			break
		url = url2

	# Clean off whitespace.
	url = url.strip()

	return url
