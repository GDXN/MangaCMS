MangaCMS
========

Comic/Manga Download tool and reader.

Plugin scrapers for:


 - Starkana.com
 - Crazytje.be (Planned)
 - Realitylapse.com (Planned, possibly)
 - MangaTraders
 - Doujin-Moe
 - Fufufuu.net
 - MangaUpdates (metadata only).

The current focus is entirely on scraping sites that provide direct-archive-downloads, though I have considered targeting image-viewer sites like batoto, etc... in the future.

Automatic ad-removal and banner-removal. Currently, Starkana inserts an irritating self-aggrandizing image at a random position in each archive downloaded from their site. This is currently automatically and silently removed from each zip-file on download.
Any download system for sites that add source banners should crop the banners automatically, or remove any intersitial cruft.

---

Streaming archive decompression so there are no temporary files or unzipped archives for the reader.

Manga reading is through @balaclark's [HTML5-Comic-Book-Reader](https://github.com/balaclark/HTML5-Comic-Book-Reader), specifically [my fork](https://github.com/fake-name/HTML5-Comic-Book-Reader), which is similar to the original, except being heavily tweaked for usage on tablets.
The reader is HTML5/javascript based, and features extremely aggressive pre-caching to provide the best reading experience possible. It actually downloads the entire manga/comic in the background as soon as it's opened, so page-changing is near-instantaneous.

Has lots of dependencies:

 - Mako
 - CherryPy
 - Pyramid
 - Beautifulsoup4
 - Selenium (to interface with PhantomJS)
 - PhantomJS
 - Colorama
 - PyInotify
 - Dateutil
 - FeedParser (possibly defunct since MT is down).

Installing:  
Run the `installDeps.sh` script in the `setuptools` directory (note: must be run with `sudo` or as root. Please review it before running for security reasons). 
Note that the setup script will forcefully update your python 3 version to python 3.4.

Once you have installed the dependencies, you have to configure the various options. Copy `settings.base.py` to `settings.py`, and then edit it:  

Note: All paths MUST be absolute. Some of the threading somewhere is eating the environment information.

 - `pickedDir`  = This is where files on any "picked" list will go, for the scrapers that support that (I hope to remove this in the near future, there are simpler ways to achieve what I want)
 - `newDir`     = For scrapers that support downloading entire manga based on some trigger functionality, the downloaded files will go here (MN = MangaNew)
 - `baseDir`    = This is where the bulk manga downloads go.

 - `fufuDir`    = Where Fufufuu.net files go
 - `djMoeDir`   = And DoujinMoe files

 - `dbName`      = Where to place the SQLite database used for storing downloads. I normally just put it in the repo root.
 - `webCtntPath` = Path to the `ctnt` directory in the repo. 


If you want to pull down MangaUpdate metadata, you need to specify your username and password in the `buSettings` fields (mangaupdate = Baka-Updates).
Eventually the starkana scraper will pull down information about your watched series as well, which is why there are fields for starkana username+pass as well. This is currently not implemented.

Finally, the actual scraper has two halves. `mainWeb.py` is the web-interface, and `mainScrape.py` is the scraper. 
Currently, if you run `mainWeb.py` having never run `mainScrape.py`, it will *probably* fail, because the scraper is responsible for setting up the database. Simply run `mainScrape.py` first. (All are run `python3 mainScrape.py` or `python3 mainWeb.py`).

The tools are currently not daemonized at all, and must be manually run after restarting. I normally just leave them running in a [screen](http://www.gnu.org/software/screen/) session on my server. 
