import mainwin_ui as uimain
import mainwin_ui_support as uimain_s
from generator import *
import os


def generateDiffDocument():
    settings = DiffGeneratorSettings.fromGuiFields(uimain_s.w)
    diffgen = DiffDocumentGenerator(settings)
    diffgen.run()


def onInit(top, gui, *args, **kwargs):
    # global w, top_level, root
    uimain_s.w = gui
    uimain_s.top_level = top
    uimain_s.root = top
    gui.edRepository.delete( 0, "end" )
    gui.edRepository.insert( 0, os.getcwd() )
    gui.edName.insert( 0, os.path.basename( os.getcwd() )) # TODO: basename of git root dir
    # if 0: gui.txtFilters.insert( 1.0, "\n".join(os.getenv( "PATH" ).split(";")) )

def setupUiMainSupport():
    uimain_s.generateDiffDocument = generateDiffDocument
    uimain_s.init = onInit

if __name__ == '__main__':
    setupUiMainSupport()
    uimain.vp_start_gui()
