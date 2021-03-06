# Collection of policies to be applied on the environment
import numpy as np
import sys, os
import random
currentDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(currentDir)
from diambraGamepad import diambraGamepad

# Human policy, retrieved via GamePad
class gamepadPolicy(object):

    def __init__(self, name="Human Player"):
        self.gamePadClass = diambraGamepad
        self.id = "gamepad"
        self.initialized = False
        self.name = name

    def initialize(self, actionList, gamepadNum=0):
        if not self.initialized:
            self.gamePad = self.gamePadClass(actionList=actionList,
                                             gamepadNum=gamepadNum)
            self.gamePad.start()
            self.initialized = True

    def getActions(self):
        return self.gamePad.getActions()
