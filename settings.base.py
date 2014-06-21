
End-User setup (README):

replace all instances of "SOMETHING" with your own directory paths.
Add your username + password for each site.


# Note: Paths have to be absolute.
pickedDir   = r"/SOMETHING/MP"
newDir      = r"/SOMETHING/MN"
baseDir     = r"/SOMETHING/Manga/"

#
fufuDir     = r"/SOMETHING/H/Fufufuu"
djMoeDir    = r"/SOMETHING/H/DjMoe"

# Paths for database and web content
dbName      = '/SOMETHING/MangaCMS/links.db'
webCtntPath = '/SOMETHING/MangaCMS/ctnt'

# Folders to scan for folders to use as download paths.
# Directories are scanned by sorted keys


badImageDir  = r"/SOMETHING/MangaCMS/removeImages"

# Why do I have two instances of each directory path here?
# TODO: Clean the config structure up!
mangaFolders = {
	1 : {
			"dir" : pickedDir,
			"interval" : 5,
			"lastScan" : 0
		},
	2 : {
			"dir" : newDir,
			"interval" : 5,
			"lastScan" : 0
		},
	10 : {
			"dir" : baseDir,
			"interval" : 45,
			"lastScan" : 0
		}
}

mtSettings = {

	"login"         : "username",
	"passWd"        : "password",

	"dlDir"         : pickedDir,
	"mDlDir"        : baseDir,

	"watchedFeedNo" : "your_user_ID",

	"dirs" : {
		"dlDir"         : pickedDir,
		"mnDir"         : newDir,
		"mDlDir"        : baseDir
		}

}

skSettings = {

	"login"         : "username",
	"passWd"        : "password",

	"dlDir"         : pickedDir,
	"mDlDir"        : baseDir,


	"dirs" : {
		"dlDir"         : pickedDir,
		"mnDir"         : newDir,
		"mDlDir"        : baseDir
		}

}

buSettings = {
	"login"         : "username",
	"passWd"        : "password",
}

fuSettings = {
	"dlDir" :  fufuDir,
	"retag" : 60*60*24*31			# 1 month
}

djSettings = {
	"dlDir" :  djMoeDir,
	"retag" : 60*60*24*31			# 1 month
}
