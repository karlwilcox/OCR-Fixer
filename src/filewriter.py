class fileWriterClass:

    def __init__(self, logger, errorNotifier):
        self.errorNotifier = errorNotifier
        self.logger = logger
        self.files = {}

    def openFile(self, filehandle, fileName):
        number = self.getNumber(filehandle)
        if number == 0:
            return False
        self.closeFile('$' + str(number))
        try:
            handle = open(fileName, "w")
        except IOError:
            self.errorNotifier.doError('Could not open ' + fileName)
            return False
        self.files[number] = handle
        return True

    def closeFile(self, filehandle, data=None):
        number = self.getNumber(filehandle)
        if number in self.files:
            if data is not None:
                self.files[number].write(data)
            self.files[number].close()
            del(self.files[number])
            return True
        return False

    def writeFile(self, filehandle, data):
        number = self.getNumber(filehandle)
        if number == 0:
            print data
            return True
        if number in self.files:
            self.files[number].write(data)
            return True
        return False

    def writelnFile(self, filehandle, data):
        number = self.getNumber(filehandle)
        if number == 0:
            print data
            return True
        if number in self.files:
            self.files[number].write(data + '\n')
            return True
        return False

    def getNumber(self, filehandle):
        if len(filehandle) > 1 and filehandle[1].isdigit():
            number = int(filehandle[1])
        else:
            number = 0
        return number
