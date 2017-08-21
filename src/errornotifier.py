class errorNotifierClass():
    """docstring for errorNotifierClass"""

    def __init__(self):
        self.controller = None
        self.messageLog = []

    def setController(self, controller):
        self.controller = controller

    def doError(self, message):
        if self.controller is None:
            print(message.strip())
        else:
            number = self.controller.getLineNo()
            line = self.controller.getLine()
            if not(number in self.messageLog):
                print(message.strip() + ' (line ' + str(number) + ') ', line)
                self.messageLog.append(number)
