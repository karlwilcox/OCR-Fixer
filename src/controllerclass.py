import re

class controllerClass:

    def __init__(self, logger, errorNotifier, fileName):
        self.localLog = []
        self.logger = logger
        self.fileName = fileName
        self.controlLines = []
        self.passMap = []
        self.currentPass = -1
        self.currentLine = -1
        self.errorNotifier = errorNotifier
        controlFileLine = 0
        passIndex = 0
        lookFor = None
        cond = ''
        act = ''
        fh =''
        hereDocStart = ''
        arg = ''
        try:
            for line in open(fileName):
                controlFileLine += 1
                if lookFor is not None:
                    if line.strip() == lookFor:
                        self.controlLines.append((hereDocStart, (cond, act, fh, arg)))
                        lookFor = None
                        hereDocStart = ''
                    else: # gather up lines in a heredoc
                        arg = arg + line
                    continue
                line = line.strip()
                if re.match('#', line):
                    continue    # ignore comment only lines
                if line == '':
                    continue    # ignore empty lines
                if line[0] == '[':
                        passName = re.findall(r'\[(.*)\]', line)
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
                (cond, act, fh, arg) = self.getParts(line)
                if arg.startswith('<<<'):
                    words = arg.split()
                    if len(words) > 1:
                        lookFor = words[1]
                        hereDocStart = controlFileLine
                        arg = ''
                else:
                    self.controlLines.append((controlFileLine, (cond, act, fh, arg)))
            self.passMap[passIndex - 1]['end'] = len(self.controlLines) - 1
            print(self.passMap)
        except IOError:
            print('Control file not found\n')
            exit()

    def dumpLogs(self):
        if self.logger.showLevel & self.logger.control:
            print(self.passMap)
            print(self.controlLines)
            for entry, level in self.localLog:
                self.logger.log(entry, level)

    def localLogger(self, message, category):
        self.localLog.append((message,category))

    def getParts(self, line):
        cond = ''
        act = ''
        fh = ''
        arg = ''

        state = 'whitespace'
        prev = ''
        nextState = 'start'

        i = 0
        while i < len(line):
            # Read a character
            ch = line[i]
            if i < len(line) - 1:
                nextCh = line[i + 1]
            else:
                nextCh = ''
            i += 1
            # if comment marker, end
            if ch == '#':
                break
            # if escaped comment marker, remove escape and carry on testing
            if ch == '\\':
                if nextCh == '#':
                    ch = nextCh
                    i += 1
            # If we are eating whitespace and find some, get another character, 
            if state == 'whitespace':
                if ch.isspace():
                    continue
                else:  # But if not space,  change state and carry on testing
                    state = nextState
            # No else, as we may have changed state above
            if state == 'start':
                if ch == '/':
                    state = 'regex'
                else:
                    state = 'cond'
                cond += ch
            elif state == 'cond':
                if ch.isspace():
                    state = 'whitespace'
                    nextState = 'action'
                else:
                    cond += ch
            elif state == 'regex':  # might contain a space, so we need to look
                if ch == '/' and prev != '\\':  # for unescaped slash
                    state = 'whitespace'  # might be followed by spaces
                    nextState = 'action'
                cond += ch
            elif state == 'filehandle1':
                if ch == '$':
                    fh = ch
                    state = 'filehandle2'
                else:
                    arg = ch
                    state = 'arg'
            elif state == 'filehandle2':
                if ch.isspace():
                    state = 'whitespace'
                    nextState = 'arg'
                else:
                    fh += ch
            elif state == 'action':
                if ch.isspace():
                    state = 'whitespace'
                    nextState = 'filehandle1'
                else:
                    act += ch
            elif state == 'arg':
                arg += ch
            prev = ch
        self.localLogger(cond + ' / ' + act + ' / ' + fh + ' / ' + arg, self.logger.control)
        # print(cond + ' / ' + act + ' / ' + fh + ' / ' + arg + '\n')
        return (cond, act, fh, arg)

    def setPass(self, index):
        self.currentPass = index
        self.currentLine = self.passMap[self.currentPass]['start'] - 1
        self.logger.log('Working on pass ' + self.passMap[self.currentPass]['name'],
                        self.logger.section)

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
            self.errorNotifier.doError("Pass name not found")
        return False

    def nextLine(self):
        if self.currentLine < self.passMap[self.currentPass]['end']:
            self.currentLine += 1
            return True
        else:
            self.logger.log('At end of pass', self.logger.passes)
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
        self.logger.log('Ignoring by going to end of section', self.logger.section)
        self.currentLine = self.passMap[self.currentPass]['end']

    def reset(self):
        self.currentLine = self.passMap[self.currentPass]['start'] - 1
