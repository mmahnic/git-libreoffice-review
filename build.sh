#!/usr/bin/env bash

opts="--noconsole --onefile"
# opts="$opts --log-level=TRACE"

if [ "$(which cygpath)" == "" ]; then
   here="$(pwd)"
   sep=":"
else
   here=$(cygpath -w $(pwd))
   sep=";"
fi
pyinstaller $opts \
   --specpath="xdata" \
   --workpath="xdata/build" \
   --distpath="xdata/dist" \
   --add-data="../template/codereview001_tmpl.odt${sep}template" \
   --add-data="../template/codereview002_tmpl.odt${sep}template" \
   gitreviewdoc.py
