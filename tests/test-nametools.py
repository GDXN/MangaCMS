
import logSetup
logSetup.initLogging()

import unittest
import nameTools as nt




class TestSequenceFunctions(unittest.TestCase):
	def setUp(self):

		test_data = [
			"Kotoura-san ",
			"Koukaku no Pandora - Ghost Urn ",
			"Koukaku no Regios - Missing Mail ",
			"Kounago Sensei ",
			"Kouya ni Kemono Doukokusu [Stalled]",
			"Kubera ",
			"Kumo no Graduale ",
			"Kunisaki Izumo no Jijou",
			"Kuraudo (NOUJOU Junichi) ",
			"Kurenai no Ookami to Ashikase no Hitsuji [WTF]",
			"Kurogane Hime",
			"Kurogane Pukapuka Tai",
			"Kurogane ",
			"Kurogane [IKEZAWA Haruto] ",
			"Kurogane no Linebarrel ",
			"Kurosagi The Black Swindler ",
			"Kuroyome ",
			"Kurozakuro [Stalled]",
			"Kutsuzure Sensen ",
			"Kuusou Kagaku Edison ",
			"Kyoshiro to Towa no Sora ",
			"Kyoukai Senjou no Rinbo ",
			"Kyoumen no Silhouette ",
			"Neko Ane ",
			"Rescue Me",
			"Maken Ki ",
			"REverSAL ",
			"Kyuusen no Shima",
			"Silva [c24]"
		]
		nt.dirNameProxy.manuallyLoadDirDict(test_data)



	def test_choice(self):
		print("Verifying directory linking mechanism")
		assert(nt.dirNameProxy["Kurogane"]["fqPath"] != None)
		assert(nt.dirNameProxy["Kyoumen no Silhouette"]["fqPath"] != None)
		assert(nt.dirNameProxy["Neko Ane "]["fqPath"] != None)
		assert(nt.dirNameProxy["Rescue Me"]["fqPath"] != None)
		assert(nt.dirNameProxy["Maken Ki!"]["fqPath"] != None)
		assert(nt.dirNameProxy[":REverSAL"]["fqPath"] != None)
		assert(nt.dirNameProxy["Silva"]["fqPath"] != None)
		assert(nt.dirNameProxy["Kouya ni Kemono Doukokusu"]["fqPath"] != None)
		assert(nt.dirNameProxy["Koukaku no Regios - Missing Mail"]["fqPath"] != None)
		assert(nt.dirNameProxy["Kuraudo (NOUJOU Junichi) "]["fqPath"] != None)

def test():
	unittest.main()

if __name__ == "__main__":
	test()
