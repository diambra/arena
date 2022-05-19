import sys, platform, os, time
from pathlib import Path
import numpy as np
import cv2

from diambraArena.utils.splashScreen import DIAMBRASplashScreen
import grpc
import diambraArena.diambraEnvLib.diambra_pb2 as diambra_pb2
import diambraArena.diambraEnvLib.diambra_pb2_grpc as diambra_pb2_grpc

# DIAMBRA Env Gym
class diambraArenaLib:
    """Diambra Environment gym interface"""

    def __init__(self, envAddress):

        self.boolDataVarsList = ["roundDone", "stageDone", "gameDone", "epDone"];

        # Opening gRPC channel
        self.channel = grpc.insecure_channel(envAddress)
        self.stub = diambra_pb2_grpc.EnvServerStub(self.channel)

        # Splash Screen
        DIAMBRASplashScreen()

    # Transforming env kwargs to string
    def envSettingsToString(self, envSettings):

        maxCharToSelect = 3
        sep = ","
        endChar = "+"

        output = ""

        output += "gameId"+           sep+"2"+sep + envSettings["gameId"] + sep
        output += "continueGame"+     sep+"3"+sep + str(envSettings["continueGame"]) + sep
        output += "showFinal"+        sep+"0"+sep + str(int(envSettings["showFinal"])) + sep
        output += "stepRatio"+        sep+"1"+sep + str(envSettings["stepRatio"]) + sep
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

        output += "disableKeyboard"+  sep+"0"+sep + str(int(envSettings["disableKeyboard"])) + sep
        output += "disableJoystick"+  sep+"0"+sep + str(int(envSettings["disableJoystick"])) + sep
        output += "rank"+             sep+"1"+sep + str(envSettings["rank"]) + sep
        output += "recordConfigFile"+ sep+"2"+sep + envSettings["recordConfigFile"] + sep

        output += endChar

        return output

    # Send environment settings, retrieve environment info and int variables list
    def envInit(self, envSettings):
        envSettingsString = self.envSettingsToString(envSettings)
        response = self.stub.EnvInit(diambra_pb2.EnvSettings(settings=envSettingsString))
        self.intDataVarsList = response.intDataList.split(",")
        self.intDataVarsList.remove("")
        return response.envInfo.split(",")

    # Set frame size
    def setFrameSize(self, hwcDim):
        self.height = hwcDim[0]
        self.width  = hwcDim[1]
        self.nChan  = hwcDim[2]
        self.frameDim = hwcDim[0] * hwcDim[1] * hwcDim[2]

    # Read data
    def readData(self, intVar, doneConds):
        intVar = intVar.split(",")

        data = {"roundDone": doneConds.round,
                "stageDone": doneConds.stage,
                "gameDone": doneConds.game,
                "epDone": doneConds.episode}

        idx = 0
        for var in self.intDataVarsList:
            data[var] = int(intVar[idx])
            idx += 1

        return data

    # Read frame
    def readFrame(self, frame):
        frame = np.frombuffer(frame, dtype='uint8').reshape(self.height, self.width, self.nChan)
        return frame

    # Reset the environment
    def reset(self):
        response = self.stub.Reset(diambra_pb2.Empty())
        data = self.readData(response.intVar, response.doneConditions)
        frame = self.readFrame(response.frame)
        return frame, data, response.player

    # Step the environment (1P)
    def step1P(self, movP1, attP1):
        command = diambra_pb2.Command()
        command.P1.mov = movP1
        command.P1.att = attP1
        response = self.stub.Step1P(command)
        data = self.readData(response.intVar, response.doneConditions)
        frame = self.readFrame(response.frame)
        return frame, data

    # Step the environment (2P)
    def step2P(self, movP1, attP1, movP2, attP2):
        command = diambra_pb2.Command()
        command.P1.mov = movP1
        command.P1.att = attP1
        command.P2.mov = movP2
        command.P2.att = attP2
        response = self.stub.Step2P(command)
        data = self.readData(response.intVar, response.doneConditions)
        frame = self.readFrame(response.frame)
        return frame, data

    # Closing DIAMBRA Arena
    def close(self):
         self.stub.Close(diambra_pb2.Empty())
         self.channel.close() # self.stub.close()
