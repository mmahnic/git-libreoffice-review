#!/usr/bin/env cat

class DiffLineVisitor:
    def __init__(self):
        pass


    def visitLines( self, text ):
        self.onStart()
        for line in text:
            if line.startswith( "[cmd]" ):
                self.onCommandStart(line)
            elif line.startswith( "diff" ):
                self.onFileStart(line)
            elif line.startswith( "@@" ):
                self.onChunkStart(line)
            elif line.startswith( "---" ):
                self.onFileRemove(line)
            elif line.startswith( "+++" ):
                self.onFileAdd(line)
            elif line.startswith( "-" ):
                self.onLineRemove(line)
            elif line.startswith( "+" ):
                self.onLineAdd(line)
            elif line.startswith( " " ):
                self.onLineUnchanged(line)
            else:
                self.onOtherLine(line)
        self.onEnd()


    def onStart(self): pass
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


