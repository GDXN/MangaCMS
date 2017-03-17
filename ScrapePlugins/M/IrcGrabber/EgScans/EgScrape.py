


import webFunctions
import re
import yaml
import json

import time

import runStatus
import settings
import pickle


import ScrapePlugins.M.IrcGrabber.IrcQueueBase


class EgTriggerLoader(ScrapePlugins.M.IrcGrabber.IrcQueueBase.IrcQueueBase):



	loggerPath = "Main.Manga.Eg.Fl"
	pluginName = "Eg-Scans Link Retreiver"
	tableKey = "irc-irh"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	feedUrl = "http://xdcc.egscans.com/search.php?nick=EasyBot"

	extractRe = re.compile(r"p\.k\[\d+\] = ({.*?});")

	# def getItemFromLine(self, line):
	# 	match = self.extractRe.search(line)
	# 	if not match:
	# 		raise ValueError("No data found in line %s" % line)
	# 	data = match.group(1)

	# 	data = data.replace(":", ": ")
	# 	data = yaml.safe_load(data)
	# 	print("Data", data)
	# 	pass

	def getMainItems(self, rangeOverride=None, rangeOffset=None):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading EgScans Main Feed")

		ret = []

		url = self.feedUrl
		page = self.wg.getpage(url)
		page = page.strip()
		matches = self.extractRe.findall(page)
		yamlData = "[%s]" % (", ".join(matches))

		# we need to massage the markup a bit to make it parseable by PyYAML.
		# Basically, the raw data looks like:
		# {b:"Suzume", n:2180, s:7, f:"Chinatsu_no_Uta_ch23_[VISCANS].rar"};
		# but {nnn}:{nnn} is not valid, YAML requires a space after the ":"
		# Therefore, we just replace ":" with ": "
		yamlData = yamlData.replace(":", ": ")

		self.log.info("Doing YAML data load")
		data = yaml.load(yamlData, Loader=yaml.CLoader)

		for item in data:
			item["server"] = "irchighway"
			item["channel"] = "eg"

			# rename a few keys that are rather confusing
			item["size"] = item.pop("s")
			item["pkgNum"] = item.pop("n")
			item["botName"] = item.pop("b")
			item["fName"] = item.pop("f")

			# I'm using the filename+botname for the unique key to the database.
			itemKey = item["fName"]+item["botName"]

			item = json.dumps(item)
			ret.append((itemKey, item))

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break


		self.log.info("All data loaded")
		return ret







