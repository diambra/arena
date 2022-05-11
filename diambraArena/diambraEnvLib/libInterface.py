import sys, platform, os
from pathlib import Path
import numpy as np

import threading
from diambraArena.diambraEnvLib.pipe import Pipe, DataPipe
from diambraArena.utils.splashScreen import DIAMBRASplashScreen
import time

def diambraApp(localExec, pipesPath, envId, romsPath, render):
    print("Args = ", localExec, pipesPath, envId, romsPath, render)

    if localExec:
        diambraAppPath = os.getenv("diambraAppPath")
        command = '{} --pipesPath {} --envId {}'.format(diambraAppPath, pipesPath, envId)
    else:
        dockerRomsFolder = "/opt/diambraArena/roms"
        dockerPipesFolder = "/tmp/"
        dockerImageName = "diambra/diambra-app:main"
        dockerContainerName = "container"+envId
        romsVol = '--mount src={},target="{}",type=bind '.format(romsPath, dockerRomsFolder)
        if render:
            x11exec = os.path.join(pipesPath, "x11docker")
            command  = '{} --cap-default --hostipc --network=host --name={}'.format(x11exec, dockerContainerName)
            command += ' --wm=host --pulseaudio --size=1024x600 -- --privileged'
            command += ' {} --mount src="{}",target="{}",type=bind'.format(romsVol, pipesPath, dockerPipesFolder)
            command += ' -v diambraService:/root/ -- {} &>/dev/null & sleep 4s;'.format(dockerImageName)
            command += ' docker exec -u $(id -u) --privileged -it {}'.format(dockerContainerName)
            command += ' sh -c "set -m; cd /opt/diambraArena/ &&'
            command += ' ./diambraApp --pipesPath {} --envId {}";'.format(dockerPipesFolder, envId)
            command += ' pkill -f "bash {}*"'.format(x11exec)
        else:
            command  = 'docker run --user $(id -u) -it --rm --privileged {}'.format(romsVol)
            command += ' --mount src="{}",target="{}",type=bind'.format(pipesPath, dockerPipesFolder)
            command += ' -v diambraService:/root/ --name {} {}'.format(dockerContainerName, dockerImageName)
            command += ' sh -c "cd /opt/diambraArena/ &&'
            command += ' ./diambraApp --pipesPath {} --envId {}"'.format(dockerPipesFolder, envId)

    print("Command = ", command)
    os.system(command)

# DIAMBRA Env Gym
class diambraArenaLib:
    """Diambra Environment gym interface"""

    def __init__(self, envSettings):

        self.pipesPath = os.path.dirname(os.path.abspath(__file__))

        # Launch diambra App
        diambraEnvArgs = [envSettings["localExec"], self.pipesPath, envSettings["envId"],\
                          envSettings["romsPath"], envSettings["render"]]
        if envSettings["localExec"]: # Ubuntu/Mint local execution (ONLY DEV!)
            print("WARNING: local execution is only for dev purposes")
            if os.getenv("diambraAppPath") == None:
                print("ERROR: local execution requires specification of \"diambraAppPath\"")
                print(" as environment variable but it was not provided")
                sys.exit(1)
            elif "mamePath" not in envSettings:
                print("ERROR: local execution requires specification of \"mamePath\"")
                print(" as environment settings but it was not provided")
                sys.exit(1)

        else: # Docker based execution
            # Mame path for docker
            envSettings["mamePath"] = "/opt/diambraArena/mame/"
            # Roms path for docker
            envSettings["romsPath"] = "/opt/diambraArena/roms/"

        if "emuPipesPath" not in envSettings:
            envSettings["emuPipesPath"] = "/tmp/DIAMBRA/"

        self.envSettings = envSettings

        # Launch thread
        self.diambraEnvThread = threading.Thread(target=diambraApp, args=diambraEnvArgs)
        self.diambraEnvThread.start()

        # Splash Screen
        DIAMBRASplashScreen()

        # Create pipes
        self.writePipe = Pipe(self.envSettings["envId"], "input", "w", self.pipesPath)
        self.readPipe = DataPipe(self.envSettings["envId"], "output", "r", self.pipesPath)

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
