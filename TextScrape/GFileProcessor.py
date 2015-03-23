


import runStatus
runStatus.preloadDicts = False

# import Levenshtein as lv

import TextScrape.RelinkLookup
import TextScrape.urlFuncs
import traceback

import TextScrape.HtmlProcessor

import TextScrape.gDocParse as gdp

class DownloadException(Exception):
	pass



########################################################################################################################
#
#	##     ##    ###    #### ##    ##     ######  ##          ###     ######   ######
#	###   ###   ## ##    ##  ###   ##    ##    ## ##         ## ##   ##    ## ##    ##
#	#### ####  ##   ##   ##  ####  ##    ##       ##        ##   ##  ##       ##
#	## ### ## ##     ##  ##  ## ## ##    ##       ##       ##     ##  ######   ######
#	##     ## #########  ##  ##  ####    ##       ##       #########       ##       ##
#	##     ## ##     ##  ##  ##   ###    ##    ## ##       ##     ## ##    ## ##    ##
#	##     ## ##     ## #### ##    ##     ######  ######## ##     ##  ######   ######
#
########################################################################################################################




class GFileProcessor(TextScrape.HtmlProcessor.HtmlPageProcessor):
	'''
	The google file interface looks a lot like a plain HTML page once it's been extracted.

	Therefore, we subclass the HtmlPageProcessor, and just override the call method to
	download the file content, and just insert the actual extract method into the normal content fetching process.
	'''

	loggerPath = "Main.GdocPageProcessor"



	def retreiveGoogleFile(self, url):


		self.log.info("Should fetch google file at '%s'", url)
		doc = gdp.GFileExtractor(url)

		attempts = 0

		while 1:
			attempts += 1
			try:
				content, fName, mType = doc.extract()
			except TypeError:
				self.log.critical('Extracting item failed!')
				for line in traceback.format_exc().strip().split("\n"):
					self.log.critical(line.strip())

				if not url.endswith("/pub"):
					url = url+"/pub"

				self.log.info("Attempting to access as plain content instead.")
				url = TextScrape.urlFuncs.urlClean(url)
				url = gdp.trimGDocUrl(url)
				self.putNewUrl(url)
				return
			if content:
				break
			if attempts > 3:
				raise DownloadException


			self.log.error("No content? Retrying!")

		self.dispatchContent(url, content, fName, mType)

def test():
	print("Test mode!")
	import webFunctions
	import logSetup
	logSetup.initLogging()

	wg = webFunctions.WebGetRobust()
	# content = wg.getpage('http://www.arstechnica.com')
	scraper = GdocPageProcessor('https://docs.google.com/document/d/1ZdweQdjIBqNsJW6opMhkkRcSlrbgUN5WHCcYrMY7oqI', 'Main.Test', 'testinating')
	print(scraper)
	extr = scraper.extractContent()
	for link in extr['fLinks']:
		print(link)
	print()
	print()
	print()
	for link in extr['iLinks']:
		print(link)
	# print(extr['fLinks'])


	'''
	--+---------------------------------------------------------------+--------
	f | https://docs.google.com/file/d/0B76cfbDgh36oaE1QbGVLWXJDSVU
	f | https://docs.google.com/file/d/0B76cfbDgh36oaWs1Tk1PRTRJZDQ
	f | https://docs.google.com/file/d/0B76cfbDgh36obnZRV3BtOVlPaWs
	f | https://docs.google.com/file/d/0B76cfbDgh36ocDc3U3NjNXlLdFE
	f | https://docs.google.com/file/d/0B76cfbDgh36odEI4WUFsZS1TTWM
	f | https://docs.google.com/file/d/0B76cfbDgh36oLXNvdTBtcE53bDA
	f | https://docs.google.com/file/d/0B76cfbDgh36oQ0xHOXdpYkNqVVU
	f | https://docs.google.com/file/d/0B76cfbDgh36oQVZhdXgtbkFjYjg
	f | https://docs.google.com/file/d/0B76cfbDgh36oR095UGZrc2NYWVU
	f | https://docs.google.com/file/d/0B76cfbDgh36oS0FYTUFTLUJXcGM
	f | https://docs.google.com/file/d/0B76cfbDgh36oSjREeVNLOVZNZjg
	f | https://docs.google.com/file/d/0B76cfbDgh36oU3dETnRGS0w3VkE
	f | https://docs.google.com/file/d/0B76cfbDgh36oWl9jMmZ0X3hWOWc
	f | https://docs.google.com/file/d/0B76cfbDgh36oWXVTYWtvWlNyWW8
	f | https://docs.google.com/file/d/0B76cfbDgh36oZHliV0NsX3d3dTA
	t | https://docs.google.com/file/d/0B1akBvgmR76mbFU5VjhTV2owQnc
	t | https://docs.google.com/file/d/0B1akBvgmR76mcE11WnhMTUhfb2s
	t | https://docs.google.com/file/d/0B1akBvgmR76mcU51cnZ2bFhRajg
	t | https://docs.google.com/file/d/0B1akBvgmR76mdTFYN1VWLXFveTA
	t | https://docs.google.com/file/d/0B1akBvgmR76mM2xLaG1kRXVhSEU
	t | https://docs.google.com/file/d/0B1akBvgmR76mNDNaQTc5eTNDbTQ
	t | https://docs.google.com/file/d/0B1akBvgmR76mOUZUc3VrMzdvQXc
	t | https://docs.google.com/file/d/0B1akBvgmR76mR0pWNkJxWWVSRk0
	t | https://docs.google.com/file/d/0B1akBvgmR76mR1Y5THNTRGVSV2s
	t | https://docs.google.com/file/d/0B1akBvgmR76mUUNzWGo5SjQydVE
	t | https://docs.google.com/file/d/0B1akBvgmR76mVUNnMm5PT0dIMHc
	t | https://docs.google.com/file/d/0B1akBvgmR76mYTZBMUFkSzJwQ28
	t | https://docs.google.com/file/d/0B1akBvgmR76mYUhoYkdSSWhHVUE
	t | https://docs.google.com/file/d/0B1akBvgmR76mZFJiRGFSdHJGZEk
	t | https://docs.google.com/file/d/0B1akBvgmR76mZGZJbjFqd3JkQTg
	t | https://docs.google.com/file/d/0B1aV_gkFqPDdbnh6Q244b1lDN0k
	t | https://docs.google.com/file/d/0B1aV_gkFqPDdM181YkRFWlBzUlE
	t | https://docs.google.com/file/d/0B1aV_gkFqPDdMUUtM3ViaVdzM0E
	t | https://docs.google.com/file/d/0B1aV_gkFqPDdY1RTNWcxcjlURDQ
	t | https://docs.google.com/file/d/0B76cfbDgh36obnNDMnB0Nk1jTjA
	t | https://docs.google.com/file/d/0B76cfbDgh36obTlTSXhsQU1EZTA
	t | https://docs.google.com/file/d/0B76cfbDgh36obVVEWkdweG5MbVE
	t | https://docs.google.com/file/d/0B76cfbDgh36odmVRQ0RTMmVKdms
	t | https://docs.google.com/file/d/0B76cfbDgh36oMVdpTHhfUVluM0k
	t | https://docs.google.com/file/d/0B76cfbDgh36oOHRudUctczA3aGc
	t | https://docs.google.com/file/d/0B76cfbDgh36oU1dUY3IzcWNDYkk
	t | https://docs.google.com/file/d/0B76cfbDgh36oUnZ1NTZiOVZ3eUk
	t | https://docs.google.com/file/d/0B76cfbDgh36oUUstTWJ0ZEV1UTQ
	t | https://docs.google.com/file/d/0B76cfbDgh36oWU5XYXoxMmZvZkE
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmaDQxY1l4VFVQTXc
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmanB5ZEZHRHNSNDg
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmeVBGcjRQUVpDSjA
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmMU1ab3g3MFhIdkk
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmNlp0a0RZSmZ3UFk
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmNUMzNWJpZnJkRkU
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmOTRCU3FWSzdYV3M
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmQjB4UE5ZMkdVeDg
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmRjhrUDNPZXlCQWs
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmSmtWVVpkZG14RVk
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmTlQ3UXY1WGlOZVk
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmU0tPeXlRYm00MHM
	t | https://docs.google.com/file/d/0B8UYgI2TD_nmWG04bG5teFdNZlk
	t | https://docs.google.com/file/d/0B9rFLdSCcaiMS1ViOEdOeE5mYU0
	t | https://docs.google.com/file/d/0B9rFLdSCcaiMTTlQakx6U1JmdHM
	t | https://docs.google.com/file/d/0B_frgc33c8FGaWJUa3pOZUdvaEk
	t | https://docs.google.com/file/d/0B_frgc33c8FGWlp2aDY3eGFiX3c
	'''







if __name__ == "__main__":
	test()

