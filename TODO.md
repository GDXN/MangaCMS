New LN Trans groups:
 - http://www.princerevolution.org/
 - http://solitarytranslation.wordpress.com/
 - http://krytykal.org/
 - Series system: http://lndb.info/

 - lookup page: http://bato.to/forums/topic/19625-where-can-i-find-recommendations/

Todo:
 - h rating system
 - gin on h tags
 - deduper expose get matching archives for spiral
 - del json response undefined
 - volume regex for highlighting misbehaving


 - Damaged Archive remover

 - ~~readability performance~~ The problem is entirely levenshtein distance calculation. Huh.
 - info table position when multiple sources
 - volumeifacator

 - Proper to-download series system

 - autotrim empty dirs

 - Trigger full series download if a series is seen by a scraper, and the local directory is both found, and rated above a threshold (Done for Batoto, needs per-plugin work. Add facilities to pluginBase?)
 - Trigger series download if on any BU list as well (partial)

 - base nt off muid system
 - ability to browse dirs by mu list cross-link

 - select 201 to determine next page
 - add half star rating options
 - h tag collation system
 - consolidation system for h tags
 - out of row colours
 - linebreaks in long filenames in reader popup need work
 - zoom mode indicator for smart mode in reader
 - ability to specify MU id in directory name? [Lnnn] or sommat?
 - way to search for non linked directories - maybe then do levenshtein search for match?
 - import all existing files somehow
 - do some clever set shit to check for misplaced items in directories
 - color code mangaupdates status in reader

 - scan times to deduper for rescanning. Also filesizes
 - Group the smaller scanlators into a single colour-code?
 - artist and author in filebrowser if i have it
 - bu page opens in new window
 - IRC grabber needs a transfer stall timeout.
 - Modularize the side-bar in the manga browser, so the plugins can each provide their own lookup interface if they present the correct API (should be automatically discovered, ideally).
 - Potential race-condition in deduper when two things are scanned by separate threads simultaneously. Add a global "deletion" lock to prevent accidental removal of all copies of file
 - Prevent full base dir refresh on directory rename.
 - prioritize downloads by rating
 - tagging in web interface
 - properly show if things are one shot
 - fork daiz numbering

 - steal code from free manga downloader?

 - most common image browse and filtering system
 	'SELECT COUNT(itemhash), itemhash FROM dedupitems GROUP BY itemhash;'

Deduper R2:

 - deduper spiral out to significant intersections on new scan (Depends on new cleaned-up deduper system)
 - phash filter by resolution for deletion decision
 - Image entropy is not useful for quantifying image ancestry

Long Term:

 - cover images in file browser?
 - Ability to disable bulk-downloading.
 - Get Watermark-Stripping system running.



<b>Add Scrapers for</b>

 - Manga
 	- MangaPark.com 
 	 - TONIGOBE
	 - http://www.netcomics.com/ - Maybe?
	 - https://www.emanga.com/ - Maybe?
	 - http://tapastic.com/series/browse ?
	 - /ak/ scans (Problematic, as there is no central release point)
	 - `http://crimson-flower.blogspot.com/p/release-archive.html` (hosted on `http://translations.omarissister.com/`)
	 - ~~Tadanohito as a H source~~
	 - ~~webtoons reader~~
	 - ~~http://nhentai.net/~~ They don't recompress (I think). Awesome!
	 - ~~KissManga.com~~
	 - ~~Dynasty Scans~~
	 - ~~webtoons.com~~
	 - ~~http://www.hbrowse.com/ as a H source~~
	 - ~~http://lonemanga.com/~~
	 - ~~http://egscans.com/~~ (Via IRC)
	 - ~~redhawkscans.com~~
	 - ~~mangajoy~~
	 - ~~http://www.cxcscans.com/~~
	 - ~~http://desperatescanners.weebly.com/~~ (They release on batoto)
	 - ~~imangascans~~ (Done, as part of IRC scraper)

 - Light Novels

	 - ~~Re:Translations (Note: Will mean I'll have to interface with Google Docs - Interesting challenge?)~~ Just used the HTML export feature. Laaaaazy
	 - ~~Baka-Tsuki~~
	 - ~~JapTem~~

<b>Reader</b>

 - fit width only if oversize?
 - make zoom mode pop up last longer
 - fancy fade out when toolbars hidden?
 - Add ability to rename directories to reader (res, name)
 - Add current page position bar when popup menus are visible.
 - Trigger directory cache update if a non-existent directory access is attempted
 - ~~smart zoom mode in overlay~~
 - ~~Make zoom mode a bit more intelligent (e.g. look at aspect ratio to guess zoom mode).~~
 - ~~show current image info~~
 - ~~Chapter read to from BU in item sidebar.~~
 -

<b>File System Organization</b>

 - Coerce directory structure to match MangaUpdates naming.
 - Scrape ALL MangaUpdates metadata, and use that to group series when different sources use different naming schemes. (WIP)
 - Automatically organize and sort directories so each series only has one directory. Aggregate multiple directories so they're named in accord with MangaUpdates
naming approach. Note <b> this makes MangaUpdates the final authority on what to refer to series as. Deal with it</b>

</p>

<b>Nametools Issues</b>

 - ~~Getsurin ni Kiri Saku~~
 - ~~Imasugu Onii-chan ni Imouto da tte Iitai!~~
 -
Bad MangaUpdates Links:

 - I think these are fixed by the latest NameTools patches.
	 - ~~Dungeon ni Deai wo Motomeru no wa Machigatteiru Darou ka~~
	 - ~~neko ane~~
	 - ~~rescue me~~
	 - ~~maken-ki!~~
	 - ~~murcielago~~
	 - ~~Keyman - The Hand of Judgement~~
	 - ~~Okusama ga Seito Kaichou! [+++][EE] npt linking~~
	 - ~~Log Horizon - Nishikaze no Ryodan not linking properly~~
	 - ~~'Hero Co., Ltd.' link only working one way~~
 - ~~Add testing to nametool system~~ (Done, wasn't the problem source)
 - ~~Everything is getting sorted into '[zion]'~~ Fixed, it was a scraper bug. Derp


Things to search for:

Partial series:
	 - 15:14 -!- Irssi: Starting query in Rizon with Sola
	 - 15:14 <Sola> hi hello ok
	 - 15:14 <Sola> Kamisama no Iutoori Ni is missing 50-74 and 76
	 - 15:15 <Sola> soul cartel 127, 134, 135
	 - 15:15 <Sola> tiara 31-34, 37-41
	 - 15:15 <Sola> Hayate no Gotoku!  c454-460 and c473
	 - 15:16 <Sola> Grappler Baki c94
	 - 15:29 <Sola> Himouto! Umaru-chan 41, 42, 44-65, 70,
	 - 15:32 <Sola> Maken-Ki! 66-68
	 - 15:38 <Sola> is all for today
	 - 15:42 <Sola> is pasting the list for duplicates so far, yes?
	 - 15:43 <Sola> I realize Crunchyroll is a special case but... whatever. I listed it too
	 - 15:43 <Sola> 13-nin no Short Suspense and Horror - KissManga, Batoto, MangaCow, IIII
	 - 15:43 <Sola> Akame ga Kill - PSY, BatotoIIII
	 - 15:43 <Sola> Ansatsu Kyoushitsu - Batoto, MangaJoyIIII
	 - 15:43 <Sola> Ao Haru Ride - MangaJoy, BatotoIIII
	 - 15:43 <Sola> Ao no Exorcist - S2S, KissManga, MangaJoyIIII
	 - 15:43 <Sola> Bartender - Batoto, MangaJoy, KissMangaIIII
	 - 15:43 <Sola> Black Haze - MangaJoy, Batoto, KissManga, MangaCowIIII
	 - 15:43 <Sola> Blind Faith Descent - MangaCow, KissMangaIIII
	 - 15:43 <Sola> Cavalier of the Abyss - VISCANS, MangaCowIIII
	 - 15:43 <Sola> Fairy Tail - MangaStream, Crunchyroll, KissMangaIIII
	 - 15:43 <Sola> Grappler Baki - KissManga, MangaJoy, BatotoIIII
	 - 15:43 <Sola> Himouto! Umaru-chan - Batoto, KissMangaIII
	 - 15:43 <Sola> Hirunaka no Ryuusei - MangaJoy, BatotoIIII
	 - 15:43 <Sola> Karate Shoukoushi Kohinata Minoru - Batoto, KissMangaIIII
	 - 15:43 <Sola> Kero Kero Chime - Batoto, KissMangaIIII
	 - 15:43 <Sola> Magical Exam Student - Webtoons.com, KissManga, MangaJoyIIII
	 - 15:43 <Sola> Maken-Ki! - Batoto, KissMangaIIII
	 - 15:43 <Sola> Metronome - Batoto, KissMangaIIII
	 - 15:43 <Sola> Nanatsu no Taizai - Crunchyroll, Batoto, KissMangaIIII
	 - 15:43 <Sola> Noah - Batoto, MangaJoyII
	 - 15:43 <Sola> Noragami - MangaJoy, KissMangaIIII
	 - 15:43 <Sola> Okitenemuru - Crunchyroll, KissMangaIIII
	 - 15:43 <Sola> Ore ga Ojou-sama - MangaJoy, BatotoIIII
	 - 15:43 <Sola> Pure-Mari - Batoto, KissManga, MangaJoyIIII
	 - 15:43 <Sola> Sailor Fuku, Tokidoki Apron - MangaBox, MangaJoyIIII
	 - 15:43 <Sola> Senyuu. - Batoto, KissManga, MangaJoyIIII
	 - 15:43 <Sola> Soul Cartel - KissManga, MangaCowIII
	 - 15:43 <Sola> Tonari no Kashiwagi-san Batoto, MangaJoyIIII
	 - 15:43 <Sola> Tonari no Seki-kun - Batoto, MangaJoyIIII
	 - 15:43 <Sola> Yamada-kun to 7-nin no Majo - Crunchyroll, MangaJoy, KissMangaIIII









<b>Complete:</b>
 - ~~Tadanohito cl sync cookies before run~~
 - ~~Delete items via web interface!~~
 - ~~sort all by rating~~ Had already done it. Huh.
 - ~~highlight chapters < 10~~
 - ~~Deduper not blocking queries while tree is rebuilt~~
 - ~~special case bolding so it only applies in aggregate views~~
 - ~~crawl all batoto~~
 - ~~change startup. start webserver first~~
 - ~~change db table generation to use found item paths for tables in directory view.~~
 - ~~strip trailing hyphens~~
 - ~~mixed case tag issues~~
 - ~~books are broken again~~ Dicked about in the scheduler. Hopefully, it's fixed?
 - ~~positive tags in green~~
 - ~~include h in mu tag view~~
 - ~~homepage table do not include deduped~~
 - ~~negative h keywords red~~
 - ~~Deduper - enable the ability to check for duplicates using phash as well. (Partial - Needs ability to search by hamming distance to work properly)~~
 - ~~bu page and rating page columns are backwards~~
 - ~~bu tag browser already~~
 - ~~mechanism for highlighting chosen tags in table (specifically deduped in J)~~
 - ~~Add failed item introspection table.~~
 - ~~ability to browse dirs by rating~~
 - ~~ability to browse by mu tags~~
 - ~~synonyms without exclamation points~~
 - ~~Madokami is fucked again. Fuck you HTTPS simple auth.~~
 - ~~chap regex prefer ch or c prefix~~
 - ~~string difference system for books~~
 - ~~tsuki has issues?~~
 - ~~unlinked autouploads broken~~
 - ~~Deduper - Move database interface into scanner, one interface per thread.
	Make each archive scan a transaction.~~
 - ~~mu tag browser - GiN/GiST index?~~
 - ~~ex filter by category too~~
 - ~~random h already updated tag~~ It's actually from the source. Not much
 	I can do.
 - ~~fix djmoe~~
 - ~~rescan series on batoto~~
 - ~~booktrie nodes decrease in size~~ (Whoops, CSS Stupid)
 - ~~rating changing is broken~~
 - ~~"None"s in btSeries markup~~ Stupid context issue
 - ~~kissmanga phash dedup~~
 - ~~move non matching dirs to another folder~~
 - ~~add ability to sort directory by rating.~~ (Added in MangaUpdates stuff, not sure if I want it elsewhere)
 - ~~filesize in browser~~
 - ~~different tag for phash desuplication~~
 - ~~fakku broken.~~
 - ~~hbrowse missing artists amd title truncated~~
 - ~~Batoto doesn't list every file in the recent updates page. Scan into series pages~~ Doing more thorough search
 - ~~Move to python-sql for dynamic sql generation~~
 - ~~reset download button in mangatable for specific key view~~
 - ~~filtered h isn't being properly skipped~~
 - ~~fix pururin page ordering already~~ It was a sorting issue in the session system? Fuuuuuuuuuuck.
 - ~~Migrate to new queries from tests.test-Queries~~ Superceeded by procedural queries using server-side cursors.
 - ~~tag/flag for when items are mirrored to mk?~~ DlState=3 means uploaded
 - ~~fakku is broken?~~ Fixed
 - ~~Load tables asynchronously from base page~~
 - ~~dlstate 3 not rendering right~~
 - ~~have vol and chap in separate columns~~
 - ~~key not found error resulting in HTTP 500 for bad path after rating change~~
 - ~~colons in seriesnames~~ Should already be removed. Not sure what's going on
 - ~~sorter not properly handling items with only volume number in filename (generally prepended by "volume {xxx}").~~
 - ~~mk uploader needs to add uploaded files to the mk downloader list so they dont get re transferred~~ Should be done, I think?
 - ~~7z support in archtool~~ Added as a result of wanting to add it to the deduper. Shared code FTW.
 - ~~figure out why bad dir-lookup matches are all defaulting to {'dirKey': 'it takes a wizard'}~~ Someone had put "None" in the alternative names for the "It takes a Wizard" manga. Whoops?
 - ~~Make user-agent randomize~~ Should have something like ~32K possible configurations now.
 - ~~import archived djm stuff?~~
 - ~~tie mk uploader in properly~~
 - ~~proxy for name lookups.~~
 - ~~fix lo colums?~~
 - ~~automover patch path in db for moved items~~ Added `fix-dl-paths` to `cleanDb`.
 - ~~mangajoy sometimes only fetches one image~~ Added some delay, hopefully it'll fix things.
 - ~~look into pu sorting issues.~~ Stupid logic error in download delay mechanism.
 - ~~check that new items in bu are updating properly~~
 - ~~djm retagger no longer running?~~
 - ~~Murcielago. again~~ ~~Hopefully fixed by forcing NFKD unicode normalization.~~ Fuck unicode. Arrrgh.
 - ~~mu not in sidebar~~ Fucked up the flags at some point. Fixed.
 - ~~tags by number for h~~
 - ~~Try to do something clever with sorting items in the directory viewer. Preprocess to extract vol/chapter inteligently?~~ Simple regex implemented. I'll have to see how it pans out
 - ~~sort bu lists contents alphabetically~~
 - ~~aggregation query is fucked. somehow.~~ Fixed with procedural filtering system.
 - ~~scan downloads, retry missing not deduped~~ Functin added to utilities.cleanDb
 - ~~irc defer dir search to actual download (mk too)~~
 - ~~push dir updating into separate thread~~ The issue wasn't dir-updating, it was the DB loading it's cache from disk. Fixed by postgre
 - ~~Better mechanism for chosing colours for rows. Use a calculating system, rather then requiring manual choice~~
 - ~~Add file existence check to tooltip in manga table I'll have to see if 200 file existence checks is a problem for page-rendering time.~~
 - ~~Logger output coloring system~~
 - ~~mangacow missing last page~~ Fucking off-by-one error
 - ~~UNIQUE constraint on buId for mangaseries table~~
 - ~~Add parent-thread info to logger path for webUtilities.~~
 - ~~Recreate triggers to update counts on insert/delete~~
 - ~~make tags case-insensitive~~ (Switch to CITEXT should do this, added .lower() to query generator anyways)
 - ~~mu cross references all broken~~
 - ~~switch relevant columns to CITEXT~~
 - ~~<b>Distinct filter not working!</b>~~
 - ~~strip metainfo from links in h (artist-, scanlators-, etc)~~ (Also added a configurable tag highlighter)
 - ~~Defer dir updating to after page-load to prevent occational 20 second page-loads.~~ ~~I think this is actually the DB loading the indexes from disk. Not sure.~~ (Hopefully fixed by move to Postgre
 - ~~IRC scraper is broken for filenames with spaces.... Yeah....~~
 - ~~proper transaction system for DB (or just go to postgres)~~ (went to postgre)
 - ~~Fix Madokami scraper~~
 - ~~batoto cross verify number of images~~ Never mind, it's not a blind exploration, it's actually using the image navigator dropdown to generate image urls.
 - ~~Implement dir moving system already!~~
 - ~~total chapters not always known. Handle sanely.~~
 - ~~find or create only choosing dirs in picked.~~ (Fixed a while ago)
 - ~~irc scrapinator~~
 - ~~auto upload to madokami~~
 - ~~automate color choices for reader; fukkit just do a naive implementstion of rotation in a hsv colour space~~
 - ~~split item color generation into hemtai and manga to provide better control~~
 - ~~remove k scale from filesize readout. ~~
 - ~~reader directory page also includes database items for series~~
 - ~~show reader some general luv~~
 - ~~fakku scraper barfs on unicode~~ (I think it's fixed?)
 - ~~itemsManga page isn't using activePlugins.mako~~
 - ~~Also the itemsPron page.~~
 - ~~scrape mangacow~~
 - ~~Non-distinct manga view is borked~~
 - ~~Queue whole of any new series on batoto when a rating is found that's >= "++"~~
 - ~~Deduper - Check that local duplicate of file found via DB still exists before deleting new downloads.~~
 - ~~Scrape Fakku~~
 - ~~optimise name cleaning.~~ Spent some time profiling. Not worth the effort (not much room for improvement).
 - ~~optimize optimize optimize! 1 second for home rendering.~~ (~0.5 seconds! Woot!)
 - ~~mangafox if they dont resize.~~ Never mind. they took down all their Manga because licensing reasons, apparently?
 - ~~clean ! from matching system.~~ (Was already done)
 - ~~split porn/nonporn again?~~
 - ~~Fix BU Watcher login issues.~~ Cookies are the fucking bane of my existence.
 - ~~Add planned routes to look into the various tables (can I share code across the various query mechanisms?) (Mostly complete)~~(I'm calling this complete, since I only have two table-generator calls ATM)
 - ~~Scrape download.japanzai.com~~
 - ~~Fix rating change facility being broken by the new reader~~
 - ~~Finish reader redesign~~
 - ~~Fix presetting of item rating field.~~ (Accidentally fixed, I think? Not sure how, but it's now working.)
 - ~~reader shits itself on unicode urls.~~
 - ~~Allow arbitrarily nested folders in reader. (added in new reader)~~
 - ~~Prefferentially rescan MangaUpdates series that got releases today (e.g. scan https://www.mangaupdates.com/releases.html).~~
 - ~~also pururin.com~~
 - ~~pagechange buttons for porn broken in some instances.~~
 - ~~MangaUpdates name lookup passthrouth in nametools.~~
 - ~~fukkit, scrape batoto.~~
 - ~~Add legend key for what row colours mean (easy).~~
 - ~~Add better time-stamp granularity to Starkana Scraper.~~ (I think?)
 - ~~MangaBaby.com scraper~~
 - ~~Flatten any found duplicate directories, when they span more then one of the manga-folders.~~
 - ~~FIX NATURAL SORTING~~ (Fixed upstream in the natsort package)
 - ~~Make series monitoring tool for MT update periodically~~
 - ~~Automated tag update mechanism!~~
 - ~~Commit hooks to track the number of items in the mangaTable, without the massive overhead `SELECT COUNT(*)` has on SQLite (this should be fun and educational in terms of SQL).~~
 - ~~Generalize the image-cleaner to remove all annoying batoto/starkana/whatever images from downloaded archives. Possibly make it possible to run in batch mode? It should have a local directory of "bad" images that are scanned on start, and compare using hashes (or full on bitwise?).~~
 - ~~Scrape perveden.com~~ Fuck them, they watermark their shit. Never mind.
 - ~~automover~~

