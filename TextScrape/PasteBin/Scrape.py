
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.WordpressScrape

import webFunctions


class Scrape(TextScrape.WordpressScrape.WordpressScrape):
	tableKey = 'pb'
	loggerPath = 'Main.PasteBin.Scrape'
	pluginName = 'PasteBinScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1

	baseUrl = [
			'https://www.example.org'
		]
	pasteBinLut = {
		          'http://pastebin.com/C8cU0ZPq' : 'Slave harem in the labyrinth of the other world - Chapter 1 - ',
		'http://pastebin.com/raw.php?i=C8cU0ZPq' : 'Slave harem in the labyrinth of the other world - Chapter 1 - ',
		          'http://pastebin.com/Gm4xYe35' : 'Slave harem in the labyrinth of the other world - Chapter 2 - ',
		'http://pastebin.com/raw.php?i=Gm4xYe35' : 'Slave harem in the labyrinth of the other world - Chapter 2 - ',
		          'http://pastebin.com/iGjtwjVR' : 'Slave harem in the labyrinth of the other world - Chapter 3 - ',
		'http://pastebin.com/raw.php?i=iGjtwjVR' : 'Slave harem in the labyrinth of the other world - Chapter 3 - ',
		          'http://pastebin.com/VyPC3Kdn' : 'Slave harem in the labyrinth of the other world - Chapter 4 - ',
		'http://pastebin.com/raw.php?i=VyPC3Kdn' : 'Slave harem in the labyrinth of the other world - Chapter 4 - ',
		          'http://pastebin.com/NS6kwFvL' : 'Slave harem in the labyrinth of the other world - Chapter 5 - ',
		'http://pastebin.com/raw.php?i=NS6kwFvL' : 'Slave harem in the labyrinth of the other world - Chapter 5 - ',

		          'http://pastebin.com/6Ar4iu9P' : 'Konjiki no Wordmaster - Chapter 41 - ',
		'http://pastebin.com/raw.php?i=6Ar4iu9P' : 'Konjiki no Wordmaster - Chapter 41 - ',
		}

	# startUrl = list(pasteBinLut.keys()) + baseUrl
	startUrl = list(pasteBinLut.keys())

	fileDomains = set(['files.wordpress.com'])

	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = [
				"/manga/",
				"/recruitment/",
				"wpmp_switcher=mobile",
				"account/begin_password_reset",
				"/comment-page-",

				# Why do people think they need a fucking comment system?
				'/?replytocom=',
				'#comments',

				# Mask out the PDFs
				"-online-pdf-viewer/",

				# Who the fuck shares shit like this anyways?
				"?share=",
				"/feed/",
				]



	decompose = [
		{'id'    :'header'},
		{'class' : 'widget-area'},
		{'id'    : 'footer'},
		{'class' : 'photo-meta'},
		{'class' : 'page-header'},
		{'class' : 'wpcnt'},
		{'class' : 'bit'},
		{'id'    : 'bit'},
		{'id'    : 'author-info'},
		{'id'    : 'secondary'},
		{'id'    : 'colophon'},
		{'id'    : 'branding'},
		{'id'    : 'nav-single'},
		{'id'    : 'likes-other-gravatars'},
		{'id'    : 'sidebar'},
		{'id'    : 'carousel-reblog-box'},
		{'id'    : 'infinite-footer'},
		{'id'    : 'nav-above'},
		{'id'    : 'nav-below'},
		{'id'    : 'jp-post-flair'},
		{'id'    : 'comments'},
		{'class' : 'entry-utility'},
		{'name'  : 'likes-master'},

	]

	stripTitle = 'Raising the Dead |'

	def prependTitle(self, title, url):
		if url in self.pasteBinLut:
			title = self.pasteBinLut[url] + title
			title = title.replace(' - Pastebin.com', '')
			self.log.info("Using title patching mechanism!")


		return title

	# Methods to allow the child-class to modify the content at various points.
	def extractMarkdownTitle(self, content, url):
		# Take the first non-empty line, and just assume it's the title. It'll be close enough.
		title = content.strip().split("\n")[0].strip()
		title = self.prependTitle(title, url)
		return title


	# Methods to allow the child-class to modify the content at various points.
	def extractTitle(self, srcSoup, doc, url):
		title = doc.title()
		title = self.prependTitle(title, url)
		return title



def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




