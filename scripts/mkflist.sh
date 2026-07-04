#!/bin/bash

file="docs/shyland/flist"
tmpfile="$file.tmp"

find `ls` | egrep -v -e '__pycache__/' -e '^ssl' > $tmpfile

cp /dev/null $file

for f in `cat $tmpfile`; do
    echo "https://raw.githubusercontent.com/KnightOfNight/games-mvc/refs/heads/main/$f" >> $file
done

rm -f $tmpfile
