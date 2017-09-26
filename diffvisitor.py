#!/usr/bin/env cat

class DiffLineVisitor:
    def __init__(self):
        self.section = ""


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
                elif line.startswith( "+" ):
                    self.onLineAdd(line)
                elif line.startswith( " " ):
                    self.onLineUnchanged(line)
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


