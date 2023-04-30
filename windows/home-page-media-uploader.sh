#!/bin/bash
today=$(printf -v date '%(%Y-%m-%d)T\n' -1)

cd c/workspace/home-page-media-scraper
./gradlew run

cd c/workspace/home-page-media-file
git add .
if [[ `git status --porcelain` ]]; then
    git commit -m "update media file $today"

    git push
fi
