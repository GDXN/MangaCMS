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
 = Dateutil
 - FeedParser (possibly defunct since MT is down).


Theoretical install procedure (WIP):
`sudo apt-get install python3 python3-setuptools phantomjs`
`sudo easy_install3 pip`
`sudo pip3 install Mako CherryPy Pyramid Beautifulsoup4 Selenium FeedParser colorama pyinotify python-dateutil apscheduler`

