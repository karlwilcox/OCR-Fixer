from collections import deque
import re


class sourceHandlerClass:

    def __init__(self, logger, errorNotifier, fileName):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.fileHandle = open(fileName)
        self.dataLine = ''
        self.fileName = fileName
        self.matches = None
        self.pipeline = deque()
        self.prependTo = None
        self.linesRead = 0 # Number to report to outside world
        self.actualLinesRead = 0 # internal count through file

    def readFromFile(self):
        lineRead = self.fileHandle.readline()
        self.actualLinesRead += 1
        return lineRead

    def nextLine(self):
        # If stuff already in the pipeline (e.g. from Append), just say we are OK
        if len(self.pipeline):
            return True
        # otherwise, try to put a new line into the pipeline from the source file
        lineRead = self.readFromFile()
        # print('line read is: %s' % lineRead)
        if lineRead != '':
            self.pipeline.append((self.actualLinesRead, lineRead))
            return True
        else:
            return False

    def appendLine(self, newText):
        self.pipeline.append((self.linesRead + 1, newText))

    def skipLines(self, number=1):
        retval = False
        try:
            num = int(number)
        except ValueError:
            num = 1
        if num < 1:
            num = 1
        for i in range(1, num):
            discard = self.readFromFile()
            if discard == '':  # EOF
                break
        self.pipeline.clear();
        retval = True
        self.logger.log('After skip line is ' + str(self.actualLinesRead), self.logger.action)
        return retval

    def gotoLine(self, number):
        try:
            num = int(number)
        except ValueError:
            self.errorNotifier.doError('Expected number: ' + number)
            return False
        if num <= self.linesRead:
            self.errorNotifier.doError('Cannot goto backwards in file')
            return False
        for i in range(self.actualLinesRead, num - 1):
            discard = self.readFromFile()
            if discard == '':  # EOF
                return False
        self.logger.log('Line is now ' + str(self.actualLinesRead), self.logger.action)
        self.pipeline.clear()
        return True

    def reset(self):
        self.dataLine = ''  # invalid until next read
        self.fileHandle.seek(0)
        self.linesRead = 0
        self.actualReadLines = 0

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
            test = self.readFromFile()
            if test == '':
                break  # EOF
            match = re.search(pattern, test)
            if match:
                self.fileHandle.seek(newpos)  # go back to previous line
                self.linesRead -= 1
                self.matches = match.groups()
                self.dataLine = None  # invalid until next read
                self.pipeline.clear()
                found = True
                break
        else:
            self.fileHandle.seek(origpos)
            self.logger.log('Pattern not found - ' + pattern, self.logger.action)
        return found

    def getLineNo(self):
        return self.linesRead

    def getLine(self):  # get current line, without reading new one
        self.linesRead, self.dataLine = self.pipeline.popleft()
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
