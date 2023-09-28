#!/usr/bin/env bash

if [[ ! -d xtemp/.venv ]]; then
   py -m venv xtemp/.venv
   source xtemp/.venv/Scripts/activate
   # Use an older version that does not scare Windows Defender.
   pip install pyinstaller==5.13.2
fi

source xtemp/.venv/Scripts/activate

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
   --specpath="xtemp" \
   --workpath="xtemp/build" \
   --distpath="xtemp/dist" \
   --add-data="../template/codereview001_tmpl.odt${sep}template" \
   --add-data="../template/codereview002_tmpl.odt${sep}template" \
   gitreviewdoc.py
