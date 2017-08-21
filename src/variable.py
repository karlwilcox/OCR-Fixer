

class variableClass():
    """docstring for variable"""
    def __init__(self, logger, errorNotifier, sourceHandler, controller):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.sourceHandler = sourceHandler
        self.controller = controller
        self.values = {}
        self.counters = {}

    def user(self, action, name, value=''):
        self.logger.log(action + ' / ' + name + ' / ' + str(value), self.logger.variable)
        retval = ''
        if action == 'set':
            self.values[name] = value
            if name == 'loglevel':
                self.logger.showLevel = int(value)
        elif action == 'get':
            if name in self.counters:
                self.counters[name] += 1
                retval = str(self.counters[name])
            else:
                retval = self.values.get(name, '(none)')
        elif action == 'counter':
            if value == '':
                value = 0
            self.counters[name] = value
        elif action == 'unset' and name in self.values:
            del self.values[name]
        else:
            self.errorNotifier.doError('Unknown action for parameter')
        return retval

    def builtin(self, varname):
        self.logger.log("Invoke builtin - " + varname, self.logger.variable)
        name = varname.lower()
        retval = ''
        if name == 'origline':
            retval = self.sourceHandler.getLine()
        elif name == 'datacount':
            retval = self.sourceHandler.getLineNo()
        elif name == 'datafile':
            retval = self.sourceHandler.fileName
        elif name == 'controlline':
            retval = self.controller.getLine()
        elif name == 'controlcount':
            retval = self.controller.getLineNo()
        elif name == 'controlfile':
            retval = self.controller.fileName
        elif name == 'section':
            retval = self.controller.getPass()
        elif name == 'match':
            retval = self.sourceHandler.lastMatch()
        elif name == 'loglevel':
            retval = self.logger.showLevel
        elif 'sub' == name[:3]:
            if len(name > 4 and name[3].isdigit()):
                subNum = name[3]
            else:
                subNum = 1
            retval = self.sourceHandler.lastMatch(subNum)
        else:
            self.errorNotifier.doError('Unknown built-in: ' + varname)
        return str(retval)
