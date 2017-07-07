
import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time

import urllib.parse
import html.parser
import zipfile
import runStatus
import traceback
import bs4
import re

from concurrent.futures import ThreadPoolExecutor

import processDownload




def checkLogin(wg):

	soup = wg.getSoup("https://bato.to/forums/index.php?app=core&module=global&section=login")
	userl = soup.find("a", id='user_link')
	if userl and "Welcome, {}".format(settings.batotoSettings['login']) in userl.get_text():
		return True

	auth_key = soup.find("input", attrs={"name":'auth_key'})

	login_data = {
		"auth_key" :     auth_key['value'],
		"ips_username" : settings.batotoSettings['login'],
		"ips_password" : settings.batotoSettings['passWd'],
		"rememberMe" :   "1",
		}

	login = wg.getSoup("https://bato.to/forums/index.php?app=core&module=global&section=login&do=process", postData=login_data)


	userl = login.find("a", id='user_link')
	if userl and "Welcome, {}".format(settings.batotoSettings['login']) in userl.get_text():
		print("Logged in successfully")
		return True
	raise ValueError("Failed to log in!")
