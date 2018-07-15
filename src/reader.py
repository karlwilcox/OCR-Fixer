#!/usr/bin/env python

import sys
from errornotifier import errorNotifierClass
from controllerclass import controllerClass
from loggerclass import loggerClass
from sourcehandlerclass import sourceHandlerClass
from condition import conditionClass
from action import actionClass


def readBook(controlFileName, dataFileName):
    # Create and link all our objects
    errorNotifier = errorNotifierClass()
    controller = controllerClass(logger, errorNotifier, controlFileName)
    errorNotifier.setController(controller)
    sourceHandler = sourceHandlerClass(logger, errorNotifier, dataFileName)
    conditionChecker = conditionClass(logger, errorNotifier)
    actionHandler = actionClass(logger, errorNotifier, sourceHandler, controller)
    conditionChecker.setHandlers(sourceHandler.setMatch, actionHandler.getLastResult)
    actionHandler.setHandlers(conditionChecker.getPreOrPostMatch)

    sourceHandler.reset()
    newPass = False
    currentPass = controller.nextPass()  # Go to the first pass
    # Process this pass
    while not(actionHandler.exitNow):
        controller.setPass(currentPass)
        # Process any pre-pass actions
        while controller.nextLine():
            condition, action, argument = controller.getLine()
            if conditionChecker.check(condition, '^', ''):
                actionHandler.doAction('', action, argument)
                newPass = actionHandler.nextPass
        # For each line of input data
        while not(actionHandler.exitNow) and sourceHandler.nextLine():
            dataLine = sourceHandler.getLine()
            dataCount = sourceHandler.getLineNo()
            controller.reset()
            # For each line in the current pass of the control file
            while not(newPass) and controller.nextLine():
                condition, action, argument = controller.getLine()
                if conditionChecker.check(condition, dataCount, dataLine):
                    dataLine = actionHandler.doAction(dataLine, action, argument)
                    newPass = actionHandler.nextPass
        # Process any post-pass actions
        controller.reset()
        while controller.nextLine():
            condition, action, argument = controller.getLine()
            if conditionChecker.check(condition, '$', ''):
                actionHandler.doAction('', action, argument)
                newPass = actionHandler.nextPass
        if not(newPass):
            newPass = controller.nextPass()
            if not(newPass):
                actionHandler.exitNow = True
        currentPass = newPass  # set the pass no. here, so we close current pass first


# Execution starts here
if len(sys.argv) < 3:
    print('Usage: ' + sys.argv[0] + ' control-file data-file {log-file}')
    exit()
if len(sys.argv) > 3:
    logger = loggerClass(sys.argv[3])
else:
    logger = loggerClass()
readBook(sys.argv[1], sys.argv[2])
