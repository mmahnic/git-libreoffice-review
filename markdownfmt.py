#!/usr/bin/env cat

from diffvisitor import DiffLineVisitor

class MarkdownFormatter(DiffLineVisitor):
    def __init__(self):
        self.result = []
        self.section = ""
        self.blockformat = ""

    def startSection( self, sectionType, setFormat="" ):
        self.endSection()
        if setFormat != "":
            self.result += [ " ", "~~~~~~~~~~~~~~~ { .%s }" % setFormat ]
        self.section = sectionType
        self.blockformat = setFormat

    def endSection(self):
        if self.section != "":
            if self.blockformat != "":
                self.result += [ "", "~~~~~~~~~~~~~~~" ]
            self.section = ""

    def onStart(self):
        self.result = []
        self.section = ""
        self.blockformat = ""

    def onCommandStart(self, line):
        self.endSection()
        self.result += [ "", line.replace( "[cmd]", "#" ) ]

    def onFileStart(self, line):
        self.endSection()
        self.result += [ "", "## " + line ]

    def onChunkStart(self, line):
        self.endSection()
        self.result += [ "", "### " + line ]

    def onFileRemove(self, line):
        if self.section != "---":
            self.startSection( "---", "filepaths" )
        self.result.append( line )

    def onFileAdd(self, line):
        if self.section != "---":
            self.startSection( "---", "filepaths" )
        self.result.append( line )

    def onLineRemove(self, line):
        if self.section != "-":
            self.startSection( "-", "removed" )
        self.result.append( line )

    def onLineAdd(self, line):
        if self.section != "+":
            self.startSection( "+", "added" )
        self.result.append( line )

    def onLineUnchanged(self, line):
        if self.section != " ":
            self.startSection( " ", "unchanged" )
        self.result.append( line )

    def onOtherLine(self, line):
        self.endSection()
        self.result.append( line )

    def onEnd(self):
        self.endSection()

    def getFormattedDiff( self, text ):
        self.visitLines( text )
        return self.result


