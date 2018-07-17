class fileWriterClass:

    def __init__(self, logger, errorNotifier):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.files = {}

    def openFile(self, number, fileName):
        if number == 0:
            return False
        self.closeFile(number)
        try:
            handle = open(fileName, "w")
        except IOError:
            self.errorNotifier.doError('Could not open ' + fileName)
            return False
        self.files[number] = handle
        return True

    def closeFile(self, number, data=None):
        if number in self.files:
            if data is not None:
                self.files[number].write(data)
            self.files[number].close()
            del(self.files[number])
            return True
        return False

    def writeFile(self, number, data):
        if number == 0:
            print data
            return True
        if number in self.files:
            self.files[number].write(data)
            return True
        return False

    def writelnFile(self, number, data):
        if number == 0:
            print data
            return True
        if number in self.files:
            self.files[number].write(data + '\n')
            return True
        return False

    def getNumber(self, wordList):
        if len(wordList[0]) > 1 and wordList[0][0] == '$' and wordList[0][1].isdigit():
            number = int(wordList[0][1])
            data = ' '.join(wordList[1:])
        else:
            number = 1
            data = ' '.join(wordList)
        return (number, data)
