

class loggerClass():
    fileHandle = None
    control = 1
    section = 2
    condition = 4
    action = 8
    variable = 16
    stream = 32
    passes = 64

    showLevel = 8

    def __init__(self, outputFile=None):
        if outputFile is not None:
            try:
                self.fileHandle = open(outputFile, "w")
            except IOError:
                print('Could not open log File ' + outputFile)
                self.fileHandle = None

    def log(self, message, pattern=255):
        if pattern & self.showLevel:
            if self.fileHandle is not None:
                self.fileHandle.write(message.strip() + '\n')
            else:
                print(message)
