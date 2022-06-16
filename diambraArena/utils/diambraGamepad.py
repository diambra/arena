import sys
import os
import time
import numpy as np
from threading import Thread, Event
from collections import defaultdict
from inputs import devices
import pickle
from os.path import expanduser
homeDir = expanduser("~")

# Function to retrieve available GamePads and select one


def availableGamepads():

    print("Available USB gamepads:\n")

    for idx, gamepad in enumerate(devices.gamepads):
        print("Gamepad {}: {}".format(idx, gamepad))

# Class to manage gampad


class diambraGamepad(Thread):  # def class typr thread
    def __init__(self, actionList=(("NoMove", "Left", "UpLeft", "Up",
                                    "UpRight", "Right", "DownRight",
                                    "Down", "DownLeft"),
                                   ("But0", "But1", "But2", "But3",
                                    "But4", "But5", "But6", "But7",
                                    "But8")),
                 cfg=["But1", "But2", "But3", "But4",
                      "But5", "But6", "But7", "But8"],
                 gamepadNum=0, force=False, skipConfigure=False):
        # thread init class (don't forget this)
        Thread.__init__(self, daemon=True)

        self.stopEvent = Event()

        self.startCode = ""
        self.selectCode = ""
        self.startBut = 0
        self.selectBut = 0
        self.eventHashMove = np.zeros(4)
        self.eventHashAttack = np.zeros(8)
        self.gamepadConfigFileName = os.path.join(
            homeDir, '.diambra/config/gamepadConfig.cfg')

        self.allActionsList = (("NoMove", "Left", "UpLeft", "Up", "UpRight",
                                "Right", "DownRight", "Down", "DownLeft"),
                               ("But0", "But1", "But2", "But3", "But4",
                                "But5", "But6", "But7", "But8"))
        self.actionList = actionList

        self.cfg = cfg
        self.gamepadNum = gamepadNum

        self.initActionList(self.actionList)

        try:
            self.gamepad = devices.gamepads[self.gamepadNum]
        except IndexError:
            raise Exception("No gamepad found.")

        print("Initializing gamepad # {}, named: {}".format(
            self.gamepadNum, self.gamepad))

        configure = False

        if not skipConfigure:
            if force:
                configure = True
            else:
                if not self.loadGamepadConfiguration():
                    configure = True

        if configure:
            # Run gamepad configuration
            self.configure()

            configurationOk = False
            while not configurationOk:

                ans = input("Want to test the configuration? (n/y): ")

                if ans == "y":
                    self.initActionList(self.allActionsList)
                    self.configTest()
                    self.initActionList(self.actionList)

                    ans = input("Want to reconfigure the GamePad? (y/n): ")
                    if ans == "y":
                        print("Restarting GamePad configuration")
                        # Run gamepad configuration
                        self.configure()
                    else:
                        configurationOk = True
                else:
                    configurationOk = True

            self.saveGamepadConfiguration()

        print("Diambra GamePad initialized on device # {}, named: {}".format(
            self.gamepadNum, self.gamepad))

    # Show gamepad events
    def showGamepadEvents(self, eventCodesToSkip=[], eventCodeToShow=None):

        print("Use Gamepad to see events")
        while True:
            for event in self.gamepad.read():
                if event.ev_type != "Sync" and event.ev_type != "Misc":
                    if event.code not in eventCodesToSkip:
                        if eventCodeToShow is not None:
                            if event.code != eventCodeToShow:
                                continue
                        print("{} {}".format(event.code, event.state))

    # Prepare gamepad config dict to be saved
    def processGamepadDictForSave(self):

        cfgDictToSave = {}
        cfgDictToSave["name"] = self.gamepad.name

        # Keys
        keyListDict = []
        for key, value in self.gamePadDict["Key"].items():
            keyListDict.append([key, value])

        cfgDictToSave["keyValuesList"] = keyListDict

        # Start and select
        startSelectList = ["", ""]
        startSelectList[0] = self.startCode
        startSelectList[1] = self.selectCode

        cfgDictToSave["startSelectList"] = startSelectList

        # Digital and Analog moves
        absListDictDigital = []
        absListDictAnalog = []
        for key1, value1 in self.gamePadDict["Absolute"].items():

            if "ABS_HAT0" in key1:
                # Digital moves
                for key2, value2 in self.gamePadDict["Absolute"][key1].items():
                    absListDictDigital.append([key1, key2, value2[0]])

            else:
                # Analog moves
                absListDictAnalog.append(
                    [key1, value1[0], value1[1], value1[2], value1[3]])

        cfgDictToSave["absoluteValuesListDigital"] = absListDictDigital
        cfgDictToSave["absoluteValuesListAnalog"] = absListDictAnalog

        return cfgDictToSave

    # Save gamepad configuration
    def saveGamepadConfiguration(self):

        print("Saving configuration in {}".format(self.gamepadConfigFileName))

        # Convert gamepad config dictionary
        cfgDictToSave = self.processGamepadDictForSave()

        # Load all gamepads configuration
        self.loadAllGamepadConfigurations()

        # Append all previous configurations but this one
        newCfgFileDictList = []
        for cfgFileDict in self.cfgFileDictList:
            if cfgFileDict["name"] != self.gamepad.name:
                newCfgFileDictList.append(cfgFileDict)
        cfgFileDictList = newCfgFileDictList

        cfgFileDictList.append(cfgDictToSave)

        # Open file (new or overwrite previous one)
        cfgFile = open(self.gamepadConfigFileName, "wb")
        pickle.dump(cfgFileDictList, cfgFile)
        cfgFile.close()

    # Load all gamepads configuration
    def loadAllGamepadConfigurations(self):

        try:
            cfgFile = open(self.gamepadConfigFileName, "rb")
            cfgFileFound = True

            # Load Pickle Dict
            cfgFileDictList = pickle.load(cfgFile)

            cfgFile.close()

        except OSError:
            print("No gamepad configuration file found in: {}".format(
                os.path.join(homeDir, '.diambra/config/')))
            configFileFolder = os.path.join(homeDir, '.diambra/')
            os.makedirs(configFileFolder, exist_ok=True)
            configFileFolder = os.path.join(homeDir, '.diambra/config/')
            os.makedirs(configFileFolder, exist_ok=True)
            cfgFileDictList = []

        self.cfgFileDictList = cfgFileDictList

    # Load gamepad configuration
    def loadGamepadConfiguration(self):

        configFound = False

        # Read all gamepads configurations
        self.loadAllGamepadConfigurations()

        # Loop among all stored GamePads
        for cfgFileDict in self.cfgFileDictList:
            if cfgFileDict["name"] == self.gamepad.name:

                try:
                    # Initialize GamePad dict
                    self.gamePadDict = {}
                    self.gamePadDict["Key"] = defaultdict(lambda: 7)
                    self.gamePadDict["Absolute"] = defaultdict(
                        lambda: defaultdict(lambda: [[], 0]))
                    self.gamePadDict["Absolute"]["ABS_HAT0Y"] = defaultdict(
                        lambda: [[], 0])  # No-op action = 0
                    self.gamePadDict["Absolute"]["ABS_HAT0X"] = defaultdict(
                        lambda: [[], 0])  # No-op action = 0
                    self.gamePadDict["Absolute"]["ABS_HAT0Y"][0] = [[0, 2], 0]
                    self.gamePadDict["Absolute"]["ABS_HAT0X"][0] = [[1, 3], 0]

                    # Read Start/Select info
                    self.startCode = cfgFileDict["startSelectList"][0]
                    self.selectCode = cfgFileDict["startSelectList"][1]

                    # Read "Key" info
                    for item in cfgFileDict["keyValuesList"]:
                        self.gamePadDict["Key"][item[0]] = item[1]

                    # Read "Absolute" info DIGITAL
                    for item in cfgFileDict["absoluteValuesListDigital"]:
                        self.gamePadDict["Absolute"][item[0]
                                                     ][item[1]] = [item[2],
                                                                   abs(item[1])]

                    # Read "Absolute" info ANALOG
                    for item in cfgFileDict["absoluteValuesListAnalog"]:
                        self.gamePadDict["Absolute"][item[0]] = [
                            item[1], item[2], item[3], item[4]]

                    configFound = True
                    print("Gamepad configuration file found in: {}".format(
                        os.path.join(homeDir, '.diambra/config/')))
                    print("Gamepad configuration file loaded.")
                except:
                    print("Invalid gamepad configuration file found in: {}".format(
                        os.path.join(homeDir, '.diambra/config/')))

        if not configFound:
            print(
                "Configuration for this gamepad not present in gamepad configuration file")

        return configFound

    # Configure GamePad buttons
    def configure(self):

        print("")
        print("")
        print("Configuring gamepad {}".format(self.gamepad))
        print("")
        print("# Buttons CFG file")
        print("               _______            ")
        print("      B7    __|digital|__   B8    ")
        print("      B5      |buttons|     B6    ")
        print("                /    \            ")
        print("                            B1    ")
        print("      |     SELECT  START         ")
        print("   --   --              B4      B2")
        print("      |      -                    ")
        print(" __/____   ( + )            B3    ")
        print("|digital|    -                    ")
        print("| move  |      \______            ")
        print(" -------       |analog|           ")
        print("               | move |           ")
        print("                ------            ")
        print("")
        print("NB: Be sure to have your analog switch on before starting.")
        print("")

        self.gamePadDict = {}
        self.gamePadDict["Key"] = defaultdict(lambda: 7)
        self.gamePadDict["Absolute"] = defaultdict(
            lambda: defaultdict(lambda: [[], 0]))

        # Buttons configuration

        # Start and Select
        print("Press START button")
        butNotSet = True
        while butNotSet:
            for event in self.gamepad.read():
                if event.ev_type == "Key":
                    if event.state == 1:
                        self.startCode = event.code
                        print("Start associated with {}".format(event.code))
                    else:
                        butNotSet = False
                        break

        print("Press SELECT button (Start to skip)")
        butNotSet = True
        while butNotSet:
            for event in self.gamepad.read():
                if event.ev_type == "Key":
                    if event.code != self.startCode and event.state == 1:
                        self.selectCode = event.code
                        print("Select associated with {}".format(event.code))
                    else:
                        butNotSet = False
                        if event.code == self.startCode:
                            print("Select association skipped")
                        break

        # Attack buttons
        endFlag = False
        for idx in range(8):

            if endFlag:
                break

            print("Press B{} button (Select / Start to end configuration)".format(idx+1))

            butNotSet = True

            while butNotSet:

                if endFlag:
                    break

                for event in self.gamepad.read():
                    if event.ev_type == "Key":
                        if (event.code != self.startCode
                                and event.code != self.selectCode):
                            if event.state == 1:
                                print("Button B{}, event code = {}".format(
                                    idx+1, event.code))
                                self.gamePadDict["Key"][event.code] = idx
                            elif event.state == 0:
                                butNotSet = False
                        else:
                            if event.state == 0:
                                print("Remaining buttons configuration skipped")
                                endFlag = True
                                break

        # Move sticks
        # Digital
        endFlag = False
        print("Configuring digital move")
        movesList = ["UP", "RIGHT", "DOWN", "LEFT"]
        eventCodesList = ["Y", "X", "Y", "X"]
        self.gamePadDict["Absolute"]["ABS_HAT0Y"] = defaultdict(lambda: [
                                                                [], 0])
        self.gamePadDict["Absolute"]["ABS_HAT0X"] = defaultdict(lambda: [
                                                                [], 0])
        self.gamePadDict["Absolute"]["ABS_HAT0Y"][0] = [[0, 2], 0]
        self.gamePadDict["Absolute"]["ABS_HAT0X"][0] = [[1, 3], 0]

        for idx, move in enumerate(movesList):

            if endFlag:
                break

            print("Press {} arrow (Start / Select to skip)".format(move))

            butNotSet = True

            while butNotSet:

                if endFlag:
                    break

                for event in self.gamepad.read():

                    if event.ev_type == "Absolute":
                        if event.code == "ABS_HAT0" + eventCodesList[idx]:
                            if abs(event.state) == 1:
                                print("{} move event code = {}, event state = {}".format(
                                    move, event.code, event.state))
                                self.gamePadDict["Absolute"][event.code][event.state] = [
                                    idx, abs(event.state)]
                            elif event.state == 0:
                                butNotSet = False
                            else:
                                print("Digital Move Stick assumes not admissible values: {}".format(
                                    event.state))
                                print(
                                    "Digital Move Stick not supported, configuration skipped")
                                endFlag = True
                                break
                    else:
                        if (event.code == self.startCode
                                or event.code == self.selectCode):
                            if event.state == 0:
                                print("Digital Move Stick configuration skipped")
                                endFlag = True
                                break

        # Move sticks
        # Analog
        print("Configuring analog move")
        movesList = ["UP", "RIGHT", "DOWN", "LEFT"]
        eventCodesList = ["Y", "X", "Y", "X"]
        self.maxAnalogVal = {}
        self.originAnalogVal = {}

        for idx, move in enumerate(movesList):

            print(
                "Move left analog in {} position, keep it there and press Start".format(move))

            butNotSet = True

            self.maxAnalogVal[move] = 0

            while butNotSet:

                for event in self.gamepad.read():

                    if event.ev_type == "Absolute":
                        if event.code == "ABS_" + eventCodesList[idx]:
                            self.maxAnalogVal[move] = event.state
                    else:
                        if event.code == self.startCode:
                            if event.state == 0:
                                butNotSet = False
                                break

        # Setting origin value, analog at rest
        for idx in range(2):
            self.originAnalogVal[movesList[idx]] = int(
                (self.maxAnalogVal[movesList[idx]] +
                 self.maxAnalogVal[movesList[idx+2]]) / 2.0)
            self.originAnalogVal[movesList[idx+2]
                                 ] = self.originAnalogVal[movesList[idx]]

        # Setting threshold to discriminate between analog values
        threshPerc = 0.5
        self.deltaPerc = {}
        for idx in range(2):
            self.deltaPerc[idx] = (self.maxAnalogVal[movesList[idx]] -
                                   self.originAnalogVal[movesList[idx]]) * threshPerc
            self.deltaPerc[idx+2] = -self.deltaPerc[idx]

        print("Delta perc = ", self.deltaPerc)

        # Addressing Y-X axis
        for idx in range(2):
            print("{} move event code = ABS_{}, ".format(movesList[idx],
                                                         eventCodesList[idx]) +
                  "event state = {}".format(self.maxAnalogVal[movesList[idx]]))
            print("{} move event code = ABS_{}, ".format(movesList[idx+2],
                                                         eventCodesList[idx+2]) +
                  " event state = {}".format(self.maxAnalogVal[movesList[idx+2]]))
            print("NO {}-{} move event code =".format(movesList[idx],
                                                      movesList[idx+2]) +
                  " ABS_{}, ".format(eventCodesList[idx]) +
                  "event state = {}".format(self.originAnalogVal[movesList[idx]]))

            eventCode = "ABS_{}".format(eventCodesList[idx])
            if self.deltaPerc[idx] > 0:
                self.gamePadDict["Absolute"][eventCode] = [
                    [self.originAnalogVal[movesList[idx]] - self.deltaPerc[idx],
                        self.originAnalogVal[movesList[idx]] + self.deltaPerc[idx]],
                    [[idx+2], 1], [[idx, idx+2], 0], [[idx], 1]]

            elif self.deltaPerc[idx] < 0:
                self.gamePadDict["Absolute"][eventCode] = [
                    [self.originAnalogVal[movesList[idx]] - self.deltaPerc[idx+2],
                        self.originAnalogVal[movesList[idx]] + self.deltaPerc[idx+2]],
                    [[idx], 1], [[idx, idx+2], 0], [[idx+2], 1]]

            else:
                print(
                    "Not admissible values found in analog stick configuration, skipping")

        print("Gamepad dict : ")
        print("Buttons (Keys) dict : ", self.gamePadDict["Key"])
        print("Moves (Absolute) dict : ", self.gamePadDict["Absolute"])

        print("Configuration completed.")

        return

    # Configuration Test
    def configTest(self):

        print("Press Start to end configuration test")

        # Execute run function in thread mode
        thread = Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

        while True:

            actions = self.getAllActions()

            if actions[0] != 0:
                print("Move action = {}. (Press START to end configuration test).".format(
                    self.allActionsList[0][actions[0]]))
            if actions[1] != 0:
                print("Attack action = {}. (Press START to end configuration test).".format(
                    self.allActionsList[1][actions[1]]))
            if actions[2] != 0:
                break

    # Creating hash dictionary
    def composeHashDict(self, dictionary, hashElem):

        keyValList = []
        keyVal = ""

        for idx, elem in enumerate(hashElem):

            if elem == 1:
                keyValList.append(self.cfg[idx])

        for elem in sorted(keyValList):
            keyVal += elem

        dictionary[keyVal] = hashElem

    # Initializa action list
    def initActionList(self, actionList):

        self.actionDictMove = defaultdict(lambda: 0)  # No-op action = 0
        self.actionDictAttack = defaultdict(lambda: 0)  # No-op action = 0

        moveActionNameToHashDict = {}
        moveActionNameToHashDict["NoMove"] = [0, 0, 0, 0]
        moveActionNameToHashDict["Up"] = [1, 0, 0, 0]
        moveActionNameToHashDict["Right"] = [0, 1, 0, 0]
        moveActionNameToHashDict["Down"] = [0, 0, 1, 0]
        moveActionNameToHashDict["Left"] = [0, 0, 0, 1]
        moveActionNameToHashDict["UpLeft"] = [1, 0, 0, 1]
        moveActionNameToHashDict["UpRight"] = [1, 1, 0, 0]
        moveActionNameToHashDict["DownRight"] = [0, 1, 1, 0]
        moveActionNameToHashDict["DownLeft"] = [0, 0, 1, 1]

        attackActionNameToHashDict = {}
        attackActionNameToHashDict["But0"] = [0, 0, 0, 0, 0, 0, 0, 0]

        # 1 button pressed
        for idx in range(8):
            hashElem = [0, 0, 0, 0, 0, 0, 0, 0]
            hashElem[idx] = 1
            self.composeHashDict(attackActionNameToHashDict, hashElem)

        # 2 buttons pressed
        for idx in range(8):
            for idy in range(idx+1, 8):
                hashElem = [0, 0, 0, 0, 0, 0, 0, 0]
                hashElem[idx] = 1
                hashElem[idy] = 1
                self.composeHashDict(attackActionNameToHashDict, hashElem)

        # 3 buttons pressed
        for idx in range(8):
            for idy in range(idx+1, 8):
                for idz in range(idy+1, 8):
                    hashElem = [0, 0, 0, 0, 0, 0, 0, 0]
                    hashElem[idx] = 1
                    hashElem[idy] = 1
                    hashElem[idz] = 1
                    self.composeHashDict(attackActionNameToHashDict, hashElem)

        # Move actions
        for idx, action in enumerate(actionList[0]):

            hashVal = moveActionNameToHashDict[action]
            self.actionDictMove[tuple(hashVal)] = idx

        # Attack actions
        for idx, action in enumerate(actionList[1]):

            hashVal = attackActionNameToHashDict[action]
            self.actionDictAttack[tuple(hashVal)] = idx

    # Retrieve all gamepad actions
    def getAllActions(self):
        return [self.actionDictMove[tuple(self.eventHashMove)],
                self.actionDictAttack[tuple(self.eventHashAttack)],
                self.startBut, self.selectBut]

    # Retrieve gamepad actions
    def getActions(self):
        return self.getAllActions()[0:2]

    # Retrieve gamepad events
    def run(self):      # run is a default Thread function
        while not self.stopEvent.is_set():   # loop until stop is called
            for event in self.gamepad.read():   # check events of gamepads, if not event, all is stop
                if event.ev_type == "Key":   # category of binary respond values

                    # Select
                    if event.code == self.selectCode:
                        self.selectBut = event.state
                    # Start
                    elif event.code == self.startCode:
                        self.startBut = event.state
                    else:
                        self.eventHashAttack[self.gamePadDict[event.ev_type]
                                             [event.code]] = event.state

                # category of move values (digital moves)
                elif "ABS_HAT0" in event.code:

                    idx = self.gamePadDict[event.ev_type][event.code][event.state][0]
                    eventState = self.gamePadDict[event.ev_type][event.code][event.state][1]
                    self.eventHashMove[idx] = eventState

                # category of move values (analog left stick)
                elif event.code == "ABS_X" or event.code == "ABS_Y":

                    threshValues = self.gamePadDict[event.ev_type][event.code][0]
                    minAct = self.gamePadDict[event.ev_type][event.code][1]
                    centrAct = self.gamePadDict[event.ev_type][event.code][2]
                    maxAct = self.gamePadDict[event.ev_type][event.code][3]

                    if event.state < threshValues[0]:
                        idx = minAct[0]
                        eventState = minAct[1]
                    elif event.state > threshValues[1]:
                        idx = maxAct[0]
                        eventState = maxAct[1]
                    else:
                        idx = centrAct[0]
                        eventState = centrAct[1]

                    for elem in idx:
                        self.eventHashMove[elem] = eventState

    # Stop the thread
    def stop(self):
        self.stopEvent.set()
