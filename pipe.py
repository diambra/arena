import os, stat
from pathlib import Path
from queue import Queue
import threading
import numpy as np
import ctypes, ctypes.util
import time
import fcntl
from select import select

# DIAMBRA Env Command Dict
diambraEnvComm = {}
diambraEnvComm["step"]          = 0
diambraEnvComm["next_round"]    = 1
diambraEnvComm["next_stage"]    = 2
diambraEnvComm["new_game"]      = 3
diambraEnvComm["continue_game"] = 4
diambraEnvComm["start"]         = 5
diambraEnvComm["show_final"]    = 6
diambraEnvComm["close"]         = 7

# Env Data Class
class EnvData:

    def __init__(self):
        self.data = {}

        # Int values
        self.fighting     = (ctypes.c_int)(*[])
        self.reward       = (ctypes.c_int)(*[])
        self.ownHealth_1  = (ctypes.c_int)(*[])
        self.ownHealth_2  = (ctypes.c_int)(*[])
        self.oppHealth_1  = (ctypes.c_int)(*[])
        self.oppHealth_2  = (ctypes.c_int)(*[])
        self.ownPosition  = (ctypes.c_int)(*[])
        self.oppPosition  = (ctypes.c_int)(*[])
        self.ownWins      = (ctypes.c_int)(*[])
        self.oppWins      = (ctypes.c_int)(*[])
        self.ownCharacter = (ctypes.c_int)(*[])
        self.oppCharacter = (ctypes.c_int)(*[])
        self.stage        = (ctypes.c_int)(*[])

        # Bool values
        self.round_done = (ctypes.c_bool)(*[])
        self.stage_done = (ctypes.c_bool)(*[])
        self.game_done  = (ctypes.c_bool)(*[])
        self.ep_done    = (ctypes.c_bool)(*[])

        # Frame
        self.frame = np.asarray([-10 for x in range(1500000)], dtype='uint8')

    def setFrameSize(self, hwc_dim):
        self.height = hwc_dim[0]
        self.width  = hwc_dim[1]
        self.nChan  = hwc_dim[2]
        self.frameDim = hwc_dim[0] * hwc_dim[1] * hwc_dim[2]

    def processData(self):

        # Int values
        self.data["fighting"]     = self.fighting.value
        self.data["reward"]       = self.reward.value
        self.data["ownHealth"]    = [self.ownHealth_1.value, self.ownHealth_2.value]
        self.data["oppHealth"]    = [self.oppHealth_1.value, self.oppHealth_2.value]
        self.data["ownPosition"]  = self.ownPosition.value
        self.data["oppPosition"]  = self.oppPosition.value
        self.data["ownWins"]      = self.ownWins.value
        self.data["oppWins"]      = self.oppWins.value
        self.data["ownCharacter"] = self.ownCharacter.value
        self.data["oppCharacter"] = self.oppCharacter.value
        self.data["stage"]        = self.stage.value

        # Bool values
        self.data["round_done"] = self.round_done.value
        self.data["stage_done"] = self.stage_done.value
        self.data["game_done"]  = self.game_done.value
        self.data["ep_done"]    = self.ep_done.value

    def processFrame(self):

        return self.frame[:self.frameDim].reshape(self.height, self.width, self.nChan)

    def read_info(self):

        self.processData()

        return self.data

    def read_data(self):

        self.processData()

        return self.processFrame(), self.data

    def read_obs(self):

        return self.processFrame()

# A thread used for reading data from a pipe
# pipes don't have very good time out functionality,
# so this is used in combination with a queue
class StreamGobbler(threading.Thread):

    def __init__(self, pipe, queue):
        threading.Thread.__init__(self)
        self.pipe = pipe
        self.queue = queue
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            # Select permits to check if there is data available in the pipe
            # 1e-5 is the timeout constant
            if select([self.pipe.fileno()], [], [], 1e-5)[0]:
                line = self.pipe.readline()
                self.queue.put(line[:-1])

    def wait_for_cursor(self):
        new_line_count = 0
        while new_line_count != 3:
            line = self.pipe.readline()
            if line == b'\n':
                new_line_count += 1

    def stop(self):
        self._stop_event.set()

def delete_old_pipes(pipes_path):
    for the_file in os.listdir(pipes_path):
        file_path = os.path.join(pipes_path, the_file)
        try:
            os.unlink(file_path)
        except Exception as e:
            print(e)

def open_pipe(pipe_queue, path, mode):
    pipe_queue.put(open(path, mode + "b"))


# A class used for creating and interacting with a Linux FIFO pipe
class Pipe(object):

    def __init__(self, env_id, pipe_id, mode, pipes_path, tmpPath):
        self.pipeId = pipe_id + "Pipe"
        self.mode = mode
        self.pipes_path = Path(pipes_path)
        if not self.pipes_path.exists():
            self.pipes_path.mkdir()

        # Pipe path definition
        self.path = self.pipes_path.joinpath(Path(pipe_id + "-" + str(env_id) + ".pipe"))
        print("Pipe: "+str(self.path.absolute()))
        if self.path.exists():
            self.path.unlink()

        os.mkfifo(str(self.path.absolute()))

        # Signal file definition
        self.tmpPath = tmpPath
        if tmpPath.exists():
            tmpPath.unlink()

    # Opens the pipe in the toolkit and in the Lua engine
    # When a pipe is opened in read mode, it will block the thread until the same pipe is opened in write mode on a different thread
    def open(self):
        try:

            # Create pipe
            pipe_queue = Queue()
            open_thread = threading.Thread(target=open_pipe, args=[pipe_queue, str(self.path.absolute()), self.mode])
            open_thread.start()
            open_thread.join(timeout=3)
            self.fifo = pipe_queue.get(timeout=1)

            if self.mode == "r":
                self.read_queue = Queue()
                self.gobbler = StreamGobbler(self.fifo, self.read_queue)
                self.gobbler.start()
        except Exception as e:
            error = "Failed to open pipe '" + str(self.path.absolute()) + "'"
            raise IOError(error)

    def close(self):
        if self.mode == "r":
            # Stop the gobbler
            self.gobbler.stop()
            self.gobbler.join()

        self.fifo.close()

    def sendComm(self, commType, P1mov=0, P1att=0, P2mov=0, P2att=0):
        commString = str(commType) + "+" + str(P1mov) + "+" + str(P1att) + "+"\
                                         + str(P2mov) + "+" + str(P2att) + "+"
        self.writeln(commString);

    # Writes to the pipe
    def writeln(self, line):
        self.fifo.write(line.encode("utf-8")+b'\n')
        self.fifo.flush()

    # Reads to the pipe
    # timeout specifies how long the pipe should wait before there is likely
    # to be a problem on the DIAMBRA Env side
    def readln(self, timeout=None):
        try:
            return self.read_queue.get(timeout=timeout)
        except Exception as e:
            error = "Failed to read value from '" + self.pipeId + "'"
            raise IOError(error)

# A special implementation of a Linux FIFO pipe which is used for reading all
# of the frame data and memory address values from the emulator
class DataPipe(object):

    def __init__(self, env_id, pipe_id, mode, pipes_path, tmpPath):
        self.pipe = Pipe(env_id, pipe_id, mode, pipes_path, tmpPath)

    def open(self):
        self.pipe.open()

    def close(self):
        self.pipe.close()

    def read_envInfo(self, timeout=None):
        line = self.pipe.readln(timeout=timeout)
        line = line.decode('utf-8')
        return line.split(",")

    # Initialize frame dims inside read pipe
    def setFrameSize(self, hwc_dim):
        self.height = hwc_dim[0]
        self.width  = hwc_dim[1]
        self.nChan  = hwc_dim[2]

    def readFlag(self, timeout=None):
        line = self.pipe.readln(timeout=timeout)
        return
