import os
import re
import zipfile
import tempfile
import gitjobs
from xml.sax.saxutils import escape as xml_escape

from diffvisitor import DiffLineVisitor

# TODO: move to DiffGeneratorSettings
INDENT_TAB_SIZE=2

Review_Styles = u"""\
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

RX_SPACES = re.compile(u" {2,}")
def _cleanForOdt( text ):
    def compress(spaces):
        return _spaces( len(spaces.group(0)) )
    s = xml_escape(text)
    return RX_SPACES.sub(compress, s)

RX_LEADTABS = re.compile("^(.)(\t+)")
def _expandIndentTabs( text ):
    def expand(tabs: re.Match):
        spaces = " " * len(tabs.group(2)) * INDENT_TAB_SIZE
        return f"{tabs.group(1)}{spaces}"
    return RX_LEADTABS.sub(expand, text)


class OdtDiffFormatter(DiffLineVisitor):
    def __init__(self):
        self.result = []
        self.prevChunkBlockType = ""
        self.sectionId = 100


    def _formatLineNumbers( self, addOldNum, addNewNum ):
        value = u"{}".format(self.oldLineNumber) if addOldNum else ''
        # We add one space at the beggining of the line because it is "eaten" in LO-6.0
        spaces = _spaces(1 + (0 if len(value) >= 3 else 3 - len(value)))
        oldNum = u"{}{}".format( spaces, value )

        value = u"{}".format(self.newLineNumber) if addNewNum else ''
        # We add one space between the numbers
        spaces = _spaces(1 + (0 if len(value) >= 3 else 3 - len(value)))
        newNum = u"{}{}".format( spaces, value )

        return (oldNum, newNum)


    def _standard(self, text):
        return u"""<text:p text:style-name="Standard">{text}</text:p>""".format(text=_cleanForOdt(text))


    def _heading(self, level, text):
        return ( u"""<text:h text:style-name="Heading_20_{level}" text:outline-level="{level}">{text}</text:h>"""
                ).format( level=level, text=_cleanForOdt(text) )


    def _diffEqual(self, text):
        oldNum, newNum = self._formatLineNumbers( True, True )
        lineno = u"{}{}".format(oldNum, newNum)
        text = _expandIndentTabs(text)
        text = _cleanForOdt(text)
        return ( u"""<text:p text:style-name="Preformatted_20_Text">"""
                """<text:span text:style-name="lineNumbers">{lineno}</text:span>"""
                """{text}</text:p>""".format(lineno=lineno, text=text) )


    def _diffStartAddBlock(self):
        self.sectionId += 1
        return NewCode_Section_Start.format(isection=self.sectionId)


    def _diffAdd(self, text):
        oldNum, newNum = self._formatLineNumbers( False, True )
        lineno = u"{}{}".format(oldNum, newNum)
        text = _expandIndentTabs(text)
        text = _cleanForOdt(text)
        return ( u"""<text:p text:style-name="diff_20_add">"""
                """<text:span text:style-name="lineNumbers">{lineno}</text:span>"""
                """{text}</text:p>""".format(lineno=lineno, text=text) )


    def _diffStartRemoveBlock(self):
        self.sectionId += 1
        return OldCode_Section_Start.format(isection=self.sectionId)


    def _diffRemove(self, text):
        oldNum, newNum = self._formatLineNumbers( True, False )
        lineno = u"{}{}".format(oldNum, newNum)
        text = _expandIndentTabs(text)
        text = _cleanForOdt(text)
        return ( u"""<text:p text:style-name="diff_20_remove">"""
                """<text:span text:style-name="lineNumbers">{lineno}</text:span>"""
                """{text}</text:p>""".format(lineno=lineno, text=text) )


    def _diffEndBlock(self):
        return Section_End


    def _diffFilenameAdd(self, text):
        return u"""<text:p text:style-name="diff_20_fn_20_add">{text}</text:p>""".format(text=_cleanForOdt(text))


    def _diffFilenameRemove(self, text):
        return u"""<text:p text:style-name="diff_20_fn_20_remove">{text}</text:p>""".format(text=_cleanForOdt(text))


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


class OdtOverviewFormatter:
    def __init__(self):
        self.result = []

    def _standard(self, text):
        return u"""<text:p text:style-name="Standard">{text}</text:p>""".format(text=_cleanForOdt(text))

    def _timeAuthorLine(self, text):
        return ( u"""<text:p text:style-name="commit_20_id">"""
                """{text}</text:p>""".format(text=text) )

    def _heading(self, level, text):
        return ( u"""<text:h text:style-name="Heading_20_{level}" text:outline-level="{level}">{text}</text:h>"""
                ).format( level=level, text=_cleanForOdt(text) )

    def visitLines( self, text ):
        rxTimeAuthor = re.compile( r"^[0-9a-zA-Z]* *\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}" )
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
        # DiffGeneratorSettings
        self.settings = settings


    def _findTemplate( self, templateName ):
        if templateName.startswith( "." ) or templateName.startswith( "/" ):
            return templateName

        return os.path.join(os.path.dirname(os.path.realpath(__file__)), templateName)


    def _getOutputName( self ):
        now = self.settings.now
        outdir = ""
        if os.path.isdir("xtemp"):
            outdir = "xtemp"
        elif os.path.isdir("xdata"):
            outdir = "xdata"
        else:
            outdir = "."
        return "{}/~{:04}{:02}{:02}_{}.odt".format(outdir, now.year, now.month, now.day, self.settings.name)


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

        parts += OdtOverviewFormatter().getFormattedOverview( overviewText );

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

