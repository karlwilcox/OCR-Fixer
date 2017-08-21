from collections import deque
import re


class sourceHandlerClass:

    def __init__(self, logger, errorNotifier, fileName):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.fileHandle = open(fileName)
        self.dataCount = 0
        self.dataLine = ''
        self.fileName = fileName
        self.matches = None
        self.pipeline = deque()
        self.prependTo = None
        self.linesRead = 0

    def nextLine(self):
        lineRead = self.fileHandle.readline()
        if lineRead != '':
            self.linesRead += 1
            self.pipeline.append((self.linesRead, lineRead))
            return True
        else:
            if len(self.pipeline):
                return True
            return False

    def appendLine(self, newText):
        self.pipeline.append((self.dataCount + 1, newText))

    def skipLines(self, number=1):
        retval = False
        try:
            num = int(number)
        except ValueError:
            num = 1
        if num < 1:
            num = 1
        self.dataLine = None  # invalid after skip, until next read
        for i in range(1, num):
            self.dataCount += 1
            discard = self.fileHandle.readline()
            if discard == '':  # EOF
                break
        else:
            retval = True
            self.logger.log('After skip line is ' + str(self.dataCount), self.logger.action)
        return retval

    def gotoLine(self, number):
        try:
            num = int(number)
        except ValueError:
            self.errorNotifier.doError('Expected number: ' + number)
            return False
        if num <= self.dataCount:
            self.errorNotifier.doError('Cannot goto backwards in file')
        self.dataLine = None  # invalid after goto, until next read
        for i in range(self.dataCount, num - 1):
            discard = self.fileHandle.readline()
            if discard == '':  # EOF
                return False
        self.dataCount = num - 1
        return True

    def reset(self):
        self.dataLine = ''  # invalid until next read
        self.dataCount = 0
        self.fileHandle.seek(0)
        self.linesRead = 0

    def findLine(self, pattern):
        found = False
        limit = 100
        digits = re.match('([0-9]+) ?(.+)$', pattern)
        if digits:
            limit = int(digits.group(1))
            pattern = digits.group(2)
        counter = 0
        origpos = self.fileHandle.tell()  # remember where we are
        while counter < limit:
            counter += 1
            newpos = self.fileHandle.tell()  # remember where we are
            test = self.fileHandle.readline()
            self.dataCount += 1
            if test == '':
                break  # EOF
            match = re.search(pattern, test)
            if match:
                self.fileHandle.seek(newpos)  # go back to previous line
                self.dataCount -= 1
                self.matches = match.groups()
                self.dataLine = None  # invalid until next read
                found = True
                break
        else:
            self.fileHandle.seek(origpos)
            self.logger.log('Pattern not found - ' + pattern, self.logger.action)
        return found

    def getLineNo(self):
        return self.dataCount

    def getLine(self):  # get current line, without reading new one
        self.dataCount, self.dataLine = self.pipeline.popleft()
        return self.dataLine

    def lastMatch(self, sub=0):
        if self.matches is None:
            return '(none)'
        if sub < len(self.matches):
            return self.matches[sub]
        else:
            return '(none)'

    def setMatch(self, matches):
        self.matches = matches
