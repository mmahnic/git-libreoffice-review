import gitreview_ui as uimain
import gitreview_ui_support as uimain_s
import os, sys
import re
import subprocess as subp


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
        self.paths = [ "." ]
        self.root = "."
        self.encoding = "utf-8"
        self.formatter = MarkdownFormatter()
        self.template = "template/codereview_tmpl.odt"


    @classmethod
    def fromGuiFields(klass, dialog):
        it = klass()
        it.commits = strippedLines(dialog.txtCommitIds.get( "1.0", "end-1c" ))
        it.ignores = strippedLines(dialog.txtFilters.get( "1.0", "end-1c" ))
        it.name = dialog.edName.get().strip()
        # it.paths = [ "." ]
        # it.root = "."
        return it


    @classmethod
    def testSettings(klass):
        it = klass()
        it.commits = [
                "e02a8165cae1afbd9a5db96b759a0747387ea5a4   233d12434260469c905a081a5de8585f748cd573",
                "9ef8b65ad997262f9901d7ee38dd75380f53dfb0" ]
        it.root = "xdata/tscodeexport"
        it.name = "test"
        return it


class MarkdownFormatter:
    def __init__(self):
        pass


    def getFormattedDiff( self, text ):
        result = []
        section = ""
        blockformat = ""

        def startSection( sectionType, setFormat="" ):
            nonlocal section, result, blockformat
            endSection()
            if setFormat != "":
                result += [ " ", "~~~~~~~~~~~~~~~ { .%s }" % setFormat ]
            section = sectionType
            blockformat = setFormat

        def endSection():
            nonlocal section, result, blockformat
            if section != "":
                if blockformat != "":
                    result += [ "", "~~~~~~~~~~~~~~~" ]
                section = ""

        for line in text:
            if line.startswith( "[cmd]" ):
                endSection()
                result += [ "", line.replace( "[cmd]", "#" ) ]
                continue
            elif line.startswith( "diff" ):
                endSection()
                result += [ "", "## " + line ]
                continue
            elif line.startswith( "@@" ):
                endSection()
                result += [ "", "### " + line ]
                continue
            elif line.startswith( "---" ) or line.startswith( "+++" ):
                if section != "---":
                    startSection( "---", "filepaths" )
            elif line.startswith( "-" ):
                if section != "-":
                    startSection( "-", "removed" )
            elif line.startswith( "+" ):
                if section != "+":
                    startSection( "+", "added" )
            elif line.startswith( " " ):
                if section != " ":
                    startSection( " ", "unchanged" )
            else:
                endSection()
            result.append( line )

        endSection()
        return result


class DiffDocumentGenerator:
    def __init__(self, settings):
        self.settings = settings


    def _getCleanCommits(self):
        rxid = re.compile( "[0-9a-fA-F]+" )
        commits = []

        for iddef in self.settings.commits:
            ids = iddef.split()
            if len(ids) > 2:
                continue

            good = []
            for code in ids:
                match = rxid.match( code )
                if match != None:
                    good.append(code)

            if len(good) == len(ids):
                commits.append( good )

        return commits


    def _getGitDiffIgnores(self):
        ignores = []
        for ignoreDef in self.settings.ignores:
            if ignoreDef.find("'") >= 0:
                continue
            ignores.append( "':!%s'" % ignoreDef )
        return ignores


    def _createGitDiffCommands( self ):
        git = ["git", "diff"]
        options = [ "-U6" ]
        commands = []
        for commit in self._getCleanCommits():
            command = [] + git
            command += options
            command += commit
            command += ["--" ] + self.settings.paths
            command += self._getGitDiffIgnores()
            commands.append( command )

        return commands


    def _createPandocCommand( self ):
        pandoc = [ "pandoc", "-t", "odt", "-o", "xdata/%s.odt" % self.settings.name ]
        if len(self.settings.template) > 0 and os.path.exists( self.settings.template ):
            pandoc += ["--reference-odt=%s" % self.settings.template ]

        # print(pandoc)
        return pandoc


    def run(self):
        difftext = []
        for command in self._createGitDiffCommands():
            cwd = os.getcwd()
            try:
                os.chdir( self.settings.root )
                difftext += ["", "[cmd] %s" % ( " ".join(command) ), ""]
                out = subp.check_output( command )
                difftext += out.decode(self.settings.encoding).split("\n")
            except Exception as e:
                difftext += ["**Error**: %s" % e, ""]
                print(e) # TODO: send to UI
            os.chdir( cwd )

        difftext = self.settings.formatter.getFormattedDiff(difftext)
        # for t in difftext: print(t.encode("utf-8").decode("cp1250"))
        # return

        PIPE=subp.PIPE
        p = subp.Popen( self._createPandocCommand(), stdout=PIPE, stdin=PIPE, stderr=PIPE )
        (pout, perr) = p.communicate(input=("\n".join(difftext)).encode("utf-8"))
        if len(pout) > 0:
            print(pout.decode()) # TODO: send to UI
        if len(perr) > 0:
            print(perr.decode()) # TODO: send to UI



def generateDiffDocument():
    settings = DiffGeneratorSettings.fromGuiFields(uimain_s.w)
    diffgen = DiffDocumentGenerator(settings)
    diffgen.run()


def setupUiMainSupport():
    uimain_s.generateDiffDocument = generateDiffDocument


def test():
    settings = DiffGeneratorSettings.testSettings()
    diffgen = DiffDocumentGenerator(settings)
    diffgen.run()

if __name__ == '__main__':
    test(); sys.exit()
    setupUiMainSupport()
    uimain.vp_start_gui()

