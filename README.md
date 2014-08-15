MangaCMS
========

Comic/Manga Download tool and reader.

Plugin scrapers for:


 - Starkana.com
 - Batoto.com
 - Crazytje.be
 - Doujin-Moe
 - download.japanzai.com
 - MangaCow
 - Manga Madokami
 - Fakku
 - Pururin
 - Exhen.Madokami
 - MangaUpdates (metadata only).
 - ~~MangaBaby.com~~ (Defunct?)
 - ~~MangaTraders~~ (Defunct)
 - ~~Fufufuu.net~~ (Defunct)
 - Realitylapse.com (Planned, possibly)

The current focus is entirely on scraping sites that provide direct-archive-downloads, though batoto is an exception. Batoto images are downloaded to memory, and then written out to an archive on-the-fly, with no temporary files used at all.

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
 - Colorama
 - PyInotify
 - Dateutil
 - Probably more

Installing:  
Run the `installDeps.sh` script in the `setuptools` directory (note: must be run with `sudo` or as root. Please review it before running for security reasons). 
Note that the setup script will forcefully update your python 3 version to python 3.4.

Once you have installed the dependencies, you have to configure the various options. Copy `settings.base.py` to `settings.py`, and then edit it:  

Note: All paths **MUST** be absolute. Some of the threading somewhere is eating the environment information. Rather then try to track down where in the complex dependency system the environment variables are being modified, it's easier to just use absolute paths.
(Note: this means that paths like `~/blah` will also not work. You have to specify `/home/{username}/blah`).

 - `pickedDir`         = Directories in this folder are preferentially used, and if a download goes in this directory, it is highlighted in the web interface.
 - `baseDir`           = This is where the bulk manga downloads go, if a folder is not found in the "picked" directory..

 - `djMoeDir`          = And DoujinMoe files
 - 'puRinDir'          = Pururin Files
 - 'ExhenMadokamiDir'  = ExHen.madokami Files
 - 'fkDir'             = Fakku Files Files
 - `fufuDir`           = Where Fufufuu.net files go

 - `dbName`      = Where to place the SQLite database used for storing downloads. I normally just put it in the repo root.
 - `webCtntPath` = Path to the `ctnt` directory in the repo. 


If you want to pull down MangaUpdate metadata, you need to specify your username and password in the `buSettings` fields (mangaupdate = Baka-Updates).
Eventually the starkana scraper will pull down information about your watched series as well, which is why there are fields for starkana username+pass as well. This is currently not implemented.

Finally, the actual scraper has two halves. `mainWeb.py` is the web-interface, and `mainScrape.py` is the scraper. 
Currently, if you run `mainWeb.py` having never run `mainScrape.py`, it will *probably* fail, because the scraper is responsible for setting up the database. Simply run `mainScrape.py` first. (All are run `python3 mainScrape.py` or `python3 mainWeb.py`).

The tools are currently not daemonized at all, and must be manually run after restarting. I normally just leave them running in a [screen](http://www.gnu.org/software/screen/) session on my server. 

---

Preliminary deduplication support is currently present, [IntraArchiveDeduplicator](using my https://github.com/fake-name/IntraArchiveDeduplicator) tool. This is intended to allow collation of files from many sources while having as few local duplicate files actually stored locally as possible.

Archives downloaded are automatically added to the deduplication database, and if a downloaded archive is found to contain no new files, it is automatically deleted, which prevents the fact that the scraper fetches files from multiple sources from resulting in duplicate downloads.

There are long-term plans for doing fuzzy image matching, using some perceptual-hashing mechanisms that are alreay in-place in the file-hashing system, but it's currently delayed by the requirement to be able to search for items by hamming distance across very large datasets (currently I have ~3 million discrete phashes).  
There is some preliminary experiments on implementing a custom BK tree for better searching, but it has non-trivial speed-issues, and will likely require at least some components to be implemented in C or a langauge that can compile to C (pyrex?).
Another alternative is to implement the indexing mechanisms directly in postgres, using the SP-GiST indexing interface, but that requires a deeper understanding of the internal mechanisms in Postgres then I currently have (and my C is /*rusty*/, particularly for desktop use).

---


Because I'm sure no one wants to just read about what MangaCMS does, here are some screenshots of the web-interface:  
![MangaUpdates link tool](http://fake-name.github.io/MangaCMS/img/Stuff%201.png)  
![Directory Browser](http://fake-name.github.io/MangaCMS/img/Stuff%202.png)  
![Reader](http://fake-name.github.io/MangaCMS/img/Stuff%203.png)  


---

Tests for all the various plugins are in the /tests/ directory. Because of how they hook into the rest of the system, they must be run as modules: `python3 -m tests.test-{name}`. This is required to avoid having to dick about with the contents of `sys.path`.

---

This was written as much for programming excercise as for practical use, so there may be some NIH-y things going on. For example, I wrote my own database abstraction layer (see MonitorDbBase.py, RetreivalDbBase.py), primarily as an opportunity to teach myself SQL. Some of the interitence structures are for a similar purpose (I wanted to play with abstract classes).

As with about everything I do, the first run through teaches me all the things I /wish/ I had done differently.