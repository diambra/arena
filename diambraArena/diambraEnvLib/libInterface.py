import sys, platform, os
from pathlib import Path
import numpy as np
import ctypes, ctypes.util

import threading
from diambraArena.diambraEnvLib.pipe import EnvData, Pipe, DataPipe
from diambraArena.utils.splashScreen import DIAMBRASplashScreen
import time

# DIAMBRA Env Gym
class diambraArenaLib:
    """Diambra Environment gym interface"""

    def __init__(self, diambraEnvKwargs):

        self.envData = EnvData()

        self.pipes_path = os.path.join("/tmp", "DIAMBRA")

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
        diambraEnv.argtypes = [
                               # INPUTS
                               ctypes.c_wchar_p, # EnvKwargs (envId+gameId+romsPath+binaryPath+ ...)
                               ctypes.c_wchar_p, # pipes_path
                               # OUTPUTS
                               ctypes.POINTER(ctypes.c_int), # data STRUCTURE INT
                               ctypes.POINTER(ctypes.c_bool), # data STRUCTURE BOOL
                               np.ctypeslib.ndpointer(dtype='uint8', ndim=1, flags='C_CONTIGUOUS')] # unsigned char* frame

        diambraEnv.restype = ctypes.c_int

        # Mame path
        if "mamePath" not in diambraEnvKwargs:
            diambraEnvKwargs["mamePath"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../mame/")
        if "emuPipesPath" not in diambraEnvKwargs:
            diambraEnvKwargs["emuPipesPath"] = diambraEnvKwargs["mamePath"]

        self.envSettings = diambraEnvKwargs

        envKwargsString = self.envKwargsToString(diambraEnvKwargs)
        diambraEnvArgs = [envKwargsString, self.pipes_path,                                  # INPUTS
                          self.envData.cIntData, self.envData.cBoolData, self.envData.frame] # OUTPUTS

        # Launch thread
        self.diambraEnvThread = threading.Thread(target=diambraEnv, args=diambraEnvArgs)
        self.diambraEnvThread.start()

        # Splash Screen
        if not diambraEnvKwargs["headless"]:
            DIAMBRASplashScreen()

        # Signal file definition
        tmpPathFileName = "pipesTmp" + diambraEnvKwargs["envId"] + ".log"
        tmpPath = Path(self.pipes_path).joinpath(tmpPathFileName)

        # Create Write Pipe
        self.writePipe = Pipe(diambraEnvKwargs["envId"], "writeToDiambra", "w", self.pipes_path, tmpPath)
        # Create Read Pipe
        self.readPipe = DataPipe(diambraEnvKwargs["envId"], "readFromDiambra", "r", self.pipes_path, tmpPath)

        # Wait until the fifo file has been created and opened on Diambra Env side
        while (not tmpPath.exists()):
            time.sleep(1)
            if not self.diambraEnvThread.is_alive():
                sys.exit(1)

        time.sleep(2)

        # Open Write Pipe
        self.writePipe.open()
        # Open Read Pipe
        self.readPipe.open()

    # Transforming env kwargs to string
    def envKwargsToString(self, envSettings):

        maxCharToSelect = 3

        output = ""

        output += "envId"+            "+2+" + envSettings["envId"] + "+"
        output += "gameId"+           "+2+" + envSettings["gameId"] + "+"
        output += "romsPath"+         "+2+" + envSettings["romsPath"] + "+"
        output += "binaryPath"+       "+2+" + envSettings["mamePath"] + "+"
        output += "emuPipesPath"+     "+2+" + envSettings["emuPipesPath"] + "+"
        output += "continueGame"+     "+3+" + str(envSettings["continueGame"]) + "+"
        output += "showFinal"+        "+0+" + str(int(envSettings["showFinal"])) + "+"
        output += "stepRatio"+        "+1+" + str(envSettings["stepRatio"]) + "+"
        output += "render"+           "+0+" + str(int(envSettings["render"])) + "+"
        output += "lockFps"+          "+0+" + str(int(envSettings["lockFps"])) + "+"
        output += "sound"+            "+0+" + str(int(envSettings["sound"])) + "+"
        output += "player"+           "+2+" + envSettings["player"] + "+"
        output += "difficulty"+       "+1+" + str(envSettings["difficulty"]) + "+"
        output += "character1"+       "+2+" + envSettings["characters"][0][0] + "+"
        output += "character2"+       "+2+" + envSettings["characters"][1][0] + "+"
        for iChar in range(1, maxCharToSelect):
            output += "character1_{}".format(iChar+1)+     "+2+" + envSettings["characters"][0][iChar] + "+"
            output += "character2_{}".format(iChar+1)+     "+2+" + envSettings["characters"][1][iChar] + "+"
        output += "charOutfits1"+     "+1+" + str(envSettings["charOutfits"][0]) + "+"
        output += "charOutfits2"+     "+1+" + str(envSettings["charOutfits"][1]) + "+"

        # SFIII Specific
        output += "superArt1"+        "+1+" + str(envSettings["superArt"][0]) + "+"
        output += "superArt2"+        "+1+" + str(envSettings["superArt"][1]) + "+"
        # UMK3 Specific
        output += "tower"+            "+1+" + str(envSettings["tower"]) + "+"
        # KOF Specific
        output += "fightingStyle1"+   "+1+" + str(envSettings["fightingStyle"][0]) + "+"
        output += "fightingStyle2"+   "+1+" + str(envSettings["fightingStyle"][1]) + "+"
        for idx in range(2):
            output += "ultimateStyleDash"+str(idx+1)+  "+1+" + str(envSettings["ultimateStyle"][idx][0]) + "+"
            output += "ultimateStyleEvade"+str(idx+1)+ "+1+" + str(envSettings["ultimateStyle"][idx][1]) + "+"
            output += "ultimateStyleBar"+str(idx+1)+   "+1+" + str(envSettings["ultimateStyle"][idx][2]) + "+"

        output += "headless"+         "+0+" + str(int(envSettings["headless"])) + "+"
        output += "displayNum"+       "+2+" + envSettings["displayNum"] + "+"
        output += "disableKeyboard"+  "+0+" + str(int(envSettings["disableKeyboard"])) + "+"
        output += "disableJoystick"+  "+0+" + str(int(envSettings["disableJoystick"])) + "+"
        output += "rank"+             "+1+" + str(envSettings["rank"]) + "+"
        output += "recordConfigFile"+ "+2+" + envSettings["recordConfigFile"] + "+"

        return output

    # Get Env Info
    def readEnvInfo(self):
        return self.readPipe.readEnvInfo()

    # Get Env Int Data Vars List
    def readEnvIntDataVarsList(self):
        envIntDataVarsList = self.readPipe.readEnvIntDataVarsList()
        envIntDataVarsList.remove("")
        self.envData.setIntDataVarsList(envIntDataVarsList)

    # Set frame size
    def setFrameSize(self, hwcDim):
        self.envData.setFrameSize(hwcDim)
        self.readPipe.setFrameSize(hwcDim)

    # Reading flag
    def readFlag(self):
        return self.readPipe.readFlag()

    # Reading reset info
    def readResetInfo(self):
        return self.readPipe.readResetInfo()

    # Reading data
    def readData(self):
        return self.envData.readData()

    # Step the environment
    def step(self, movP1=0, attP1=0, movP2=0, attP2=0):
        self.writePipe.sendComm(0, movP1, attP1, movP2, attP2);

    # Reset the environment
    def reset(self):
        self.writePipe.sendComm(1);

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
