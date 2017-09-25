import os
import re
import zipfile
import tempfile
import shutil
import subprocess as subp

from markdownfmt import MarkdownFormatter

class PandocOdtGenerator:
    def __init__(self, settings):
        self.settings = settings


    def _findTemplate( self, templateName ):
        if templateName.startswith( "." ) or templateName.startswith( "/" ):
            return templateName

        return os.path.join(os.path.dirname(os.path.realpath(__file__)), templateName)


    def _getOutputName( self ):
        now = self.settings.now
        return "xdata/%04d%02d%02d_%s.odt" % (now.year, now.month, now.day, self.settings.name)


    def _createPandocCommand( self ):
        pandoc = [ "pandoc", "-t", "odt", "-o", self._getOutputName() ]
        if len(self.settings.template) > 0:
            template = self._findTemplate( self.settings.template )
            if template != None and os.path.exists( template ):
                pandoc += ["--reference-odt=%s" % template ]
            else:
                print( "Template '%s' not found" % template ) # TODO: send to UI

        # print(pandoc)
        return pandoc


    def _applyOpenOfficeDiffStyles( self, content ):
        rxp = re.compile( '"P[0-9]+"' )
        tasks = [
                [ r'(<text:p text:style-name=)"P[0-9]+"(>\+\+\+ )', 'diff-fn-add' ],
                [ r'(<text:p text:style-name=)"P[0-9]+"(>--- )', 'diff-fn-remove' ],
                [ r'(<text:p text:style-name=)"P[0-9]+"(>\+)', 'diff-add' ],
                [ r'(<text:p text:style-name=)"P[0-9]+"(>-)', 'diff-remove' ]
                ]
        for task in tasks:
            rx = re.compile( task[0] )
            sub = r'\1"%s"\2' % self.settings.templateStyles[task[1]]
            content = rx.sub(sub, content)

        return content


    def _patchOpenOfficeDocument( self ):
        # We can not define the styles for ODT in markdown. We edit the
        # content.xml file of the generated document, instead.
        docfile = self._getOutputName()
        if not os.path.exists(docfile):
            return

        doc = zipfile.ZipFile(docfile, "r")
        tmphandle, tmpname = tempfile.mkstemp()
        newdoc = zipfile.ZipFile(tmpname, "w", zipfile.ZIP_DEFLATED)
        for item in doc.infolist():
            buffer = doc.read(item.filename)
            if (item.filename == 'content.xml'):
                content = doc.read(item).decode("utf-8")
                content = self._applyOpenOfficeDiffStyles( content )
                newdoc.writestr("content.xml", content.encode("utf-8"))
            else:
                newdoc.writestr(item, buffer)
        doc.close()
        newdoc.close()
        os.close(tmphandle)
        shutil.move(tmpname, docfile)


    def writeDocument(self, diffGenerator):
        difftext = diffGenerator.generateDiff()
        difftext = MarkdownFormatter().getFormattedDiff(difftext)
        # open("xdata/difftext.txt", "w").write("\n".join(difftext).encode("utf-8", "replace").decode("cp1250"))

        PIPE=subp.PIPE
        p = subp.Popen( self._createPandocCommand(), stdout=PIPE, stdin=PIPE, stderr=PIPE )
        (pout, perr) = p.communicate(input=("\n".join(difftext)).encode("utf-8", "replace"))
        if len(pout) > 0:
            print(pout.decode()) # TODO: send to UI
        if len(perr) > 0:
            print(perr.decode()) # TODO: send to UI

        self._patchOpenOfficeDocument()


