import sys, platform, os
from pathlib import Path
import numpy as np
import ctypes, ctypes.util

import threading
from diambraArena.diambraEnvLib.pipe import Pipe, DataPipe
from diambraArena.utils.splashScreen import DIAMBRASplashScreen
import time

# DIAMBRA Env Gym
class diambraArenaLib:
    """Diambra Environment gym interface"""

    def __init__(self, diambraEnvKwargs):

        self.pipesPath = os.path.join("/tmp", "DIAMBRA")

        # Launch diambra env core
        # Load library
        if "libPath" not in diambraEnvKwargs:
            diambraEnvKwargs["libPath"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libdiambraEnv.so")

        if not diambraEnvKwargs["libPath"]:
           print("Unable to find the specified library: {}".format(diambraEnvKwargs["libPath"]))
           sys.exit()

        try:
           diambraEnvLib = ctypes.CDLL(diambraEnvKwargs["libPath"])
        except OSError as e:
           print("Unable to load the system C library:", e)
           sys.exit()

        diambraEnv = diambraEnvLib.diambraEnv
        diambraEnv.restype = ctypes.c_int

        # Mame path
        if "mamePath" not in diambraEnvKwargs:
            diambraEnvKwargs["mamePath"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../mame/")
        if "emuPipesPath" not in diambraEnvKwargs:
            diambraEnvKwargs["emuPipesPath"] = diambraEnvKwargs["mamePath"]

        self.envSettings = diambraEnvKwargs

        # Launch thread
        self.diambraEnvThread = threading.Thread(target=diambraEnv)
        self.diambraEnvThread.start()

        # Splash Screen
        if not diambraEnvKwargs["headless"]:
            DIAMBRASplashScreen()

        # Signal file definition
        tmpPathFileName = "pipesTmp" + diambraEnvKwargs["envId"] + ".log"
        tmpPath = Path(self.pipesPath).joinpath(tmpPathFileName)

        # Create Write Pipe
        self.writePipe = Pipe(diambraEnvKwargs["envId"], "writeToDiambra", "w", self.pipesPath, tmpPath)
        # Create Read Pipe
        self.readPipe = DataPipe(diambraEnvKwargs["envId"], "readFromDiambra", "r", self.pipesPath, tmpPath)

        # Wait until the fifo file has been created and opened on Diambra Env side
        while (not tmpPath.exists()):
            print("Waiting for file to be written, filename = ", tmpPath)
            time.sleep(1)
            if not self.diambraEnvThread.is_alive():
                sys.exit(1)

        time.sleep(2)

        # Open Write Pipe
        self.writePipe.open()
        # Open Read Pipe
        self.readPipe.open()

        # Send environment settings
        envSettingsString = self.envSettingsToString(self.envSettings)
        print("Writing envSettings = ", envSettingsString)
        self.writePipe.sendEnvSettings(envSettingsString)

    # Transforming env kwargs to string
    def envSettingsToString(self, envSettings):

        maxCharToSelect = 3
        sep = ","
        endChar = "+"

        output = ""

        output += "envId"+            sep+"2"+sep + envSettings["envId"] + sep
        output += "gameId"+           sep+"2"+sep + envSettings["gameId"] + sep
        output += "romsPath"+         sep+"2"+sep + envSettings["romsPath"] + sep
        output += "binaryPath"+       sep+"2"+sep + envSettings["mamePath"] + sep
        output += "emuPipesPath"+     sep+"2"+sep + envSettings["emuPipesPath"] + sep
        output += "continueGame"+     sep+"3"+sep + str(envSettings["continueGame"]) + sep
        output += "showFinal"+        sep+"0"+sep + str(int(envSettings["showFinal"])) + sep
        output += "stepRatio"+        sep+"1"+sep + str(envSettings["stepRatio"]) + sep
        output += "render"+           sep+"0"+sep + str(int(envSettings["render"])) + sep
        output += "lockFps"+          sep+"0"+sep + str(int(envSettings["lockFps"])) + sep
        output += "sound"+            sep+"0"+sep + str(int(envSettings["sound"])) + sep
        output += "player"+           sep+"2"+sep + envSettings["player"] + sep
        output += "difficulty"+       sep+"1"+sep + str(envSettings["difficulty"]) + sep
        output += "character1"+       sep+"2"+sep + envSettings["characters"][0][0] + sep
        output += "character2"+       sep+"2"+sep + envSettings["characters"][1][0] + sep
        for iChar in range(1, maxCharToSelect):
            output += "character1_{}".format(iChar+1)+     sep+"2"+sep + envSettings["characters"][0][iChar] + sep
            output += "character2_{}".format(iChar+1)+     sep+"2"+sep + envSettings["characters"][1][iChar] + sep
        output += "charOutfits1"+     sep+"1"+sep + str(envSettings["charOutfits"][0]) + sep
        output += "charOutfits2"+     sep+"1"+sep + str(envSettings["charOutfits"][1]) + sep

        # SFIII Specific
        output += "superArt1"+        sep+"1"+sep + str(envSettings["superArt"][0]) + sep
        output += "superArt2"+        sep+"1"+sep + str(envSettings["superArt"][1]) + sep
        # UMK3 Specific
        output += "tower"+            sep+"1"+sep + str(envSettings["tower"]) + sep
        # KOF Specific
        output += "fightingStyle1"+   sep+"1"+sep + str(envSettings["fightingStyle"][0]) + sep
        output += "fightingStyle2"+   sep+"1"+sep + str(envSettings["fightingStyle"][1]) + sep
        for idx in range(2):
            output += "ultimateStyleDash"+str(idx+1)+  sep+"1"+sep + str(envSettings["ultimateStyle"][idx][0]) + sep
            output += "ultimateStyleEvade"+str(idx+1)+ sep+"1"+sep + str(envSettings["ultimateStyle"][idx][1]) + sep
            output += "ultimateStyleBar"+str(idx+1)+   sep+"1"+sep + str(envSettings["ultimateStyle"][idx][2]) + sep

        output += "headless"+         sep+"0"+sep + str(int(envSettings["headless"])) + sep
        output += "displayNum"+       sep+"2"+sep + envSettings["displayNum"] + sep
        output += "disableKeyboard"+  sep+"0"+sep + str(int(envSettings["disableKeyboard"])) + sep
        output += "disableJoystick"+  sep+"0"+sep + str(int(envSettings["disableJoystick"])) + sep
        output += "rank"+             sep+"1"+sep + str(envSettings["rank"]) + sep
        output += "recordConfigFile"+ sep+"2"+sep + envSettings["recordConfigFile"] + sep

        output += endChar

        return output

    # Get Env Info
    def readEnvInfo(self):
        return self.readPipe.readEnvInfo()

    # Get Env Int Data Vars List
    def readEnvIntDataVarsList(self):
        self.readPipe.readEnvIntDataVarsList()

    # Set frame size
    def setFrameSize(self, hwcDim):
        self.readPipe.setFrameSize(hwcDim)

    # Reset the environment
    def reset(self):
        self.writePipe.sendComm(1);
        frame, data, self.playerSide = self.readPipe.readResetData()
        return frame, data

    # Step the environment
    def step(self, movP1=0, attP1=0, movP2=0, attP2=0):
        self.writePipe.sendComm(0, movP1, attP1, movP2, attP2);
        frame, data = self.readPipe.readStepData()
        return frame, data

    # Closing DIAMBRA Arena
    def close(self):
        self.writePipe.sendComm(2)

        # Close pipes
        self.writePipe.close()
        self.readPipe.close()

        self.diambraEnvThread.join(timeout=30)
        if self.diambraEnvThread.isAlive():
            error = "Failed to close DIAMBRA Env process"
            raise RuntimeError(error)
