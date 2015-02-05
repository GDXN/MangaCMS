## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%namespace name="ut"              file="utilities.mako"/>
<html>
<head>
	<meta charset="utf-8">
	<title>WAT WAT IN THE BATT</title>
	${ut.headerBase()}
</head>

<%startTime = time.time()%>

<%namespace name="sideBar" file="gensidebar.mako"/>

<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path

from operator import itemgetter

import nameTools as nt

colours = {
	# Download Status
	"failed"          : "000000",
	"no matching dir" : "FF9999",
	"moved"           : "FFFF99",
	"downloaded"      : "99FF99",
	"processing"      : "9999FF",
	"queued"          : "FF77FF",
	"created-dir"     : "FFE4B2",
	"not checked"     : "FFFFFF",

	# Categories

	"valid category"  : "FFFFFF",
	"bad category"    : "999999"}

import logging

logger =  logging.getLogger("Main.WebSrv")



%>

<%



def updateNameDBifneeded():

	# If there is a pageArg that tells us to replace a value in the DB, do that
	# e.g. replaces item with a baseName of originalName with the value of newName

	print("request.params", request.params)

	with sqlCon.cursor() as cur:
		if 'target' in request.params and request.params['target'] == "mu-mt":
			if 'originalName' in request.params and  'newName' in request.params and  'columnName' in request.params:

				columnName = request.params['columnName']
				oldName = request.params['originalName']
				newName = request.params['newName']

				logger.info("Changing column '%s' from '%s' to '%s'", columnName, oldName, newName)

				validColumns = ["mangaUpdates", "mangaTraders"]
				if columnName not in validColumns:
					print("Invalid column!")
					return False
				else:

					cur.execute('UPDATE mangaNameMappings SET %s=? WHERE %s=?;' % (columnName, columnName), (newName, oldName))
					print(cur.fetchall())
					sqlCon.commit()

					return True

			elif 'muName' in request.params and 'mtName' in request.params:
				if 'delete' in request.params:
					print("Should Delete!")
					muName = request.params['muName']
					mtName = request.params['mtName']
					logger.info("deleting name-mapping: mu - %s -> mt - %s", muName, mtName)

					cur.execute(u"DELETE FROM mangaNameMappings WHERE mangaUpdates=? AND mangaTraders=?;", (muName, mtName))
					print(cur.fetchall())
					sqlCon.commit()

				elif 'add' in request.params:

					muName = request.params['muName']
					mtName = request.params['mtName']
					logger.info("Adding new name-mapping item: mu - %s -> mt - %s", muName, mtName)

					cur.execute('INSERT INTO mangaNameMappings VALUES (?, ?);', (muName, mtName))
					print(cur.fetchall())
					sqlCon.commit()
				else:
					print("wut")
		elif 'target' in request.params and request.params['target'] == "mt-dir":
			if 'originalName' in request.params and  'newName' in request.params and  'columnName' in request.params:

				columnName = request.params['columnName'].rstrip().lstrip()
				oldName = request.params['originalName'].rstrip().lstrip()
				newName = request.params['newName'].rstrip().lstrip()

				logger.info("Changing column '%s' from '%s' to '%s'", columnName, oldName, newName)

				validColumns = ["baseName", "folderName"]
				if columnName not in validColumns:
					print("Invalid column!")
					return False
				else:

					cur.execute('UPDATE folderNameMappings SET %s=? WHERE %s=?;' % (columnName, columnName), (newName, oldName))
					print(cur.fetchall())
					sqlCon.commit()

					return True

			elif 'muName' in request.params and 'mtName' in request.params:
				if 'delete' in request.params:
					print("Should Delete!")
					muName = request.params['muName'].rstrip().lstrip()
					mtName = request.params['mtName'].rstrip().lstrip()
					logger.info("deleting name-mapping: mu - %s -> mt - %s", muName, mtName)

					cur.execute(u"DELETE FROM folderNameMappings WHERE baseName=? AND folderName=?;", (muName, mtName))
					print(cur.fetchall())
					sqlCon.commit()

				elif 'add' in request.params:

					muName = nt.sanitizeString(request.params['muName'])
					mtName = request.params['mtName'].rstrip().lstrip()
					logger.info("Adding new name-mapping item: base - %s -> dir - %s", muName, mtName)

					cur.execute('INSERT INTO folderNameMappings VALUES (?, ?);', (muName, mtName))
					print(cur.fetchall())
					sqlCon.commit()
				else:
					print("wut")

		else:
			print('target' in request.params)
			logger.warning("Didn't know how to parse GET args!")

nameFixer = {}
# checkInitDB()
updateNameDBifneeded()

print("DirsLookup = ",  nt.dirsLookup.items)

# for key, value in nt.nameLookup.iteritems():
# 	print(key, " - ", value)
%>




<%def name="genNameMappingTable()">
	<table border="1px" style="width:1000px;">
		<tr>
				<th class="uncoloured padded" width="450">MangaUpdates Name</th>
				<th class="uncoloured padded" width="450">MangaTraders Name</th>
				<th class="uncoloured padded" width="30">Del</th>
		</tr>

		% for key, value in nt.nameLookup.iteritems():
			<tr>

				<td>
					<form>
						<input type="hidden" name="target", value="mu-mt">
						<input type="hidden" name="columnName", value="mangaUpdates">
						<input type="hidden" name="originalName", value="${key}">
						<input type="text"   name="newName",      value="${key}" size=53>
						<input type="submit" value="Go">


					</form>
				</td>
				<td>
					<form>
						<input type="hidden" name="target", value="mu-mt">
						<input type="hidden" name="columnName", value="mangaTraders">
						<input type="hidden" name="originalName", value="${value}">
						<input type="text"   name="newName",      value="${value}" size=50>
						<input type="submit" value="Go">
					</form>
				</td>
				<td>

					<form>
						<input type="hidden" name="target", value="mu-mt">
						<input type="hidden" name="muName", value="${key}">
						<input type="hidden" name="mtName", value="${value}">
						<input type="hidden" name="delete", value="True">
						<input type="submit" value="X">
					</form>
				</td>
			</tr>
		% endfor

	</table>
</%def>

<%def name="genFolderMappingTable()">
	<table border="1px" style="width:1000px;">
		<tr>
				<th class="uncoloured padded" width="450">Base Item Name</th>
				<th class="uncoloured padded" width="450">Directory Name</th>
				<th class="uncoloured padded" width="30">Del</th>
		</tr>

		% for key, value in nt.dirsLookup.iteritems():
			<tr>

				<td>
					<form>
						<input type="hidden" name="target", value="mt-dir">
						<input type="hidden" name="columnName", value="baseName">
						<input type="hidden" name="originalName", value="${key | h}">
						<input type="text"   name="newName",      value="${key | h}" size=53>
						<input type="submit" value="Go">


					</form>
				</td>
				<td>
					<form>
						<input type="hidden" name="target", value="mt-dir">
						<input type="hidden" name="columnName", value="folderName">
						<input type="hidden" name="originalName", value="${value | h}">
						<input type="text"   name="newName",      value="${value | h}" size=50>
						<input type="submit" value="Go">
					</form>
				</td>
				<td>

					<form>
						<input type="hidden" name="target", value="mt-dir">
						<input type="hidden" name="muName", value="${key | h}">
						<input type="hidden" name="mtName", value="${value | h}">
						<input type="hidden" name="delete", value="True">
						<input type="submit" value="X">
					</form>
				</td>
			</tr>
		% endfor

	</table>
</%def>



<%

# ------------------------------------------------------------------------
# This is the top of the main
# page generation section.
# Execution begins here
# ------------------------------------------------------------------------






items = {}





%>

<body>

<div>

	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv" style="width:1020px;">

		<div class="subdiv mtMainId">
			<div class="contentdiv">
				<h3>MangaUpdates → MangaTraders name mappings</h3>


				<div>
					<form>
						Add new item:
						<input type="hidden" name="add", value="True">
						<input type="hidden" name="target", value="mu-mt">
						<div style="display: inline-block;">
							<table>
								<tr>
									<td>MangaUpdates Name = </td>
									<td><input type="text" name="muName", value="" size=50></td>
								</tr>
								<tr>
									<td>MangaTraders Name = </td>
									<td><input type="text" name="mtName", value="" size=50></td>
								</tr>
							</table>
						</div>
						<input type="submit" value="Add">
					</form>
				</div>
				<hr>
				${genNameMappingTable()}
				<hr>
				<h3>Base Name → Folder Name name mappings</h3>
					<form>
						Add new item:
						<input type="hidden" name="add", value="True">
						<input type="hidden" name="target", value="mt-dir">
						<div style="display: inline-block;">
							<table>
								<tr>
									<td>BaseName = </td>
									<td><input type="text" name="muName", value="" size=50></td>
								</tr>
								<tr>
									<td>FolderName = </td>
									<td><input type="text" name="mtName", value="" size=50></td>
								</tr>
							</table>
						</div>
						<input type="submit" value="Add">
					</form>
				${genFolderMappingTable()}
			</div>
		</div>

	</div>
<div>


<%
stopTime = time.time()
timeDelta = stopTime - startTime
%>

<p>This page rendered in ${timeDelta} seconds.</p>

</body>
</html>