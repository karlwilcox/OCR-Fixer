

class narrativeClass(object):
    """docstring for narrativeClass"""
    def __init__(self, arg):
        super(narrativeClass, self).__init__()
        self.arg = arg
        self.paragraph = ''
        self.lineInPara = 0
        self.paraStart = '<p>'
        self.paraEnd = '</p>'
        self.headingStart = '<h2>'
        self.headingEnd = '</h2>'

    def setParaStart(self, arg):
        self.paraStart = arg

    def setParaEnd(self, arg):
        self.paraEnd = arg

    def setHeadingStart(self, arg):
        self.headingStart = arg

    def setHeadingEnd(self, arg):
        self.headingEnd = arg


def paragraph(line, writeFunc, args):
    # returns true if a paragraph is written, false otherwise
    if True or args == 'blank':
        if len(line) > 0:  # got some text
            if paragraph.text == '':
                paragraph.text = line
            else:
                if paragraph.text[-1] == '-':
                    paragraph.text = paragraph.text[0:-1] + line
                else:
                    paragraph.text += ' ' + line
            return False
        else:  # blank line, end of paragraph
            if len(paragraph.text):
                writeFunc('<p>' + paragraph.text + '</p>\n')
                paragraph.text = ''
                return True
            return False
    return False


paragraph.text = ''


def paraWithHeadings(line, writeFunc, args):
    # TODO get paragraph and heading tags from args
    if line is None or len(line) > 0:  # Not blank
        if paraWithHeadings.paragraph == '':  # new para
            paraWithHeadings.paragraph = line
        else:  # add to existing para
            if paraWithHeadings.paragraph.text[-1] == '-':
                paraWithHeadings.paragraph.text = paragraph.text[0:-1] + line
            else:
                paraWithHeadings.paragraph.text += ' ' + line
        paraWithHeadings.lineInPara += 1
        return False
    else:  # blank line, end of para (or heading)
        if paraWithHeadings.lineInPara == 1:  # Assume single line is a heading
            writeFunc('\n<h2>%s</h2>\n' % paraWithHeadings.paragraph)
            paraWithHeadings.paragraph = ''
            paraWithHeadings.lineInPara = 0
        elif paraWithHeadings.lineInPara > 1:  # Assume this is a paragraph
            writeFunc('\n<p>%s</p>\n' % paraWithHeadings.paragraph)
            paraWithHeadings.paragraph = ''
            paraWithHeadings.lineInPara = 0
        # else no content, so do nothing
        return True




