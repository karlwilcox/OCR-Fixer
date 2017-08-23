from superclasses import processSuperClass


class addTagsClass(processSuperClass):
    """docstring for narrativeClass"""
    def __init__(self, args):
        super(addTagsClass, self).__init__()
        if len(args) < 2:
            self.endTag = '</div>'
        else:
            self.endTag = args[1]
        if len(args) < 1:
            self.startTag = '<div>'
        else:
            self.startTag = args[0]

    def doAction(self, content):
        return '\n%s%s%s\n' % (self.startTag, content, self.endTag)
