<%!

#
# Module level members can be accessed via
# {modulename}.attr.{membername}
#
sidebarItemList = [
		{
			'dbKey'      : "SkLoader",
			'name'       : "Starkana",
			'dictKey'    : "sk",
			'cssClass'   : "skId",
			'baseColour' : "#BBBBFF",
			'evenRow'    : "#ddddff",
			'oddRow'     : "#f5f5ff",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Manga'
		},

		{
			'dbKey'      : "CzLoader",
			'name'       : "Crazy's Manga",
			'dictKey'    : "cz",
			'cssClass'   : "czId",
			'baseColour' : "#BBFFBB",
			'evenRow'    : "#ddffdd",
			'oddRow'     : "#f5fff5",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Manga'
		},

		{
			'dbKey'      : "MbLoader",
			'name'       : "MangaBaby",
			'dictKey'    : "mb",
			'cssClass'   : "mbId",
			'baseColour' : "#FFBBBB",
			'evenRow'    : "#ffdddd",
			'oddRow'     : "#fff5f5",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Manga'
		},

		{
			'dbKey'      : "BtLoader",
			'name'       : "Batoto",
			'dictKey'    : "bt",
			'cssClass'   : "btId",
			'baseColour' : "#FFFFC5",
			'evenRow'    : "#FFFFDB",
			'oddRow'     : "#FFFFC5",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Manga'
		},

		{
			'dbKey'      : "JzLoader",
			'name'       : "Japanzai",
			'dictKey'    : "jz",
			'cssClass'   : "jzId",
			'baseColour' : "#B5FFFC",
			'evenRow'    : "#CEFFFD",
			'oddRow'     : "#F2FFFE",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Manga'
		},

		{
			'dbKey'      : "JzLoader",
			'name'       : "MangaCow",
			'dictKey'    : "mc",
			'cssClass'   : "mcId",
			'baseColour' : "#B5FFFC",
			'evenRow'    : "#CEFFFD",
			'oddRow'     : "#F2FFFE",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Manga'
		},

		{
			'dbKey'      : "MkLoader",
			'name'       : "Madokami",
			'dictKey'    : "mk",
			'cssClass'   : "mkId",
			'baseColour' : "FFF",
			'evenRow'    : "#FFE7C4",
			'oddRow'     : "#FFF1DE",
			'showOnHome' : False,
			'genRow'     : True,
			'type'       : 'Manga'
		},

		{
			'dbKey'      : "BuMon",
			'name'       : "MU Mon",
			'dictKey'    : None,
			'cssClass'   : "buId",
			'baseColour' : "#BBFFBB",
			'genRow'     : False,
			'type'       : 'Info'
		},

		{
			'dbKey'      : False,
			'name'       : "Mt Mon",
			'dictKey'    : None,
			'cssClass'   : "mtMonId",
			'baseColour' : "#FFF79A;",
			'evenRow'    : "#dddddd",
			'oddRow'     : "#f5f5f5",
			'showOnHome' : True,
			'genRow'     : False,
			'type'       : 'Manga-defunct'
		},

		{
			'dbKey'      : "DjMoe",
			'name'       : "DjMoe",
			'dictKey'    : "djm",
			'cssClass'   : "btId",
			'baseColour' : "#EE99EE",
			'evenRow'    : "#ddffdd",
			'oddRow'     : "#f5fff5",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Porn'
		},

		{
			'dbKey'      : "Pururin",
			'name'       : "Pururin",
			'dictKey'    : "pu",
			'cssClass'   : "puId",
			'baseColour' : "#BBFFFF",
			'evenRow'    : "#ffdddd",
			'oddRow'     : "#fff5f5",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Porn'
		},

		{
			'dbKey'      : "EmLoader",
			'name'       : "ExHenMado",
			'dictKey'    : "em",
			'cssClass'   : "emId",
			'baseColour' : "#BBFFBB",
			'evenRow'    : "#FFE7C4",
			'oddRow'     : "#FFF1DE",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Porn'
		},

		{
			'dbKey'      : "FkLoader",
			'name'       : "Fakku",
			'dictKey'    : "fk",
			'cssClass'   : "fkId",
			'baseColour' : "#FFBE85",
			'evenRow'    : "#ddddff",
			'oddRow'     : "#f5f5ff",
			'showOnHome' : True,
			'genRow'     : True,
			'type'       : 'Porn'
		}

	]

inHomepageMangaTable = ["bt", "sk", "cz", "mb", "jz", "mk", "mc"]
activeNonPorn        = ["bt", "sk", "cz", "mb", "jz", "mk", "mt", "mc"]
activePorn           = ["pu", "fu", "djm", "em", "fk"]

%>
