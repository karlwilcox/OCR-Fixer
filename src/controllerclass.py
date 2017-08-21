import re


class controllerClass:

    def __init__(self, logger, errorNotifier, fileName):
        self.fileName = fileName
        self.controlLines = []
        self.passMap = []
        self.currentPass = -1
        self.currentLine = -1
        self.logger = logger
        self.errorNotifier = errorNotifier
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
        self.logger.log(cond + ' / ' + act + ' / ' + arg, self.logger.control)
        return (cond, act, arg)

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
            self.logger.log('At end of pass', 10)
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
