#!/usr/bin/env cat
import re

class DiffLineVisitor:
    def __init__(self):
        self.section = ""
        self.oldLineNumber = 0
        self.newLineNumber = 0


    def _startSection( self, section ):
        if self.section == section:
            return
        prev = self.section
        self._endSection()
        self.section = section
        self.onStartSection( prev, self.section )


    def _endSection( self ):
        if self.section != "":
            self.onEndSection( self.section )
            self.section = ""


    rxChunkHead = re.compile( r"^@@\s+\-(\d+),\d+\s+\+(\d+),\d+\s+@@" )
    def _extractChunkLineNumbers(self, line):
        mo = DiffLineVisitor.rxChunkHead.search( line )
        if mo == None:
            self.oldLineNumber = 0
            self.newLineNumber = 0
            return
        self.oldLineNumber = int(mo.group(1))
        self.newLineNumber = int(mo.group(2))


    def visitLines( self, text ):
        self.section = ""
        self.onStart()
        for line in text:
            # line += " /%s/" % self.section
            if line.startswith( "[cmd] " ):
                self._startSection( "command-head" )
                self.onCommandStart(line[6:])
                self._startSection( "command" )
            elif line.startswith( "diff" ):
                self._startSection( "diff-head" )
                self.onFileStart(line)
                self._startSection( "diff" )
            elif line.startswith( "@@" ):
                self._startSection( "chunk-head" )
                self._extractChunkLineNumbers(line)
                self.onChunkStart(line)
                self._startSection( "chunk" )
            elif self.section == "diff":
                if line.startswith( "---" ):
                    self.onFileRemove(line)
                elif line.startswith( "+++" ):
                    self.onFileAdd(line)
                else:
                    self.onOtherLine(line)
            elif self.section == "chunk":
                if line.startswith( "-" ):
                    self.onLineRemove(line)
                    self.oldLineNumber += 1
                elif line.startswith( "+" ):
                    self.onLineAdd(line)
                    self.newLineNumber += 1
                elif line.startswith( " " ):
                    self.onLineUnchanged(line)
                    self.oldLineNumber += 1
                    self.newLineNumber += 1
                else:
                    self.onOtherLine(line)
            else:
                if self.section != "":
                    self.onOtherLine(line)

        self._endSection()
        self.onEnd()


    def onStart(self): pass
    def onStartSection(self, prevSection, newSection ): pass
    def onEndSection(self, curSection): pass
    def onCommandStart(self, line): pass
    def onFileStart(self, line): pass
    def onChunkStart(self, line): pass
    def onFileRemove(self, line): pass
    def onFileAdd(self, line): pass
    def onLineRemove(self, line): pass
    def onLineAdd(self, line): pass
    def onLineUnchanged(self, line): pass
    def onOtherLine(self, line): pass
    def onEnd(self): pass


