#!/usr/bin/env python

import re
import sys
import os
from collections import deque
from narrative import *


class Logger():
    fileHandle = None
    control = 1
    section = 2
    condition = 4
    action = 8
    variable = 16
    showLevel = 0

    def __init__(self, outputFile=None):
        if outputFile is not None:
            try:
                self.fileHandle = open(outputFile, "w")
            except IOError:
                doError('Could not open log File ' + outputFile)
                self.fileHandle = None

    def log(self, message, pattern=255):
        if pattern & self.showLevel:
            if self.fileHandle is not None:
                self.fileHandle.write(message.strip + '\n')
            else:
                print(message.strip())


def checkRange(condition, line):
    retval = False
    if condition == ':blank:':
        if len(line) == 0 or re.match('^[[:blank:]]*$', line):
            retval = True
    elif condition == ':all-upper:':
        retval = not(re.match('[^[:upper:][:punct:]]', line))
    else:
        doError("Unknown special case match - " + condition)
    return retval


def checkCondition(condition, lineNo, line):
    retval = False
    start = 0
    end = 0
    negate = False

    ch = condition[0]

    if ch == '!':
        negate = True
        condition = condition[1:]
        ch = condition[0]
    if ch == '&':
        retval = checkCondition.lastCheck
    elif ch == '?':
        if checkCondition.lastCheck:
            retval = processLineActions.result
        if negate:  # only negate the last action, NOT the
            retval = not(retval)  # last condition
            negate = False
    else:
        # Special case matches first, only true if special values for lineNo
        if lineNo == '^' or lineNo == '$':
            retval = (lineNo == ch)
            checkCondition.matchedPreOrPost = retval
        else:  # and nothing else ever matches
            checkCondition.matchedPreOrPost = False
            if ch == '^' or ch == '$':
                retval = False  # These never match anywhere else
            elif ch == '*':
                retval = True
            elif ch == '/':
                logger.log('Testing for match with ' + condition[1:-1], logger.condition)
                match = re.search(condition[1:-1], line)
                if match:
                    retval = True
                    dataObject.matches = match.groups()
            elif ch.isdigit():
                try:
                    dash = condition.find('-')
                    if dash > 0:  # must be a range
                        start = int(condition[0:dash])
                        end = int(condition[dash + 1:])
                    else:
                        start = int(condition)
                        end = start
                except ValueError:
                    doError('range condition should be number-number')
                else:
                    if end < start:
                        doError('end is before start')
                    else:
                        lineNo = int(lineNo)
                        logger.log('testing ' + str(lineNo) + ' against range ' +
                                   str(start) + ' to ' + str(end), logger.condition)
                        retval = lineNo >= start and lineNo <= end
            elif ch == ':':
                retval = checkRange(condition, line)
            else:
                doError('Unknown condition')
    if retval:
        logger.log('Condition ' + condition + ' matches: ' + str(line), logger.condition)
    if negate:
        retval = not(retval)
    checkCondition.lastCheck = retval
    return retval


checkCondition.lastCheck = False
checkCondition.matchedPreOrPost = False  # flag to show if condition was ^ or $


def variable(action, name, value=''):
    global logger
    logger.log(action + ' / ' + name + ' / ' + str(value), logger.variable)
    retval = ''
    if action == 'set':
        variable.values[name] = value
        if name == 'loglevel':
            logger.showLevel = int(value)
    elif action == 'get':
        if name in variable.counters:
            variable.counters[name] += 1
            retval = str(variable.counters[name])
        else:
            retval = variable.values.get(name, '(none)')
    elif action == 'counter':
        if value == '':
            value = 0
        variable.counters[name] = value
    elif action == 'unset' and name in variable.values:
        del variable.values[name]
    else:
        doError('Unknown action for parameter')
    return retval


variable.values = {}
variable.counters = {}


def builtin(varname):
    logger.log("Invoke builtin - " + varname, logger.variable)
    name = varname.lower()
    retval = ''
    if name == 'origline':
        retval = dataObject.getLine()
    elif name == 'datacount':
        retval = dataObject.getLineNo()
    elif name == 'datafile':
        retval = dataObject.fileName
    elif name == 'controlline':
        retval = controlObject.getLine()
    elif name == 'controlcount':
        retval = controlObject.getLineNo()
    elif name == 'controlfile':
        retval = controlObject.fileName
    elif name == 'section':
        retval = controlObject.getPass()
    elif name == 'match':
        retval = dataObject.lastMatch()
    elif name == 'loglevel':
        retval = logger.showLevel
    elif 'sub' == name[:3]:
        if len(name > 4 and name[3].isdigit()):
            subNum = name[3]
        else:
            subNum = 1
        retval = dataObject.lastMatch(subNum)
    else:
        doError('Unknown built-in: ' + varname)
    return str(retval)


def doError(message):
    number = controlObject.getLineNo()
    line = controlObject.getLine()
    if not(number in doError.messageLog):
        print(message.strip() + ' (line ' + str(number) + ') ', line)
        doError.messageLog.append(number)


doError.messageLog = []


def subVar(match):
    return variable('get', match.group(1))


def subBuiltin(match):
    return builtin(match.group(1))


class fileWriterClass:
    def __init__(self):
        self.files = {}

    def openFile(self, number, fileName):
        self.closeFile(number)
        try:
            handle = open(fileName, "w")
        except IOError:
            doError('Could not open ' + fileName)
            return False
        self.files[number] = handle
        return True

    def closeFile(self, number):
        if number in self.files:
            self.files[number].close()
            del(self.files[number])
            return True
        return False

    def writeFile(self, number, data):
        if number in self.files:
            self.files[number].write(data)
            return True
        return False

    def writelnFile(self, number, data):
        if number in self.files:
            self.files[number].write(data + '\n')
            return True
        return False

    def getNumber(self, controlLine):
        if controlLine[0].isdigit():
            number = controlLine[0]
            controlLine = controlLine[1:].strip()
        else:
            number = '1'
        return (number, controlLine)


class dataFile:
    def __init__(self, fileName):
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
            logger.log('After skip line is ' + str(self.dataCount), logger.action)
        return retval

    def gotoLine(self, number):
        try:
            num = int(number)
        except ValueError:
            doError('Expected number: ' + number)
            return False
        if num <= self.dataCount:
            doError('Cannot goto backwards in file')
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
            logger.log('Pattern not found - ' + pattern, logger.action)
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


class controlFile:
    def __init__(self, fileName):
        self.fileName = fileName
        self.controlLines = []
        self.passMap = []
        self.currentPass = -1
        self.currentLine = -1
        controlFileLine = 0
        passIndex = 0
        try:
            for line in open(fileName):
                controlFileLine += 1
                line = line.strip()
                if re.match('#', line):
                    continue    # ignore comment only lines
                if line == '':
                    continue    # ignore empty lines
                if line[0] == '[':
                        passName = re.findall('\[(.*)\]', line)
                        self.passMap.append({'name': passName[0],
                                             'start': len(self.controlLines)})
                        if passIndex > 0:
                            self.passMap[passIndex - 1]['end'] = len(self.controlLines) - 1
                        passIndex += 1
                        continue
                if passIndex == 0:  # We have a control, but no passname as yet
                    self.passMap.append({'name': '(unnamed)',
                                        'start': len(self.controlLines)})
                    passIndex = 1
                self.controlLines.append((controlFileLine, self.getParts(line)))
            self.passMap[passIndex - 1]['end'] = len(self.controlLines) - 1
        except IOError:
            print('Control file not found\n')
            exit()
        if logger.showLevel & logger.control:
            print(self.passMap)
            print(self.controlLines)

    def getParts(self, line):
        cond = ''
        act = ''
        arg = ''
        inQuotes = False

        state = 'start'
        prev = ''

        i = 0
        while i < len(line):
            ch = line[i]
            if i < len(line) - 1:
                nextCh = line[i + 1]
            else:
                nextCh = ''
            i += 1
            # Not else
            if ch == '#':
                break
            if ch == '"':
                if inQuotes:
                    inQuotes = False
                else:
                    inQuotes = True
                continue
            if ch == '\\':
                if (nextCh == '"' or nextCh == '#' or
                   nextCh == '%' or nextCh == '_'):
                    ch = nextCh
                    i += 1
            # Not else
            if state == 'start':
                if not(inQuotes) and ch.isspace():
                    continue
                if ch == '/':
                    state = 'regex'
                else:
                    state = 'cond'
                cond += ch
            elif state == 'cond':
                if not(inQuotes) and ch.isspace():
                    state = 'action'
                else:
                    cond += ch
            elif state == 'regex':  # might contain a space, so we need to look
                if ch == '/' and prev != '\\':  # for unescaped slash
                    state = 'spaces1'  # might be followed by spaces
                cond += ch
            elif state == 'spaces1':
                if not(inQuotes) and ch.isspace():
                    continue  # ignore initial whitespace
                else:
                    act = ch
                    state = 'action'
            elif state == 'action':
                if not(inQuotes) and ch.isspace():
                    state = 'arg'
                else:
                    act += ch
            elif state == 'arg':
                arg += ch
            prev = ch
        logger.log(cond + ' / ' + act + ' / ' + arg, logger.control)
        return (cond, act, arg)

    def setPass(self, index):
        self.currentPass = index
        self.currentLine = self.passMap[self.currentPass]['start'] - 1
        logger.log('Working on pass ' + self.passMap[self.currentPass]['name'], logger.section)

    def nextPass(self):
        nextPassIndex = self.currentPass + 1
        if nextPassIndex < len(self.passMap):
            return nextPassIndex
        else:
            return False

    def namedPass(self, name):
        for i in range(0, len(self.passMap)):
            if name == self.passMap[i]['name']:
                return i
        else:  # no matching name
            doError("Pass name not found")
        return False

    def nextLine(self):
        if self.currentLine < self.passMap[self.currentPass]['end']:
            self.currentLine += 1
            return True
        else:
            logger.log('At end of pass', 10)
            # self.currentLine = self.passMap[self.currentPass]['start']
            return False

    def getPass(self):
        if self.currentPass >= 0 and self.currentPass < len(self.passMap):
            return self.passMap[self.currentPass]['name']
        else:
            return '(None)'

    def getLine(self):
        if self.currentLine >= 0:
            return self.controlLines[self.currentLine][1]
        else:
            return '(None)'

    def getLineNo(self):
        if self.currentLine >= 0:
            return self.controlLines[self.currentLine][0]
        else:
            return '(None)'

    def ignoreRest(self):
        logger.log('Ignoring by going to end of section', logger.section)
        self.currentLine = self.passMap[self.currentPass]['end']

    def reset(self):
        self.currentLine = self.passMap[self.currentPass]['start'] - 1


def doSub(expression, line):
    parts = re.search('/(?P<patt>.*?)/(?P<repl>.*?)/(?P<flag>.*)$',
                      expression)
    if not(parts):
        doError('Error in substitution')
        return line
    pattern = parts.group('patt')
    replacement = parts.group('repl')
    flagstring = parts.group('flag').lower()
    flags = 0
    for f in flagstring:
        if f == 'i':
            flags |= re.IGNORECASE
        elif f == 'm':
            flags |= re.MULTILINE
        elif f == 's':
            flags |= re.DOTALL
        elif f == 'u':
            flags |= re.UNICODE
    logger.log(pattern + ' / ' + replacement + ' / ' + flagstring, logger.action)
    return re.sub(pattern, replacement, line, flags=flags)


def subDataline(match):
    if subDataline.dataLine is None:
        doError('_dataline_ is not valid after some instructions')
        return ''
    return subDataline.dataLine


def processLineActions(line, action, argument):
    global fileWriter
    processLineActions.result = True  # Most actions always succeed,
    retval = line                     # so set this to default
    argument = re.sub('%([a-zA-z0-9-]+?)%', subVar, argument)
    subDataline.dataLine = line
    argument = re.sub('_dataline_', subDataline, argument)
    argument = re.sub('_([a-zA-z0-9-]+?)_', subBuiltin, argument)

    if action == 'include':
        if os.path.isfile(argument):
            import argument
        else:
            processLineActions.result = False
            doError('Cannot find file ' + argument)
    elif action == 'goto':
        if dataObject.gotoLine(argument):
            retval = None  # dataLine is invalid after goto
    elif action == 'skip' or action == 'ignore':
        if dataObject.skipLines(argument):
            retval = None  # dataLine is invalid after skip
    elif action == 'search':
        processLineActions.result = dataObject.findLine(argument)
        if processLineActions.result:
            retval = None  # dataline is invalid after a successful search
    elif action == 'sub':
        retval = doSub(argument, line)
    elif action == 'replace':
        retval = argument
    elif action == 'finish':
        controlObject.ignoreRest()
    elif action == 'set':
        words = argument.split()
        variable('set', words[0], ' '.join(words[1:]))
    elif action == 'counter':
        words = argument.split()
        variable('counter', words[0], ' '.join(words[1:]))
    elif action == 'unset':
        variable('unset', argument)
    elif action == 'open':
        fileWriter.openFile(*fileWriter.getNumber(argument))
    elif action == 'write':
        fileWriter.writeFile(*fileWriter.getNumber(argument))
    elif action == 'writeln':
        fileWriter.writelnFile(*fileWriter.getNumber(argument))
    elif action == 'close':
        fileWriter.closeFile(argument)
    elif action == 'append':
        dataObject.appendLine(argument)
    elif action == 'echo':
        print(argument.strip())
    elif action == 'process' or action == 'complete':
        if argument != '':
            words = argument.split()
            logger.log('Calling process ' + words[0], logger.action)
            if len(words) > 1:  # name, file handle, data
                if not(words[1].isdigit()):
                    doError('Expected output stream number')
                else:
                    firstArg = None
                    if action == 'process':
                        firstArg = line
                    try:
                        res = globals()[words[0]](firstArg,
                                                  function(a)
                                                  (fileWriter.write(words[1], a)),
                                                  ' '.join(words[2:]))
                        processLineActions.result = res
                    except NameError:
                        doError("No process to call - " + words[0])
            else:
                doError('Usage: process function <0-9> {arguments}')
    elif action == 'call':
        if argument != '':
            words = argument.split()
            logger.log('Calling ' + words[0], logger.action)
            args = None
            if len(words) > 2:  # name, args
                args = ' '.join(words[2:])
            try:
                res = globals()[words[0]](args)
                processLineActions.result = res
            except NameError:
                doError("No process to call - " + words[0])
        else:
            doError('Usage: call function {arguments}')
    elif action == 'filter':
        try:
            retval = globals()[argument](line)
        except NameError:
            doError("No filter to call - " + argument)
    elif action == 'restart':
        if checkCondition.matchedPreOrPost:
            logger.log('Calling reset', logger.section | logger.action)
            dataObject.reset()
        else:
            doError('Reset only valid with ^ or $ condition')
    else:
        doError('Unknown action')
    return retval


def readBook(controlFileName, dataFileName):
    global controlObject
    global dataObject
    global fileWriter

    controlObject = controlFile(controlFileName)
    dataObject = dataFile(dataFileName)
    fileWriter = fileWriterClass()

    exitNow = False
    dataObject.reset()
    currentPass = controlObject.nextPass()  # Go to the first pass
    # Process this pass
    while not(exitNow):
        newPass = False
        controlObject.setPass(currentPass)
        # Process any pre-pass actions
        while controlObject.nextLine():
            condition, action, argument = controlObject.getLine()
            if checkCondition(condition, '^', ''):
                processLineActions('', action, argument)
        # For each line of input data
        while not(exitNow) and dataObject.nextLine():
            dataLine = dataObject.getLine()
            controlObject.reset()
            # For each line in the current pass of the control file
            while not(newPass) and controlObject.nextLine():
                condition, action, argument = controlObject.getLine()
                if checkCondition(condition, dataObject.getLineNo(), dataLine):
                    # process pass related commands first
                    if action == 'next':
                        newPass = controlObject.nextPass()
                        break
                    elif action == 'section':
                        newPass = controlObject.namedPass(argument)
                    elif action == 'quit' or action == 'exit':
                        exitNow = True  # Force exit from outer loop
                        break
                    else:  # action must be related to the actual content
                        dataLine = processLineActions(dataLine, action, argument)
        # Process any post-pass actions
        controlObject.reset()
        while controlObject.nextLine():
            condition, action, argument = controlObject.getLine()
            if checkCondition(condition, '$', ''):
                processLineActions('', action, argument)
        if not(newPass):
            newPass = controlObject.nextPass()
            if not(newPass):
                exitNow = True
        currentPass = newPass  # set the pass no. here, so we close current pass first


# Execution starts here
if len(sys.argv) < 3:
    print('Usage: ' + sys.argv[0] + ' control-file data-file {log-file}')
    exit()
if len(sys.argv) > 3:
    logger = Logger(sys.argv[3])
else:
    logger = Logger()
readBook(sys.argv[1], sys.argv[2])
