import re
import os
from filewriter import fileWriterClass
from variable import variableClass
from process import processStoreClass
from process import pipelineStoreClass


class actionClass():
    """docstring for actionClass"""
    def __init__(self, logger, errorNotifier, sourceHandler, controller):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.sourceHandler = sourceHandler
        self.controller = controller
        self.dataLine = None
        self.result = None
        self.fileWriter = fileWriterClass(logger, errorNotifier)
        self.variable = variableClass(logger, errorNotifier, sourceHandler, controller)
        self.matchedPreOrPost = None
        self.processStore = processStoreClass(logger, errorNotifier)
        self.streamStore = pipelineStoreClass(logger, errorNotifier, self.processStore)

    def setHandlers(self, matchedPreOrPost):
        self.matchedPreOrPost = matchedPreOrPost

    def getLastResult(self):
        return self.result

    def subVar(self, match):
        return self.variable.user('get', match.group(1))

    def subBuiltin(self, match):
        return self.variable.builtin(match.group(1))

    def doSub(self, expression, line):
        parts = re.search('/(?P<patt>.*?)/(?P<repl>.*?)/(?P<flag>.*)$',
                          expression)
        if not(parts):
            self.errorNotifier.doError('Error in substitution')
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
        self.logger.log(pattern + ' / ' + replacement + ' / ' + flagstring, self.logger.action)
        return re.sub(pattern, replacement, line, flags=flags)

    def subDataline(self, match):
        if self.dataLine is None:
            self.errorNotifier.doError('_dataline_ is not valid')
            return ''
        return self.dataLine

    def argToWords(self, arg):
        '''split input into words, respecting quotation marks (& escapes).
        Returns tuple of words'''
        words = []
        word = ''
        inQuotes = False
        i = 0
        while i < len(arg):
            ch = arg[i]
            if ch == '\\':
                if i + 1 < len(arg) and arg[i + 1] == '"':
                    word += '"'
                    i += 2
                else:
                    word += ch
            elif ch == '"':
                if inQuotes:
                    inQuotes = False
                    if word != '':
                        words.append(word)
                        word = ''
                else:
                    inQuotes = True
            elif ch.isspace():
                if word != '':
                    words.append(word)
                    word = ''
            else:
                word += ch
            i += 1
        if word != '':
            words.append(word)
        return tuple(words)

    def doAction(self, line, action, argument):
        self.result = True  # Most actions always succeed,
        retval = line                     # so set this to default
        argument = re.sub('%([a-zA-z0-9-]+?)%', self.subVar, argument)
        self.dataLine = line
        argument = re.sub('_dataline_', self.subDataline, argument)
        argument = re.sub('_([a-zA-z0-9-]+?)_', self.subBuiltin, argument)
        words = self.argToWords(argument)
        if action == 'goto':
            if self.sourceHandler.gotoLine(words[0]):
                retval = None  # dataLine is invalid after goto
        elif action == 'skip' or action == 'ignore':
            if self.sourceHandler.skipLines(words[0]):
                retval = None  # dataLine is invalid after skip
        elif action == 'search':
            self.result = self.sourceHandler.findLine(words[0])
            if self.result:
                retval = None  # dataline is invalid after a successful search
        elif action == 'sub':
            retval = self.doSub(words[0], line)
        elif action == 'replace':
            retval = argument  # NOTE, does not use words version
        elif action == 'finish' or action == 'moveon':
            self.controller.ignoreRest()
        elif action == 'set':
            self.variable.user('set', words[0], ' '.join(words[1:]))
        elif action == 'counter':
            self.variable.user('counter', words[0], ' '.join(words[1:]))
        elif action == 'unset':
            for w in words:
                self.variable.user('unset', w)
        elif action == 'open':
            self.fileWriter.openFile(*self.fileWriter.getNumber(words))
        elif action == 'write':
            self.fileWriter.writeFile(*self.fileWriter.getNumber(words))
        elif action == 'writeln':
            self.fileWriter.writelnFile(*self.fileWriter.getNumber(words))
        elif action == 'close':
            self.fileWriter.closeFile(*self.fileWriter.getNumber(words))
        elif action == 'append':
            self.sourceHandler.appendLine(argument)  # NOTE, does not use words
        elif action == 'echo':
            print(' '.join(words))
        elif action == 'process':
            if len(words):
                self.logger.log('Calling process ' + words[0], self.logger.action)
                if len(words) > 1:  # [0-9] name args...
                    try:
                        number = int(words[0])
                        if len(words) > 2:
                            args = words[2:]
                        else:
                            args = None
                        self.processStore.addProcess(number, words[1], args)
                    except ValueError:
                        self.errorNotifier.doError('Expected process number')
                else:
                    self.errorNotifier.doError('Usage: process [0-9] name {arguments}')
        elif action == 'stream':
            if len(words):
                self.logger.log('Calling process ' + words[0], self.logger.action)
                if len(words) > 1:  # name, processes
                    if not(words[0].islower()):
                        self.errorNotifier.doError('Expected stream id (a-z)')
                    else:
                        args = words[1:]
                        self.streamStore.addPipeline(words[0], args)
                else:
                    self.errorNotifier.doError('Usage: stream [a-z] [0-9]+')
        elif action == 'sendto':
            if len(words):
                self.logger.log('Calling process ' + words[0], self.logger.action)
                if len(words) > 1:
                    stream = words[0]
                    content = words[1:]
                    self.streamStore.runPipeline(stream, ' '.join(content))
                else:
                    print ('content missing')
            else:
                print ('stream id missing')
        elif action == 'flush':
            if len(words):
                self.logger.log('Calling process ' + words[0], self.logger.action)
                if len(words) > 0:
                    stream = words[0]
                    self.streamStore.flushPipeline(stream)
                else:
                    print ('content missing')
            else:
                print ('stream id missing')

        elif action == 'filter':
            if len(words):
                self.logger.log('Calling process ' + words[0], self.logger.action)
                if len(words) > 1:
                    stream = words[0]
                    content = words[1:]
                    retval = self.streamStore.runPipeline(stream, ' '.join(content))
                else:
                    print ('content missing')
            else:
                print ('stream id missing')
        elif action == 'restart':
            if self.matchedPreOrPost():
                self.logger.log('Calling reset', self.logger.section | self.logger.action)
                self.sourceHandler.reset()
            else:
                self.errorNotifier.doError('Reset only valid with ^ or $ condition')
        else:
            self.errorNotifier.doError('Unknown action')
        return retval
