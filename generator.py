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
        self.root = "."
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
        it.root = dialog.edRepository.get().strip()
        if len(it.name) == 0:
            it.name = "review"
        if len(it.root) == 0:
            it.root = "."
        return it


    @classmethod
    def testSettings(klass):
        it = klass()
        if 1:
            it.commits = [
                    "c4af5e4c47a710e4e69a192c7016c97e394b96fd 8abb36628690685c7aec6fda4ee184984d512c20",
                    "5dfc658a0d4fad01ae7672a72bb1d7bab3eff9c0" ]
            it.root = "."
        elif 1:
            it.commits = [ "2679e04a3554def1dd198937bddc9f377b847a7d" ]
            it.root = r"C:\Users\mmarko\prj\gitapps\wideocar4"
        it.name = "test"
        return it


    def getCleanCommits(self):
        rxid = re.compile( "[0-9a-fA-F]+" )
        commits = []

        for iddef in self.commits:
            ids = iddef.split()
            if len(ids) > 2 or len(ids) == 0:
                continue

            good = []
            for code in ids:
                match = rxid.match( code )
                if match != None:
                    good.append(code)

            if len(good) == len(ids):
                # NOTE: we can't display the initial commit this way, it has no parent!
                if len(good) == 1:
                    commits.append( ["%s^" % good[0], "%s" % good[0]] )
                elif len(good) == 2:
                    commits.append( ["%s^" % good[0], "%s" % good[1]]  )

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
            command += commit
            command += ["--" ] + self.settings.paths
            command += self.settings.getGitDiffIgnores()
            commands.append( ( command, commit ) )

        return commands


    def generateDiff(self):
        difftext = []
        for command, commit in self.createGitDiffCommands():
            cwd = os.getcwd()
            try:
                os.chdir( self.settings.root )
                difftext += ["[cmd] %s" % ( " ".join(commit) )]
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
        self.logFormat = '''--pretty=format:%ai %cn%n%B'''
        self.merges = "--no-merges"


    def createGitLogCommands( self ):
        git = ["git", "log"]
        options = [ self.logFormat, self.merges ]
        commands = []
        for commit in self.settings.getCleanCommits():
            command = [] + git
            command += options
            command += [ "{}..{}".format(commit[0], commit[1]) ]
            commands.append( ( command, commit ) )

        return commands


    def generateOverview(self):
        logText = []
        for command, commit in self.createGitLogCommands():
            cwd = os.getcwd()
            try:
                os.chdir( self.settings.root )
                out = subp.check_output( command )
                logText += out.decode(self.settings.encoding, "replace").split("\n")
            except Exception as e:
                logText += ["**Error**: %s" % e, ""]
                print(e) # TODO: send to UI
            os.chdir( cwd )

        print logText
        return logText



def test():
    from odt import OdtGenerator as DocGenerator
    settings = DiffGeneratorSettings.testSettings()
    diffcmd = DiffGenerator(settings)
    overviewCmd = OverviewGenerator(settings)
    diffgen = DocGenerator(settings)
    diffgen.writeDocument( diffcmd, overviewCmd )


if __name__ == '__main__':
    test()

