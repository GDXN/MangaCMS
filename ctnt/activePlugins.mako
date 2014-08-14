<%!

#
# Module level members can be accessed via
# {modulename}.attr.{membername}
#

#import colorsys

# List of visually distinct colours
# Note: these /will/ suck for colour-blind people. Sorry about that.
# TODO: Generate these in an automated manner. Somehow
# Creating visually distinct colours is /hard/
spacedColours = [
	(0xff, 0x8c, 0x8c),
	(0xff, 0xab, 0x8c),
	(0xff, 0xba, 0x8c),
	(0x8c, 0xff, 0xab),
	(0xf7, 0xff, 0x8c),
	(0x8c, 0xff, 0xd9),
	(0x8c, 0xff, 0xf7),
	(0xff, 0xd9, 0x8c),
	(0x9c, 0x8c, 0xff),
	(0xc9, 0xff, 0x8c),
	(0xd9, 0x8c, 0xff),
	(0x8c, 0xba, 0xff),
	(0xff, 0x8c, 0xe8),
	(0x8c, 0xe8, 0xff),
	(0xff, 0x8c, 0xba)
]


sidebarItemList = [
		{
			"num"           : 1,
			'dbKey'         : "SkLoader",
			'name'          : "Starkana",
			'dictKey'       : "sk",
			'cssClass'      : "skId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : True,
			'type'          : 'Manga'
		},

		{
			"num"           : 2,
			'dbKey'         : "CzLoader",
			'name'          : "Crazy's Manga",
			'dictKey'       : "cz",
			'cssClass'      : "czId",
			'showOnHome'    : True,
			'renderSideBar' : False,
			'genRow'        : True,
			'type'          : 'Manga'
		},

		{
			"num"           : 3,
			'dbKey'         : "MbLoader",
			'name'          : "MangaBaby",
			'dictKey'       : "mb",
			'cssClass'      : "mbId",
			'showOnHome'    : True,
			'renderSideBar' : False,
			'genRow'        : True,
			'type'          : 'Manga-defunct'
		},

		{
			"num"           : 4,
			'dbKey'         : "BtLoader",
			'name'          : "Batoto",
			'dictKey'       : "bt",
			'cssClass'      : "btId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : True,
			'type'          : 'Manga'
		},

		{
			"num"           : 5,
			'dbKey'         : "JzLoader",
			'name'          : "Japanzai",
			'dictKey'       : "jz",
			'cssClass'      : "jzId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : True,
			'type'          : 'Manga'
		},

		{
			"num"           : 6,
			'dbKey'         : "McLoader",
			'name'          : "MangaCow",
			'dictKey'       : "mc",
			'cssClass'      : "mcId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : True,
			'type'          : 'Manga'
		},

		{
			"num"           : 7,
			'dbKey'         : "MkLoader",
			'name'          : "Madokami",
			'dictKey'       : "mk",
			'cssClass'      : "mkId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : True,
			'type'          : 'Manga'
		},

		{
			"num"           : 8,
			'dbKey'         : "BuMon",
			'name'          : "MU Mon",
			'dictKey'       : None,
			'cssClass'      : "buId",
			'showOnHome'    : False,
			'renderSideBar' : False,
			'genRow'        : False,
			'type'          : 'Info'
		},

		{
			"num"           : 9,
			'dbKey'         : False,
			'name'          : "Mt Mon",
			'dictKey'       : None,
			'cssClass'      : "mtMonId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : False,
			'type'          : 'Manga-defunct'
		},

		{
			"num"           : 10,
			'dbKey'         : "DjMoe",
			'name'          : "DjMoe",
			'dictKey'       : "djm",
			'cssClass'      : "btId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : True,
			'type'          : 'Porn'
		},

		{
			"num"           : 11,
			'dbKey'         : "Pururin",
			'name'          : "Pururin",
			'dictKey'       : "pu",
			'cssClass'      : "puId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : True,
			'type'          : 'Porn'
		},

		{
			"num"           : 12,
			'dbKey'         : "EmLoader",
			'name'          : "ExHenMado",
			'dictKey'       : "em",
			'cssClass'      : "emId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : True,
			'type'          : 'Porn'
		},

		{
			"num"           : 13,
			'dbKey'         : "FkLoader",
			'name'          : "Fakku",
			'dictKey'       : "fk",
			'cssClass'      : "fkId",
			'showOnHome'    : True,
			'renderSideBar' : True,
			'genRow'        : True,
			'type'          : 'Porn'
		}

	]


def tupToHSV(tup):
	r, g, b = (var*(1.0/256) for var in tup)
	return colorsys.rgb_to_hsv(r, g, b)

def hsvToHex(ftup):
	ftup = colorsys.hsv_to_rgb(*ftup)
	r, g, b = (max(0, min(int(var*256), 255)) for var in ftup)
	ret = "#{r:02x}{g:02x}{b:02x}".format(r=r, g=g, b=b)
	return ret

import colorsys

keys = []
for index, item in enumerate(sidebarItemList):

	keys.append((item["num"], index))

keys.sort()

for dummy_num, idx in keys:
	h, s, v = tupToHSV(spacedColours[idx % len(spacedColours)])

	baseC = (h,s,v)
	light1 = (h,s,v+0.6)
	light2 = (h,s,v+0.4)

	sidebarItemList[idx]["baseColour"] = hsvToHex(baseC)
	sidebarItemList[idx]["evenRow"] = hsvToHex(light1)
	sidebarItemList[idx]["oddRow"] = hsvToHex(light2)

inHomepageMangaTable = [item["dictKey"] for item in sidebarItemList if item["showOnHome"] and "Manga" in item["type"]]
activeNonPorn        = [item["dictKey"] for item in sidebarItemList if                        "Manga" in item["type"]]
activePorn           = [item["dictKey"] for item in sidebarItemList if                        "Porn"  in item["type"]]

%>
