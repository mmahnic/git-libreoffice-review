import os, sys
import re
import subprocess as subp
import datetime as dt


def strippedLines(text):
    def emptyOrComment(l):
        return len(l) == 0 or l.startswith("#")
    return  [x for x in [l.strip() for l in text.split("\n")]
            if not emptyOrComment(x)]


class DiffGeneratorSettings:
    def __init__(self):
        self.commits = []
        self.ignores = []
        self.name = ""
        self.now = dt.datetime.now()
        self.paths = [ "." ]
        self.rootDir = "."
        self.encoding = "utf-8"
        self.template = "template/codereview_tmpl.odt"
        self.templateStyles = {
                "diff-add": "diff_20_add",
                "diff-remove": "diff_20_remove",
                "diff-fn-add": "diff_20_fn_20_add",
                "diff-fn-remove": "diff_20_fn_20_remove" }


    @classmethod
    def fromGuiFields(klass, dialog):
        it = klass()
        it.commits = strippedLines(dialog.txtCommitIds.get( "1.0", "end-1c" ))
        it.ignores = strippedLines(dialog.txtFilters.get( "1.0", "end-1c" ))
        it.name = dialog.edName.get().strip()
        it.rootDir = dialog.edRepository.get().strip()
        if len(it.name) == 0:
            it.name = "review"
        if len(it.rootDir) == 0:
            it.rootDir = "."
        return it


    def getCleanCommits(self):
        rxid = re.compile( "[0-9a-fA-F]+" )
        commits = []

        for iddef in self.commits:
            ids = iddef.split()
            if len(ids) > 2 or len(ids) == 0:
                print( "Bad commit range: ", iddef )
                continue

            if len(ids) == 1:
                if ids[0].find("..") >= 0:
                    commits.append(ids[0])
                else:
                    commits.append( "{0}^..{0}".format( ids[0] ) )

            if len(ids) == 2:
                if ids[0].find("..") >= 0 or ids[1].find("..") >= 0:
                    print( "Bad commit range: ", iddef )
                    continue
                commits.append( "{0}..{1}".format( ids[0], ids[1] ) )

        return commits


    def getGitDiffIgnores(self):
        ignores = []
        for ignoreDef in self.ignores:
            if ignoreDef.find("'") >= 0:
                continue
            ignores.append( ":^%s" % ignoreDef )
        return ignores


class DiffGenerator:
    def __init__(self, settings):
        self.settings = settings
        self.diffMode = "-U6"
        self.algorithm = "--diff-algorithm=minimal"


    def createGitDiffCommands( self ):
        git = ["git", "diff"]
        options = [ self.diffMode, self.algorithm ]
        commands = []
        for commit in self.settings.getCleanCommits():
            command = [] + git
            command += options
            command += [commit]
            command += ["--" ] + self.settings.paths
            command += self.settings.getGitDiffIgnores()
            commands.append( ( command, commit ) )

        return commands


    def generateDiff(self):
        difftext = []
        for command, commit in self.createGitDiffCommands():
            cwd = os.getcwd()
            try:
                os.chdir( self.settings.rootDir )
                difftext += ["[cmd] %s" % ( commit )]
                difftext += ["%s" % ( " ".join(command) )]
                out = subp.check_output( command )
                difftext += out.decode(self.settings.encoding, "replace").split("\n")
            except Exception as e:
                difftext += ["**Error**: %s" % e, ""]
                print(e) # TODO: send to UI
            os.chdir( cwd )

        return difftext


class OverviewGenerator:
    def __init__(self, settings):
        self.settings = settings
        self.logFormat = '''--pretty=format:$%m$s%H %ai %cn%n%B'''
        self.merges = "--no-merges"


    def createGitLogCommands( self ):
        # We are trying to keep only the commits that contribute to the diff.
        git = ["git", "log", "--left-right" ]
        options = [ self.logFormat, self.merges ]
        commands = []
        for commit in self.settings.getCleanCommits():
            command = [] + git
            command += options
            command += [commit]
            commands.append( ( command, commit ) )

        return commands


    # Keep right (>) commits from log --left-right
    def _kipRightCommits( self, lines ):
        rxLeftRight = re.compile( r"^\$[-<>]\$[0-9a-fA-F]{6,}" )
        side = ""
        res = []
        for l in lines:
            mo = rxLeftRight.search( l )
            if mo is not None:
                side = l[1]
                if side == ">":
                    l = l[3:]

            if side == ">":
                res.append( l )

        return res


    def generateOverview(self):
        logText = []
        for command, commit in self.createGitLogCommands():
            cwd = os.getcwd()
            try:
                os.chdir( self.settings.rootDir )
                out = subp.check_output( command )
                logText += self._kipRightCommits( out.decode(
                        self.settings.encoding, "replace").split("\n") )
            except Exception as e:
                logText += ["**Error**: %s" % e, ""]
                print(e) # TODO: send to UI
            os.chdir( cwd )

        return logText



def test():
    emptyHash = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    headHash = subp.check_output( ["git", "rev-parse", "HEAD"] ).strip()
    from odt import OdtGenerator as DocGenerator

    settings = DiffGeneratorSettings()
    settings.name = "zero-to-head"
    settings.commits = [ "{} {}".format(emptyHash, headHash) ]

    diffcmd = DiffGenerator(settings)
    overviewCmd = OverviewGenerator(settings)
    diffgen = DocGenerator(settings)
    diffgen.writeDocument( diffcmd, overviewCmd )

    settings.name = "headancestor-to-head"
    settings.commits = [ "HEAD^^...HEAD" ]
    diffgen.writeDocument( diffcmd, overviewCmd )


if __name__ == '__main__':
    test()

