import gym, os
from gym import spaces
import numpy as np
import pickle, bz2, cv2
import numpy as np
import json
from threading import Thread
import hashlib

# Save compressed pickle files in parallel
class parallelPickleWriter(Thread): # def class typr thread
   def __init__(self, savePath, to_save):
      Thread.__init__(self)   # thread init class (don't forget this)

      self.savePath = savePath
      self.to_save = to_save

   def run(self):      # run is a default Thread function
       outfile = bz2.BZ2File(self.savePath, 'w')
       print("Writing RL Trajectory to {} ...".format(self.savePath))
       pickle.dump(self.to_save, outfile)
       print("... done.")
       outfile.close()

# Recursive nested dict print
def nestedDictObsSpace(space, kList=[], level=0):
    for k in space.spaces:
        v = space[k]
        if isinstance(v, gym.spaces.dict.Dict):
            kList = kList[0:level]
            kList.append(k)
            nestedDictObsSpace(v, kList, level=level+1)
        else:
            kList = kList[0:level]
            outString = "observation_space"
            indentation = "    "*level
            for idK in kList:
                outString += "[\"{}\"]".format(idK)
            outString += "[\"{}\"]".format(k)
            outString = indentation+outString+":"
            print(outString, v)
            if isinstance(v, gym.spaces.MultiDiscrete):
                print(indentation+"Space size:", v.nvec.shape)
            elif isinstance(v, gym.spaces.Discrete):
                pass
            elif isinstance(v, gym.spaces.Box):
                print("        Space type =", v.dtype)
                print("        Space high bound =", v.high)
                print("        Space low bound =", v.low)
            print("")


# Print out environment spaces summary
def envSpacesSummary(env):

    # Printing out observation space description
    print("Observation space:")
    print("")
    if isinstance(env.observation_space, gym.spaces.dict.Dict):
        nestedDictObsSpace(env.observation_space)
    else:
        print("observation_space:", env.observation_space)
        print("    Space type =", env.observation_space.dtype)
        print("    Space high bound =", env.observation_space.high)
        print("    Space low bound =", env.observation_space.low)


    # Printing action spaces
    print("Action space:")
    print("")
    if isinstance(env.action_space, gym.spaces.dict.Dict):

        for k in env.action_space.spaces:
            print("action_space = ", env.action_space[k])
            print("  Space type = ", env.action_space[k].dtype)
            if type(env.action_space[k]) == gym.spaces.MultiDiscrete:
                print("    Space n = ", env.action_space[k].nvec)
            else:
                print("    Space n = ", env.action_space[k].n)
    else:
        print("action_space = ", env.action_space)
        print("  Space type = ", env.action_space.dtype)
        if type(env.action_space) == gym.spaces.MultiDiscrete:
            print("    Space n = ", env.action_space.nvec)
        else:
            print("    Space n = ", env.action_space.n)

# Utility to convert a Gym compliant Dict Space to a standard Dict
def gymObsDictSpaceToStandardDict(observationSpaceDict):

    standardDict = {}

    # Looping among all Dict items
    for k, v in observationSpaceDict.spaces.items():
        if isinstance(v, gym.spaces.dict.Dict):
            standardDict[k] = gymObsDictSpaceToStandardDict(v)
        else:
            standardDict[k] = v

    return standardDict

# Utility to create a Gym compliant Dict Space from the InternalObsDict
def standardDictToGymObsDict(obsStandardDict):

    for k, v in obsStandardDict.items():
        if isinstance(v, dict):
            obsStandardDict[k] = standardDictToGymObsDict(v)
        else:
            obsStandardDict[k] = v

    return spaces.Dict(obsStandardDict)


# Discrete to multidiscrete action conversion
def discreteToMultiDiscreteAction(action, nMoveActions):

    movAct = 0
    attAct = 0

    if action <= nMoveActions - 1:
        # Move action or no action
        movAct = action # For example, for DOA++ this can be 0 - 8
    else:
        # Attack action
        attAct = action - nMoveActions + 1 # For example, for DOA++ this can be 1 - 7

    return movAct, attAct

# Visualize Gym Obs content
def showGymObs(observation, charList, partnerList=[], waitKey=1, viz=True):
    if type(observation) == dict:
        for k, v in observation.items():
            if k != "frame":
                if type(v) == dict:
                    for k2, v2 in v.items():
                        if "ownChar" in k2 or "oppChar" in k2:
                            print("observation[\"{}\"][\"{}\"]: {}".format(k,k2,charList[v2]))
                        elif "ownPartner" in k2 or "oppPartner" in k2:
                            print("observation[\"{}\"][\"{}\"]: {}".format(k,k2,partnerList[v2]))
                        else:
                            print("observation[\"{}\"][\"{}\"]: {}".format(k,k2,v2))
                else:
                    print("observation[\"{}\"]: {}".format(k,v))
            else:
                print("observation[\"frame\"].shape:", observation["frame"].shape)

        if viz:
            obs = np.array(observation["frame"]).astype(np.float32)/255
    else:
        if viz:
            obs = np.array(observation).astype(np.float32)/255

    if viz:
        cv2.imshow("Frame", obs[:, :, ::-1]) #bgr 2 rgb
        cv2.waitKey(waitKey)

# Visualize Obs content
def showWrapObs(observation, nActionsStack, charList, partnerList=[], waitKey=1, viz=True):
    if type(observation) == dict:
        for k, v in observation.items():
            if k != "frame":
                if type(v) == dict:
                    for k2, v2 in v.items():
                        if type(v2) == dict:
                            for k3, v3 in v2.items():
                                print("observation[\"{}\"][\"{}\"][\"{}\"]:\n{}"\
                                      .format(k,k2,k3,np.reshape(v3, [nActionsStack,-1])))
                        elif "ownChar" in k2 or "oppChar" in k2:
                            print("observation[\"{}\"][\"{}\"]: {} / {}".format(k,k2,v2,\
                                                      charList[np.where(v2 == 1)[0][0]]))
                        elif "ownPartner" in k2 or "oppPartner" in k2:
                            print("observation[\"{}\"][\"{}\"]: {} / {}".format(k,k2,v2,\
                                                      partnerList[np.where(v2 == 1)[0][0]]))
                        else:
                            print("observation[\"{}\"][\"{}\"]: {}".format(k,k2,v2))
                else:
                    print("observation[\"{}\"]: {}".format(k,v))
            else:
                print("observation[\"frame\"].shape:", observation["frame"].shape)

        if viz:
            obs = np.array(observation["frame"]).astype(np.float32)
    else:
        if viz:
            obs = np.array(observation).astype(np.float32)

    if viz:
        for idx in range(obs.shape[2]):
            cv2.imshow("Frame-"+str(idx), obs[:,:,idx])

        cv2.waitKey(waitKey)

# List all available games
def availableGames(printOut=True, details=False):
    basePath = os.path.dirname(os.path.abspath(__file__))
    gamesFilePath = os.path.join(basePath, 'utils/integratedGames.json')
    gamesFile = open(gamesFilePath)
    gamesDict = json.load(gamesFile)

    if printOut:
        for k, v in gamesDict.items():
            print("")
            print(" Title: {} - GameId: {}".format(v["name"], v["id"]))
            print("   Difficulty levels: Min {} - Max {}".format(v["difficulty"][0], v["difficulty"][1]))
            if details:
                print("   SHA256 sum: {}".format(v["sha256"]))
                print("   Original ROM name: {}".format(v["original_rom_name"]))
                print("   Search keywords: {}".format(v["search_keywords"]))
                if v["notes"] != "":
                    print("   " + "\033[91m\033[4m\033[1m" + "Notes: {}".format(v["notes"]) + "\033[0m")
                print("   Characters list: {}".format(v["charList"]))
    else:
        return gamesDict

# List sha256 per game
def gameSha256(gameId=None):

    basePath = os.path.dirname(os.path.abspath(__file__))
    gamesFilePath = os.path.join(basePath, 'utils/integratedGames.json')
    gamesFile = open(gamesFilePath)
    gamesDict = json.load(gamesFile)

    if gameId == None:
        for k, v in gamesDict.items():
            print("")
            print(" Title: {}\n ID: {}\n SHA256: {}".format(v["name"], v["id"], v["sha256"]))
    else:
        v = gamesDict[gameId]
        print(" Title: {}\n ID: {}\n SHA256: {}".format(v["name"], v["id"], v["sha256"]))

# Check rom sha256
def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()

def checkGameSha256(path, gameId=None):

    basePath = os.path.dirname(os.path.abspath(__file__))
    gamesFilePath = os.path.join(basePath, 'utils/integratedGames.json')
    gamesFile = open(gamesFilePath)
    gamesDict = json.load(gamesFile)

    fileChecksum = sha256_checksum(path)

    if gameId == None:

        found = False
        for k, v in gamesDict.items():
            if fileChecksum == v["sha256"]:
                found = True
                print("Correct ROM file for {}, sha256 = {}".format(v["name"], v["sha256"]))
                break
        if found == False:
            print("ERROR: ROM file not valid")
    else:
        if fileChecksum == gamesDict[gameId]["sha256"]:
            print("Correct ROM file for {}, sha256 = {}".format(gamesDict[gameId]["name"], v["sha256"]))
        else:
            print("Expected  SHA256 Checksum: {}".format(gamesDict[gameId]["sha256"]))
            print("Retrieved SHA256 Checksum: {}".format(fileChecksum))
