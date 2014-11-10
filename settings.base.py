
End-User setup (README):

replace all instances of "SOMETHING" with your own directory paths.
Add your username + password for each site.
Yes, this is all stored in plaintext. It's not high security.
You are not using the same password everywhere anyways, .... right?

# Note: Paths have to be absolute.
pickedDir        = r"/SOMETHING/MP"
newDir           = r"/SOMETHING/MN"
baseDir          = r"/SOMETHING/Manga/"

#
fufuDir          = r"/SOMETHING/H/Fufufuu"
djMoeDir         = r"/SOMETHING/H/DjMoe"
puRinDir         = r"/SOMETHING/H/Pururun"
ExhenMadokamiDir = r"/SOMETHING/H/ExhenMadokami"
fkDir            = r"/SOMETHING/H/Fakku"
hbDir            = r"/SOMETHING/H/H-Browse"
nhDir            = r"/SOMETHING/H/N-Hentai"
spDir            = r"/SOMETHING/H/ExHentai"

# Paths for database and web content
dbName           = '/SOMETHING/MangaCMS/links.db'
webCtntPath      = '/SOMETHING/MangaCMS/ctnt'
bookCachePath    = '/SOMETHING/MangaCMS/BookCache'


# Path to the directory of images that get auto-removed from archives on download.
badImageDir  = r"/SOMETHING/MangaCMS/removeImages"

# This is the path to the deduplication tool database API python file.
# and the file hashing python file.
# You only need to set this if you want to use the on-the-fly duplicate
# removal, which is complex and not fully finished at this time.
# You must have https://github.com/fake-name/IntraArchiveDeduplicator somewhere,
# and have allowed it to build a database of the extant local files for it to
# be of any use.
dedupApiFile = '/SOMETHING/Deduper/dbApi.py'
fileHasher   = '/SOMETHING/Deduper/hashFile.py'

# Folders to scan for folders to use as download paths.
# Directories are scanned by sorted keys
mangaFolders = {
	1 : {
			"dir" : pickedDir,
			"interval" : 5,
			"lastScan" : 0
		},
	10 : {
			"dir" : newDir,
			"interval" : 5,
			"lastScan" : 0
		},
	# Keys above 100 are not included in normal directory search behaviour
	100 : {
			"dir" : baseDir,
			"interval" : 45,
			"lastScan" : 0
		}
}


ratingsSort = {
	"thresh"  : 5,
	"tokey"   : 1,
	"fromkey" : [10, 12],
}

# Check that the ratingsSort values are valid by verifying they
# map to key present in the mangaVolders dict.
for key in ratingsSort['fromkey']:
	if key not in mangaFolders:
		raise ValueError("All fromKey values in ratingsSort must be present in the mangaFolders dict.")
if not ratingsSort['tokey'] in mangaFolders:
	raise ValueError("ratingsSort tokey must be present in the mangaFolders dict.")



tagHighlight = [
	"tags",
	"to",
	"highlight",
	"in",
	"the",
	"hentai"
	"table"
	]


skipTags = [
	'tags to not download'
]

noHighlightAddresses = [
	"IP Addresses which won't get the tag highlighting behaviour"
]


# IP range that is shown the hentai tables. In CIDR notation
pronWhiteList = '192.168.1.0/24'

# Directory of files/images that will be removed from any and all downloads.
badImageDir  = r"/somepath/dir"

# Manga Updates
buSettings = {
	"login"         : "username",
	"passWd"        : "password",
}



# ExHentai
sadPanda = {

	"login"         : "username",
	"passWd"        : "pass",

	"dlDir"        :  spDir,

	# Sadpanda searches to scrape, and tags which will not be downloaded
	"sadPandaSearches" :
	[
		'stuff'
	],

	"sadPandaExcludeTags" :
	[
		'other stuff'

	],

}



# Starkana.com
skSettings = {

	"login"         : "username",
	"passWd"        : "password",

	"dirs" : {
		"dlDir"         : pickedDir,
		"mnDir"         : newDir,
		"mDlDir"        : baseDir
		}

}
# Manga.Madokami
skSettings = {

	"login"         : "username",
	"passWd"        : "password",

	"dirs" : {
		"dlDir"         : pickedDir,
		"mDlDir"        : baseDir
		}

}

jzSettings = {


	"dirs" : {
		"dlDir"         : pickedDir,
		"mnDir"         : newDir,
		"mDlDir"        : baseDir
		}

}
mbSettings = {

	"dirs" : {
		"dlDir"         : pickedDir,
		"mnDir"         : newDir,
		"mDlDir"        : baseDir
		}

}

czSettings = {

	"dlDir"         : pickedDir,
	"mDlDir"        : baseDir,


	"dirs" : {
		"dlDir"         : pickedDir,
		"mDlDir"        : baseDir
		}

}


fuSettings = {
	"dlDir" :  fufuDir,
	"retag" : 60*60*24*31			# 1 month
}

djSettings = {
	"dlDir" :  djMoeDir,
	"retag" : 60*60*24*31			# 1 month
}

puSettings = {
	"dlDir"        :  puRinDir,
	"retag"        : 60*60*24*31,			# 1 month
	"retagMissing" : 60*60*24*7,				# 7 Days (This is for items that have *no* tags)
	"accountKey"   : "YOUR ACOCUNT KEY GOES HERE!"
}



emSettings = {
	"dlDir"        : ExhenMadokamiDir
}

fkSettings = {
	"dlDir"        :  fkDir
}

hbSettings = {
	"dlDir"        :  hbDir
}
nhSettings = {
	"dlDir"        :  nhDir
}


ircBot = {
	"name"           : "YOUR-BOT-NAME",
	"rName"          : "YOUR BOT REAL NAME",
	"unknown-series" : "WHERE TO PUT ITEMS FOR WHICH THE SERIES CANNOT BE INFERRED FROM THE TITLE",
	"pubmsg_prefix"  : "PREFIX TO MESSAGES TO THE BOT THAT CAUSES THE BOT TO SAY THEM ",
	"dlDir"          : pickedDir

}


# Your postgres SQL database credentials for the primary database.
# the DATABASE_USER must have write access to the database DATABASE_DB_NAME
DATABASE_USER    = "MangaCMSUser"
DATABASE_PASS    = "{yourpassword}"
DATABASE_DB_NAME = "MangaCMS"
DATABASE_IP      = "127.0.0.1"


# Your postgres SQL database credentials for the deduper.
# the PSQL_USER must have write access to the database PSQL_DB_NAME

PSQL_IP      = "server IP"
PSQL_PASS    = "password"

PSQL_USER    = "deduper"
PSQL_DB_NAME = "deduper_db"

