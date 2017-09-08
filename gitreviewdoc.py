import gitreview_ui as uimain
import gitreview_ui_support as uimain_s
from gitreviewdoc import *


def generateDiffDocument():
    settings = DiffGeneratorSettings.fromGuiFields(uimain_s.w)
    diffgen = DiffDocumentGenerator(settings)
    diffgen.run()


def setupUiMainSupport():
    uimain_s.generateDiffDocument = generateDiffDocument


if __name__ == '__main__':
    setupUiMainSupport()
    uimain.vp_start_gui()
