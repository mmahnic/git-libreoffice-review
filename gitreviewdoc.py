import os, re
import mainwin_ui as uimain
import mainwin_ui_support as uimain_s
import gitjobs
from generator import DiffGeneratorSettings, DiffGenerator, OverviewGenerator
from odt import OdtGenerator as DocGenerator

def updateDocumentNameCb():
    gui = uimain_s.w
    txtIds = gui.txtCommitIds
    text = txtIds.get( "1.0", "end-1c" ).strip()
    lines = [ l.strip() for l in text.split("\n") if len(l.strip()) > 0 ]
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
    commitId = re.sub( "[^a-zA-Z0-9]+", "_", commitId )

    repo = os.path.basename(gui.edRepository.get().strip())
    repo = re.sub( "[^a-zA-Z0-9]+", "_", repo )

    gui.edName.delete( 0, "end" )
    if len(commitId) > 0:
        gui.edName.insert( 0, "{}-{}".format(repo, commitId) )
    else:
        gui.edName.insert( 0, "{}".format(repo) )


def generateDiffDocumentCb():
    settings = DiffGeneratorSettings.fromGuiFields(uimain_s.w)
    diffcmd = DiffGenerator(settings)
    overviewCmd = OverviewGenerator(settings)
    diffgen = DocGenerator(settings)
    diffgen.writeDocument( diffcmd, overviewCmd )


def addBranchDiffFromCommonAncestorCb():
    def fixBranch( branch ):
        return "HEAD" if len(branch.strip()) == 0 else branch.strip()

    dialog = uimain_s.w
    txtIds = dialog.txtCommitIds
    fromBranch = fixBranch(uimain_s.comboBaseBranch.get())
    toBranch = fixBranch(uimain_s.comboToBranch.get())

    text = txtIds.get( "1.0", "end-1c" ).strip()
    lines = text.split( "\n" ) if len(text) > 0 else []
    lines.append( "{}...{}".format( fromBranch, toBranch ) )
    txtIds.delete( 0.0, "end" )
    txtIds.insert( 0.0, "\n".join( lines ))

    if len(dialog.edName.get().strip()) < 1:
        updateDocumentNameCb()


def prepareMainWindow( gui, guivars ):
    gitroot = findGitDir( os.getcwd() ) or os.getcwd()
    branches, curBranch = gitjobs.getBranches( gitroot )

    gui.edRepository.delete( 0, "end" )
    gui.edRepository.insert( 0, gitroot )

    gui.comboBaseBranch.configure(values=branches)
    gui.comboToBranch.configure(values=branches)
    if "develop" in branches:
        guivars.comboBaseBranch.set( "develop" )
    elif "master" in branches:
        guivars.comboBaseBranch.set( "master" )
    if curBranch not in ["develop", "master"]:
        guivars.comboToBranch.set( curBranch )

    # TODO: default ignore patterns should be read from a config file
    ignored = [ "*.sln", "*.vcxproj", "*.filters", "*.svg", "*.rc", "**/autogen/**",
            "*.odt", "*.fodt", "*.odg", "*.fodg" ]
    gui.txtFilters.insert( 1.0, "\n".join(ignored) )


def onInit(top, gui, *args, **kwargs):
    # global w, top_level, root
    uimain_s.w = gui
    uimain_s.top_level = top
    uimain_s.root = top
    prepareMainWindow( gui, uimain_s )


def findGitDir( startdir ):
    curdir = startdir
    while len(curdir) > 4:
        if os.path.exists( os.path.join( curdir, ".git" )):
            return curdir
        curdir = os.path.dirname( curdir )
    return None


def setupUiMainSupport():
    uimain_s.generateDiffDocument = generateDiffDocumentCb
    uimain_s.addBranchDiffFromCommonAncestor = addBranchDiffFromCommonAncestorCb
    uimain_s.init = onInit

if __name__ == '__main__':
    setupUiMainSupport()
    uimain.vp_start_gui()
