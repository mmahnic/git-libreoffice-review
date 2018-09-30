
from diffvisitor import DiffLineVisitor

class TkTextDiffFormatter(DiffLineVisitor):
    def __init__(self, tkText):
        self.tkText = tkText


    def _insertLineNumbers( self, addOldNum, addNewNum ):
        width = max(3, len("{}".format( self.oldLineNumber )))
        style = 'removedLineNum' if addOldNum and not addNewNum else 'keptLineNum'
        value = self.oldLineNumber if addOldNum else ''
        self.tkText.insert( 'end', "{:{}}".format(value, width), ( style, ) )

        width = max(3, len("{}".format( self.newLineNumber )))
        style = 'addedLineNum' if not addOldNum and addNewNum else 'keptLineNum'
        value = self.newLineNumber if addNewNum else ''
        self.tkText.insert( 'end', " {:{}}".format(value, width), ( style, ) )

    def _insertNewLine( self ):
        self.tkText.insert( 'end', "\n" )

    def onStart(self):
        red = 'red'
        green = 'green'
        grey = 'lightgrey'
        black = 'black'
        blue = 'blue'

        def courier( size ):
            return 'courier {}'.format( size )

        def helvetica( size, extra=None ):
            return 'helvetica {}{}'.format( size, " " + extra if extra is not None else "" )

        self.tkText.tag_configure( 'standard', foreground=black, font=helvetica(10) )
        self.tkText.tag_configure( 'heading1', font=helvetica(16, "bold") )
        self.tkText.tag_configure( 'heading2', font=helvetica(14, "bold") )
        self.tkText.tag_configure( 'heading3', foreground=blue, font=helvetica(10, "bold") )
        self.tkText.tag_configure( 'diffFilenameRemove', foreground=red, background=grey, font=courier(10) )
        self.tkText.tag_configure( 'diffFilenameAdd', foreground=green, background=grey, font=courier(10) )
        self.tkText.tag_configure( 'diffRemove', foreground=red, font=courier(10) )
        self.tkText.tag_configure( 'diffAdd', foreground=green, font=courier(10) )
        self.tkText.tag_configure( 'diffKeep', foreground=black, font=courier(10) )
        self.tkText.tag_configure( 'removedLineNum', foreground=red, font=courier(9) )
        self.tkText.tag_configure( 'addedLineNum', foreground=green, font=courier(9) )
        self.tkText.tag_configure( 'keptLineNum', foreground=black, font=courier(9) )

    def onStartSection(self, prevSection, newSection):
        pass

    def onEndSection(self, section):
        pass

    def onCommandStart(self, line):
        self.tkText.insert( 'end', line, ( 'heading1', ) )
        self._insertNewLine()

    def onFileStart(self, line):
        self.tkText.insert( 'end', line, ( 'heading2', ) )
        self._insertNewLine()

    def onChunkStart(self, line):
        self.tkText.insert( 'end', line, ( 'heading3', ) )
        self._insertNewLine()

    def onFileRemove(self, line):
        self.tkText.insert( 'end', line, ( 'diffFilenameRemove', ) )
        self._insertNewLine()

    def onFileAdd(self, line):
        self.tkText.insert( 'end', line, ( 'diffFilenameAdd', ) )
        self._insertNewLine()

    def onLineRemove(self, line):
        self._insertLineNumbers( True, False )
        self.tkText.insert( 'end', line, ( 'diffRemove', ) )
        self._insertNewLine()

    def onLineAdd(self, line):
        self._insertLineNumbers( False, True )
        self.tkText.insert( 'end', line, ( 'diffAdd', ) )
        self._insertNewLine()

    def onLineUnchanged(self, line):
        self._insertLineNumbers( True, True )
        self.tkText.insert( 'end', line, ( 'diffKeep', ) )
        self._insertNewLine()

    def onOtherLine(self, line):
        if len(line) > 0:
            self.tkText.insert( 'end', line, ( 'standard', ) )
            self._insertNewLine()

    def onEnd(self): pass

    def getFormattedDiff( self, text ):
        self.visitLines( text )
        return []


class TkTextGenerator:
    def __init__(self, settings, tkText):
        self.settings = settings
        self.tkText = tkText

    def writeDocument(self, diffGenerator, overviewGenerator=None):
        if overviewGenerator is not None:
            overviewText = overviewGenerator.generateOverview()

        diffText = diffGenerator.generateDiff()

        # TkTextOverviewFormatter(tkText).getFormattedDiff( diffText )
        TkTextDiffFormatter(self.tkText).getFormattedDiff( diffText )
