import re
from filewriter import fileWriterClass
from variable import variableClass
from process import processStoreClass
from process import pipelineStoreClass
from superclasses import processSuperClass
from html import htmlTagsClass


class actionClass():
    """docstring for actionClass"""
    def __init__(self, logger, errorNotifier, sourceHandler, controller):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.sourceHandler = sourceHandler
        self.controller = controller
        self.result = None
        self.fileWriter = fileWriterClass(logger, errorNotifier)
        self.variable = variableClass(logger, errorNotifier, sourceHandler, controller)
        processSuperClass.variables = self.variable
        self.matchedPreOrPost = None
        self.processStore = processStoreClass(logger, errorNotifier)
        self.streamStore = pipelineStoreClass(logger, errorNotifier, self.processStore)
        self.html = htmlTagsClass(logger, self.fileWriter, self.variable, errorNotifier)
        self.exitNow = False
        self.nextPass = False

    def setHandlers(self, matchedPreOrPost):
        self.matchedPreOrPost = matchedPreOrPost

    def getLastResult(self):
        return self.result

    def doSub(self, line, expression):
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

    def doCorrect(self, line, argument):
        words = self.argToWords(argument)
        if len(words) != 2:
            self.errorNotifier.doError("usage: correct original replacement")
            return line
        return line.replace(words[0], words[1])

    def doDelete(self, line, argument):
        words = self.argToWords(argument)
        for word in words:
            line = line.replace(word, '')
        return line

    def argToWords(self, arg, min = 1):
        '''split input into words, respecting quotation marks (& escapes).
        Returns tuple of words at least min words long'''
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
        if len(words) < min:
            words.append('')
        return tuple(words)

    def doAction(self, line, action, filehandle, argument, match):
        self.result = True  # Most actions always succeed, so set as default
        self.nextPass = False
        retval = line
        if argument != "":
            # substitute variable, unless % characters are preceeded by backslash
            argument = self.variable.subAll(argument, line)
            # words = self.argToWords(argument)
            # allWords = ' '.join(words)
        # else:
        #     words = ['','']
        #     allWords = '';
        self.logger.log('> ' + action + ' ' + argument, self.logger.action)
        if action == 'next':
            self.nextPass = self.controller.nextPass()
            self.controller.ignoreRest()
        elif action == 'section':
            self.nextPass = self.controller.namedPass(argument)          # substituted
            self.controller.ignoreRest()
        elif action == 'goto':
            if self.sourceHandler.gotoLine(argument):
                retval = None  # dataLine is invalid after goto
                self.controller.ignoreRest()
        elif action == 'skip' or action == 'ignore':
            if self.sourceHandler.skipLines(argument):
                retval = None  # dataLine is invalid after skip
                self.controller.ignoreRest()
        elif action == 'quit' or action == 'exit':
            self.exitNow = True  # Force exit from outer loop
        elif action == 'search':
            self.result = self.sourceHandler.findLine(argument)
            if self.result:
                retval = None  # dataline is invalid after a successful search
        elif action == 'correct' or action == 'fix':
            retval = self.doCorrect(line, argument)
        elif action == 'delete' or action == 'del':
            retval = self.doDelete(line, argument)
        elif action == 'sub':
            retval = self.doSub(line, argument)
        elif action == 'replace':
            retval = argument  
        elif action == 'finish' or action == 'moveon':
            self.controller.ignoreRest()
        elif action == 'set':
            self.variable.user('set', self.argToWords(argument, 2))
        elif action == 'counter':
            self.variable.user('counter', self.argToWords(argument, 2))
        elif action == 'unset':
            self.variable.user('unset',  self.argToWords(argument, 2))
        elif len(action) > 1 and action[0] == 'h' and action[1].isdigit():
            self.html.heading(action[1], filehandle, argument)
        elif action == 'figure' or action == 'fig':
            self.html.figure( filehandle, self.argToWords(argument))
        elif action == 'para':
            self.html.para( filehandle, argument)
        elif action == 'open':
            self.fileWriter.openFile( filehandle, argument)
        elif action == 'write':
            self.fileWriter.writeFile( filehandle, argument)
        elif action == 'writeln':
            self.fileWriter.writelnFile( filehandle, argument)
        elif action == 'close':
            self.fileWriter.closeFile( filehandle, argument)
        elif action == 'append':
            self.sourceHandler.appendLine(argument)  
        elif action == 'echo':
            print(argument)
        elif action == 'logfile':
            self.logger.logfile(argument)
        elif action == 'log':
            self.logger.log(argument, self.logger.user)
        elif action == 'source':
            self.sourceHandler.openSource(argument)
        # elif action == 'process':
        #     if len(words):
        #         self.logger.log('Calling process ' + words[0], self.logger.action)
        #         if len(words) > 1:  # [0-9] name args...
        #             try:
        #                 number = int(words[0])
        #                 if len(words) > 2:
        #                     args = words[2:]
        #                 else:
        #                     args = None
        #                 self.processStore.addProcess(number, words[1], args)
        #             except ValueError:
        #                 self.errorNotifier.doError('Expected process number')
        #         else:
        #             self.errorNotifier.doError('Usage: process [0-9] name {arguments}')
        # elif action == 'stream':
        #     if len(words):
        #         self.logger.log('Calling process ' + words[0], self.logger.action)
        #         if len(words) > 1:  # name, processes
        #             if not(words[0].islower()):
        #                 self.errorNotifier.doError('Expected stream id (a-z)')
        #             else:
        #                 args = words[1:]
        #                 self.streamStore.addPipeline(words[0], args)
        #         else:
        #             self.errorNotifier.doError('Usage: stream [a-z] [0-9]+')
        # elif action == 'sendto':
        #     if len(words):
        #         self.logger.log('Calling process ' + words[0], self.logger.action)
        #         stream = words[0]
        #         content = ''
        #         if len(words) > 1:
        #             content = ' '.join(words[1:])
        #         self.streamStore.runPipeline(stream, content)
        #     else:
        #         print ('stream id missing')
        # elif action == 'flush':
        #     if len(words):
        #         self.logger.log('Flushing stream ' + words[0], self.logger.action)
        #         stream = words[0]
        #         self.streamStore.flushPipeline(stream)
        #     else:
        #         print ('stream id missing')
        # elif action == 'filter':
        #     if len(words):
        #         self.logger.log('Calling process ' + words[0], self.logger.action)
        #         if len(words) > 1:
        #             stream = words[0]
        #             content = words[1:]
        #             retval = self.streamStore.runPipeline(stream, ' '.join(content))
        #         else:
        #             print ('content missing')
        #     else:
        #         print ('stream id missing')  
        elif action == 'restart':
            if self.matchedPreOrPost(): # This is nonsense
                self.logger.log('Calling restart', self.logger.section | self.logger.action)
                self.sourceHandler.reset()
            else:
                self.errorNotifier.doError('Restart only valid with ^ or $ condition')
        else:
            self.errorNotifier.doError('Unknown action')
        return retval
