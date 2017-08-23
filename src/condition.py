import re


class conditionClass():
    """docstring for conditionClass"""
    def __init__(self, logger, errorNotifier):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.lastCheck = False
        self.matchedPreOrPost = False
        self.setMatch = None
        self.getLastResult = None

    def setHandlers(self, match, result):
        self.setMatch = match
        self.getLastResult = result

    def getPreOrPostMatch(self):
        return self.matchedPreOrPost

    def checkRange(self, condition, line):
        retval = False
        if condition == ':blank:':
            if len(line) == 0 or re.match('^[[:blank:]]*$', line):
                retval = True
        elif condition == ':all-upper:':
            retval = not(re.match('[^[:upper:][:punct:]]', line))
        else:
            self.errorNotifier.doError("Unknown special case match - " + condition)
        return retval

    def check(self, condition, lineNo, line):
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
            retval = self.lastCheck
        elif ch == '?':
            if self.lastCheck:
                retval = self.getLastResult()
            if negate:  # only negate the last action, NOT the
                retval = not(retval)  # last condition
                negate = False
        else:
            # Special case matches first, only true if special values for lineNo
            if lineNo == '^' or lineNo == '$':
                retval = (lineNo == ch)
                self.matchedPreOrPost = retval
            else:  # and nothing else ever matches
                self.matchedPreOrPost = False
                if ch == '^' or ch == '$':
                    retval = False  # These never match anywhere else
                elif ch == '*':
                    retval = True
                elif ch == '/':
                    self.logger.log('Testing for match with ' + condition[1:-1],
                                    self.logger.condition)
                    match = re.search(condition[1:-1], line)
                    if match:
                        retval = True
                        self.setMatch(match.groups())
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
                        self.errorNotifier.doError('range condition should be number-number')
                    else:
                        if end < start:
                            self.errorNotifier.doError('end is before start')
                        else:
                            lineNo = int(lineNo)
                            self.logger.log('testing ' + str(lineNo) + ' against range ' +
                                            str(start) + ' to ' + str(end),
                                            self.logger.condition)
                            retval = lineNo >= start and lineNo <= end
                elif ch == ':':
                    retval = self.checkRange(condition, line)
                else:
                    self.errorNotifier.doError('Unknown condition')
        if retval:
            self.logger.log('Condition ' + condition + ' matches: ' + str(line),
                            self.logger.condition)
        if negate:
            retval = not(retval)
        self.lastCheck = retval
        return retval