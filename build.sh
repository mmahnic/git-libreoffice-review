#!/usr/bin/env bash

opts="--noconsole"
# opts="$opts --log-level=TRACE"

here=$(cygpath -w $(pwd))
pyinstaller $opts \
   --specpath="xdata" \
   --workpath="xdata/build" \
   --distpath="xdata/dist" \
   --add-data="../template/codereview_tmpl.odt;template" \
   gitreviewdoc.py
