import re
import os
from filewriter import fileWriterClass
from variable import variableClass


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
            self.errorNotifier.doError('_dataline_ is not valid after some instructions')
            return ''
        return self.dataLine

    def doAction(self, line, action, argument):
        self.result = True  # Most actions always succeed,
        retval = line                     # so set this to default
        argument = re.sub('%([a-zA-z0-9-]+?)%', self.subVar, argument)
        self.dataLine = line
        argument = re.sub('_dataline_', self.subDataline, argument)
        argument = re.sub('_([a-zA-z0-9-]+?)_', self.subBuiltin, argument)

        if action == 'include':
            if os.path.isfile(argument):
                import argument
            else:
                self.result = False
                self.errorNotifier.doError('Cannot find file ' + argument)
        elif action == 'goto':
            if self.sourceHandler.gotoLine(argument):
                retval = None  # dataLine is invalid after goto
        elif action == 'skip' or action == 'ignore':
            if self.sourceHandler.skipLines(argument):
                retval = None  # dataLine is invalid after skip
        elif action == 'search':
            self.result = self.sourceHandler.findLine(argument)
            if self.result:
                retval = None  # dataline is invalid after a successful search
        elif action == 'sub':
            retval = self.doSub(argument, line)
        elif action == 'replace':
            retval = argument
        elif action == 'finish':
            self.controller.ignoreRest()
        elif action == 'set':
            words = argument.split()
            self.variable.user('set', words[0], ' '.join(words[1:]))
        elif action == 'counter':
            words = argument.split()
            self.variable.user('counter', words[0], ' '.join(words[1:]))
        elif action == 'unset':
            self.variable.user('unset', argument)
        elif action == 'open':
            self.fileWriter.openFile(*self.fileWriter.getNumber(argument))
        elif action == 'write':
            self.fileWriter.writeFile(*self.fileWriter.getNumber(argument))
        elif action == 'writeln':
            self.fileWriter.writelnFile(*self.fileWriter.getNumber(argument))
        elif action == 'close':
            self.fileWriter.closeFile(argument)
        elif action == 'append':
            self.sourceHandler.appendLine(argument)
        elif action == 'echo':
            print(argument.strip())
        elif action == 'process' or action == 'complete':
            if argument != '':
                words = argument.split()
                self.logger.log('Calling process ' + words[0], self.logger.action)
                if len(words) > 1:  # name, file handle, data
                    if not(words[1].isdigit()):
                        self.errorNotifier.doError('Expected output stream number')
                    else:
                        firstArg = None
                        if action == 'process':
                            firstArg = line
                        try:
                            res = globals()[words[0]](firstArg,
                                                      function(a)
                                                      (self.fileWriter.write(words[1], a)),
                                                      ' '.join(words[2:]))
                            self.result = res
                        except NameError:
                            self.errorNotifier.doError("No process to call - " + words[0])
                else:
                    self.errorNotifier.doError('Usage: process function <0-9> {arguments}')
        elif action == 'call':
            if argument != '':
                words = argument.split()
                self.logger.log('Calling ' + words[0], self.logger.action)
                args = None
                if len(words) > 2:  # name, args
                    args = ' '.join(words[2:])
                try:
                    res = globals()[words[0]](args)
                    self.result = res
                except NameError:
                    self.errorNotifier.doError("No process to call - " + words[0])
            else:
                self.errorNotifier.doError('Usage: call function {arguments}')
        elif action == 'filter':
            try:
                retval = globals()[argument](line)
            except NameError:
                self.errorNotifier.doError("No filter to call - " + argument)
        elif action == 'restart':
            if self.matchedPreOrPost():
                self.logger.log('Calling reset', self.logger.section | self.logger.action)
                self.sourceHandler.reset()
            else:
                self.errorNotifier.doError('Reset only valid with ^ or $ condition')
        else:
            self.errorNotifier.doError('Unknown action')
        return retval
