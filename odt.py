import os
import re
import zipfile
import tempfile
import subprocess as subp
from xml.sax.saxutils import escape as xml_escape

from markdownfmt import MarkdownFormatter
from diffvisitor import DiffLineVisitor

Review_Styles = """
    <style:style style:name="PX1" style:family="paragraph" style:parent-style-name="Standard"/>
    <style:style style:name="PX2" style:family="paragraph" style:parent-style-name="Preformatted_20_Text"/>
    <style:style style:name="PX3" style:family="paragraph" style:parent-style-name="diff_20_add"/>
    <style:style style:name="PX4" style:family="paragraph" style:parent-style-name="diff_20_remove"/>
    <style:style style:name="PX5" style:family="paragraph" style:parent-style-name="diff_20_fn_20_add"/>
    <style:style style:name="PX6" style:family="paragraph" style:parent-style-name="diff_20_fn_20_remove"/>
    <style:style style:name="PX7" style:family="paragraph" style:parent-style-name="review_20_split"/>
    <style:style style:name="PX8" style:family="paragraph" style:parent-style-name="review_20_comment"/>
"""


class OdtFormatter(DiffLineVisitor):
    def __init__(self):
        self.result = []

    def _clean(self, text):
        def compress(spaces):
            return """<text:s text:c="%d"/>""" % len(spaces.group(0))
        s = xml_escape(text)
        s = re.sub( " {2,}", compress, s)
        if s.startswith( " " ):
            s = """<text:s text:c="1"/>""" + s[1:]
        return s


    def _standard(self, text):
        return """<text:p text:style-name="PX1">{text}</text:p>""".format(text=self._clean(text))


    def _heading(self, level, text):
        return ( """<text:h text:style-name="Heading_20_{level}" text:outline-level="{level}">{text}</text:h>"""
                ).format( level=level, text=self._clean(text) )


    def _diffEqual(self, text):
        return """<text:p text:style-name="PX2">{text}</text:p>""".format(text=self._clean(text))


    def _diffAdd(self, text):
        return """<text:p text:style-name="PX3">{text}</text:p>""".format(text=self._clean(text))


    def _diffRemove(self, text):
        return """<text:p text:style-name="PX4">{text}</text:p>""".format(text=self._clean(text))


    def _diffFilenameAdd(self, text):
        return """<text:p text:style-name="PX5">{text}</text:p>""".format(text=self._clean(text))


    def _diffFilenameRemove(self, text):
        return """<text:p text:style-name="PX6">{text}</text:p>""".format(text=self._clean(text))


    def onStart(self): pass

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
        self.result.append( self._diffRemove( line) )

    def onLineAdd(self, line):
        self.result.append( self._diffAdd( line) )

    def onLineUnchanged(self, line):
        self.result.append( self._diffEqual( line) )

    def onOtherLine(self, line):
        if len(line) > 0:
            self.result.append( self._standard( line) )

    def onEnd(self): pass

    def getFormattedDiff( self, text ):
        self.visitLines( text )
        return self.result


class OdtGenerator:
    def __init__(self, settings):
        self.settings = settings


    def _findTemplate( self, templateName ):
        if templateName.startswith( "." ) or templateName.startswith( "/" ):
            return templateName

        return os.path.join(os.path.dirname(os.path.realpath(__file__)), templateName)


    def _getOutputName( self ):
        now = self.settings.now
        return "xdata/%04d%02d%02d_%s.odt" % (now.year, now.month, now.day, self.settings.name)


    def _writeDiffToOdf( self, difftext, contentTemplate ):
        style = [ """<office:automatic-styles>""", """</office:automatic-styles>""" ]
        text = [ """<office:text>""", """</office:text>""" ]
        stylestart = contentTemplate.find(style[0]) + len(style[0])
        styleend = contentTemplate.find(style[1])
        textstart = contentTemplate.find(text[0]) + len(text[0])
        textend = contentTemplate.find(text[1])

        parts = [
                contentTemplate[:stylestart],
                Review_Styles,
                contentTemplate[styleend:textstart]
                ]

        parts += OdtFormatter().getFormattedDiff( difftext )

        parts += [
                contentTemplate[textend:]
                ]

        return "".join(parts)


    def writeDocument(self, diffGenerator):
        difftext = diffGenerator.generateDiff()
        template = self._findTemplate( self.settings.template )
        docfile = self._getOutputName()
        doc = zipfile.ZipFile(template, "r")
        tmphandle, tmpname = tempfile.mkstemp()
        newdoc = zipfile.ZipFile(docfile, "w", zipfile.ZIP_DEFLATED)
        for item in doc.infolist():
            buffer = doc.read(item.filename)
            if (item.filename == 'content.xml'):
                content = doc.read(item).decode("utf-8")
                content = self._writeDiffToOdf( difftext, content )
                newdoc.writestr("content.xml", content.encode("utf-8"))
            else:
                newdoc.writestr(item, buffer)
        doc.close()
        newdoc.close()
