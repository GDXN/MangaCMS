

if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()


import ScrapePlugins.FufufuuLoader.Run
import ScrapePlugins.FufufuuLoader.Retag
import ScrapePlugins.BuMonitor.Run
import ScrapePlugins.DjMoeLoader.Run
import ScrapePlugins.DjMoeLoader.Retag
import ScrapePlugins.SkBaseManager.Run
import ScrapePlugins.CzLoader.Run
import ScrapePlugins.MbLoader.Run
import ScrapePlugins.BtBaseManager.Run
import ScrapePlugins.PururinLoader.Run
import ScrapePlugins.JzLoader.Run


# Plugins in this dictionary are the active plugins. Comment out a plugin to disable it.
# plugin keys are not important, but cannot be duplicates. All they do is specify the order in which plugins
# are run, initially, spaced by 1-minue intervals
scrapePlugins = {
	0  : (ScrapePlugins.BtBaseManager.Run,    60*60),
	1  : (ScrapePlugins.BuMonitor.Run,        60*60),
	2  : (ScrapePlugins.FufufuuLoader.Run,    60*45),
	#  3 : (ScrapePlugins.FufufuuLoader.Retag,  60*60),
	4  : (ScrapePlugins.DjMoeLoader.Run,      60*45),
	5  : (ScrapePlugins.DjMoeLoader.Retag,    60*60),
	6  : (ScrapePlugins.CzLoader.Run,         60*60*4),   # Every 4 hours, since I have to scrape a lot of pages to update properly
	7  : (ScrapePlugins.SkBaseManager.Run,    60*60),
	8  : (ScrapePlugins.MbLoader.Run,         60*60),
	9  : (ScrapePlugins.PururinLoader.Run,    60*60),
	10 : (ScrapePlugins.JzLoader.Run,         60*60*8)   # Every 8 hours, since I have to scrape a lot of pages, and it's not a high-volume source anyways
}



if __name__ == "__main__":

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
	except:
		traceback.print_exc()

	print("Complete")

	nt.dirNameProxy.stop()
	sys.exit()
