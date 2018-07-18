#!/usr/bin/env python

import sys
from errornotifier import errorNotifierClass
from controllerclass import controllerClass
from loggerclass import loggerClass
from sourcehandlerclass import sourceHandlerClass
from condition import conditionClass
from action import actionClass


def readBook(controlFileName):
    # Create and link all our objects
    logger = loggerClass()
    errorNotifier = errorNotifierClass()
    controller = controllerClass(logger, errorNotifier, controlFileName)
    controller.dumpLogs()
    errorNotifier.setController(controller)
    sourceHandler = sourceHandlerClass(logger, errorNotifier)
    conditionChecker = conditionClass(logger, errorNotifier)
    actionHandler = actionClass(logger, errorNotifier, sourceHandler, controller)
    conditionChecker.setHandlers(sourceHandler.setMatch, actionHandler.getLastResult)
    actionHandler.setHandlers(conditionChecker.getPreOrPostMatch)

    newPass = False
    currentPass = controller.nextPass()  # Go to the first pass
    # Process this pass
    while not(actionHandler.exitNow):
        controller.setPass(currentPass)
        # Process any pre-pass actions
        while controller.nextLine():
            condition, action, filehandle, argument = controller.getLine()
            match = conditionChecker.check(condition, '^', '')
            if match != conditionClass.NOMATCH:
                actionHandler.doAction('', action, filehandle, argument, match)
                newPass = actionHandler.nextPass
        # For each line of input data
        while not(actionHandler.exitNow) and sourceHandler.nextLine():
            dataLine = sourceHandler.getLine()
            dataCount = sourceHandler.getLineNo()
            controller.reset()
            # For each line in the current pass of the control file
            while not(newPass) and controller.nextLine():
                condition, action, filehandle, argument = controller.getLine()
                match = conditionChecker.check(condition, dataCount, dataLine)
                if match != conditionClass.NOMATCH:
                    dataLine = actionHandler.doAction(dataLine, action, filehandle, argument, match)
                    newPass = actionHandler.nextPass
        # Process any post-pass actions
        controller.reset()
        while controller.nextLine():
            condition, action, filehandle, argument = controller.getLine()
            match = conditionChecker.check(condition, '$', '')
            if match != conditionClass.NOMATCH:
                actionHandler.doAction('', action, filehandle, argument, match)
                newPass = actionHandler.nextPass
        if not(newPass):
            newPass = controller.nextPass()
            if not(newPass):
                actionHandler.exitNow = True
        currentPass = newPass  # set the pass no. here, so we close current pass first


# Execution starts here
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' control-file')
    exit()
readBook(sys.argv[1])
