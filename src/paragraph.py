from superclasses import processSuperClass


class paragraphClass(processSuperClass):
    """docstring for narrativeClass"""
    def __init__(self, args):
        super(paragraphClass, self).__init__()
        self.text = ''
        self.lineInPara = 0
        self.args = args

    def doAction(self, line):
        retval = None
        if line is not None and len(line) > 0:  # got some text
            if self.text == '':
                self.text = line
            else:
                if self.text[-1] == '-':
                    self.text = self.text[0:-1] + line
                else:
                    self.text += ' ' + line
        else:  # blank line, end of paragraph
            retval = ''  # pass on the blank line
            if self.text != '':
                retval = self.text
                self.text = ''
                self.lineInPara = 0
        return retval

    def flush(self, line):
        if line is not None:
            self.text += line
        return self.text
