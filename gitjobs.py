import os, sys
import re
import subprocess as subp

encoding = "utf-8"

def getBranches( gitroot ):
    cmd = ["git", "branch", "-a"]
    cwd = os.getcwd()
    try:
        os.chdir( gitroot )
        out = subp.check_output( cmd ).decode( encoding, "replace" )
        branches = [ line for line in out.split( "\n" ) if len(line.strip()) > 0 ]
        curbranch = u""
        for branch in branches:
            if branch.startswith( "*" ):
                curbranch = branch[1:].strip()
        branches = [b[1:].strip() for b in branches]
        return (branches, curbranch)
    except Exception as e:
        difftext += ["**Error**: %s" % e, ""]
        print(e) # TODO: send to UI

    os.chdir( cwd )
