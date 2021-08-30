import gym
from gym import spaces
import numpy as np
import pickle, bz2, cv2
import numpy as np
from threading import Thread

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
def showGymObs(observation, charList, waitKey=1, viz=True):
    if type(observation) == dict:
        for k, v in observation.items():
            if k != "frame":
                if type(v) == dict:
                    for k2, v2 in v.items():
                        if "ownChar" in k2 or "oppChar" in k2:
                            print("observation[\"{}\"][\"{}\"]: {}".format(k,k2,charList[v2]))
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
        cv2.imshow("image", obs[:, :, ::-1]) #bgr 2 rgb
        cv2.waitKey(waitKey)

# Visualize Obs content
def showWrapObs(observation, nActionsStack, charList, waitKey=1, viz=True):
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
            cv2.imshow("image"+str(idx), obs[:,:,idx])

        cv2.waitKey(waitKey)
