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

    exitNow = False
    sourceHandler.reset()
    currentPass = controller.nextPass()  # Go to the first pass
    # Process this pass
    while not(exitNow):
        newPass = False
        controller.setPass(currentPass)
        # Process any pre-pass actions
        while controller.nextLine():
            condition, action, argument = controller.getLine()
            if conditionChecker.check(condition, '^', ''):
                actionHandler.doAction('', action, argument)
        # For each line of input data
        while not(exitNow) and sourceHandler.nextLine():
            dataLine = sourceHandler.getLine()
            controller.reset()
            # For each line in the current pass of the control file
            while not(newPass) and controller.nextLine():
                condition, action, argument = controller.getLine()
                if conditionChecker.check(condition, sourceHandler.getLineNo(), dataLine):
                    # process pass related commands first
                    if action == 'next':
                        newPass = controller.nextPass()
                        break
                    elif action == 'section':
                        newPass = controller.namedPass(argument)
                    elif action == 'quit' or action == 'exit':
                        exitNow = True  # Force exit from outer loop
                        break
                    else:  # action must be related to the actual content
                        dataLine = actionHandler.doAction(dataLine, action, argument)
        # Process any post-pass actions
        controller.reset()
        while controller.nextLine():
            condition, action, argument = controller.getLine()
            if conditionChecker.check(condition, '$', ''):
                actionHandler.doAction('', action, argument)
        if not(newPass):
            newPass = controller.nextPass()
            if not(newPass):
                exitNow = True
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
