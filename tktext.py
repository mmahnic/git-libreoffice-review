
from diffvisitor import DiffLineVisitor

class TkTextDiffFormatter(DiffLineVisitor):
    def __init__(self, tkText):
        self.text = tkText
        self.prevChunkBlockType = ""

    def onStart(self):
        pass

    def onStartSection(self, prevSection, newSection):
        if newSection == "chunk":
            self.prevChunkBlockType = ""

    def onEndSection(self, section):
        if section == "chunk":
            self._decorateChunkBlock("")

    def onCommandStart(self, line):
        self.result.append( self._heading( 1, line) )

    def onFileStart(self, line):
        self.result.append( self._heading( 2, line) )

    def onChunkStart(self, line):
        self.result.append( self._heading( 3, line) )

    def onFileRemove(self, line):
        self.result.append( self._diffFilenameRemove( line) )

    def onFileAdd(self, line):
        self.result.append( self._diffFilenameAdd( line) )

    def onLineRemove(self, line):
        self._decorateChunkBlock("-")
        self.result.append( self._diffRemove( line) )

    def onLineAdd(self, line):
        self._decorateChunkBlock("+")
        self.result.append( self._diffAdd( line) )

    def onLineUnchanged(self, line):
        self._decorateChunkBlock(" ")
        self.result.append( self._diffEqual( line) )

    def onOtherLine(self, line):
        if self.section == "chunk":
            self._decorateChunkBlock("")
        if len(line) > 0:
            self.result.append( self._standard( line) )

    def onEnd(self): pass

    def getFormattedDiff( self, text ):
        self.visitLines( text )
        return self.result

class TkTextGenerator:
    def __init__(self, settings):
        self.settings = settings

    def writeDocument(self, diffGenerator, overviewGenerator=None):
        diffText = diffGenerator.generateDiff()
