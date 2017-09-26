#!/usr/bin/env cat

from diffvisitor import DiffLineVisitor

class MarkdownFormatter(DiffLineVisitor):
    def __init__(self):
        self.result = []
        self.blockformat = ""

    def onStartSection(self, prevSection, newSection):
        pass

    def onEndSection(self, section):
        if section != "" and self.blockformat != "":
            self.result += [ "~~~~~~~~~~~~~~~" ]
            self.blockformat = ""

    def startMkdBlock( self, blockformat ):
        if self.blockformat == blockformat:
            return
        if self.blockformat != "":
            self.result += [ "~~~~~~~~~~~~~~~" ]

        self.blockformat = blockformat
        self.result += [ "", "~~~~~~~~~~~~~~~ { .%s }" % blockformat ]

    def onStart(self):
        self.result = []
        self.blockformat = ""

    def onCommandStart(self, line):
        self.result += [ "", "#" + line, "" ]

    def onFileStart(self, line):
        self.result += [ "", "## " + line, "" ]

    def onChunkStart(self, line):
        self.result += [ "", "### " + line, "" ]

    def onFileRemove(self, line):
        self.startMkdBlock( "filepaths" )
        self.result.append( line )

    def onFileAdd(self, line):
        self.startMkdBlock( "filepaths" )
        self.result.append( line )

    def onLineRemove(self, line):
        self.startMkdBlock( "removed" )
        self.result.append( line )

    def onLineAdd(self, line):
        self.startMkdBlock( "added" )
        self.result.append( line )

    def onLineUnchanged(self, line):
        self.startMkdBlock( "unchanged" )
        self.result.append( line )

    def onOtherLine(self, line):
        self.result.append( line )

    def onEnd(self):
        pass

    def getFormattedDiff( self, text ):
        self.visitLines( text )
        return self.result


