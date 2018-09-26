import os
import re
import zipfile
import tempfile
import subprocess as subp
from xml.sax.saxutils import escape as xml_escape

from diffvisitor import DiffLineVisitor

Review_Styles = u"""\
    <style:style style:name="PX1" style:family="paragraph" style:parent-style-name="Standard"/>
    <style:style style:name="PX2" style:family="paragraph" style:parent-style-name="Preformatted_20_Text"/>
    <style:style style:name="PX3" style:family="paragraph" style:parent-style-name="diff_20_add"/>
    <style:style style:name="PX4" style:family="paragraph" style:parent-style-name="diff_20_remove"/>
    <style:style style:name="PX5" style:family="paragraph" style:parent-style-name="diff_20_fn_20_add"/>
    <style:style style:name="PX6" style:family="paragraph" style:parent-style-name="diff_20_fn_20_remove"/>
    <style:style style:name="PX7" style:family="paragraph" style:parent-style-name="review_20_split"/>
    <style:style style:name="PX8" style:family="paragraph" style:parent-style-name="review_20_comment"/>
    <style:style style:name="Sect1" style:family="section">
      <style:section-properties style:editable="false">
        <style:columns fo:column-count="1" fo:column-gap="0cm"/>
      </style:section-properties>
    </style:style>\
"""

# A document variable 'DisplayMode' is set in a hidden section 'Settings'.
# Other sections are hidden based on the value of the 'DisplayMode' variable.
# The variable will be controlled by a macro that will be installed as an ooo extension.
Document_Variables = u"""\
      <text:variable-decls>
        <text:variable-decl office:value-type="float" text:name="DisplayMode"/>
      </text:variable-decls>
      <text:section text:style-name="Sect1" text:name="Settings" text:display="none">
        <text:p text:style-name="Standard">Display Mode: 1-aded, 2-removed, 3-All <text:s/><text:variable-set text:name="DisplayMode" office:value-type="float" office:value="3" style:data-style-name="N0">3</text:variable-set> </text:p>
      </text:section>\
"""

NewCode_Section_Start = u"""\
      <text:section text:style-name="Sect1" text:name="diff{isection}" text:condition="ooow:(DisplayMode != 1) AND (DisplayMode != 3)" text:display="condition">\
"""

OldCode_Section_Start = u"""\
      <text:section text:style-name="Sect1" text:name="diff{isection}" text:condition="ooow:(DisplayMode != 2) AND (DisplayMode != 3)" text:display="condition">\
"""

Section_End = u"""</text:section>"""

def _spaces( numSpaces ):
    if numSpaces < 1: return u""
    if numSpaces == 1: return u" "
    return u""" <text:s text:c="{}"/>""".format(numSpaces-1)

def _cleanOdt( text ):
    def compress(spaces):
        return _spaces( len(spaces.group(0)) )
    s = xml_escape(text)
    s = re.sub( u" {2,}", compress, s)
    return s


class OdtDiffFormatter(DiffLineVisitor):
    def __init__(self):
        self.result = []
        self.prevChunkBlockType = ""
        self.sectionId = 100


    def _standard(self, text):
        return u"""<text:p text:style-name="Standard">{text}</text:p>""".format(text=_cleanOdt(text))


    def _heading(self, level, text):
        return ( u"""<text:h text:style-name="Heading_20_{level}" text:outline-level="{level}">{text}</text:h>"""
                ).format( level=level, text=_cleanOdt(text) )


    def _diffEqual(self, text):
        lineno = u"{} {}".format( self.oldLineNumber, self.newLineNumber )
        text = _cleanOdt(text)
        return ( u"""<text:p text:style-name="Preformatted_20_Text">"""
                """<text:span text:style-name="lineNumbers">{lineno}</text:span>"""
                """{text}</text:p>""".format(lineno=lineno, text=text) )


    def _diffStartAddBlock(self):
        self.sectionId += 1
        return NewCode_Section_Start.format(isection=self.sectionId)


    def _diffAdd(self, text):
        lineno = u"""<text:s text:c="{}"/>{}""".format(len("%d " % self.oldLineNumber), self.newLineNumber)
        text = _cleanOdt(text)
        return ( u"""<text:p text:style-name="diff_20_add">"""
                """<text:span text:style-name="lineNumbers">{lineno}</text:span>"""
                """{text}</text:p>""".format(lineno=lineno, text=text) )


    def _diffStartRemoveBlock(self):
        self.sectionId += 1
        return OldCode_Section_Start.format(isection=self.sectionId)


    def _diffRemove(self, text):
        lineno = u"""{}<text:s text:c="{}"/>""".format(self.oldLineNumber, len(" %d" % self.newLineNumber))
        text = _cleanOdt(text)
        return ( u"""<text:p text:style-name="diff_20_remove">"""
                """<text:span text:style-name="lineNumbers">{lineno}</text:span>"""
                """{text}</text:p>""".format(lineno=lineno, text=text) )


    def _diffEndBlock(self):
        return Section_End


    def _diffFilenameAdd(self, text):
        return u"""<text:p text:style-name="diff_20_fn_20_add">{text}</text:p>""".format(text=_cleanOdt(text))


    def _diffFilenameRemove(self, text):
        return u"""<text:p text:style-name="diff_20_fn_20_remove">{text}</text:p>""".format(text=_cleanOdt(text))


    def _decorateChunkBlock(self, blockType):
        if blockType == self.prevChunkBlockType:
            return
        if self.prevChunkBlockType in [ "+", "-" ]:
            self.result.append(self._diffEndBlock())
        if blockType == "+":
            self.result.append(self._diffStartAddBlock())
        elif blockType == "-":
            self.result.append(self._diffStartRemoveBlock())
        self.prevChunkBlockType = blockType


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


class OdtOverviewGenerator:
    def __init__(self):
        self.result = []

    def _standard(self, text):
        return u"""<text:p text:style-name="Standard">{text}</text:p>""".format(text=_cleanOdt(text))

    def _timeAuthorLine(self, text):
        return ( u"""<text:p text:style-name="diff_20_add">"""
                """{text}</text:p>""".format(text=text) )

    def _heading(self, level, text):
        return ( u"""<text:h text:style-name="Heading_20_{level}" text:outline-level="{level}">{text}</text:h>"""
                ).format( level=level, text=_cleanOdt(text) )

    def visitLines( self, text ):
        rxTimeAuthor = re.compile( r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}" )
        def isTimeAuthorLine( line ):
            mo = rxTimeAuthor.search( line )
            return mo is not None

        self.result.append( self._heading( 1, "Overview" ) )
        for line in text:
            if isTimeAuthorLine( line ):
                self.result.append( self._timeAuthorLine( line) )
            else:
                self.result.append( self._standard( line) )


    def getFormattedOverview( self, text ):
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


    def _writeDiffToOdf( self, overviewText, diffText, contentTemplate ):
        style = [ u"""<office:automatic-styles[^>]*>""", u"""</office:automatic-styles>""" ]
        text = [ u"""<office:text[^>]*>""", u"""</office:text>""" ]

        stylestart = re.search( style[0], contentTemplate ).end(0)
        styleend = contentTemplate.find(style[1])
        textstart = re.search( text[0], contentTemplate ).end(0)
        textend = contentTemplate.find(text[1])

        parts = [
                contentTemplate[:stylestart],
                Review_Styles,
                contentTemplate[styleend:textstart],
                Document_Variables
                ]

        parts += OdtOverviewGenerator().getFormattedOverview( overviewText );

        parts += OdtDiffFormatter().getFormattedDiff( diffText )

        parts += [
                contentTemplate[textend:]
                ]

        return "".join(parts)


    def writeDocument(self, diffGenerator, overviewGenerator=None):
        diffText = diffGenerator.generateDiff()

        overviewText = ""
        if overviewGenerator is not None:
            overviewText = overviewGenerator.generateOverview()

        template = self._findTemplate( self.settings.template )
        docfile = self._getOutputName()
        doc = zipfile.ZipFile(template, "r")
        tmphandle, tmpname = tempfile.mkstemp()
        newdoc = zipfile.ZipFile(docfile, "w", zipfile.ZIP_DEFLATED)

        for item in doc.infolist():
            buffer = doc.read(item.filename)
            if (item.filename == 'content.xml'):
                content = doc.read(item).decode("utf-8")
                content = self._writeDiffToOdf( overviewText, diffText, content )
                newdoc.writestr("content.xml", content.encode("utf-8"))
            else:
                newdoc.writestr(item, buffer)

        doc.close()
        newdoc.close()

