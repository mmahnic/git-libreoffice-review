
class MarkdownFormatter:
    def __init__(self):
        pass


    def getFormattedDiff( self, text ):
        result = []
        section = ""
        blockformat = ""

        def startSection( sectionType, setFormat="" ):
            nonlocal section, result, blockformat
            endSection()
            if setFormat != "":
                result += [ " ", "~~~~~~~~~~~~~~~ { .%s }" % setFormat ]
            section = sectionType
            blockformat = setFormat

        def endSection():
            nonlocal section, result, blockformat
            if section != "":
                if blockformat != "":
                    result += [ "", "~~~~~~~~~~~~~~~" ]
                section = ""

        for line in text:
            if line.startswith( "[cmd]" ):
                endSection()
                result += [ "", line.replace( "[cmd]", "#" ) ]
                continue
            elif line.startswith( "diff" ):
                endSection()
                result += [ "", "## " + line ]
                continue
            elif line.startswith( "@@" ):
                endSection()
                result += [ "", "### " + line ]
                continue
            elif line.startswith( "---" ) or line.startswith( "+++" ):
                if section != "---":
                    startSection( "---", "filepaths" )
            elif line.startswith( "-" ):
                if section != "-":
                    startSection( "-", "removed" )
            elif line.startswith( "+" ):
                if section != "+":
                    startSection( "+", "added" )
            elif line.startswith( " " ):
                if section != " ":
                    startSection( " ", "unchanged" )
            else:
                endSection()
            result.append( line )

        endSection()
        return result


