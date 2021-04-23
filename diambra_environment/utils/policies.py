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

# Util to copy P2 additional OBS into P1 position on 7th channel
def P2ToP1AddObsMove(observation):

    shp = observation.shape
    startIdx = int((shp[0]*shp[1])/2)
    observation = np.reshape(observation, (-1))
    numAddParP2 = int(observation[startIdx])
    addParP2 = observation[startIdx:startIdx+numAddParP2 + 1]
    observation[0:numAddParP2 + 1] = addParP2
    observation = np.reshape(observation, (shp[0], -1))

    return observation
