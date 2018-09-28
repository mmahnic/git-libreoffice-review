import os, re
import gitjobs
import mainwin_ui_support
from generator import DiffGeneratorSettings, DiffGenerator, OverviewGenerator
from odt import OdtGenerator
from tktext import TkTextGenerator
from settings import globalSettings, APPTITLE

def setupUiMainSupport():
    """Replace the globals in mainwin_ui_support with globals from this module
    so that ui_support can be freely regenerated."""

    support = mainwin_ui_support
    support.generateDiffDocument = generateDiffDocumentCb
    support.addBranchDiffFromCommonAncestor = addBranchDiffFromCommonAncestorCb
    support.displayDiffPreview = displayDiffPreviewCb
    support.init = onInit


def onInit(top, gui, *args, **kwargs):
    # global w, top_level, root
    support = mainwin_ui_support
    support.w = gui
    support.top_level = top
    support.root = top
    prepareMainWindow()


class MainWindow():
    """An adapter for mainwin_ui_support to make the names more understandable."""

    def frame(self):
        return mainwin_ui_support.top_level

    def controls(self):
        return mainwin_ui_support.w

    def controlVars(self):
        return mainwin_ui_support


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


def updateDocumentNameCb():
    ctrls = MainWindow().controls()
    ctrlVars = MainWindow().controlVars()

    txtIds = ctrls.txtCommitIds
    text = txtIds.get( "1.0", "end-1c" ).strip()
    lines = [ l.strip() for l in text.split("\n") if len(l.strip()) > 0 ]
    commitId = _findCommitIdForName( lines )

    repo = os.path.basename(globalSettings.gitRoot())
    repo = re.sub( "[^a-zA-Z0-9]+", "_", repo )

    if len(commitId) > 0:
        ctrlVars.edName.set( "{}-{}".format(repo, commitId) )
    else:
        ctrlVars.edName.set( "{}".format(repo) )


def generateDiffDocumentCb():
    settings = DiffGeneratorSettings.fromGuiFields(MainWindow().controls())
    settings.rootDir = globalSettings.gitRoot()

    diffcmd = DiffGenerator(settings)
    overviewCmd = OverviewGenerator(settings)
    diffgen = OdtGenerator(settings)
    diffgen.writeDocument( diffcmd, overviewCmd )


def displayDiffPreviewCb():
    settings = DiffGeneratorSettings.fromGuiFields(MainWindow().controls())
    settings.rootDir = globalSettings.gitRoot()

    diffcmd = DiffGenerator(settings)
    overviewCmd = OverviewGenerator(settings)
    tkText = MainWindow().controls().txtFilters # TODO: Popup window, modal!
    tkText.delete( 0.0, "end" )
    diffgen = TkTextGenerator(settings, tkText)
    diffgen.writeDocument( diffcmd, overviewCmd )


def addBranchDiffFromCommonAncestorCb():
    def fixBranch( branch ):
        return "HEAD" if len(branch.strip()) == 0 else branch.strip()

    ctrls = MainWindow().controls()
    ctrlVars = MainWindow().controlVars()

    fromBranch = fixBranch(ctrlVars.comboBaseBranch.get())
    toBranch = fixBranch(ctrlVars.comboToBranch.get())

    txtIds = ctrls.txtCommitIds
    text = txtIds.get( "1.0", "end-1c" ).strip()
    lines = text.split( "\n" ) if len(text) > 0 else []
    lines.append( "{}...{}".format( fromBranch, toBranch ) )
    txtIds.delete( 0.0, "end" )
    txtIds.insert( 0.0, "\n".join( lines ))

    if len(ctrlVars.edName.get().strip()) < 1:
        updateDocumentNameCb()


def prepareMainWindow():
    ctrls = MainWindow().controls()
    ctrlVars = MainWindow().controlVars()
    frame = MainWindow().frame()

    gitroot = globalSettings.gitRoot()
    branches, curBranch = gitjobs.getBranches( gitroot )

    title = "{} - {} ({})".format(
            APPTITLE,
            os.path.basename(gitroot),
            os.path.dirname(gitroot))

    frame.title(title)

    ctrls.comboBaseBranch.configure(values=branches)
    ctrls.comboToBranch.configure(values=branches)

    if "develop" in branches:
        ctrlVars.comboBaseBranch.set( "develop" )
    elif "master" in branches:
        ctrlVars.comboBaseBranch.set( "master" )
    if curBranch not in ["develop", "master"]:
        ctrlVars.comboToBranch.set( curBranch )

    # TODO: default ignore patterns should be read from a config file
    ignored = [ "*.sln", "*.vcxproj", "*.filters", "*.svg", "*.rc", "**/autogen/**",
            "*.odt", "*.fodt", "*.odg", "*.fodg" ]
    ctrls.txtFilters.insert( 1.0, "\n".join(ignored) )
