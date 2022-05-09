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

    def __init__(self, envSettings):

        self.pipesPath = os.path.join("/tmp", "DIAMBRA")

        # Launch diambra env core
        # Load library
        if "libPath" not in envSettings:
            envSettings["libPath"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libdiambraEnv.so")

        if not envSettings["libPath"]:
           print("Unable to find the specified library: {}".format(envSettings["libPath"]))
           sys.exit()

        try:
           diambraEnvLib = ctypes.CDLL(envSettings["libPath"])
        except OSError as e:
           print("Unable to load the system C library:", e)
           sys.exit()

        diambraEnv = diambraEnvLib.diambraEnv
        diambraEnv.argtypes = [ctypes.c_wchar_p, # pipesPath
                               ctypes.c_wchar_p] # envId
        diambraEnv.restype = ctypes.c_int

        # Mame path
        if "mamePath" not in envSettings:
            envSettings["mamePath"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../mame/")
        if "emuPipesPath" not in envSettings:
            envSettings["emuPipesPath"] = envSettings["mamePath"]

        self.envSettings = envSettings
        diambraEnvArgs = [self.pipesPath, envSettings["envId"]]

        # Launch thread
        self.diambraEnvThread = threading.Thread(target=diambraEnv, args=diambraEnvArgs)
        self.diambraEnvThread.start()

        # Splash Screen
        if not self.envSettings["headless"]:
            DIAMBRASplashScreen()

        # Create pipes
        self.writePipe = Pipe(self.envSettings["envId"], "writeToDiambra", "w", self.pipesPath)
        self.readPipe = DataPipe(self.envSettings["envId"], "readFromDiambra", "r", self.pipesPath)

        # Signal files definition
        tmpPathFileNameP2c = "pipesTmp" + self.envSettings["envId"] + "P2c.log"
        tmpPathFileNameC2p = "pipesTmp" + self.envSettings["envId"] + "C2p.log"
        tmpPathP2c = Path(self.pipesPath).joinpath(tmpPathFileNameP2c)
        tmpPathC2p = Path(self.pipesPath).joinpath(tmpPathFileNameC2p)

        # Signal pipes are ready
        os.system("touch " + str(tmpPathP2c))

        # Wait C++ read pipe ready
        counter = 0;
        print("Waiting for library connection to be opened ...")
        while (not tmpPathC2p.exists()):
            time.sleep(1)
            print("...")
            counter += 1
            if not self.diambraEnvThread.is_alive() or counter > 20:
                sys.exit(1)
        print("... done.")

        # Remove pipes signal
        os.system("rm {}".format(tmpPathC2p))

        # Open pipes
        self.writePipe.open()
        self.readPipe.open()

        # Send environment settings
        envSettingsString = self.envSettingsToString()
        self.writePipe.sendEnvSettings(envSettingsString)

    # Transforming env kwargs to string
    def envSettingsToString(self):

        maxCharToSelect = 3
        sep = ","
        endChar = "+"

        output = ""

        output += "envId"+            sep+"2"+sep + self.envSettings["envId"] + sep
        output += "gameId"+           sep+"2"+sep + self.envSettings["gameId"] + sep
        output += "romsPath"+         sep+"2"+sep + self.envSettings["romsPath"] + sep
        output += "binaryPath"+       sep+"2"+sep + self.envSettings["mamePath"] + sep
        output += "emuPipesPath"+     sep+"2"+sep + self.envSettings["emuPipesPath"] + sep
        output += "continueGame"+     sep+"3"+sep + str(self.envSettings["continueGame"]) + sep
        output += "showFinal"+        sep+"0"+sep + str(int(self.envSettings["showFinal"])) + sep
        output += "stepRatio"+        sep+"1"+sep + str(self.envSettings["stepRatio"]) + sep
        output += "render"+           sep+"0"+sep + str(int(self.envSettings["render"])) + sep
        output += "lockFps"+          sep+"0"+sep + str(int(self.envSettings["lockFps"])) + sep
        output += "sound"+            sep+"0"+sep + str(int(self.envSettings["sound"])) + sep
        output += "player"+           sep+"2"+sep + self.envSettings["player"] + sep
        output += "difficulty"+       sep+"1"+sep + str(self.envSettings["difficulty"]) + sep
        output += "character1"+       sep+"2"+sep + self.envSettings["characters"][0][0] + sep
        output += "character2"+       sep+"2"+sep + self.envSettings["characters"][1][0] + sep
        for iChar in range(1, maxCharToSelect):
            output += "character1_{}".format(iChar+1)+     sep+"2"+sep + self.envSettings["characters"][0][iChar] + sep
            output += "character2_{}".format(iChar+1)+     sep+"2"+sep + self.envSettings["characters"][1][iChar] + sep
        output += "charOutfits1"+     sep+"1"+sep + str(self.envSettings["charOutfits"][0]) + sep
        output += "charOutfits2"+     sep+"1"+sep + str(self.envSettings["charOutfits"][1]) + sep

        # SFIII Specific
        output += "superArt1"+        sep+"1"+sep + str(self.envSettings["superArt"][0]) + sep
        output += "superArt2"+        sep+"1"+sep + str(self.envSettings["superArt"][1]) + sep
        # UMK3 Specific
        output += "tower"+            sep+"1"+sep + str(self.envSettings["tower"]) + sep
        # KOF Specific
        output += "fightingStyle1"+   sep+"1"+sep + str(self.envSettings["fightingStyle"][0]) + sep
        output += "fightingStyle2"+   sep+"1"+sep + str(self.envSettings["fightingStyle"][1]) + sep
        for idx in range(2):
            output += "ultimateStyleDash"+str(idx+1)+  sep+"1"+sep + str(self.envSettings["ultimateStyle"][idx][0]) + sep
            output += "ultimateStyleEvade"+str(idx+1)+ sep+"1"+sep + str(self.envSettings["ultimateStyle"][idx][1]) + sep
            output += "ultimateStyleBar"+str(idx+1)+   sep+"1"+sep + str(self.envSettings["ultimateStyle"][idx][2]) + sep

        output += "headless"+         sep+"0"+sep + str(int(self.envSettings["headless"])) + sep
        output += "displayNum"+       sep+"2"+sep + self.envSettings["displayNum"] + sep
        output += "disableKeyboard"+  sep+"0"+sep + str(int(self.envSettings["disableKeyboard"])) + sep
        output += "disableJoystick"+  sep+"0"+sep + str(int(self.envSettings["disableJoystick"])) + sep
        output += "rank"+             sep+"1"+sep + str(self.envSettings["rank"]) + sep
        output += "recordConfigFile"+ sep+"2"+sep + self.envSettings["recordConfigFile"] + sep

        output += endChar

        return output

    # Set frame size
    def setFrameSize(self, hwcDim):
        self.readPipe.setFrameSize(hwcDim)

    # Get Env Info
    def readEnvInfo(self):
        return self.readPipe.readEnvInfo()

    # Get Env Int Data Vars List
    def readEnvIntDataVarsList(self):
        self.readPipe.readEnvIntDataVarsList()

    # Reset the environment
    def reset(self):
        self.writePipe.sendComm(1);
        return self.readPipe.readResetData()

    # Step the environment
    def step(self, movP1=0, attP1=0, movP2=0, attP2=0):
        self.writePipe.sendComm(0, movP1, attP1, movP2, attP2);
        return self.readPipe.readStepData()

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
