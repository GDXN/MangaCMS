
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


	def getUrlFormat1(self, page):
		indiceQuery = re.compile(r'var next_first_visible = (\d+);')
		jsFrag1     = re.compile(r" ajax_root: '/ajax/\?req=RpcApiManga_GetMangaCollectionCarouselPage',.+?},.+callback: function\(resp\)", re.DOTALL)
		indice = indiceQuery.search(page)
		frag   = jsFrag1.search(page)
		if not indice or not frag:
			return []

		paramRe = re.compile(r'params_obj: ({.+})', re.DOTALL)
		urlParams = paramRe.search(frag.group(0))
		if not urlParams:
			return []


		# YAML insists on a space after a colon. Since our intput is
		# really a js literal which doesn't need (or have) those spaces,
		# we fudge the space in to make PyYAML not error.
		params = urlParams.group(1).replace(":", ": ")
		params = yaml.load(params)
		params['first_index'] = indice.group(1)
		params['req'] = "RpcApiManga_GetMangaCollectionCarouselPage"
		ajaxUrl = '%s?%s' % (self.ajaxRoot, urllib.parse.urlencode(params))
		return [ajaxUrl]

	def getUrlFormat2(self, page):
		jsFrag2     = re.compile(r"{\W+req:'RpcApiManga_GetMangaCollectionCarousel',.*?}", re.DOTALL)

		link_all = jsFrag2.findall(page)
		ret = []
		for item in link_all:
			params = item.replace(":", ": ")
			try:
				params = yaml.load(params)
				# print(params)
				params['req'] = "RpcApiManga_GetMangaCollectionCarousel"
				ajaxUrl = '%s?%s' % (self.ajaxRoot, urllib.parse.urlencode(params))
				ret.append(ajaxUrl)
			except (ValueError, yaml.parser.ParserError):
				# print("Failed parsing: ", params)
				pass

		return ret

	def extractItemPage(self, page):
		# Extract the information needed to determine the ajax call that will let us get the
		# recent items for the series.
		if not page:
			return False

		urls = self.getUrlFormat1(page) + self.getUrlFormat2(page)
		urls = [url for url in urls if url]
		# http://www.crunchyroll.com/ajax/?req=RpcApiManga_GetMangaCollectionCarouselPage&media_type=manga&first_index=4&volume_id=1139&series_id=397&manga_premium
		# http://www.crunchyroll.com/ajax/?req=RpcApiManga_GetMangaCollectionCarousel&volume_id=1139&series_id=397&locale=enUS&media_type=manga&manga_premium

		ret = []
		for url in urls:
			tmp = self.wg.getpage(url)
			if tmp:
				ret.append(tmp)
		if not page:
			return False

		return ret

	def extractUrl(self, page):
		# print(page)
		mangaCarousels = self.extractItemPage(page)
		if not mangaCarousels:
			return False

		ret = []
		for mangaCarousel in mangaCarousels:
			# There is some XSS (I think?) blocking stuff, namely the whole AJAX response is
			# wrapped in comments to protect from certain parsing attacks or something?
			# ANyways, get rid of that.
			mangaCarousel = mangaCarousel.replace("/*-secure-", "").replace("*/", "")
			data = json.loads(mangaCarousel)
			if data['result_code'] != 1:
				# Failure?
				continue

			if not data['data']:
				continue

			# print(data['data'].keys())

			if isinstance(data['data'], str):
				raw = data['data']
			else:
				raw = ''.join(data['data'].values())


			soup = bs4.BeautifulSoup(raw, "lxml")
			links = soup.find_all("a")

			for link in links:
				if 'comics_read' in link['href']:
					link = urllib.parse.urljoin(self.urlBase, link['href'])
					ret.append(link)

		return list(set(ret))


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
		# run.parseItem('http://www.crunchyroll.com/comics/manga/tales-of-wedding-rings/volumes')


