
End-User setup (README):

replace all instances of "SOMETHING" with your own directory paths.
Add your username + password for each site.
Yes, this is all stored in plaintext. It's not high security.
You are not using the same password everywhere anyways, .... right?

Delete all lines above and including this one before trying to run anything, please.

# Your postgres SQL database credentials for the primary database.
# the DATABASE_USER must have write access to the database DATABASE_DB_NAME
DATABASE_USER    = "MangaCMSUser"
DATABASE_PASS    = "password"
DATABASE_DB_NAME = "MangaCMS"
DATABASE_IP      = "127.0.0.1"
# Note that a local socket will be tried before the DATABASE_IP value, so if DATABASE_IP is
# invalid, it may work anyways.

# If you have a statsd instance, put it's IP here. Otherwise, just leave it at localhost or any routable IP
# UDP messages are sent to the address in question, but because they're UDP, pointing
# them at an address where no one is listening is harmless.
GRAPHITE_DB_IP = "127.0.0.1"

# Note: Paths have to be absolute.
pickedDir        = r"/SOMETHING/MP"
baseDir          = r"/SOMETHING/Manga/"
unlinkedDir      = r"/SOMETHING/MangaUnlinked/"

# The directory "Context" of all the hentai items.
# This determines the path mask that will be used when deduplicating
# hentai items.
# If you aren't running the deduper, just specify something basic, like "/"
mangaCmsHContext = r"/SOMETHING/H/"
fufuDir          = r"/SOMETHING/H/Fufufuu"
djMoeDir         = r"/SOMETHING/H/DjMoe"
puRinDir         = r"/SOMETHING/H/Pururin"
ExhenMadokamiDir = r"/SOMETHING/H/ExhenMadokami"
fkDir            = r"/SOMETHING/H/Fakku"
hbDir            = r"/SOMETHING/H/H-Browse"
nhDir            = r"/SOMETHING/H/N-Hentai"
spDir            = r"/SOMETHING/H/ExHentai"
tadanohitoDir    = r"/SOMETHING/H/Tadanohito"


globalDedupContext = [pickedDir, baseDir, unlinkedDir, mangaCmsHContext]

# Paths for database and web content
webCtntPath      = '/SOMETHING/MangaCMS/ctnt/oldCtnt'
webMvcPath       = '/SOMETHING/MangaCMS/ctnt/mvcCtnt'
staticCtntPath   = '/SOMETHING/MangaCMS/ctnt/staticContent'
bookCachePath    = '/SOMETHING/MangaCMS/BookCache'


# This is the path to the deduplication tool database API python file.
# and the file hashing python file.
# You only need to set this if you want to use the on-the-fly duplicate
# removal, which is complex and not fully finished at this time.
# You must have https://github.com/fake-name/IntraArchiveDeduplicator somewhere,
# and have allowed it to build a database of the extant local files for it to
# be of any use.
# TODO: Allow remote deduper addresses (right now, localhost is assumed).

# Folders to scan for folders to use as download paths.
# Directories are scanned by sorted keys
# the key 0 is special, and should not be used.
mangaFolders = {
	1 : {
			"dir" : pickedDir,
			"interval" : 5,
			"lastScan" : 0
		},
	10 : {
			"dir" : baseDir,
			"interval" : 5,
			"lastScan" : 0
		},
	# Keys above 100 are not included in normal directory search behaviour when
	# deciding where to place downloaded files (e.g. downloads will never be placed
	# in a directory with a key >= 100)
	#100 : {
	#		"dir" : baseDir,
	#		"interval" : 45,
	#		"lastScan" : 0
	#	}
}


ratingsSort = {
	"thresh"  : 2,    # At or greater then what rating is the automover is triggered.
	"tokey"   : 1,
	"fromkey" : [10],
}

# How long should entries in the logging table be kept for?
# Units are in seconds
maxLogAge = 60*60*24*3  # Keep logs for 3 days

# Check that the ratingsSort values are valid by verifying they
# map to key present in the mangaVolders dict.
for key in ratingsSort['fromkey']:
	if key not in mangaFolders:
		raise ValueError("All fromKey values in ratingsSort must be present in the mangaFolders dict.")
if not ratingsSort['tokey'] in mangaFolders:
	raise ValueError("ratingsSort tokey must be present in the mangaFolders dict.")


captcha_solvers = {
	"2captcha" : {
		'api_key' : "<KEY GOES HERE>"
	}

}


tagHighlight = [
	"tags",
	"to",
	"highlight",
	"in",
	"the",
	"hentai"
	"table"
	]


# Items with one of the tags in this list will be NOT downloaded.
skipTags = [
	'tags to not download'
]

tagNegativeHighlight = [
]

noHighlightAddresses = [
	# "IP Addresses which won't get the tag highlighting behaviour"
]



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

	# Exclude compound tags are slightly complex. Basically, if the first item is present,
	# and the second is *NOT*, the item will be filtered. In the below case, if something is tagged
	# "translated", and is not also tagged "english", it will be filtered (and not downloaded)
	"excludeCompoundTags" :
	[
		['translated', 'english']
	],

	# Categories to exclude
	"sadPandaExcludeCategories" :
	[
		"gamecg",
		'misc'
	]

}

# Extract contents of searches, and add them to the tag-highlight list.
for tag in sadPanda['sadPandaSearches']:
	tag = tag.split(":")[-1]
	tag = tag.replace(" ", "-")
	if tag not in tagHighlight:
		tagHighlight.append(tag)

# General Conf
noHighlightAddresses = [
	"10.1.1.47"
]

pronWhiteList = '10.1.1.0/24'


# Directory of files/images that will be removed from any and all downloads.
badImageDir  = r"/somepath/dir"

# When files are "deleted" through the web UI, they're moved here.
recycleBin = r'/media/Storage/MangaRecycleBin'


batotoSettings = {

	"login"         : "username",
	"passWd"        : "password",

}
suraSettings = {

	"login"         : "username",
	"passWd"        : "password",

}


# Manga.Madokami
mkSettings = {

	"login"         : "username",
	"passWd"        : "password",


	"dirs" : {
		"dlDir"         : pickedDir,
		"mDlDir"        : baseDir
		},

	# And settings for the automated upload system
	# "ftpAddr"             : "ftp.madokami.com",
	# "mainContainerDir"    : "/Manga",
	# "uploadContainerDir"  : "/Manga/_Autouploads",
	# "uploadDir"           : "Name this directory"

}

tadanohito = {

	"login"         : "username",
	"passWd"        : "password",

	'dlDir'         : tadanohitoDir,

}


mbSettings = {


	"dirs" : {
		"dlDir"         : pickedDir,
		"mDlDir"        : baseDir
		}

}


jzSettings = {


	"dirs" : {
		"dlDir"         : pickedDir,
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

# Manga Updates
buSettings = {
	"login"         : "username",
	"passWd"        : "password",
}

djSettings = {
	"dlDir"        : djMoeDir,
	"retag"        : 60*60*24*31,			# 1 month
	"retagMissing" : 60*60*24*1				# 7 Days (This is for items that have *no* tags)
}

puSettings = {
	"dlDir"        : puRinDir,
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


# Hat-tip to Penny arcade re:bot naming
ircBot = {
	"name"           : "YOUR-BOT-NAME",
	"rName"          : "YOUR BOT REAL NAME",
	"unknown-series" : "WHERE TO PUT ITEMS FOR WHICH THE SERIES CANNOT BE INFERRED FROM THE TITLE",
	"pubmsg_prefix"  : "PREFIX TO MESSAGES TO THE BOT THAT CAUSES THE BOT TO SAY THEM ",
	"dlDir"          : pickedDir

}


# Channels to ignore when looking for triggers in channel MOTDs.
ircMotdScraperMaskChannels = [
	'#bodzio'
]



