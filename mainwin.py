import os, re
import gitjobs
import mainwin_ui_support as support
import textreport
from generator import DiffGeneratorSettings, DiffGenerator, OverviewGenerator
from odt import OdtGenerator
from tktext import TkTextGenerator
from settings import globalSettings, APPTITLE

def setupSupport():
    """Replace the globals in mainwin_ui_support with globals from this module
    so that ui_support can be freely regenerated."""

    support.generateDiffDocument = generateDiffDocumentCb
    support.addBranchDiffFromCommonAncestor = addBranchDiffFromCommonAncestorCb
    support.displayDiffPreview = displayDiffPreviewCb
    support.init = onInit


def onInit(top, gui, *args, **kwargs):
    # global w, top_level, root
    support.w = gui
    support.top_level = top
    support.root = top
    gui.top_level = top
    prepareMainWindow(gui)


def prepareMainWindow(gui):
    frame = gui.top_level

    gitroot = globalSettings.gitRoot()
    branches, curBranch = gitjobs.getBranches( gitroot )

    title = "{} - {} ({})".format(
            APPTITLE,
            os.path.basename(gitroot),
            os.path.dirname(gitroot))

    frame.title(title)

    gui.comboBaseBranch.configure(values=branches)
    gui.comboToBranch.configure(values=branches)

    if "develop" in branches:
        gui.varBaseBranch.set( "develop" )
    elif "master" in branches:
        gui.varBaseBranch.set( "master" )
    if curBranch not in ["develop", "master"]:
        gui.varToBranch.set( curBranch )

    # TODO: default ignore patterns should be read from a config file
    ignored = [ "*.sln", "*.vcxproj", "*.filters", "*.svg", "*.rc", "**/autogen/**",
            "*.odt", "*.fodt", "*.odg", "*.fodg" ]
    gui.txtFilters.insert( 1.0, "\n".join(ignored) )


def _findCommitIdForName( lines ):
    commitId = ""
    for l in lines:
        if l.find("..") > 0:
            commitId = l.split("..")[1].strip(". \t")
            break

    if len(commitId) < 1:
        for l in lines:
            if len(l.split()) > 1:
                commitId = l.split()[1]
                break

    return re.sub( "[^a-zA-Z0-9]+", "_", commitId )


def updateDocumentNameCb(gui):
    txtIds = gui.txtCommitIds
    text = txtIds.get( "1.0", "end-1c" ).strip()
    lines = [ l.strip() for l in text.split("\n") if len(l.strip()) > 0 ]
    commitId = _findCommitIdForName( lines )

    repo = os.path.basename(globalSettings.gitRoot())
    repo = re.sub( "[^a-zA-Z0-9]+", "_", repo )

    if len(commitId) > 0:
        gui.varName.set( "{}-{}".format(repo, commitId) )
    else:
        gui.varName.set( "{}".format(repo) )


def generateDiffDocumentCb(gui):
    settings = DiffGeneratorSettings.fromGuiFields(gui)
    settings.rootDir = globalSettings.gitRoot()

    diffcmd = DiffGenerator(settings)
    overviewCmd = OverviewGenerator(settings)
    diffgen = OdtGenerator(settings)
    diffgen.writeDocument( diffcmd, overviewCmd )


def displayDiffPreviewCb(gui):
    settings = DiffGeneratorSettings.fromGuiFields(gui)
    settings.rootDir = globalSettings.gitRoot()

    (reportFrame, reportGui) = textreport.getOrCreateTextReport(gui.top_level)
    reportGui.top_level.title( "Diff Preview" )

    diffcmd = DiffGenerator(settings)
    overviewCmd = OverviewGenerator(settings)
    tkText = reportGui.txtReport
    tkText.delete( 0.0, "end" )
    diffgen = TkTextGenerator(settings, tkText)
    diffgen.writeDocument( diffcmd, overviewCmd )


def addBranchDiffFromCommonAncestorCb(gui):
    def fixBranch( branch ):
        return "HEAD" if len(branch.strip()) == 0 else branch.strip()

    fromBranch = fixBranch(gui.varBaseBranch.get())
    toBranch = fixBranch(gui.varToBranch.get())

    txtIds = gui.txtCommitIds
    text = txtIds.get( "1.0", "end-1c" ).strip()
    lines = text.split( "\n" ) if len(text) > 0 else []
    lines.append( "{}...{}".format( fromBranch, toBranch ) )
    txtIds.delete( 0.0, "end" )
    txtIds.insert( 0.0, "\n".join( lines ))

    if len(gui.varName.get().strip()) < 1:
        updateDocumentNameCb(gui)


