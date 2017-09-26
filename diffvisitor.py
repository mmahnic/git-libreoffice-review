#!/usr/bin/env cat

class DiffLineVisitor:
    def __init__(self):
        self.section = ""


    def visitLines( self, text ):
        self.section = ""
        self.onStart()
        for line in text:
            if line.startswith( "[cmd] " ):
                self.section = "command"
                self.onCommandStart(line[6:])
            elif line.startswith( "diff" ):
                self.section = "diff"
                self.onFileStart(line)
            elif line.startswith( "@@" ):
                self.section = "chunk"
                self.onChunkStart(line)
            elif line.startswith( "---" ):
                self.onFileRemove(line)
            elif line.startswith( "+++" ):
                self.onFileAdd(line)
            elif line.startswith( "-" ):
                if self.section == "chunk":
                    self.onLineRemove(line)
                else:
                    self.onOtherLine(line)
            elif line.startswith( "+" ):
                if self.section == "chunk":
                    self.onLineAdd(line)
                else:
                    self.onOtherLine(line)
            elif line.startswith( " " ):
                if self.section == "chunk":
                    self.onLineUnchanged(line)
                else:
                    self.onOtherLine(line)
            else:
                if self.section != "":
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


