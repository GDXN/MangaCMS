MangaCMS
========

Comic/Manga Download tool and reader.

Plugin scrapers for:

 
 - Starkana.com (WIP)
 - Crazytje.be (Planned)
 - MangaTraders
 - Doujin-Moe
 - Fufufuu.net
 - MangaUpdates (metadata only).

Streaming archive decompression so there are no temprary files or unzipped archives for the reader.

Manga reading is through @balaclark's [HTML5-Comic-Book-Reader](https://github.com/balaclark/HTML5-Comic-Book-Reader), specifically [my fork](https://github.com/fake-name/HTML5-Comic-Book-Reader), which is similar to the original, except being heavily tweaked for usage on tablets.
The reader is HTML5/javascript based, and features extremely aggressive pre-caching to provide the best reading experience possible. It actually downloads the entire manga/comic in the background as soon as it's opened, so page-changing is near-instantaneous.

Has lots of dependencies:

 - Mako
 - CherryPy
 - Pyramid
 - Beautifulsoup
 - Selenium (to interface with GhostJS)
 - GhostJS
 - FeedParser (possibly defunct since MT is down).
