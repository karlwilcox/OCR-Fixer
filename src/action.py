import re
# import os
from filewriter import fileWriterClass
from variable import variableClass
from process import processStoreClass
from process import pipelineStoreClass
from superclasses import processSuperClass


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
        processSuperClass.variables = self.variable
        self.matchedPreOrPost = None
        self.processStore = processStoreClass(logger, errorNotifier)
        self.streamStore = pipelineStoreClass(logger, errorNotifier, self.processStore)
        self.exitNow = False
        self.nextPass = False

    def setHandlers(self, matchedPreOrPost):
        self.matchedPreOrPost = matchedPreOrPost

    def getLastResult(self):
        return self.result

    def subVar(self, match):
        return self.variable.user('get', match.group(1))

    def subBuiltin(self, match):
        return self.variable.builtin(match.group(1))

    def doSub(self, expression, line):
        # TODO need to search for \/ in string somehow..? Allow search for forward slash
        parts = re.search('(.)(?P<patt>.*?)\1(?P<repl>.*?)\1(?P<flag>.*)$',
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
        self.logger.log(pattern + ' / ' + replacement + ' / ' + flagstring + ' ' + line, self.logger.action)
        return re.sub(pattern, replacement, line, flags=flags)

    def subDataline(self, match):
        if self.dataLine is None:
            self.errorNotifier.doError('_dataline_ for line no. ' + str(self.sourceHandler.getLineNo()) + ' is not valid')
            return ''
        return self.dataLine

    def doCorrect(self, line, words):
        if len(words) != 2:
            self.errorNotifier.doError("usage: correct original replacement")
            return line
        return line.replace(words[0], words[1])


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
                    i += 1
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
                if inQuotes:
                    word += ch
                else:
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
        self.result = True  # Most actions always succeed, so set as default
        self.newPass = False
        retval = line
        if argument != "":
            # substitute variable, unless % characters are preceeded by backslash
            argument = re.sub('(?<!\\\\)%([a-zA-z0-9-]+?)(?<!\\\\)%', self.subVar, argument)
            self.dataLine = line
            # substitute current data, unless _ characters are preceeded by backslash
            argument = re.sub('(?<!\\\\)_dataline_(?<!\\\\)', self.subDataline, argument)
            # substitute built-ins, unless _ characters are preceeded by backslash
            argument = re.sub('(?<!\\\\)_([a-zA-z0-9-]+?)(?<!\\\\)_', self.subBuiltin, argument)
            # Now remove any backslashes that were escaping the above
            argument = re.sub('\\\\(?=[%_])', '', argument)
            # finally, split the argument into words, respecting quote marks (and more escapes!)
            words = self.argToWords(argument)
        else:
            words = ['',''];
        self.logger.log('> ' + action + ' ' + argument, self.logger.action)
        if action == 'next':
            self.newPass = self.controller.nextPass()
        elif action == 'section':
            self.newPass = self.controller.namedPass(words[0])          # substituted
        elif action == 'goto':
            if self.sourceHandler.gotoLine(words[0]):
                retval = None  # dataLine is invalid after goto
                self.controller.ignoreRest()
        elif action == 'skip' or action == 'ignore':
            if self.sourceHandler.skipLines(words[0]):
                retval = None  # dataLine is invalid after skip
                self.controller.ignoreRest()
        elif action == 'quit' or action == 'exit':
            self.exitNow = True  # Force exit from outer loop
        elif action == 'search':
            self.result = self.sourceHandler.findLine(words[0])
            if self.result:
                retval = None  # dataline is invalid after a successful search
        elif action == 'correct' or action == 'fix':
            retval = self.doCorrect(line, words)
        elif action == 'delete' or action == 'del':
            retval = self.doCorrect(line, [words[0], ''])
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
                stream = words[0]
                content = ''
                if len(words) > 1:
                    content = ' '.join(words[1:])
                self.streamStore.runPipeline(stream, content)
            else:
                print ('stream id missing')
        elif action == 'flush':
            if len(words):
                self.logger.log('Flushing stream ' + words[0], self.logger.action)
                stream = words[0]
                self.streamStore.flushPipeline(stream)
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
