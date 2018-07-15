
class processSuperClass(object):
    """docstring for processClass"""
    variables = None

    def __init__(self):
        pass

    def doAction(self, input):
        assert False, 'doAction must be defined for process'

    def flush(self, input):
        return input
