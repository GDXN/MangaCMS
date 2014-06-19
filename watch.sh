#!/bin/bash
sqlite3 -column -header links.db 'SELECT * FROM MangaItemCounts;'