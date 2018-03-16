import os
import mainwin_ui as uimain
import mainwin_ui_support as uimain_s
from generator import DiffGeneratorSettings, DiffGenerator
from odt import OdtGenerator as DocGenerator


def generateDiffDocument():
    settings = DiffGeneratorSettings.fromGuiFields(uimain_s.w)
    diffcmd = DiffGenerator(settings)
    diffgen = DocGenerator(settings)
    diffgen.writeDocument( diffcmd )


def onInit(top, gui, *args, **kwargs):
    # global w, top_level, root
    uimain_s.w = gui
    uimain_s.top_level = top
    uimain_s.root = top
    gitroot = findGitDir( os.getcwd() ) or os.getcwd()
    gui.edRepository.delete( 0, "end" )
    gui.edRepository.insert( 0, gitroot )
    gui.edName.insert( 0, os.path.basename( gitroot ))
    # if 0: gui.txtFilters.insert( 1.0, "\n".join(os.getenv( "PATH" ).split(";")) )

    # TODO: default ignore patterns should be read from a config file
    ignored = [ "*.vcxproj", "*.filters", "*.svg", "*.rc", "**/autogen/**" ]
    gui.txtFilters.insert( 1.0, "\n".join(ignored) )


def findGitDir( startdir ):
    curdir = startdir
    while len(curdir) > 4:
        if os.path.exists( os.path.join( curdir, ".git" )):
            return curdir
        curdir = os.path.dirname( curdir )
    return None


def setupUiMainSupport():
    uimain_s.generateDiffDocument = generateDiffDocument
    uimain_s.init = onInit

if __name__ == '__main__':
    setupUiMainSupport()
    uimain.vp_start_gui()
