from superclasses import processSuperClass
import re


class paragraphClass(processSuperClass):
    """docstring for narrativeClass"""
    def __init__(self, args):
        super(paragraphClass, self).__init__()
        self.text = ''
        self.lineInPara = 0
        # self.blank = True
        self.nosingle = True
        try:
            if 'nosingle' in args:
                self.nosingle = True
        except TypeError:
            pass
        # if 'short' in args:
        #     self.short = True

    def doAction(self, line):
        retval = None
        if line is not None and len(line) > 0:  # got some text
            if self.text == '':
                self.text = line
            else:
                if self.text[-1] == '-':
                    self.text = self.text[0:-1] + line
                else:
                    self.text += ' ' + line
        else:  # blank line, end of paragraph
            retval = ''  # pass on the blank line
            if self.text != '':
                if not(self.nosingle and self.lineInPara > 1):
                    retval = self.text
                self.text = ''
                self.lineInPara = 0
        return retval

    def flush(self, line):
        if line is not None:
            self.text += line
        return self.text


class headingClass(processSuperClass):
    def __init__(self, args):
        super(headingClass, self).__init__()
        self.text = ''
        self.lineCount = 0
        self.args = args

    def doAction(self, line):
        retval = None
        if line is not None and len(line) > 0:  # Got some text
            self.text = line
            self.lineCount += 1
        else:  # got blank line
            if self.lineCount == 1:  # Single line, so header
                retval = self.text
                self.text = ''
            self.lineCount = 0
        return retval

    def flush(self, line):
        if self.lineCount == 1:
            return self.text
        else:
            return ''


class alphaEntryClass(processSuperClass):
    """docstring for alphaEntryClass"""
    def __init__(self, args):
        super(alphaEntryClass, self).__init__()
        self.args = args
        self.entry = ''
        self.inEntry = False
        self.sourceLine = 0

    def doAction(self, line):
        retval = None
        if line == '':
            return retval

        matches = re.search('^([[:upper:]][[:upper:][:punct:]]+)', line)
        if matches:  # and matches.group(1)[1] != '.':  # start a new entry
            if self.inEntry:
                retval = self.entry
            self.inEntry = True
            self.sourceLine = processSuperClass.variables.builtin('dataCount')
            self.entry = line
        else:
            self.entry += ' ' + line
        return retval

    def flush(self, line):
        if line != '':
            self.entry += ' ' + line
        self.inEntry = False
        return self.entry
