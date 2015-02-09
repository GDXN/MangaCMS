

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

import TextScrape.SolitaryTranslation.Run
import TextScrape.PrinceRevolution.Run
import TextScrape.Krytyk.Run

import TextScrape.UnlimitedNovelFailures.Run
import TextScrape.Yoraikun.Run
import TextScrape.SkyTheWood.Run
import TextScrape.Imoutolicious.Run

import TextScrape.UntunedTranslation.Run
import TextScrape.CETranslation.Run
import TextScrape.HereticTranslation.Run

import TextScrape.NanoDesuTranslation.Run
import TextScrape.SakuraHonyakuTranslation.Run
import TextScrape.KyakkaTranslation.Run
import TextScrape.UnbreakableMachineDollTrans.Run



import ScrapePlugins.MangaMadokami.mkContentLoader
import ScrapePlugins.MangaMadokami.mkFeedLoader

# Convenience functions to make intervals clearer.
def days(num):
	return 60*60*24*num
def hours(num):
	return 60*60*num

# Plugins in this dictionary are the active plugins. Comment out a plugin to disable it.
# plugin keys specify when plugins will start, and cannot be duplicates.
# All they do is specify the order in which plugins
# are run, initially, starting after 1-minue*{key} intervals
scrapePlugins = {
	0  : (ScrapePlugins.BtBaseManager.Run,                   hours(1)),
	2  : (ScrapePlugins.BuMonitor.Run,                       hours(1)),

	3  : (ScrapePlugins.JzLoader.Run,                        hours(8)),   # Every 8 hours, since I have to scrape a lot of pages, and it's not a high-volume source anyways
	4  : (ScrapePlugins.DjMoeLoader.Run,                     hours(1)),
	5  : (ScrapePlugins.DjMoeLoader.Retag,                   hours(1)),
	6  : (ScrapePlugins.McLoader.Run,                        hours(12)),  # every 12 hours, it's just a single scanlator site.
	7  : (ScrapePlugins.SkBaseManager.Run,                   hours(1)),
	8  : (ScrapePlugins.IrcGrabber.IrcEnqueueRun,            hours(12)),  # Queue up new items from IRC bots.
	9  : (ScrapePlugins.PururinLoader.Run,                   hours(1)),
	10 : (ScrapePlugins.FakkuLoader.Run,                     hours(1)),
	11 : (ScrapePlugins.CxLoader.Run,                        hours(12)),  # every 12 hours, it's just a single scanlator site.
	# 12 : (ScrapePlugins.MjLoader.Run,                        hours(1)),
	13 : (ScrapePlugins.IrcGrabber.BotRunner,                hours(1)),  # Irc bot never returns. It runs while the app is live. Rerun interval doesn't matter, as a result.
	14 : (ScrapePlugins.FoolSlide.RhLoader.Run,              hours(12)),
	15 : (ScrapePlugins.LoneMangaLoader.Run,                 hours(12)),
	16 : (ScrapePlugins.WebtoonLoader.Run,                   hours(8)),
	17 : (ScrapePlugins.DynastyLoader.Run,                   hours(8)),
	18 : (ScrapePlugins.HBrowseLoader.Run,                   hours(1)),
	19 : (ScrapePlugins.KissLoader.Run,                      hours(1)),
	20 : (ScrapePlugins.NHentaiLoader.Run,                   hours(1)),
	21 : (ScrapePlugins.Crunchyroll.Run,                     hours(6)),
	22 : (ScrapePlugins.SadPandaLoader.Run,                  hours(2)),
	23 : (ScrapePlugins.WebtoonsReader.Run,                  hours(6)),
	24 : (ScrapePlugins.Tadanohito.Run,                      hours(6)),

	# FoolSlide modules
	30 : (ScrapePlugins.FoolSlide.VortexLoader.Run,          hours(12)),
	31 : (ScrapePlugins.FoolSlide.RoseliaLoader.Run,         hours(12)),
	32 : (ScrapePlugins.FoolSlide.SenseLoader.Run,           hours(12)),
	33 : (ScrapePlugins.FoolSlide.ShoujoSenseLoader.Run,     hours(12)),
	34 : (ScrapePlugins.FoolSlide.TwistedHel.Run,            hours(12)),
	35 : (ScrapePlugins.FoolSlide.CasanovaScans.Run,         hours(12)),
	36 : (ScrapePlugins.FoolSlide.MangatopiaLoader.Run,      hours(12)),




	# Madokami is two separate sections, because the feedLoader takes
	# 5+ hours just to run.
	40  : (ScrapePlugins.MangaMadokami.mkContentLoader,    hours(1)),       # Content loader runs each hour, because it only downloads 100 items per-run
	150 : (ScrapePlugins.MangaMadokami.mkFeedLoader,       days(4)),  # every 4 days, because I have to iterate over the ENTIRE site.



	80 : (TextScrape.BakaTsuki.Run,                       days(7)),  # Every 7 days, because books is slow to update
	81 : (TextScrape.JapTem.Run,                          days(5)),
	82 : (TextScrape.Guhehe.Run,                          days(5)),
	83 : (TextScrape.SolitaryTranslation.Run,             days(5)),
	84 : (TextScrape.PrinceRevolution.Run,                days(5)),
	85 : (TextScrape.Krytyk.Run,                          days(5)),

	86 : (TextScrape.UnlimitedNovelFailures.Run,          days(2)),
	87 : (TextScrape.Yoraikun.Run,                        days(2)),
	88 : (TextScrape.SkyTheWood.Run,                      days(2)),
	89 : (TextScrape.Imoutolicious.Run,                   days(2)),

	90 : (TextScrape.ReTranslations.Run,                  days(1)),   # There's not much to actually scrape here, and it's google, so I don't mind hitting their servers a bit.

	91 : (TextScrape.UntunedTranslation.Run,              days(2)),
	92 : (TextScrape.CETranslation.Run,                   days(2)),
	93 : (TextScrape.HereticTranslation.Run,              days(2)),

	94 : (TextScrape.NanoDesuTranslation.Run,             days(2)),
	95 : (TextScrape.SakuraHonyakuTranslation.Run,        days(2)),
	96 : (TextScrape.KyakkaTranslation.Run,               days(2)),
	97 : (TextScrape.UnbreakableMachineDollTrans.Run,     days(2)),


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
