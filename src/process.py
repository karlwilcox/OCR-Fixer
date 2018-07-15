from content import paragraphClass, headingClass, alphaEntryClass
from html import addTagsClass
from superclasses import processSuperClass


class echoProcessClass(processSuperClass):
    """Demonstration class for processing"""
    def __init__(self, args):
        super(echoProcessClass, self).__init__()
        self.args = args

    def doAction(self, content):
        # print 'Echo %s\n%s\nEcho Ends\n' % (self.args, content)
        print content
        return content


class outputProcessClass(processSuperClass):
    """Demonstration class for processing"""
    def __init__(self, args):
        super(outputProcessClass, self).__init__()
        self.fileHandle = None
        if len(args):
            try:
                self.fileHandle = open(args[0], "w")
            except IOError:
                # self.errorNotifier.doError('Could not open ' + args[0])
                print "Could not open file"

    def doAction(self, content):
        if self.fileHandle is not None:
            self.fileHandle.write(content)
        return content

    def flush(self, content):
        if self.fileHandle is not None:
            if content is not None:
                self.fileHandle.write(content)
            self.fileHandle.close()


class processStoreClass():
    """docstring for processStore"""
    def __init__(self, logger, errorNotifier):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.processes = {}
        self.processMap = {
            'para': paragraphClass,
            'heading': headingClass,
            'tags': addTagsClass,
            'echo': echoProcessClass,
            'alphaEntry': alphaEntryClass,
            'output': outputProcessClass
        }

    def addProcess(self, number, name, args):
        if name in self.processMap:
            newProcess = self.processMap[name](args)
            self.logger.log('Adding process %s as id %s' % (name, number), self.logger.stream)
            self.processes[number] = newProcess
        else:
            self.errorNotifier.doError('Unknown process')

    def runProcess(self, number, content):
        if number in self.processes:
            self.logger.log('Running process %s' % number, self.logger.stream)
            return self.processes[number].doAction(content)
        else:
            self.errorNotifier.doError('Unknown process number')
            return content

    def flushProcess(self, number, content):
        if number in self.processes:
            self.logger.log('Flushing process %s' % number, self.logger.stream)
            return self.processes[number].flush(content)
        else:
            self.errorNotifier.doError('Unknown process number')
            return None


class pipelineStoreClass():
    def __init__(self, logger, errorNotifier, processStore):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.pipelineMap = {}
        self.processStore = processStore

    def addPipeline(self, pipelineLetter, processNumbers):
        self.logger.log('storing processes %s in stream %s' % (processNumbers, pipelineLetter),
                        self.logger.stream)
        procNums = []
        try:
            for n in processNumbers:
                num = int(n)
                procNums.append(num)
            self.pipelineMap[pipelineLetter] = procNums
        except ValueError:
            self.errorNotifier.doError('Expected process numbers')

    def runPipeline(self, pipelineLetter, content):
        self.logger.log('sending content %s to stream %s' % (content, pipelineLetter),
                        self.logger.stream)
        if pipelineLetter in self.pipelineMap:
            for processNum in self.pipelineMap[pipelineLetter]:
                content = self.processStore.runProcess(processNum, content)
                if content is None:
                    break
        else:
            self.errorNotifier.doError('Unknown stream identifier')
        return content

    def flushPipeline(self, pipelineLetter):
        self.logger.log('flushing stream %s' % pipelineLetter,
                        self.logger.stream)
        content = ''
        if pipelineLetter in self.pipelineMap:
            for processNum in self.pipelineMap[pipelineLetter]:
                content = self.processStore.flushProcess(processNum, content)
        else:
            self.errorNotifier.doError('Unknown stream identifier')
        return content

