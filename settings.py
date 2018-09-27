import os, sys
import argparse

APPTITLE = "Git Review"

def findGitDir( startdir ):
    curdir = startdir
    while len(curdir) > 4:
        if os.path.exists( os.path.join( curdir, ".git" )):
            return curdir
        curdir = os.path.dirname( curdir )

    return None

class Arguments(object):
    pass

class Settings:
    def __init__(self):
        self.arguments = Arguments()
        self._gitRoot = None
        self._workDir = None

        self._parseSysArgs()


    def workingDir(self):
        if self._workDir is None:
            args = self.arguments
            if args.working_dir is None or len(args.working_dir) == 0:
                args.working_dir = [os.getcwd()]
            workdir = args.working_dir[0] if len(args.working_dir) > 0 else os.getcwd()
            self._workDir = os.path.abspath( workdir )

        return self._workDir


    def gitRoot(self):
        if self._gitRoot is None:
            self._gitRoot = findGitDir( self.workingDir() )
        return self._gitRoot


    def _parseSysArgs(self):
        parser = argparse.ArgumentParser()
        parser.add_argument( "--working-dir", nargs=1, action="store" )
        parser.parse_args(namespace=self.arguments)


globalSettings = Settings()

