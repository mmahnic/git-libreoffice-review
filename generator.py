import os, sys
import re
import subprocess as subp
import datetime as dt

from pandocodt import PandocOdtGenerator


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
                    "1740318e200bfae82987e33267626fda7f955c39   233d12434260469c905a081a5de8585f748cd573",
                    "9ef8b65ad997262f9901d7ee38dd75380f53dfb0" ]
            it.root = "xdata/tscodeexport"
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
                # FIXME: we can't display the initial commit this way, it has no parent!
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
            ignores.append( "':!%s'" % ignoreDef )
        return ignores


class DiffGenerator:
    def __init__(self, settings):
        self.settings = settings


    def createGitDiffCommands( self ):
        git = ["git", "diff"]
        options = [ "-U6" ]
        commands = []
        for commit in self.settings.getCleanCommits():
            command = [] + git
            command += options
            command += commit
            command += ["--" ] + self.settings.paths
            command += self.settings.getGitDiffIgnores()
            commands.append( command )

        return commands


    def generateDiff(self):
        difftext = []
        for command in self.createGitDiffCommands():
            cwd = os.getcwd()
            try:
                os.chdir( self.settings.root )
                difftext += ["", "[cmd] %s" % ( " ".join(command) ), ""]
                out = subp.check_output( command )
                difftext += out.decode(self.settings.encoding, "replace").split("\n")
            except Exception as e:
                difftext += ["**Error**: %s" % e, ""]
                print(e) # TODO: send to UI
            os.chdir( cwd )

        return difftext


def test():
    settings = DiffGeneratorSettings.testSettings()
    diffcmd = DiffGenerator(settings)
    diffgen = PandocOdtGenerator(settings)
    diffgen.writeDocument( diffcmd )


if __name__ == '__main__':
    test()

