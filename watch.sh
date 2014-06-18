#!/bin/bash
echo 'SELECT COUNT(*) FROM AllMangaItems WHERE sourceSite="fu" and dlState=0;' | sqlite3 links.db
echo 'SELECT COUNT(*) FROM AllMangaItems WHERE sourceSite="fu" and dlState=1;' | sqlite3 links.db
echo 'SELECT COUNT(*) FROM AllMangaItems WHERE sourceSite="fu" and dlState=2;' | sqlite3 links.db