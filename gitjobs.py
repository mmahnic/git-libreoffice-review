import os, sys
import re
import subprocess as subp

encoding = "utf-8"

def getBranches( gitroot ):
    cmd = ["git", "branch", "-a"]
    cwd = os.getcwd()

    def clean( branch ):
        if branch.find("->") > 0:
            return u""
        return branch.rstrip()

    try:
        os.chdir( gitroot )
        out = subp.check_output( cmd ).decode( encoding, "replace" )
        branches = [ clean(line) for line in out.split( "\n" ) if len(clean(line)) > 0 ]
        curbranch = u""
        for branch in branches:
            if branch.startswith( "*" ):
                curbranch = branch[1:].strip()
        branches = [b[1:].strip() for b in branches]
        return (branches, curbranch)
    except Exception as e:
        print(e) # TODO: send to UI

    os.chdir( cwd )
