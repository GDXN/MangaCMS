

if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()

import ScrapePlugins.BuMonitor.Run
import ScrapePlugins.DjMoeLoader.Run
import ScrapePlugins.DjMoeLoader.Retag
import ScrapePlugins.SkBaseManager.Run
import ScrapePlugins.BtBaseManager.Run
import ScrapePlugins.PururinLoader.Run
import ScrapePlugins.Tadanohito.Run
import ScrapePlugins.JzLoader.Run

import ScrapePlugins.FakkuLoader.Run
import ScrapePlugins.McLoader.Run
import ScrapePlugins.CxLoader.Run
import ScrapePlugins.MjLoader.Run
import ScrapePlugins.LoneMangaLoader.Run
import ScrapePlugins.WebtoonLoader.Run            # Yeah. There is webtoon.com. and WebtoonsReader.com. Confusing, et?
import ScrapePlugins.WebtoonsReader.Run
import ScrapePlugins.KissLoader.Run
import ScrapePlugins.SadPandaLoader.Run
import ScrapePlugins.NHentaiLoader.Run
import ScrapePlugins.DynastyLoader.Run
import ScrapePlugins.HBrowseLoader.Run
import ScrapePlugins.Crunchyroll.Run
import ScrapePlugins.IrcGrabber.IrcEnqueueRun
import ScrapePlugins.IrcGrabber.BotRunner

import ScrapePlugins.FoolSlide.RhLoader.Run
import ScrapePlugins.FoolSlide.VortexLoader.Run
import ScrapePlugins.FoolSlide.RoseliaLoader.Run
import ScrapePlugins.FoolSlide.SenseLoader.Run
import ScrapePlugins.FoolSlide.ShoujoSenseLoader.Run
import ScrapePlugins.FoolSlide.TwistedHel.Run
import ScrapePlugins.FoolSlide.CasanovaScans.Run
import ScrapePlugins.FoolSlide.MangatopiaLoader.Run


import TextScrape.BakaTsuki.Run
import TextScrape.JapTem.Run
import TextScrape.Guhehe.Run
import TextScrape.ReTranslations.Run

import ScrapePlugins.MangaMadokami.mkContentLoader
import ScrapePlugins.MangaMadokami.mkFeedLoader

# Plugins in this dictionary are the active plugins. Comment out a plugin to disable it.
# plugin keys specify when plugins will start, and cannot be duplicates.
# All they do is specify the order in which plugins
# are run, initially, starting after 1-minue*{key} intervals
scrapePlugins = {
	0  : (ScrapePlugins.BtBaseManager.Run,                   60*60   ),
	2  : (ScrapePlugins.BuMonitor.Run,                       60*60   ),

	3  : (ScrapePlugins.JzLoader.Run,                        60*60*8 ),   # Every 8 hours, since I have to scrape a lot of pages, and it's not a high-volume source anyways
	4  : (ScrapePlugins.DjMoeLoader.Run,                     60*45   ),
	5  : (ScrapePlugins.DjMoeLoader.Retag,                   60*60   ),
	6  : (ScrapePlugins.McLoader.Run,                        60*60*12),  # every 12 hours, it's just a single scanlator site.
	7  : (ScrapePlugins.SkBaseManager.Run,                   60*60   ),
	8  : (ScrapePlugins.IrcGrabber.IrcEnqueueRun,            60*60*12),  # Queue up new items from IRC bots.
	9  : (ScrapePlugins.PururinLoader.Run,                   60*60   ),
	10 : (ScrapePlugins.FakkuLoader.Run,                     60*60   ),
	11 : (ScrapePlugins.CxLoader.Run,                        60*60*12),  # every 12 hours, it's just a single scanlator site.
	12 : (ScrapePlugins.MjLoader.Run,                        60*60   ),
	13 : (ScrapePlugins.IrcGrabber.BotRunner,                60*60   ),  # Irc bot never returns. It runs while the app is live. Rerun interval doesn't matter, as a result.
	14 : (ScrapePlugins.FoolSlide.RhLoader.Run,              60*60*12),
	15 : (ScrapePlugins.LoneMangaLoader.Run,                 60*60*12),
	16 : (ScrapePlugins.WebtoonLoader.Run,                   60*60*8 ),
	17 : (ScrapePlugins.DynastyLoader.Run,                   60*60*8 ),
	18 : (ScrapePlugins.HBrowseLoader.Run,                   60*60   ),
	19 : (ScrapePlugins.KissLoader.Run,                      60*60   ),
	20 : (ScrapePlugins.NHentaiLoader.Run,                   60*60   ),
	21 : (ScrapePlugins.Crunchyroll.Run,                     60*60*6 ),
	22 : (ScrapePlugins.SadPandaLoader.Run,                  60*60*2 ),
	23 : (ScrapePlugins.WebtoonsReader.Run,                  60*60*6 ),
	24 : (ScrapePlugins.Tadanohito.Run,                      60*60*6 ),

	# FoolSlide modules
	30 : (ScrapePlugins.FoolSlide.VortexLoader.Run,          60*60*12),
	31 : (ScrapePlugins.FoolSlide.RoseliaLoader.Run,         60*60*12),
	32 : (ScrapePlugins.FoolSlide.SenseLoader.Run,           60*60*12),
	33 : (ScrapePlugins.FoolSlide.ShoujoSenseLoader.Run,     60*60*12),
	34 : (ScrapePlugins.FoolSlide.TwistedHel.Run,            60*60*12),
	35 : (ScrapePlugins.FoolSlide.CasanovaScans.Run,         60*60*12),
	36 : (ScrapePlugins.FoolSlide.MangatopiaLoader.Run,      60*60*12),




	# Madokami is two separate sections, because the feedLoader takes
	# 5+ hours just to run.
	40  : (ScrapePlugins.MangaMadokami.mkContentLoader,    60*60),
	500 : (ScrapePlugins.MangaMadokami.mkFeedLoader,       60*60*24*4),  # every 4 days, because I have to iterate over the ENTIRE site.



	510 : (TextScrape.BakaTsuki.Run,                       60*60*24*7),  # Every 7 days, because books is slow to update
	511 : (TextScrape.JapTem.Run,                          60*60*24*5),
	513 : (TextScrape.Guhehe.Run,                          60*60*24*5),
	512 : (TextScrape.ReTranslations.Run,                  60*60*24*1)   # There's not much to actually scrape here, and it's google, so I don't mind hitting their servers a bit.


}



if __name__ == "__main__":

	scrapePlugins = {
	0 : (TextScrape.BakaTsuki.Run,                       60*60*24*7),  # Every 7 days, because books is slow to update
	1 : (TextScrape.JapTem.Run,                          60*60*24*5),
	3 : (TextScrape.Guhehe.Run,                          60*60*24*5),
	2 : (TextScrape.ReTranslations.Run,                  60*60*24*1)   # There's not much to actually scrape here, and it's google, so I don't mind hitting their servers a bit.


}



	import nameTools as nt

	def callGoOnClass(passedModule):
		print("Passed module = ", passedModule)
		print("Calling class = ", passedModule.Runner)
		instance = passedModule.Runner()
		instance.go()


	import signal
	import runStatus

	def signal_handler(dummy_signal, dummy_frame):
		if runStatus.run:
			runStatus.run = False
			print("Telling threads to stop")
		else:
			print("Multiple keyboard interrupts. Raising")
			raise KeyboardInterrupt


	signal.signal(signal.SIGINT, signal_handler)
	import sys
	import traceback
	print("Starting")
	try:
		if len(sys.argv) > 1 and int(sys.argv[1]) in scrapePlugins:
			plugin, interval = scrapePlugins[int(sys.argv[1])]
			print(plugin, interval)
			callGoOnClass(plugin)
		else:
			for plugin, interval in scrapePlugins.values():
				print(plugin, interval)
				callGoOnClass(plugin)
	except:
		traceback.print_exc()

	print("Complete")

	nt.dirNameProxy.stop()
	sys.exit()
