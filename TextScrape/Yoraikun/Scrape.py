
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'yora'
	loggerPath = 'Main.Yor.Scrape'
	pluginName = 'YoraikunScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 4

	baseUrl = "https://yoraikun.wordpress.com/"
	fileDomains = set(['files.wordpress.com/'])
	startUrl = baseUrl

	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = [
					'/disclaimer/',
					'/about/',
					'like_comment=',
					'replytocom=',
					'?share=',
					'/comment-page-',
					'wp-login.php',
					'gravatar.com',
				]

	decomposeBefore = [
		{'name'     : 'likes-master'},  # Bullshit sharing widgets
		{'id'       : 'jp-post-flair'},
		{'class'    : 'commentlist'},  # Scrub out the comments so we don't try to fetch links from them
		{'id'       : 'comments'},
	]


	decompose = [
		{'class'           : 'commentlist'},  # Scrub out the comments so we don't try to fetch links from them
		{'class'           : 'loggedout-follow-normal'},
		{'class'           : 'sd-content'},
		{'class'           : 'sd-title'},
		{'class'           : 'widget-area'},
		{'class'           : 'xoxo'},
		{'class'           : 'wpcnt'},
		{'id'              : 'calendar_wrap'},
		{'id'              : 'comments'},
		{'id'              : 'footer'},
		{'id'              : 'header'},
		{'id'              : 'entry-author-info'},
		{'id'              : 'jp-post-flair'},
		{'id'              : 'likes-other-gravatars'},
		{'id'              : 'nav-above'},
		{'id'              : 'nav-below'},
		{'id'              : 'primary'},
		{'id'              : 'secondary'},
		{'name'            : 'likes-master'},  # Bullshit sharing widgets
		{'style'           : 'display:none'},


	]

	# Grab all images, ignoring host domain
	allImages = True


def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.baseUrl)


if __name__ == "__main__":
	test()




