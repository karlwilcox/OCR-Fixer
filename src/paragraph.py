# from process import processSuperClass


class paragraphClass():
    """docstring for narrativeClass"""
    def __init__(self, args):
        # super(paragraphClass, self).__init__()
        self.text = ''
        self.lineInPara = 0
        self.args = args

    def doAction(self, line):
        if len(line) > 0:  # got some text
            if self.text == '':
                self.text = line
            else:
                if self.text[-1] == '-':
                    self.text = self.text[0:-1] + line
                else:
                    self.text += ' ' + line
            return None
        else:  # blank line, end of self
            return self.flush()

    def flush(self):
        retval = None
        if self.text != '':
            retval = self.text
            self.text = ''
            self.lineInPara = 0
        return retval
