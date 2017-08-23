from paragraph import paragraphClass
from html import addTagsClass
from superclasses import processSuperClass


class echoProcessClass(processSuperClass):
    """Demonstration class for processing"""
    def __init__(self, args):
        super(echoProcessClass, self).__init__()
        self.args = args

    def doAction(self, content):
        print 'Echo %s\n%s\nEcho Ends\n' % (self.args, content)
        return content


class doubleProcessClass(processSuperClass):
    """Demonstration class for processing"""
    def __init__(self, args):
        super(doubleProcessClass, self).__init__()

    def doAction(self, content):
        return content + content


class processStoreClass():
    """docstring for processStore"""
    def __init__(self, logger, errorNotifier):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.processes = {}
        self.processMap = {'para': paragraphClass,
                           'tags': addTagsClass,
                           'echo': echoProcessClass,
                           'double': doubleProcessClass}

    def addProcess(self, number, name, args):
        if name in self.processMap:
            newProcess = self.processMap[name](args)
            self.logger.log('Adding process %s as id %s' % (name, number))
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


class pipelineStoreClass():
    def __init__(self, logger, errorNotifier, processStore):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.pipelineMap = {}
        self.processStore = processStore

    def addPipeline(self, pipelineLetter, processNumbers):
        self.logger.log('storing processes %s in stream %s' % (processNumbers, pipelineLetter),
                        self.logger.stream)
        self.pipelineMap[pipelineLetter] = processNumbers

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
        content = None
        if pipelineLetter in self.pipelineMap:
            for processNum in self.pipelineMap[pipelineLetter]:
                self.processStore.runProcess(processNum, content)
        else:
            self.errorNotifier.doError('Unknown stream identifier')
