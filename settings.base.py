


pickedDir = r"/SOMETHING/MP"
newDir = r"/SOMETHING/MN"
baseDir = r"/SOMETHING/Manga/"


# Folders to scan for folders to use as download paths.
# Directories are scanned by sorted keys

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

oldDbName =   '/script_location/links.db'
dbName =      '/script_location/links.db'
webCtntPath = '/script_location/ctnt'

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

buSettings = {
	"login"         : "username",
	"passWd"        : "password",
}

fuSettings = {
	"dlDir" :  r"/SOMETHING/H/Fufufuu",
	"retag" : 60*60*24*31			# 1 month
}

djSettings = {
	"dlDir" :  r"/SOMETHING/H/DjMoe",
	"retag" : 60*60*24*31			# 1 month
}
