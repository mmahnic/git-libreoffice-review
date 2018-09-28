import os, sys
import re
import subprocess as subp


# A wrapper around subprocess.check_output with different stdin and stderr
# defaults so that the call does not crash on Windows.
def check_output( command, cwd=".", stdin=subp.PIPE, stderr=subp.PIPE, encoding="utf-8" ):
    return subp.check_output( command, stdin=stdin, stderr=stderr,
            shell=False, cwd=cwd ).decode( encoding, "replace" )


def getBranches( gitroot ):
    cmd = ["git", "branch", "-a"]

    def clean( branch ):
        if branch.find("->") > 0:
            return u""
        return branch.rstrip()

    out = check_output( cmd, cwd=gitroot )
    branches = [ clean(line) for line in out.split( "\n" ) if len(clean(line)) > 0 ]
    curbranch = u""
    for branch in branches:
        if branch.startswith( "*" ):
            curbranch = branch[1:].strip()
    branches = [b[1:].strip() for b in branches]

    return (branches, curbranch)
