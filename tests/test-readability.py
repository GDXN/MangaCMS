
import logSetup
# if __name__ == "__main__":
# 	logSetup.initLogging()


import runStatus
runStatus.preloadDicts = False

from TextScrape.BakaTsuki.tsukiScrape import TsukiScrape
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

	wg = webFunctions.WebGetRobust()

	# pg = wg.getpage("http://japtem.com/")
	pg = wg.getpage("http://japtem.com/knm-volume-11-chapter-5/")


	soup = bs4.BeautifulSoup(pg, "lxml")
	strip = ['slider-container', 'secondarymenu-container', 'mainmenu-container', 'mobile-menu', 'footer', 'sidebar', 'disqus_thread', 'sharedaddy', 'scrollUp']
	for rm in strip:
		[tag.decompose() for tag in soup.find_all("div", class_=rm)]
		[tag.decompose() for tag in soup.find_all("select", class_=rm)]
		[tag.decompose() for tag in soup.find_all("div", id=rm)]

	pg = soup.prettify()
	doc = readability.readability.Document(pg, positive_keywords=['main_content'])
	doc.parse()
	print(doc.title())
	# content = doc.content()

	# soup = bs4.BeautifulSoup(content, "lxml")
	# out = soup.prettify()

	# print(out)


if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		pass
		# import nameTools as nt
		# nt.dirNameProxy.stop()

