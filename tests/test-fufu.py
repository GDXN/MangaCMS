
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

# import ScrapePlugins.H.FufufuuLoader.Run
import nameTools as nt
from ScrapePlugins.H.FufufuuLoader.fufufuDbLoader import FuFuFuuDbLoader
from ScrapePlugins.H.FufufuuLoader.fufufuContentLoader import FuFuFuuContentLoader
from ScrapePlugins.H.FufufuuLoader.Run import Runner
from ScrapePlugins.H.FufufuuLoader.Retag import Runner as TagRunner

import signal
import runStatus

def signal_handler(dummy_signal, dummy_frame):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt


def test():

	signal.signal(signal.SIGINT, signal_handler)
	# print(ScrapePlugins.H.FufufuuLoader.Run)
	# runner = ScrapePlugins.H.FufufuuLoader.Run.Runner()

	# dbInt = FuFuFuuDbLoader()
	# dbInt.go()
	# clInt = FuFuFuuContentLoader()

	dbInt = Runner()
	dbInt.go()

	tRun = TagRunner()
	tRun.go()



	# # runner.setup()

	# # dlLink = "http://fufufuu.net/m/12683/heavens-door/"

	# # runner.cl.log.info("Resetting stuck downloads in DB")
	# # runner.cl.conn.execute('UPDATE fufufuu SET downloaded=0, processing=1 WHERE dlLink=?;', (dlLink, ))
	# # runner.cl.conn.commit()
	# # runner.cl.log.info("Download reset complete")

	# # runner.cl.downloadItem({"dlLink" : dlLink})
	# # runner.loadNewFiles()
	# runner.setup()
	# for x in range(0, 450):
	# 	runner.checkFeed(pageOverride=x)
	# #runner.loadNewFiles()

	nt.dirNameProxy.stop()

if __name__ == "__main__":
	test()
