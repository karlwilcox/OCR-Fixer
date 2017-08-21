class fileWriterClass:

    def __init__(self, logger, errorNotifier):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.files = {}

    def openFile(self, number, fileName):
        self.closeFile(number)
        try:
            handle = open(fileName, "w")
        except IOError:
            self.errorNotifier.doError('Could not open ' + fileName)
            return False
        self.files[number] = handle
        return True

    def closeFile(self, number):
        if number in self.files:
            self.files[number].close()
            del(self.files[number])
            return True
        return False

    def writeFile(self, number, data):
        if number in self.files:
            self.files[number].write(data)
            return True
        return False

    def writelnFile(self, number, data):
        if number in self.files:
            self.files[number].write(data + '\n')
            return True
        return False

    def getNumber(self, controlLine):
        if controlLine[0].isdigit():
            number = controlLine[0]
            controlLine = controlLine[1:].strip()
        else:
            number = '1'
        return (number, controlLine)
