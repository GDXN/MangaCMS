
import webFunctions
import runStatus

import calendar
import bs4
from dateutil import parser
import urllib.parse
import settings

import time

blockedIDs = [
	"3", "4", "6", "14", "20", "21", "24", "29", "37", "52", "204", "204", "237", "308", "327", "327", "455", "471",
	"593", "603", "671", "849", "970", "1012", "1170", "1266", "1296", "1360", "1383", "1391", "1394", "1402",
	"1428", "1433", "1436", "1440", "1452", "1454", "1468", "1587", "1611", "1613", "1644", "1653", "1658",
	"1700", "1857", "1862", "1869", "1896", "1912", "1924", "1943", "1962", "1974", "1987", "2035", "2050",
	"2065", "2099", "2100", "2110", "2123", "2190", "2206", "2228", "2235", "2244", "2292", "2338", "2376",
	"2424", "2479", "2507", "2509", "2527", "2559", "2573", "2574", "2606", "2644", "2680", "2748", "2760",
	"2769", "2824", "2843", "2844", "2881", "2894", "2909", "3023", "3151", "3246", "3308", "3311", "3324",
	"3328", "3337", "3445", "3476", "3479", "3484", "3507", "3524", "3559", "3602", "3675", "3681", "3704",
	"3706", "3707", "3716", "3718", "3719", "3720", "3721", "3724", "3732", "3755", "3804", "3805", "3806",
	"3832", "3851", "3864", "3919", "4057", "4077", "4136", "4141", "4142", "4166", "4183", "4199", "4200",
	"4227", "4228", "4273", "4329", "4386", "4399", "4407", "4425", "4458", "4474", "4491", "4508", "4522",
	"4524", "4540", "4550", "4564", "4591", "4602", "4639", "4652", "4735", "4756", "4791", "4806", "4821",
	"4876", "4876", "4879", "4893", "4894", "4895", "4898", "5016", "5018", "5022", "5025", "5064", "5065",
	"5084", "5103", "5113", "5117", "5133", "5139", "5143", "5168", "5210", "5261", "5309", "5319", "5352",
	"5377", "5382", "5416", "5431", "5479", "5560", "5584", "5585", "5586", "5593", "5601", "5602", "5603",
	"5674", "5704", "5718", "5736", "5804", "5824", "5848", "5911", "5915", "6052", "6113", "6128", "6139",
	"6162", "6246", "6290", "6291", "6299", "6325", "6490", "6537", "6614", "6665", "6804", "6806", "6918",
	"6964", "6989", "7041", "7047", "7451", "7538", "7682", "7752", "7803", "8692", "9221", "9448", "9800",
	"9846", "9847"
]


import ScrapePlugins.MonitorDbBase
import ScrapePlugins.MtMonitor.Inserter


class MtWatchMonitor(ScrapePlugins.MonitorDbBase.MonitorDbBase):


	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Mt.Watcher"
	pluginName = "MangaTraders Series Watcher"
	tableName = "mt"
	dbName = settings.dbName
	urlBase = "http://www.mangatraders.com/"



	def go(self):
		self.really_go()

	def really_go(self, idOverride=None, limit=None):
		self.inserter = ScrapePlugins.MtMonitor.Inserter.Inserter()

		self.checkLogin()
		self.downloadNewFiles(idOverride=idOverride, limit=limit)

		self.inserter.closeDB()
		self.inserter = None

	def downloadNewFiles(self, idOverride=None, limit=None):


		self.log.info("Done. Fetching relevant manga IDs")

		if not idOverride:
			ids = self.getMangaIDs()
		else:
			self.log.warning("ID Overridden")
			ids = idOverride

		# print("Manga IDs = ")
		# for mId in ids:
		# 	print("		", mId)

		newIDs = self.filterDownloadIDs(ids)
		self.log.info("Done. Processing IDs.")


		idRet = 0
		for mId in newIDs:
			self.getMangaFilesForID(mId)
			if not runStatus.run:
				self.log.info( "Breaking MOAR due to exit flag being set")
				break
			if limit and idRet > limit :
				self.log.info( "Breaking MOAR due to retreival limit being set")
				break

			idRet += 1

		self.wg.saveCookies()

	def getMangaIDs(self):

		profileUrl = urllib.parse.urljoin(self.urlBase, "profile/612668/profile")
		pageCtnt = self.wg.getpage(profileUrl)

		items = set()

		pgSoup = bs4.BeautifulSoup(pageCtnt)


		watched = pgSoup.find("div", id="watch_list")


		if not watched:	# Exit for 404 errors
			return []

		watched = watched.find_all("a", target="_blank")


		for item in watched:
			mangaID = urllib.parse.urljoin(self.urlBase, item["href"]).split("/")[-1]
			if mangaID:
				items.add(mangaID)

		self.log.info("Found %d watched items.", len(items))

		# I have no idea why this search doesn't work. It's valid syntax, and it works when I
		# test it outside of this context
		# favorite = pgSoup.find("div", id="favorites_list")


		allLinks = pgSoup.find_all("a", target="_blank")

		for item in allLinks:

			mangaID = urllib.parse.urljoin(self.urlBase, item["href"]).split("/")[-1]

			try:
				int(mangaID)
				items.add(mangaID)

				if mangaID:
					#print "Favorite = ", urlparse.urljoin(self.urlBase, item["href"]).split("/")[-1]
					items.add(mangaID)
			except ValueError:
				# Dunno what this is, but there is always one instance of it.
				if mangaID != "p-98XDV-1ukMJdc":
					self.log.error("Invalid manga ID = %s", mangaID)

		items = list(items)
		items.sort()
		return items

	def filterDownloadIDs(self, mangaIDs):


		haveIDs = self.getColumnItems("mtId")

		newIDs = []
		oldIDs = []
		for item in mangaIDs:
			if not item in haveIDs and not item in blockedIDs:
				newIDs.append(item)
			if not item in blockedIDs:
				oldIDs.append(item)
			else:
				self.log.info("No-DL Manga ID = %s" % item)
		self.log.info("New Manga IDs:")
		for item in newIDs:
			self.log.info("	%s", item)
		self.log.info("Already have %d items.", len(set(oldIDs)))
		# for item in oldIDs:
		# 	self.log.info("	%s", item)
		return newIDs

	def getMangaFilesForID(self, mangaID):

		fileUrl = urllib.parse.urljoin(self.urlBase, "/manga/series/%s/files" % mangaID)

		self.log.info("Getting manga base-page at: %s", fileUrl)

		pageCtnt = self.wg.getpage(fileUrl)
		soup = bs4.BeautifulSoup(pageCtnt)

		if not soup.root.file:
			self.log.warning("No contents at page!")
			return

		seriesName = soup.root.file.cat_disp.string

		self.log.info("SeriesName - %s", seriesName)

		rows = self.getRowsByValue(buName=seriesName)
		if not rows:
			self.log.info("Did not have item in database. Adding new item.")
			self.insertIntoDb(mtId=mangaID, itemAdded=time.time())
			rows = self.getRowsByValue(mtId=mangaID)
		else:
			self.log.info("Had item in database. Adding to existing item.")

		# print("matching items in dict:", rows)

		if len(rows) != 1:
			raise ValueError("WAT?")
		rowId = rows.pop()["dbId"]



		updatedDate = 0

		haveAllFiles = True
		toRetreive = []
		fileBlocks = soup.find_all("file")
		for fileBlock in fileBlocks:
			tmp = [fileBlock.fileid.string, fileBlock.file_disp.string]
			if not bool(fileBlock.downloaded.string):
				toRetreive.append(tmp)
			haveAllFiles &= bool(fileBlock.downloaded.string)

			addDate = calendar.timegm(parser.parse(fileBlock.file_add_date.string).utctimetuple())
			if addDate > updatedDate:
				updatedDate = addDate

		if haveAllFiles:
			self.log.info("Do not need to download any of %s files.", len(fileBlocks))

			if not mangaID:
				raise ValueError("Trying to insert empty item!")


			# cur.execute('INSERT INTO MtMonitoredIDs VALUES(?, ?, ?, ?, ?);',(mangaID, time.time(), seriesName, len(fileBlocks), updatedDate))
			# self.conn.commit()

		else:
			seriesName = soup.file.cat_disp.string
			fileName = soup.file.file_disp.string
			for fileID, fileName in toRetreive:

				sourceUrl = "http://www.mangatraders.com/download/file/%s" % fileID
				self.inserter.insertItems(sourceUrl, fileName, seriesName, mangaID)


				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break


		self.updateDbEntry(rowId, mtId=mangaID, mtName=seriesName, lastChanged=updatedDate)

	def checkLogin(self):
		for cookie in self.wg.cj:
			if "SMFCookie232" in str(cookie):   # We have a log-in cookie
				return True

		self.log.info( "Getting Login cookie")
		logondict = {"login-user" : settings.mtSettings["login"], "login-pass" : settings.mtSettings["passWd"], "rememberme" : "on"}
		self.wg.getpage('http://www.mangatraders.com/login/processlogin', postData=logondict)

		self.wg.saveCookies()
