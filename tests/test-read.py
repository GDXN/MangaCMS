
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


# import runStatus
# runStatus.preloadDicts = False

# from ScrapePlugins.RhLoader.Run import Runner
# from ScrapePlugins.RhLoader.RhFeedLoader import RhFeedLoader
# from ScrapePlugins.RhLoader.RhContentLoader import RhContentLoader
import signal

import readability.readability
import webFunctions
import bs4
# import nameTools as nt

import os.path

def customHandler(signum, stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

def test():


	wg = webFunctions.WebGetRobust(logPath="Main.Wat?")

	print(wg)
	srcUrl = 'http://www.baka-tsuki.org/project/index.php?title=HEAVY_OBJECT'


	gotPage = wg.getpage(srcUrl)
	doc = readability.readability.Document(gotPage, base_url=srcUrl, debug=True, negative_keywords=['mw-normal-catlinks', "printfooter", "mw-panel", 'portal'])
	doc.parse()
	content = doc.content()
	soup = bs4.BeautifulSoup(content)

	[tag.extract() for tag in soup.find_all(role="navigation")]

	print(soup.prettify())

	print(doc.title())

	# loader = RhFeedLoader()
	# loader.go()


	# # loader.getAllItems()
	# # loader.getItemPages('http://manga.redhawkscans.com/reader/series/white_album/')

	# # # feedItems = loader.getItemsFromContainer("Ore no Kanojo + H", loader.quoteUrl("http://download.japanzai.com/Ore no Kanojo + H/index.php"))
	# # # loader.log.info("Processing feed Items")
	# # for item in feedItems:
	# # 	print("Item", item)

	# loader.closeDB()

	# # nt.dirNameProxy.startDirObservers()

	# # runner = Runner()
	# # runner.go()

	# # cl = RhContentLoader()
	# # cl.go()



if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		pass
		# import nameTools as nt
		# nt.dirNameProxy.stop()

