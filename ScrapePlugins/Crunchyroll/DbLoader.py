
import webFunctions

import re
import settings
import yaml
import json
import urllib.parse
import time
import bs4

import ScrapePlugins.RetreivalDbBase


#  ##      ##    ###    ########  ##    ## #### ##    ##  ######
#  ##  ##  ##   ## ##   ##     ## ###   ##  ##  ###   ## ##    ##
#  ##  ##  ##  ##   ##  ##     ## ####  ##  ##  ####  ## ##
#  ##  ##  ## ##     ## ########  ## ## ##  ##  ## ## ## ##   ####
#  ##  ##  ## ######### ##   ##   ##  ####  ##  ##  #### ##    ##
#  ##  ##  ## ##     ## ##    ##  ##   ###  ##  ##   ### ##    ##
#   ###  ###  ##     ## ##     ## ##    ## #### ##    ##  ######
#
# This plugin's codebase is HORRIBLE!
# This is largely a consequence of the fact that crunchyroll uses a
# frankly ridiculous amount of ajax and javascript bullshit to build
# EVERY page. As a result, the pages are not really parseable without
# either a full-on javascript engine, or doing things with regexes
# that are more or less crimes against humanity.
#
# Since I don't like javascript, I've opted for the later. Be warned.
#

class DbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.CrunchyRoll.Fl"
	pluginName = "CrunchyRoll Link Retreiver"
	tableKey    = "cr"
	urlBase = "http://www.crunchyroll.com/"
	urlFeed = "http://www.crunchyroll.com/comics/manga/updated"
	ajaxRoot = "http://www.crunchyroll.com/ajax/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"



	def getInfo(self, inMarkup):
		ret = {}
		soup = bs4.BeautifulSoup(inMarkup, "lxml")
		header = soup.find("h1", class_='ellipsis')

		# Remove the leading breadcrumb link
		header.a.decompose()

		name = header.get_text()
		name = name.lstrip("> ").strip()


		ret["seriesName"] = name
		ret['retreivalTime'] = time.time()

		return ret



	def extractItemPage(self, page):
		# Extract the information needed to determine the ajax call that will let us get the
		# recent items for the series.
		if not page:
			return False

		indiceQuery = re.compile(r'var next_first_visible = (\d+);')
		jsFrag      = re.compile(r" ajax_root: '/ajax/\?req=RpcApiManga_GetMangaCollectionCarouselPage',.+?},.+callback: function\(resp\)", re.DOTALL)


		indice = indiceQuery.search(page)
		frag   = jsFrag.search(page)
		if not indice or not frag:
			return None

		paramRe = re.compile(r'params_obj: ({.+})', re.DOTALL)
		urlParams = paramRe.search(frag.group(0))
		if not urlParams:
			return None


		# YAML insists on a space after a colon. Since our intput is
		# really a js literal which doesn't need (or have) those spaces,
		# we fudge the space in to make PyYAML not error.
		params = urlParams.group(1).replace(":", ": ")
		params = yaml.load(params)
		params['first_index'] = indice.group(1)
		params['req'] = "RpcApiManga_GetMangaCollectionCarouselPage"
		ajaxUrl = '%s?%s' % (self.ajaxRoot, urllib.parse.urlencode(params))


		page = self.wg.getpage(ajaxUrl)
		if not page:
			return False

		return page

	def extractUrl(self, page):

		mangaCarousel = self.extractItemPage(page)
		if not mangaCarousel:
			return False

		# There is some XSS (I think?) blocking stuff, namely the whole AJAX response is
		# wrapped in comments to protect from certain parsing attacks or something?
		# ANyways, get rid of that.
		mangaCarousel = mangaCarousel.replace("/*-secure-", "").replace("*/", "")
		data = json.loads(mangaCarousel)
		if data['result_code'] != 1:
			# Failure?
			return False

		if not data['data']:
			return False

		# print(data['data'].keys())


		raw = ''.join(data['data'].values())


		soup = bs4.BeautifulSoup(raw, "lxml")
		links = soup.find_all("a")

		ret = []
		for link in links:
			if 'comics_read' in link['href']:
				link = urllib.parse.urljoin(self.urlBase, link['href'])
				ret.append(link)

		return ret


	def parseItem(self, pageUrl):

		page = self.wg.getpage(pageUrl)
		info = self.getInfo(page)

		ctntUrl = self.extractUrl(page)
		if not ctntUrl:
			return []

		ret = []
		for url in ctntUrl:

			item = {'sourceUrl':url}
			item.update(info)

			ret.append(item)

		self.log.info("Found %s accessible items on page!", len(ret))
		for item in ret:
			self.log.info("	Item: '%s'", item)

		return ret

	def getFeed(self):

		soup = self.wg.getSoup(self.urlFeed)

		if not soup:
			return []

		mainDiv = soup.find("div", id="main_content")
		lis = mainDiv.find_all("li", class_='group-item')

		ret = []
		for listItem in lis:
			itemUrl = urllib.parse.urljoin(self.urlBase, listItem.a['href'])

			for item in self.parseItem(itemUrl):
				ret.append(item)

		return ret





	def go(self):
		self.resetStuckItems()
		dat = self.getFeed()


		self.processLinksIntoDB(dat)




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		# getHistory()
		run = DbLoader()
		# run.getFeed()
		run.go()


