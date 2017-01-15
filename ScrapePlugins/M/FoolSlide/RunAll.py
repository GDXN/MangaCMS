



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
import utilities.testBase as tb

modules = [
	ScrapePlugins.M.FoolSlide.Modules.CanisMajorRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.ChibiMangaRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.DokiRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.GoMangaCoRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.IlluminatiMangaRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.JaptemMangaRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.MangatopiaRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.RoseliaRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.S2Run.Runner,
	ScrapePlugins.M.FoolSlide.Modules.SenseRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.ShoujoSenseRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.TripleSevenRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.TwistedHelRun.Runner,
	ScrapePlugins.M.FoolSlide.Modules.VortexRun.Runner,
]

if __name__ == '__main__':

	with tb.testSetup():
		for module in modules:
			mod = module()
			mod.go()

