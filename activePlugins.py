

if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()

import ScrapePlugins.M.BuMonitor.Run
import ScrapePlugins.M.BtBaseManager.Run

import ScrapePlugins.H.DjMoeLoader.Run
import ScrapePlugins.H.DjMoeLoader.Retag
import ScrapePlugins.H.PururinLoader.Run
import ScrapePlugins.H.SadPandaLoader.Run
import ScrapePlugins.H.NHentaiLoader.Run
import ScrapePlugins.H.HBrowseLoader.Run
import ScrapePlugins.H.HitomiLoader.Run


import ScrapePlugins.M.McLoader.Run
import ScrapePlugins.M.CxLoader.Run
import ScrapePlugins.M.WebtoonLoader.Run            # Yeah. There is webtoon.com. and WebtoonsReader.com. Confusing much?
import ScrapePlugins.M.KissLoader.Run
import ScrapePlugins.M.DynastyLoader.Run
import ScrapePlugins.M.Crunchyroll.Run
import ScrapePlugins.M.IrcGrabber.IrcEnqueueRun
import ScrapePlugins.M.IrcGrabber.BotRunner
import ScrapePlugins.M.Kawaii.Run
import ScrapePlugins.M.ZenonLoader.Run
import ScrapePlugins.M.MangaBox.Run
import ScrapePlugins.M.MangaHere.Run
import ScrapePlugins.M.MangaStreamLoader.Run
import ScrapePlugins.M.YoMangaLoader.Run
import ScrapePlugins.M.SurasPlace.Run
import ScrapePlugins.M.GameOfScanlationLoader.Run

import ScrapePlugins.M.FoolSlide.Modules.CanisMajorRun
import ScrapePlugins.M.FoolSlide.Modules.ChibiMangaRun
import ScrapePlugins.M.FoolSlide.Modules.DokiRun
import ScrapePlugins.M.FoolSlide.Modules.GoMangaCoRun
import ScrapePlugins.M.FoolSlide.Modules.IlluminatiMangaRun
import ScrapePlugins.M.FoolSlide.Modules.JaptemMangaRun
import ScrapePlugins.M.FoolSlide.Modules.MangatopiaRun
import ScrapePlugins.M.FoolSlide.Modules.RoseliaRun
import ScrapePlugins.M.FoolSlide.Modules.S2Run
import ScrapePlugins.M.FoolSlide.Modules.SenseRun
import ScrapePlugins.M.FoolSlide.Modules.ShoujoSenseRun
import ScrapePlugins.M.FoolSlide.Modules.TripleSevenRun
import ScrapePlugins.M.FoolSlide.Modules.TwistedHelRun
import ScrapePlugins.M.FoolSlide.Modules.VortexRun
import ScrapePlugins.M.FoolSlide.Modules.MangazukiRun



import ScrapePlugins.M.MangaMadokami.Run
import ScrapePlugins.M.BooksMadokami.Run

# Convenience functions to make intervals clearer.
def days(num):
	return 60*60*24*num
def hours(num):
	return 60*60*num
def minutes(num):
	return 60*num

# Plugins in this dictionary are the active plugins. Comment out a plugin to disable it.
# plugin keys specify when plugins will start, and cannot be duplicates.
# All they do is specify the order in which plugins
# are run, initially, starting after 1-minue*{key} intervals
scrapePlugins = {
	0   : (ScrapePlugins.M.BtBaseManager.Run,                   hours( 1)),
	1   : (ScrapePlugins.M.MangaStreamLoader.Run,               hours( 6)),
	2   : (ScrapePlugins.M.BuMonitor.Run,                       hours( 1)),

	11  : (ScrapePlugins.M.McLoader.Run,                        hours(12)),  # every 12 hours, it's just a single scanlator site.
	12  : (ScrapePlugins.M.IrcGrabber.IrcEnqueueRun,            hours(12)),  # Queue up new items from IRC bots.
	13  : (ScrapePlugins.M.CxLoader.Run,                        hours(12)),  # every 12 hours, it's just a single scanlator site.
	15  : (ScrapePlugins.M.IrcGrabber.BotRunner,                hours( 1)),  # Irc bot never returns. It runs while the app is live. Rerun interval doesn't matter, as a result.
	16  : (ScrapePlugins.M.MangaHere.Run,                       hours(12)),
	17  : (ScrapePlugins.M.WebtoonLoader.Run,                   hours( 8)),
	18  : (ScrapePlugins.M.DynastyLoader.Run,                   hours( 8)),
	19  : (ScrapePlugins.M.KissLoader.Run,                      hours( 1)),
	20  : (ScrapePlugins.M.Crunchyroll.Run,                     hours( 4)),
	22  : (ScrapePlugins.M.Kawaii.Run,                          hours(12)),
	23  : (ScrapePlugins.M.ZenonLoader.Run,                     hours(24)),
	24  : (ScrapePlugins.M.MangaBox.Run,                        hours(12)),
	25  : (ScrapePlugins.M.YoMangaLoader.Run,                   hours(12)),
	26  : (ScrapePlugins.M.GameOfScanlationLoader.Run,          hours(12)),


	41  : (ScrapePlugins.H.HBrowseLoader.Run,                   hours( 2)),
	42  : (ScrapePlugins.H.PururinLoader.Run,                   hours( 2)),
	44  : (ScrapePlugins.H.NHentaiLoader.Run,                   hours( 2)),
	45  : (ScrapePlugins.H.SadPandaLoader.Run,                  hours(12)),
	46  : (ScrapePlugins.H.DjMoeLoader.Run,                     hours( 4)),
	47  : (ScrapePlugins.H.HitomiLoader.Run,                    hours( 4)),
	55  : (ScrapePlugins.H.DjMoeLoader.Retag,                   hours(24)),

	# FoolSlide modules

	61 : (ScrapePlugins.M.FoolSlide.Modules.CanisMajorRun,      hours(12)),
	62 : (ScrapePlugins.M.FoolSlide.Modules.ChibiMangaRun,      hours(12)),
	63 : (ScrapePlugins.M.FoolSlide.Modules.DokiRun,            hours(12)),
	64 : (ScrapePlugins.M.FoolSlide.Modules.GoMangaCoRun,       hours(12)),
	65 : (ScrapePlugins.M.FoolSlide.Modules.IlluminatiMangaRun, hours(12)),
	66 : (ScrapePlugins.M.FoolSlide.Modules.JaptemMangaRun,     hours(12)),
	67 : (ScrapePlugins.M.FoolSlide.Modules.MangatopiaRun,      hours(12)),
	68 : (ScrapePlugins.M.FoolSlide.Modules.RoseliaRun,         hours(12)),
	69 : (ScrapePlugins.M.FoolSlide.Modules.S2Run,              hours(12)),
	70 : (ScrapePlugins.M.FoolSlide.Modules.SenseRun,           hours(12)),
	71 : (ScrapePlugins.M.FoolSlide.Modules.ShoujoSenseRun,     hours(12)),
	72 : (ScrapePlugins.M.FoolSlide.Modules.TripleSevenRun,     hours(12)),
	73 : (ScrapePlugins.M.FoolSlide.Modules.TwistedHelRun,      hours(12)),
	74 : (ScrapePlugins.M.FoolSlide.Modules.VortexRun,          hours(12)),
	75 : (ScrapePlugins.M.FoolSlide.Modules.MangazukiRun,       hours(12)),

	80 : (ScrapePlugins.M.MangaMadokami.Run,                    hours(4)),
	81 : (ScrapePlugins.M.BooksMadokami.Run,                    hours(4)),

}


if __name__ == "__main__":

	# scrapePlugins = {
		# 0 : (TextScrape.BakaTsuki.Run,                       60*60*24*7),  # Every 7 days, because books is slow to update
		# 1 : (TextScrape.JapTem.Run,                          60*60*24*5),
		# 3 : (TextScrape.Guhehe.Run,                          60*60*24*5),
		# 2 : (TextScrape.ReTranslations.Run,                  60*60*24*1)   # There's not much to actually scrape here, and it's google, so I don't mind hitting their servers a bit.
	# }

	print("Test run!")
	import nameTools as nt

	def callGoOnClass(passedModule):
		print("Passed module = ", passedModule)
		print("Calling class = ", passedModule.Runner)
		instance = passedModule.Runner()
		instance.go()
		print("Instance:", instance)


	nt.dirNameProxy.startDirObservers()
	import signal
	import runStatus

	def signal_handler(dummy_signal, dummy_frame):
		if runStatus.run:
			runStatus.run = False
			print("Telling threads to stop (activePlugins)")
		else:
			print("Multiple keyboard interrupts. Raising")
			raise KeyboardInterrupt

	run = [
			ScrapePlugins.H.PururinLoader.Run,
			ScrapePlugins.H.NHentaiLoader.Run,
			ScrapePlugins.H.SadPandaLoader.Run,
			ScrapePlugins.H.DjMoeLoader.Run,
			ScrapePlugins.H.DjMoeLoader.Retag,
			ScrapePlugins.H.HitomiLoader.Run,
			ScrapePlugins.M.FoolSlide.Modules.CanisMajorRun,
			ScrapePlugins.M.FoolSlide.Modules.ChibiMangaRun,
			ScrapePlugins.M.FoolSlide.Modules.DokiRun,
			ScrapePlugins.M.FoolSlide.Modules.GoMangaCoRun,
			ScrapePlugins.M.FoolSlide.Modules.IlluminatiMangaRun,
			ScrapePlugins.M.FoolSlide.Modules.JaptemMangaRun,
			ScrapePlugins.M.FoolSlide.Modules.MangatopiaRun,
			ScrapePlugins.M.FoolSlide.Modules.RoseliaRun,
			ScrapePlugins.M.FoolSlide.Modules.S2Run,
			ScrapePlugins.M.FoolSlide.Modules.SenseRun,
			ScrapePlugins.M.FoolSlide.Modules.ShoujoSenseRun,
			ScrapePlugins.M.FoolSlide.Modules.TripleSevenRun,
			ScrapePlugins.M.FoolSlide.Modules.MangazukiRun,
			ScrapePlugins.M.MangaMadokami.Run,
			ScrapePlugins.M.BooksMadokami.Run,
			ScrapePlugins.M.CxLoader.Run,
			ScrapePlugins.M.ZenonLoader.Run,
			ScrapePlugins.M.FoolSlide.Modules.TwistedHelRun,
			ScrapePlugins.M.FoolSlide.Modules.VortexRun,
			ScrapePlugins.M.McLoader.Run,
			ScrapePlugins.M.MangaHere.Run,
			ScrapePlugins.M.WebtoonLoader.Run,
			ScrapePlugins.M.DynastyLoader.Run,
			ScrapePlugins.M.KissLoader.Run,
			ScrapePlugins.M.Crunchyroll.Run,
			ScrapePlugins.M.Kawaii.Run,
			ScrapePlugins.M.MangaBox.Run,
			ScrapePlugins.M.YoMangaLoader.Run,
			ScrapePlugins.M.GameOfScanlationLoader.Run,
			ScrapePlugins.H.HBrowseLoader.Run,
		]
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

			print("Loopin!", scrapePlugins)
			for plugin in run:
				print(plugin)
				try:
					callGoOnClass(plugin)
				except Exception:
					print()
					print("Wat?")
					traceback.print_exc()
					# raise
					print("Continuing on with next source.")

	except:
		traceback.print_exc()


	print("Complete")

	nt.dirNameProxy.stop()
	sys.exit()
