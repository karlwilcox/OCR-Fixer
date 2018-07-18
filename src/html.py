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
        if content is not None and len(content):
            content = '\n%s%s%s\n' % (self.startTag, content, self.endTag)
        return content

    def flush(self, content):
        return self.doAction(content)

class htmlTagsClass():
    """Docstring for htmlTagsClass"""
    def __init__(self, logger, fileWriter, variables, errorNotifier):
        self.logger = logger
        self.fileWriter = fileWriter
        self.variables = variables
        self.errorNotifier = errorNotifier
        self.commonAttrs = 'data-source-line="_datacount_" data-source-file="_datafile_"'
        self.subbedAttrs = ''
        self.paraStore = ''
        self.paraHyphen = False

    def reflow(self, text, limit = 80):
        retval = b''
        count = 0
        if limit < 10:
            limit = 10
        words = text.split(' ')
        for word in words:
            retval = retval + ' ' + word
            count += len(word) + 1
            if count > limit:
                count = 0
                retval = retval + '\n'
        retval = retval + '\n\n'
        return retval

    def getCommonAttrs(self):
        retval = ''
        if self.commonAttrs != '':
            retval = ' ' + self.variables.subAll(self.commonAttrs)
        return retval

    def figure(self, fileHandle, words):
        if len(words) < 1:
            self.errorNotifier.doError(r'Usage: figure <filename> {caption}')
            return False
        imageFile = words[0]
        extra = ''
        caption = ''
        altText = ' alt="%s" ' % imageFile
        if len(words) > 1:
            caption = words[1]
            altText = ' alt="%s" ' % caption
        if len(words) > 2:
            extra = ' ' + words[2] + ' '
        content = '<figure>\n<img src="%s" %s %s />\n' % (imageFile, altText, extra)
        if caption:
            content += '<figcaption>%s</figcaption>\n' % caption
        content += '</figure>'
        self.fileWriter.writeFile( fileHandle, content)



    def para(self, fileHandle, line):
        line = line.rstrip('\n ')
        if line == None or line == '': # End of paragraph (possibly)
            if self.paraStore != '': # Yes it is!
                self.fileWriter.writeFile( fileHandle, self.reflow('<p' + self.subbedAttrs + '>' + self.paraStore + '</p>'))
                self.paraStore = ''
                # otherwise ignore it
        else: # there is data on the line
            if self.paraStore == '': # new paragraph
                self.subbedAttrs = self.getCommonAttrs()
            gap = ' '
            if self.paraHyphen:
                gap = ''
                self.paraHyphen = False
            if line[-1] == '-':
                line = line[:-1]
                self.paraHyphen = True
            self.paraStore = self.paraStore + gap + line  

    def heading(self, level, fileHandle, content):
        self.fileWriter.writeFile(fileHandle, '<h' + level + self.getCommonAttrs() + '>' + content + '</h' + level + '>\n\n')      
