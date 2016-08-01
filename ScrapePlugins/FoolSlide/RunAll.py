



import ScrapePlugins.FoolSlide.Modules.CanisMajorRun
import ScrapePlugins.FoolSlide.Modules.ChibiMangaRun
import ScrapePlugins.FoolSlide.Modules.DokiRun
import ScrapePlugins.FoolSlide.Modules.GoMangaCoRun
import ScrapePlugins.FoolSlide.Modules.IlluminatiMangaRun
import ScrapePlugins.FoolSlide.Modules.JaptemMangaRun
import ScrapePlugins.FoolSlide.Modules.MangatopiaRun
import ScrapePlugins.FoolSlide.Modules.RoseliaRun
import ScrapePlugins.FoolSlide.Modules.S2Run
import ScrapePlugins.FoolSlide.Modules.SenseRun
import ScrapePlugins.FoolSlide.Modules.ShoujoSenseRun
import ScrapePlugins.FoolSlide.Modules.TripleSevenRun
import ScrapePlugins.FoolSlide.Modules.TwistedHelRun
import ScrapePlugins.FoolSlide.Modules.VortexRun
import utilities.testBase as tb

modules = [
	ScrapePlugins.FoolSlide.Modules.CanisMajorRun.Runner,
	ScrapePlugins.FoolSlide.Modules.ChibiMangaRun.Runner,
	ScrapePlugins.FoolSlide.Modules.DokiRun.Runner,
	ScrapePlugins.FoolSlide.Modules.GoMangaCoRun.Runner,
	ScrapePlugins.FoolSlide.Modules.IlluminatiMangaRun.Runner,
	ScrapePlugins.FoolSlide.Modules.JaptemMangaRun.Runner,
	ScrapePlugins.FoolSlide.Modules.MangatopiaRun.Runner,
	ScrapePlugins.FoolSlide.Modules.RoseliaRun.Runner,
	ScrapePlugins.FoolSlide.Modules.S2Run.Runner,
	ScrapePlugins.FoolSlide.Modules.SenseRun.Runner,
	ScrapePlugins.FoolSlide.Modules.ShoujoSenseRun.Runner,
	ScrapePlugins.FoolSlide.Modules.TripleSevenRun.Runner,
	ScrapePlugins.FoolSlide.Modules.TwistedHelRun.Runner,
	ScrapePlugins.FoolSlide.Modules.VortexRun.Runner,
]

if __name__ == '__main__':

	with tb.testSetup():
		for module in modules:
			mod = module()
			mod.go()

