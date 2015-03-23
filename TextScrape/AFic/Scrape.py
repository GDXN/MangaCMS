
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

from TextScrape.SiteArchiver import SiteArchiver

import webFunctions
import http.cookiejar
import urllib.parse

class Scrape(SiteArchiver):
	tableKey = 'adfic'
	loggerPath = 'Main.Text.AdFic.Scrape'
	pluginName = 'AdFicScrape'

	tableName       = "book_western_items"
	changeTableName = "book_western_changes"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 10

	FOLLOW_GOOGLE_LINKS = False
	allImages = False


	baseUrl = [
		"http://www.adult-fanfiction.org",
		"http://adult-fanfiction.org",
		"http://original.adult-fanfiction.org",

		# Fukkit, if you're going to scrape fanfic, you might as well scrape ALL THE FANFIC, right?
		"http://members.adult-fanfiction.org",
		"http://anime.adult-fanfiction.org",
		"http://anime2.adult-fanfiction.org",
		"http://books.adult-fanfiction.org",
		"http://bleach.adult-fanfiction.org",
		"http://buffy.adult-fanfiction.org",
		"http://cartoon.adult-fanfiction.org",
		"http://comics.adult-fanfiction.org",
		"http://celeb.adult-fanfiction.org",
		"http://ff.adult-fanfiction.org",
		"http://games.adult-fanfiction.org",
		"http://hp.adult-fanfiction.org",
		"http://inu.adult-fanfiction.org",
		"http://lotr.adult-fanfiction.org",
		"http://manga.adult-fanfiction.org",
		"http://movies.adult-fanfiction.org",
		"http://naruto.adult-fanfiction.org",
		"http://tv.adult-fanfiction.org",
		"http://xmen.adult-fanfiction.org",
		"http://ygo.adult-fanfiction.org",
		"http://yuyu.adult-fanfiction.org",

		]
	startUrl = 'http://www.adult-fanfiction.org/html-index.php'

	badwords = [
				"/about/",
				"/join-us/",
				"/chat/",
				'&format=pdf',
				'/adpeeps/',
				'/ads/',
				'/java/'
				'/globals/',
				'adpeeps.php',
				'?format=pdf',
				'?replytocom=',
				"/forum/",
				"/forum",
				"/forums/",
				"/forums",
				"/games/",
				"/betareaders/",
				"/poetry/", # Really?

				"/post.php?",
				"/author.php?",
				"big.oscar.aol.com",

				'ne.adult-fanfiction.org',   # Non-english

				'review.php?', # Filter reviews (possibly should be revisited?)
				]

	# Content Stripping needs to be determined.
	decomposeBefore = [

	]

	decompose = [

	]

	stripTitle = ''




	def preprocessBody(self, soup):
		if 'Birthdate Verification Page' in soup.prettify():
			raise RuntimeError("Cookie generation failed!")
		return soup

	def spoofCookies(self):

		# Generate a fake adult check bypass cookie for each domain
		# and verify it's valid.

		# Uses some undocumented http.cookiejar functionality.

		for domain in self.baseUrl:
			url = urllib.parse.urlparse(domain)
			params = {
				'version'            :  0,
				'name'               :  'HasVisited',
				'value'              :  'bypass page next time',
				'port'               :  None,
				'port_specified'     :  False,
				'domain'             :  url.netloc,
				'domain_specified'   :  False,
				'domain_initial_dot' :  False,
				'path'               :  '/',
				'path_specified'     :  True,
				'secure'             :  False,
				'expires'            :  1949915305,
				'discard'            :  False,
				'comment'            :  None,
				'comment_url'        :  None,
				'rest'               :  {}

			}

			newCookie = http.cookiejar.Cookie(**params)

			self.wg.cj.set_cookie(newCookie)
		self.wg.saveCookies()


		checkPage = self.wg.getpage('http://www.adult-fanfiction.org/html-index.php')
		if "I am 18 years of age or older." in checkPage:
			self.log.info("Faux ack cookie did not work?")
			raise ValueError
		else:
			self.log.info("Adult Check bypassed.")
			return

	def spoofVerifier(self):

		checkPage = self.wg.getpage('http://original.adult-fanfiction.org/form_adult.php')
		if not 'Birthdate Verification Page' in checkPage:
			self.log.info("Already age-verified")
			return

		acceptParams = {
			'cmbmonth' : '1',
			'cmbday'   : '1',
			'cmbyear'  : '1973',
			'cmbname'  : 'Giant Cock',
			'Submit'   : 'Click here to submit',
		}

		acceptPage = self.wg.getpage('http://original.adult-fanfiction.org/check.php', postData=acceptParams)
		if 'Birthdate Verification Page' in acceptPage:
			raise ValueError("Accept Page failed to work?")




	def preFlight(self):
		self.spoofCookies()
		self.spoofVerifier()



def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

