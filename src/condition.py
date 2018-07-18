import re


class conditionClass():
    # Flag values for match type
    NOMATCH = 0
    EXACT = 1
    STARTRANGE = 2
    MIDRANGE = 4
    ENDRANGE = 8
    STAR = 16
    REGEX = 32
    START = 64
    END = 128
    ALSO = 256
    IFTRUE = 512
    NEGATE = 1024
    BUILTIN = 2048
    """docstring for conditionClass"""
    def __init__(self, logger, errorNotifier):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.lastCheck = False
        self.matchedPreOrPost = False
        self.setMatch = None
        self.getLastResult = None
        self.prevMatchType = 0

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
        matchType = conditionClass.NOMATCH
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
            if retval:
                matchType |= self.prevMatchType | conditionClass.ALSO
        elif ch == '?':
            if self.lastCheck:
                retval = self.getLastResult
            if negate:  # only negate the last action, NOT the
                retval = not(retval)  # last condition
                negate = False
        else:
            # Special case matches first, only true if special values for lineNo
            if lineNo == '^' or lineNo == '$':
                retval = (lineNo == ch)
                self.matchedPreOrPost = retval
                if retval:
                    if lineNo == '^':
                        matchType |= conditionClass.START
                    else:
                        matchType |= conditionClass.END
            else:  # and nothing else ever matches
                self.matchedPreOrPost = False
                if ch == '^' or ch == '$':
                    retval = False  # These never match anywhere else
                elif ch == '*':
                    retval = True
                    matchType |= conditionClass.STAR
                elif ch == '/':
                    self.logger.log('Testing for match with ' + condition[1:-1],
                                    self.logger.condition)
                    match = re.search(condition[1:-1], line)
                    if match:
                        matchType |= conditionClass.REGEX
                        retval = True
                        self.setMatch(match.groups())
                elif ch.isdigit():
                    lineVal = int(lineNo)
                    dash = condition.find('-')
                    comma = condition.find(',')
                    if dash > 0:  # should be a range
                        try:
                            start = int(condition[0:dash])
                            end = int(condition[dash + 1:])
                        except ValueError:
                            self.errorNotifier.doError('range condition should be number-number')
                        else:
                            if end < start:
                                self.errorNotifier.doError('end is before start')
                            self.logger.log('testing ' + lineNo + ' against range ' +
                                            str(start) + ' to ' + str(end),
                                            self.logger.condition)
                            retval = lineVal >= start and lineVal <= end
                            if retval:
                                if lineVal == start:
                                    matchType |= conditionClass.STARTRANGE
                                elif lineVal == end:
                                    matchType |= conditionClass.ENDRANGE
                                else:
                                    matchType |= conditionClass.MIDRANGE
                    elif comma > 0:
                        tests = condition.split(',')
                        for test in tests:
                            try:
                                if lineVal == int(test):
                                    matchType = conditionClass.EXACT
                                    retval = True
                                    break
                            except ValueError:
                                self.errorNotifier.doError('Non-digit found in line number list')
                    else: # just a plain number
                        try:
                            exact = int(condition)
                        except ValueError:
                            self.logger.log('testing ' + lineNo + ' against ' + str(exact),
                                            self.logger.condition)
                            self.errorNotifier.doError('Invalid line no: %s' % condition)
                        else:
                            retval = lineVal == exact
                            if retval:
                                matchType |= conditionClass.EXACT
                elif ch == ':':
                    retval = self.checkRange(condition, line)
                    if retval:
                        matchType |= conditionClass.BUILTIN
                else:
                    self.errorNotifier.doError('Unknown condition')
        if retval:
            self.logger.log('Condition ' + condition + ' matches: ' + str(line),
                            self.logger.condition)
        if negate:
            matchType |= conditionClass.NEGATE
            retval = not(retval)
        self.lastCheck = retval
        # return retval
        if retval:
            self.prevMatchType = matchType
            return matchType
        else:
            self.prevMatchType = conditionClass.NOMATCH
            return conditionClass.NOMATCH
