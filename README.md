MangaCMS
========

Comic/Manga/Light-Novel Download tool and reader.

Plugin scrapers for:


 - Manga Sites:
	 - Batoto.com
	 - download.japanzai.com
	 - MangaCow
	 - MangaJoy
	 - Starkana.com
	 - CXC Scans
	 - RedHawk Scans
	 - Webtoons.com
	 - LoneManga.com
	 - EasyGoing Scans
	 - Dynasty Scans
	 - Manga.Madokami
	 - Numerous IRC bots.
 - Hentai Sites:
	 - Fakku
	 - Doujin Moe
	 - Pururin
	 - Exhen.Madokami
	 - HBrowse
 - Light Novels:
	 - Baka-Tsuki 
	 - JapTem
	 - Re:Translations
 - Metadata:
	 - MangaUpdates (metadata only).
 - Defunct:
	 - ~~Crazytje.be~~ (Defunct)
	 - ~~MangaBaby.com~~ (Defunct?)
	 - ~~MangaTraders~~ (Defunct)
	 - ~~Fufufuu.net~~ (Defunct)
	 - Realitylapse.com (Planned, possibly)

 - To Add:
	 - http://illuminati-manga.com/
	 - http://www.ipitydafoo.com/  

I prefer to focus on scraping sites that offer archive downloads, but those are fairly rare, so image-hosting sites are also scraped. Scraped images are automatically packed into per-chapter archives. My only absolute criteria for inclusion at this time is that the site not resize or watermark files, since that prevents the deduplication system from working properly (note: I'm more relaxed about this for the H sites, primarily out of necessity).

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
 - Psycopg2 (And a PostgreSQL install!)
 - Beautifulsoup4
 - FeedParser
 - colorama
 - pyinotify
 - python-dateutil
 - apscheduler
 - rarfile
 - python-magic
 - babel
 - cython
 - irc
 - python-sql
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

The database must be somewhat manually set up at this time.

```
postgres=# CREATE USER mangacmsuser;
CREATE ROLE
postgres=# \password mangacmsuser
Enter new password:   { Type your Password }
Enter it again:   { Type your Password }
postgres=# CREATE DATABASE mangacms;
CREATE DATABASE
postgres=# GRANT ALL PRIVILEGES ON DATABASE mangacms to mangacmsuser;
GRANT

```

Note: using capitals in usernames/tablenames/columnames in postgres is rather difficult, just don't do it.

You must then specify the Database server's IP, the username, databasename, and password in the `settings.py` file.

You also have to add the line

`local   mangacms        all                                     md5`

to `/etc/postgresql/9.3/main/pg_hba.conf`, to allow local connections to the postgres database with password auth.



---

Preliminary deduplication support is currently present, (using my [IntraArchiveDeduplicator](https://github.com/fake-name/IntraArchiveDeduplicator)) tool. This is intended to allow collation of files from many sources while having as few local duplicate files actually stored locally as possible.

Archives downloaded are automatically added to the deduplication database, and if a downloaded archive is found to contain no new files, it is automatically deleted, which prevents the fact that the scraper fetches files from multiple sources from resulting in duplicate downloads.

There is some support for fuzzy image matching using perceptual-hashing mechanisms that are already in-place in [perceptual-hashing system](https://github.com/fake-name/IntraArchiveDeduplicator/blob/master/hashFile.py#L101). Right now, it's limited to keyhole-optimized searches, generally searching for duplicates within a specific directory.
I currently use a [python-cython BK tree implementation](https://github.com/fake-name/MangaCMS/blob/master/deduplicator/cyHamDb.pyx) that is fairly fast, but memory hungry and non-persistent, so right now for each search I have to load the local phash search set from the database (where the "local" set is the hashes of the files in the same directory). 

I have long-term plans to enable the requirement to be able to search for items by hamming distance across very large datasets (currently I have ~3 million discrete phashes) by implementing a BK tree index directly in postgres, using the GiST indexing interface, but that is currently stalled out due to the complexity of implementing custom indexing in postgresql, and the rather non-existent documentation. The current local-search system is quite effective, and I have done some work on implementing a postgres index. See the [Hamming GiST](https://github.com/fake-name/pg-spgist_hamming) repo.

---


Because I'm sure no one wants to just read about what MangaCMS does, here are some screenshots of the web-interface:  
![MangaUpdates link tool](http://fake-name.github.io/MangaCMS/img/Stuff%201.png)    
![Directory Browser](http://fake-name.github.io/MangaCMS/img/Stuff%202.png)    
![Reader](http://fake-name.github.io/MangaCMS/img/Stuff%203.png)  


---

Tests for all the various plugins are in the /tests/ directory. Because of how they hook into the rest of the system, they must be run as modules: `python3 -m tests.test-{name}`. This is required to avoid having to dick about with the contents of `sys.path`.

---

### Q&A

Q: Is this hard to use?  
A: It requires at minimum a decent familiarity with the Linux command line. Python and/or SQL knowledge is also helpful.    
   I generally idle in #madokami on irchighway, so you can ask me questions if you need there, though I'm not actually present behind my client a lot of the time. I'll help with whatever, though I can't exactly give a complete lesson on "how to linux" or so forth.

Q: You're scraping my site! Don't do that!  
A: Your *web-site*. That you posted **publically**. You don't really understand how this whole "internet" thing works, do you?  
  TL;DR No.  

---

This was written as much for programming excercise as for practical use, so there may be some NIH-y things going on. For example, I wrote my own database abstraction layer (see MonitorDbBase.py, RetreivalDbBase.py), primarily as an opportunity to teach myself SQL. Some of the interitence structures are for a similar purpose (I wanted to play with abstract classes).

~~The light-novel scraper uses SqlAlchemy, so it's not all NIH.~~ Dumped SqlAlchemy. The documentation is too poor for it to be useable.

~~Currently looking at [python-sql](https://pypi.python.org/pypi/python-sql/) for dynamic SQL where I have more control over the generated SQL.~~ Most of the database interfacing now uses [python-sql](https://pypi.python.org/pypi/python-sql/) for dynamic query generation, and all query variables are parameterized, so SQL injection *should* be fairly challenging.   
There are a few unparameterized variables, primarily because there are some things that *cannot* be parameterized, such as table names. However, the only unparameterized variable (tablename) can only be altered by modifying local plugin python files, so I think it's at least an acceptable risk.  
AFICT, the primary issue I had with SQLAlchemy is that my current page-generation mechanisms are very procedural in nature, which meshes extremely poorly with a database API that is basically only designed to support OOP-y ORM-style code structures. 

Realistically, the ENTIRE web interface is something of an afterthought. This project was initially **only** a scraper, and the web interface was initially more of a "oh look, I can run a web server with twistd" thing. It kind of grew from there, but the database schema was always designed from the get-go to be scraper-centric. 

This was basically the first web application I'd ever written as well.

As with about everything I do, the first run through teaches me all the things I /wish/ I had done differently.