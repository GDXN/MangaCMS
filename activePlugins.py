

if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()


import ScrapePlugins.MtBaseManager.Run
import ScrapePlugins.FufufuuLoader.Run
import ScrapePlugins.FufufuuLoader.Retag
import ScrapePlugins.BuMonitor.Run
import ScrapePlugins.DjMoeLoader.Run
import ScrapePlugins.DjMoeLoader.Retag

scrapePlugins = {
	# 0 : (ScrapePlugins.MtBaseManager.Run,    60*75),
	1 : (ScrapePlugins.BuMonitor.Run,        60*60),
	2 : (ScrapePlugins.FufufuuLoader.Run,    60*45),
	3 : (ScrapePlugins.FufufuuLoader.Retag,  60*60),
	4 : (ScrapePlugins.DjMoeLoader.Run,      60*45),
	5 : (ScrapePlugins.DjMoeLoader.Retag,    60*60)
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
